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

@st.cache_resource
def get_gs_client():
    creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

@st.cache_data(ttl=1) # Đặt TTL cực thấp để luôn lấy data mới nhất
def load_all_data():
    client = get_gs_client(); sh = client.open_by_url(SPREADSHEET_URL)
    df_leads = pd.DataFrame(sh.get_worksheet(0).get_all_records())
    try:
        df_links = pd.DataFrame(sh.worksheet("Links").get_all_records())
    except:
        df_links = pd.DataFrame(columns=["Category", "Title", "URL"])
    return df_leads, df_links

st.set_page_config(page_title="TMC Master Tool", layout="wide")
df_leads, df_links = load_all_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛠️ Control Center")
    with st.expander("🔗 Thêm Link / Video Mới"):
        with st.form("add_link_form", clear_on_submit=True):
            cat = st.selectbox("Loại", ["Quick Link", "Sales Kit"]); tit = st.text_input("Tiêu đề"); url = st.text_input("URL")
            if st.form_submit_button("Thêm ngay"):
                if tit and url:
                    client = get_gs_client(); ws = client.open_by_url(SPREADSHEET_URL).worksheet("Links")
                    ws.append_row([cat, tit, url]); st.cache_data.clear(); st.rerun()

    with st.expander("🚀 Quick Links", expanded=True):
        q_links = df_links[df_links['Category'] == 'Quick Link']
        for _, l in q_links.iterrows(): st.markdown(f"**[{l['Title']}]({l['URL']})**")

    with st.expander("📚 Sales Kit (Video)"):
        videos = df_links[df_links['Category'] == 'Sales Kit']
        for _, v in videos.iterrows(): st.caption(v['Title']); st.video(v['URL'])

    st.divider()
    with st.expander("➕ Add New Lead", expanded=True):
        with st.form("new_lead"):
            n = st.text_input("Tên KH"); i = st.text_input("ID CRM"); p = st.text_input("Cell"); w = st.text_input("Work"); e = st.text_input("Email"); s = st.text_input("State")
            if st.form_submit_button("Lưu"):
                client = get_gs_client(); ws = client.open_by_url(SPREADSHEET_URL).get_worksheet(0)
                ws.append_row([n, i, p, w, e, s, "New", "", "", ""]); st.cache_data.clear(); st.rerun()

# --- MAIN VIEW ---
st.title("💼 Pipeline Processing")
c_filter, c_refresh = st.columns([3, 1])
with c_filter: days = st.slider("Hiện khách chưa đụng tới quá (ngày):", 0, 90, 0)
with c_refresh: 
    if st.button("🔄 Refresh Data"): st.cache_data.clear(); st.rerun()

df_leads['real_row'] = range(2, len(df_leads) + 2)
df_leads['Last_Interact_DT'] = pd.to_datetime(df_leads['Last_Interact'], errors='coerce')

if days == 0:
    df_display = df_leads
else:
    mask = (df_leads['Last_Interact_DT'].isna()) | ((datetime.now() - df_leads['Last_Interact_DT']).dt.days >= days)
    df_display = df_leads[mask]

# --- RENDER PIPELINE ---
for idx, row in df_display.iterrows():
    real_sheet_row = int(row['real_row'])
    with st.container():
        c_left, c_note, c_action = st.columns([4.0, 5.0, 1.0])
        with c_left:
            st.markdown(f"#### {row['Name KH']}")
            raw_id = str(row['ID']).strip().replace('#', '').lower()
            id_html = f"""<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;"><span style="background-color: #7d3c98; color: white; padding: 1px 4px; border-radius: 3px; font-weight: bold; font-size: 10px;">ID</span><span onclick="navigator.clipboard.writeText('{raw_id}'); alert('Copied ID: {raw_id}')" style="color: #e83e8c; cursor: pointer; font-family: monospace; font-weight: bold; background: #f8f9fa; border: 1px dashed #e83e8c; padding: 2px 6px; border-radius: 4px; white-space: nowrap;">📋 {raw_id}</span></div>"""
            st.markdown(id_html, unsafe_allow_html=True)
            p_cell = str(row['Cellphone']).strip(); p_work = str(row.get('Workphone','')).strip()
            n_enc = urllib.parse.quote(str(row['Name KH'])); m_enc = urllib.parse.quote(f"Chao {row['Name KH']}, em goi tu TMC...")
            comm_html = f"""<div style="display: flex; align-items: center; gap: 15px;"><span>📱 <a href="tel:{p_cell}" style="color:#28a745; font-weight:bold; text-decoration:none;">{p_cell}</a></span><a href="rcmobile://sms?number={p_cell}&body={m_enc}" target="_self">💬</a><a href="mailto:{row.get('Email','')}?subject=TMC&body={m_enc}" target="_self">📧</a><a href="https://calendar.google.com/calendar/r/eventedit?text=TMC_{n_enc}" target="_blank">📅</a></div>"""
            st.markdown(comm_html, unsafe_allow_html=True)
            if p_work and p_work not in ['0', '']: st.markdown(f'📞 Work: <a href="tel:{p_work}" style="color:#28a745; font-weight:bold; text-decoration:none;">{p_work}</a>', unsafe_allow_html=True)
            st.caption(f"📍 State: {row.get('State','N/A')}")

        with c_note:
            st.caption("📝 Ghi chú cộng dồn:")
            st.text_area("History", value=row.get('Note',''), height=80, disabled=True, key=f"h_{idx}")
            
            # Ô NHẬP NOTE MỚI - NHẤN ENTER LÀ LƯU
            new_n = st.text_input("Nhập note mới rồi nhấn Enter...", key=f"in_{idx}", label_visibility="collapsed")
            if new_n:
                client = get_gs_client(); ws_u = client.open_by_url(SPREADSHEET_URL).get_worksheet(0)
                now = datetime.now()
                now_str = now.strftime("%Y-%m-%d %H:%M:%S")
                new_history = f"[{now.strftime('%m/%d')}]: {new_n}\n{row.get('Note','')}"
                
                # Ghi lên Google Sheets
                ws_u.update(range_name=f'H{real_sheet_row}:I{real_sheet_row}', 
                          values=[[now_str, new_history[:5000]]])
                
                # XÓA CACHE VÀ LÀM MỚI NGAY LẬP TỨC
                st.cache_data.clear()
                st.rerun()

        with c_action:
            with st.popover("⋮"):
                st.write("✏️ EDIT LEAD")
                e_name = st.text_input("Name", value=row['Name KH'], key=f"en_{idx}"); e_id = st.text_input("ID", value=row['ID'], key=f"ei_{idx}"); e_cell = st.text_input("Cell", value=row['Cellphone'], key=f"ec_{idx}"); e_work = st.text_input("Work", value=row.get('Workphone',''), key=f"ew_{idx}"); e_email = st.text_input("Email", value=row.get('Email',''), key=f"ee_{idx}"); e_state = st.text_input("State", value=row.get('State',''), key=f"es_{idx}")
                if st.button("Save", key=f"sv_{idx}"):
                    client = get_gs_client(); ws_e = client.open_by_url(SPREADSHEET_URL).get_worksheet(0)
                    ws_e.update(range_name=f'A{real_sheet_row}:F{real_sheet_row}', 
                              values=[[e_name, e_id, e_cell, e_work, e_email, e_state]])
                    st.cache_data.clear(); st.rerun()
        st.divider()
