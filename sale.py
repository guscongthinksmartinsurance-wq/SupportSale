import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime

# --- 1. XÁC THỰC (GIỮ NGUYÊN) ---
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

def load_all_data():
    client = get_gs_client(); sh = client.open_by_url(SPREADSHEET_URL)
    df_leads = pd.DataFrame(sh.get_worksheet(0).get_all_records())
    try:
        df_links = pd.DataFrame(sh.worksheet("Links").get_all_records())
    except:
        df_links = pd.DataFrame(columns=["Category", "Title", "URL"])
    return df_leads, df_links

# Hàm xử lý Lưu Note: Ép App ghi nhận vào bộ nhớ TRƯỚC khi ghi Sheet
def save_note_final(idx, r_row, old_h, key):
    new_msg = st.session_state[key]
    if new_msg:
        now = datetime.now()
        new_h = f"[{now.strftime('%m/%d')}]: {new_msg}\n{old_h}"
        
        # CẬP NHẬT NGAY VÀO BỘ NHỚ APP (Chìa khóa nằm ở đây)
        st.session_state[f"force_h_{idx}"] = new_h
        
        # Ghi vào Sheet (Chạy ngầm, App không thèm đợi nó)
        client = get_gs_client(); ws = client.open_by_url(SPREADSHEET_URL).get_worksheet(0)
        ws.update_cell(r_row, 8, now.strftime("%Y-%m-%d %H:%M:%S"))
        ws.update_cell(r_row, 9, new_h[:5000])
        st.toast("✅ Đã ghi nhận Note!")

# --- 3. GIAO DIỆN ---
st.set_page_config(page_title="TMC CRM Pro", layout="wide")

# Chỉ load dữ liệu 1 lần khi bắt đầu hoặc nhấn Refresh
if 'main_df' not in st.session_state or st.sidebar.button("🔄 Sync Google Sheet"):
    leads, links = load_all_data()
    st.session_state.main_df = leads
    st.session_state.links_df = links

with st.sidebar:
    st.title("🛠️ Control Center")
    with st.expander("🚀 Quick Links", expanded=True):
        for _, l in st.session_state.links_df[st.session_state.links_df['Category'] == 'Quick Link'].iterrows():
            st.markdown(f"**[{l['Title']}]({l['URL']})**")
    with st.expander("📚 Sales Kit", expanded=True):
        for _, v in st.session_state.links_df[st.session_state.links_df['Category'] == 'Sales Kit'].iterrows():
            st.caption(v['Title']); st.video(v['URL'])
    st.divider()
    with st.expander("➕ Add New Lead"):
        with st.form("add_l"):
            n = st.text_input("Name"); i = st.text_input("ID"); p = st.text_input("Cell"); w = st.text_input("Work"); e = st.text_input("Email"); s = st.text_input("State")
            if st.form_submit_button("Save"):
                ws = get_gs_client().open_by_url(SPREADSHEET_URL).get_worksheet(0)
                ws.append_row([n, i, p, w, e, s, "New", "", "", ""]); st.rerun()

# --- MAIN VIEW ---
df = st.session_state.main_df
df['real_row'] = range(2, len(df) + 2)
df['Last_Interact_DT'] = pd.to_datetime(df['Last_Interact'], errors='coerce')

days = st.slider("Hiện khách chưa đụng tới quá (ngày):", 0, 90, 0)
df_disp = df if days == 0 else df[(df['Last_Interact_DT'].isna()) | ((datetime.now() - df['Last_Interact_DT']).dt.days >= days)]

for idx, row in df_disp.iterrows():
    r_row = int(row['real_row'])
    # Lấy history từ bộ nhớ App (nếu có) hoặc từ dữ liệu gốc
    h_val = st.session_state.get(f"force_h_{idx}", row.get('Note',''))
    
    with st.container():
        c1, c2, c3 = st.columns([4, 5, 1])
        with c1:
            st.markdown(f"#### {row['Name KH']}")
            rid = str(row['ID']).strip().replace('#', '').lower()
            st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;"><span style="background:#7d3c98;color:white;padding:1px 4px;border-radius:3px;font-size:10px;">ID</span><span onclick="navigator.clipboard.writeText('{rid}');alert('Copied ID: {rid}')" style="color:#e83e8c;cursor:pointer;font-family:monospace;font-weight:bold;background:#f8f9fa;border:1px dashed #e83e8c;padding:2px 6px;border-radius:4px;">📋 {rid}</span></div>""", unsafe_allow_html=True)
            p_c = str(row['Cellphone']).strip(); p_w = str(row.get('Workphone','')).strip(); n_e = urllib.parse.quote(str(row['Name KH'])); m_e = urllib.parse.quote(f"Chao {row['Name KH']}...")
            st.markdown(f"""<div style="display:flex;gap:15px;align-items:center;"><span>📱 <a href="tel:{p_c}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_c}</a></span><a href="rcmobile://sms?number={p_c}&body={m_e}">💬</a><a href="mailto:{row.get('Email','')}?body={m_e}">📧</a><a href="https://calendar.google.com/calendar/r/eventedit?text=TMC_{n_e}" target="_blank">📅</a></div>""", unsafe_allow_html=True)
            if p_w and p_w not in ['0', '']:
                st.markdown(f'📞 Work: <a href="tel:{p_w}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_w}</a>', unsafe_allow_html=True)
        
        with c2:
            st.text_area("History", value=h_val, height=100, disabled=True, key=f"area_{idx}", label_visibility="collapsed")
            st.text_input("Ghi chú mới & Enter", key=f"in_{idx}", on_change=save_note_final, args=(idx, r_row, h_val, f"in_{idx}"), label_visibility="collapsed")

        with c3:
            with st.popover("⋮"):
                en = st.text_input("Name", value=row['Name KH'], key=f"en_{idx}"); ei = st.text_input("ID", value=row['ID'], key=f"ei_{idx}"); ec = st.text_input("Cell", value=row['Cellphone'], key=f"ec_{idx}"); ew = st.text_input("Work", value=row.get('Workphone',''), key=f"ew_{idx}"); ee = st.text_input("Email", value=row.get('Email',''), key=f"ee_{idx}"); es = st.text_input("State", value=row.get('State',''), key=f"es_{idx}")
                if st.button("Save Edit", key=f"sv_{idx}"):
                    ws = get_gs_client().open_by_url(SPREADSHEET_URL).get_worksheet(0)
                    ws.update_cell(r_row, 1, en); ws.update_cell(r_row, 2, ei); ws.update_cell(r_row, 3, ec); ws.update_cell(r_row, 4, ew); ws.update_cell(r_row, 5, ee); ws.update_cell(r_row, 6, es); st.rerun()
        st.divider()
