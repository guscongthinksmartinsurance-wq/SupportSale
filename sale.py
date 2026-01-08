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

def load_data():
    client = get_gs_client(); sh = client.open_by_url(SPREADSHEET_URL)
    ws = sh.get_worksheet(0).get_all_records()
    df = pd.DataFrame(ws); df.columns = [str(col).strip() for col in df.columns]
    return df

# --- 3. GIAO DIỆN ---
st.set_page_config(page_title="TMC Pipeline Pro", layout="wide")

with st.sidebar:
    st.header("➕ Add Lead")
    with st.form("add_form", clear_on_submit=True):
        f_name = st.text_input("Name KH"); f_id = st.text_input("CRM Lead ID")
        f_cell = st.text_input("Cellphone"); f_work = st.text_input("Workphone")
        f_email = st.text_input("Email"); f_state = st.text_input("State")
        if st.form_submit_button("Save"):
            client = get_gs_client(); ws = client.open_by_url(SPREADSHEET_URL).get_worksheet(0)
            ws.append_row([f_name, f_id, f_cell, f_work, f_email, f_state, "New", "", "", ""])
            st.cache_data.clear(); st.rerun()

df = load_data()
c_filter, c_refresh = st.columns([3, 1])
with c_filter: days = st.slider("Chưa tương tác quá (ngày):", 1, 60, 1)
with c_refresh: 
    if st.button("🔄 Refresh"): st.cache_data.clear(); st.rerun()

# --- 4. RENDER PIPELINE ---
for index, row in df.iterrows():
    sheet_row = index + 2
    with st.container():
        c_left, c_note, c_action = st.columns([4.0, 5.0, 1.0])
        
        with c_left:
            st.markdown(f"#### {row['Name KH']}")
            
            # --- DÒNG ID (FIX ĐỒNG NHẤT NÚT COPY) ---
            raw_id = str(row['ID']).strip().replace('#', '').lower()
            lead_url = f"https://www.7xcrm.com/lead-management/lead-details/{raw_id}/overview"
            
            c_id_label, c_id_link, c_id_copy = st.columns([0.5, 1.2, 2.3])
            c_id_label.markdown("**🆔 ID:**")
            c_id_link.markdown(f"[Link CRM]({lead_url})")
            # Nút Copy đồng nhất cho mọi dòng
            if c_id_copy.button(f"📋 {raw_id if raw_id else 'No ID'}", key=f"cp_{index}", help="Nhấn để hiện mã copy"):
                st.info(f"Mã của {row['Name KH']}:")
                st.code(raw_id)
            
            # --- DÒNG LIÊN LẠC ---
            p = str(row['Cellphone']).strip()
            n_enc = urllib.parse.quote(str(row['Name KH']))
            m_enc = urllib.parse.quote(f"Chao {row['Name KH']}, em goi tu TMC...")
            comm_html = f"""
            <div style="display: flex; align-items: center; gap: 15px; margin-top: 5px;">
                <span>📱 <a href="tel:{p}" style="color:#28a745; font-weight:bold; text-decoration:none;">{p}</a></span>
                <a href="rcmobile://sms?number={p}&body={m_enc}" target="_self">💬</a>
                <a href="mailto:{row.get('Email','')}?subject=TMC&body={m_enc}" target="_self">📧</a>
                <a href="https://calendar.google.com/calendar/r/eventedit?text=TMC_{n_enc}" target="_blank">📅</a>
            </div>
            """
            st.markdown(comm_html, unsafe_allow_html=True)
            st.caption(f"📍 State: {row.get('State','N/A')}")

        with c_note:
            st.caption("📝 Ghi chú & Xử lý:")
            st.text_area("History", value=row.get('Note',''), height=65, disabled=True, key=f"h_{index}")
            c_in, c_btn = st.columns([3, 1])
            new_n = c_in.text_input("Note mới...", key=f"in_{index}", label_visibility="collapsed")
            if c_btn.button("XONG ✅", key=f"done_{index}"):
                client = get_gs_client(); ws_u = client.open_by_url(SPREADSHEET_URL).get_worksheet(0)
                now = datetime.now()
                ws_u.update_cell(sheet_row, 8, now.strftime("%Y-%m-%d %H:%M:%S"))
                if new_n:
                    combined = f"[{now.strftime('%m/%d')}]: {new_n}\n{row.get('Note','')}"
                    ws_u.update_cell(sheet_row, 9, combined[:5000])
                st.cache_data.clear(); st.rerun()

        with c_action:
            with st.popover("⋮"):
                if st.button("Edit", key=f"ed_{index}"): st.write("Dùng sidebar để sửa")
        st.divider()

st.subheader("🎬 Video Sales Kit")
v1, v2 = st.columns(2)
v1.video("https://www.youtube.com/watch?v=HHfsKefOwA4")
v2.video("https://www.youtube.com/watch?v=OJruIuIs_Ag")
