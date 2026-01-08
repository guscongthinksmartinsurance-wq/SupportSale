import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime

# --- 1. XÁC THỰC ---
PK_RAW = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC+8HRC1BZcrafY
yI+MlMqX3tJ0Rt5FuDdJlew0kZggLJpr0z1OshwSOJ8++8lgyPkvkZumb3CLZkB1
3PVprn3Qw7YkPcBBosq6J4VTNWazgx0OMZUi/sJJbWoKu3Z2BAk/7nFkBqESO7/F
2OSandv+8FFen8B9Ie5SBXRHLMOMMbkkqPKBU76tT1yhMFtDRZWNWFb0wJoJ2XRm
WCGj6taTMZy0aOw+jVB4DjTAuJN3gUv5tALbGX/C9HE39vl098stNRrKmQ4CcvYs
ZAvqyye9GoI1KEI6OEXCA86aFYVfjDeIh3VLlQC5feWqPWHSv3mOktZHoVt+b1Gu
sPKM49GjAgMBAAECggEAG4KklZ5eLHM+zD61ZBFqETCjDOrLCquMl7cYpchWbUhP
5Xo1ipmh7sQmuZnofV/ne0GU9gl3YzZT0keIOnZQHVydaSJWiX5tjB22mXMHvZSG
Aq4FKVogXxj7Htm8qytQs9vkjX9hBLIEIvrpkRdug5BXgPUudDkHz9yGUNzzvcaK
OpGr3fVwLwal/FYx0XLy5Hpdl5zkVsiuK4Q7IBvketKZg3Sy9xYnhPqOdkvIoIr6
cVXVE+hCVYt6+FtLmuOBQO5EfTiXY+S/CP/qUsNYz0J6pPsTxQAdRYHwoVFP117t
hlQ/dnWT1hg8wDWXZR/EwLI8H4mP2vPNqmG9f0CZiQKBgQD0NGkEqISRa1ac32Lt
2U1HSkjoGa0d2ZATdfMWJyz/IUFiDEhgY02eauPm2QJCcMXg3qJieRnsNKh5fy7I
2PHSXzW+AQCUcx0g/HIEyLccCRoTZJcrVuvZ5UAxpepAeQDmCHyNfp1I7SjnBd0J
PbLBOLJFHziXF/x/uY0DRVI9CwKBgQDIKWq9ZSutX7euZH5TVC27r5Eh4wwcsoCi
EanEwf9QOIcYZmBGIa5gDJgGqQKfseXA2c3ZpjcYGHY4cPhXQ/LhrisHEyyHDFsp
f01RJIAK0bHI/RBwUB0QVKwhfqfsYG4YVCRJlgnqUNLgnhq1GCESD9JPsJlCSrkF
p3R8cvwsyQKBgQDVjYuU/kVH4eURNCyQMOpqgGS3S9Te+KYMzqWwZrvrtEo4EuOs
Hsr+0RzRgE6AiZwRpL++e4aW0AnQjc785vK59HbL3JaEOxJrCTgwRNIUG0WJVfr4
dH+1wcvcXuo2TVrizuMU3XdwEa0mMjN0ZFcQr6L93WqgfuJZU4skJBfhtwKBgGp4
xYObhmFB8iX85MmUlIMqv8vDx5SYSx5qwOCdxR66AvqysnF7xxLmgBPC4VdrPOiZ
swschF/32yLozOE2jsMHb3Hi/COWKgPn6IvKG6Ylpylfm9fydZNTRwDGK7LsFIQy
dd8CxaFzfsjmsRQ1kpnV+qxTJyMBNmxQiAEO9R8pAoGBAJDB8lvIXnAkRQZ/cWDg
zoHC+8FyTIEkkcD7/7KZD25DjD7FW247Mx7OfMGwqs9Wj67+ec5mTHco1TFrs15F
MWcgHed08BRLsxm5PETmUQhciTQ3yHuFkIqbND9V8XRA+YuBMCcJcpoU+WrExB3N
UvNQNXmUy4VQRI8i9CHtAZdp
-----END PRIVATE KEY-----"""

info = {
    "type": "service_account", "project_id": "caramel-hallway-481517-q8",
    "private_key": PK_RAW.strip(), "client_email": "tmc-assistant@caramel-hallway-481517-q8.iam.gserviceaccount.com",
    "token_uri": "https://oauth2.googleapis.com/token",
}
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1QSMUSOkeazaX1bRpOQ4DVHqu0_j-uz4maG3l7Lj1c1M/edit"

# --- 2. HÀM DỮ LIỆU ---
@st.cache_resource
def get_gs_client():
    creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

@st.cache_data(ttl=5) # Tăng nhẹ TTL để ổn định
def load_all_data():
    client = get_gs_client(); sh = client.open_by_url(SPREADSHEET_URL)
    df_leads = pd.DataFrame(sh.get_worksheet(0).get_all_records())
    try:
        df_links = pd.DataFrame(sh.worksheet("Links").get_all_records())
    except:
        df_links = pd.DataFrame(columns=["Category", "Title", "URL"])
    return df_leads, df_links

# Cơ chế xử lý Note kiểu CRM (Ghi đè hiển thị trước)
def handle_note_crm(r_idx, old_note, k_name, lead_name):
    new_text = st.session_state[k_name]
    if new_text:
        now = datetime.now()
        ts = now.strftime("%Y-%m-%d %H:%M:%S")
        combined = f"[{now.strftime('%m/%d')}]: {new_text}\n{old_note}"
        
        # 1. Ghi vào Google Sheet (Chạy ngầm)
        try:
            client = get_gs_client()
            ws = client.open_by_url(SPREADSHEET_URL).get_worksheet(0)
            ws.update_cell(r_idx, 8, ts)
            ws.update_cell(r_idx, 9, combined[:5000])
            
            # 2. ÉP GIAO DIỆN CẬP NHẬT NGAY (Lưu vào session_state của Streamlit)
            st.session_state[f"temp_note_{lead_name}"] = combined
            st.cache_data.clear()
            st.toast("✅ Đã lưu Note thành công!")
        except Exception as e:
            st.error(f"Lỗi khi ghi dữ liệu: {e}")

# --- 3. GIAO DIỆN ---
st.set_page_config(page_title="TMC Master CRM", layout="wide")
df_leads, df_links = load_all_data()

with st.sidebar:
    st.title("🛠️ Control Center")
    with st.expander("🚀 Quick Links", expanded=True):
        q_links = df_links[df_links['Category'] == 'Quick Link']
        for _, l in q_links.iterrows(): st.markdown(f"**[{l['Title']}]({l['URL']})**")
    with st.expander("📚 Sales Kit (Video)", expanded=True):
        videos = df_links[df_links['Category'] == 'Sales Kit']
        for _, v in videos.iterrows(): st.caption(v['Title']); st.video(v['URL'])
    st.divider()
    with st.expander("➕ Add New Lead"):
        with st.form("new_l"):
            n = st.text_input("Tên"); i = st.text_input("ID"); p = st.text_input("Cell")
            if st.form_submit_button("Lưu"):
                ws = get_gs_client().open_by_url(SPREADSHEET_URL).get_worksheet(0)
                ws.append_row([n, i, p, "", "", "", "New", "", "", ""]); st.cache_data.clear(); st.rerun()

# --- MAIN VIEW ---
st.title("💼 Pipeline Processing")
c_filter, c_refresh = st.columns([3, 1])
with c_filter: days = st.slider("Hiện khách chưa đụng tới quá (ngày):", 0, 90, 0)
with c_refresh: 
    if st.button("🔄 Refresh Data"): st.cache_data.clear(); st.rerun()

df_leads['real_row'] = range(2, len(df_leads) + 2)
df_leads['Last_Interact_DT'] = pd.to_datetime(df_leads['Last_Interact'], errors='coerce')
df_disp = df_leads if days == 0 else df_leads[(df_leads['Last_Interact_DT'].isna()) | ((datetime.now() - df_leads['Last_Interact_DT']).dt.days >= days)]

# --- RENDER PIPELINE ---
for idx, row in df_disp.iterrows():
    r_row = int(row['real_row'])
    l_name = row['Name KH']
    k_in = f"in_{idx}"
    
    # Kiểm tra xem có note tạm thời vừa gõ không
    current_history = st.session_state.get(f"temp_note_{l_name}", row.get('Note',''))
    
    with st.container():
        c_info, c_note, c_action = st.columns([4, 5, 1])
        with c_info:
            st.markdown(f"#### {l_name}")
            rid = str(row['ID']).strip().replace('#', '').lower()
            st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;"><span style="background:#7d3c98;color:white;padding:1px 4px;border-radius:3px;font-size:10px;">ID</span><span onclick="navigator.clipboard.writeText('{rid}');alert('Copied ID: {rid}')" style="color:#e83e8c;cursor:pointer;font-family:monospace;font-weight:bold;background:#f8f9fa;border:1px dashed #e83e8c;padding:2px 6px;border-radius:4px;">📋 {rid}</span></div>""", unsafe_allow_html=True)
            p = str(row['Cellphone']).strip(); n_e = urllib.parse.quote(str(l_name)); m_e = urllib.parse.quote(f"Chao {l_name}...")
            st.markdown(f"""<div style="display:flex;gap:15px;"><span>📱 <a href="tel:{p}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p}</a></span><a href="rcmobile://sms?number={p}&body={m_e}">💬</a><a href="mailto:{row.get('Email','')}?body={m_e}">📧</a><a href="https://calendar.google.com/calendar/r/eventedit?text=TMC_{n_e}" target="_blank">📅</a></div>""", unsafe_allow_html=True)
            st.caption(f"📍 State: {row.get('State','N/A')}")
        
        with c_note:
            # Dùng History từ Session State để đảm bảo nó hiện ngay lập tức
            st.text_area("History", value=current_history, height=100, disabled=True, key=f"h_{idx}", label_visibility="collapsed")
            st.text_input("Ghi chú mới & Enter", key=k_in, on_change=handle_note_crm, args=(r_row, current_history, k_in, l_name), placeholder="Nhập note...")

        with c_action:
            with st.popover("⋮"):
                st.write("✏️ EDIT")
                en = st.text_input("Name", value=row['Name KH'], key=f"en_{idx}")
                ei = st.text_input("ID", value=row['ID'], key=f"ei_{idx}")
                ec = st.text_input("Cell", value=row['Cellphone'], key=f"ec_{idx}")
                if st.button("Save", key=f"sv_{idx}"):
                    ws = get_gs_client().open_by_url(SPREADSHEET_URL).get_worksheet(0)
                    ws.update_cell(r_row, 1, en); ws.update_cell(r_row, 2, ei); ws.update_cell(r_row, 3, ec)
                    st.cache_data.clear(); st.rerun()
        st.divider()
