import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime

# --- 1. XÁC THỰC (Giữ nguyên Keys đã chạy tốt) ---
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
    "type": "service_account",
    "project_id": "caramel-hallway-481517-q8",
    "private_key": PK_RAW.strip(),
    "client_email": "tmc-assistant@caramel-hallway-481517-q8.iam.gserviceaccount.com",
    "token_uri": "https://oauth2.googleapis.com/token",
}

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1QSMUSOkeazaX1bRpOQ4DVHqu0_j-uz4maG3l7Lj1c1M/edit"

# --- 2. HÀM XỬ LÝ DỮ LIỆU ---
@st.cache_resource
def get_gs_client():
    creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

@st.cache_data(ttl=300)
def load_data():
    client = get_gs_client()
    sh = client.open_by_url(SPREADSHEET_URL)
    data = sh.get_worksheet(0).get_all_records()
    df = pd.DataFrame(data)
    df.columns = [str(col).strip() for col in df.columns]
    return df

# --- 3. GIAO DIỆN ---
st.set_page_config(page_title="TMC Final V2.1", layout="wide")
st.title("💼 TMC Sales Pipeline - Bản Dứt Điểm Link")

# Sidebar thêm khách
with st.sidebar:
    st.header("➕ Add Lead")
    with st.form("add_form", clear_on_submit=True):
        f_name = st.text_input("Name KH")
        f_id = st.text_input("CRM Lead ID")
        f_cell = st.text_input("Cellphone")
        f_work = st.text_input("Workphone")
        f_email = st.text_input("Email")
        f_state = st.text_input("State")
        if st.form_submit_button("Save"):
            client = get_gs_client()
            ws = client.open_by_url(SPREADSHEET_URL).get_worksheet(0)
            ws.append_row([f_name, f_id, f_cell, f_work, f_email, f_state, "New", "", "", ""])
            st.cache_data.clear()
            st.rerun()

df = load_data()
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# --- 4. HIỂN THỊ DANH SÁCH ---
for index, row in df.iterrows():
    sheet_row = index + 2
    with st.container():
        c_info, c_comm, c_note, c_action = st.columns([2.5, 3.5, 3.2, 0.8])
        
        with c_info:
            st.markdown(f"#### {row['Name KH']}")
            
            # XỬ LÝ ID TUYỆT ĐỐI: Xóa #, Xóa khoảng trắng, Chuyển về CHỮ THƯỜNG
            raw_id = str(row['ID']).strip()
            clean_id = raw_id.replace('#', '').lower() 
            
            lead_url = f"https://www.7xcrm.com/lead-management/lead-details/{clean_id}/overview"
            
            st.markdown(f"🆔 ID: [#{clean_id[:8]}...]({lead_url})", help="Mở 7xCRM")
            st.caption(f"📍 State: {row.get('State','N/A')}")

        with c_comm:
            p = str(row['Cellphone']).strip()
            w = str(row['Workphone']).strip()
            m_enc = urllib.parse.quote(f"Chao {row['Name KH']}, em goi tu TMC...")
            st.write(f"📱 {p} | 📞 {w}")
            b1, b2, b3 = st.columns(3)
            b1.markdown(f'<a href="tel:{p}" target="_self" style="text-decoration:none;"><div style="background-color:#28a745;color:white;padding:5px;border-radius:5px;text-align:center;font-size:12px;">📞 GỌI</div></a>', unsafe_allow_html=True)
            b2.markdown(f'<a href="rcmobile://sms?number={p}&body={m_enc}" target="_self" style="text-decoration:none;"><div style="background-color:#17a2b8;color:white;padding:5px;border-radius:5px;text-align:center;font-size:12px;">💬 SMS</div></a>', unsafe_allow_html=True)
            if row.get('Email'):
                b3.markdown(f'<a href="mailto:{row["Email"]}?subject=TMC&body={m_enc}" target="_self" style="text-decoration:none;"><div style="background-color:#fd7e14;color:white;padding:5px;border-radius:5px;text-align:center;font-size:12px;">📧 MAIL</div></a>', unsafe_allow_html=True)

        with c_note:
            st.caption("📝 Ghi chú cộng dồn:")
            st.text_area("Lịch sử", value=row.get('Note',''), height=70, disabled=True, key=f"h_{index}")
            new_n = st.text_input("Note mới...", key=f"in_{index}")
            if st.button("XONG ✅", key=f"done_{index}", use_container_width=True):
                client = get_gs_client()
                ws_u = client.open_by_url(SPREADSHEET_URL).get_worksheet(0)
                now = datetime.now()
                ws_u.update_cell(sheet_row, 8, now.strftime("%Y-%m-%d %H:%M:%S"))
                if new_n:
                    combined = f"[{now.strftime('%m/%d')}]: {new_n}\n{row.get('Note','')}"
                    ws_u.update_cell(sheet_row, 9, combined[:5000])
                st.cache_data.clear()
                st.rerun()

        with c_action:
            with st.popover("⋮"):
                if st.button("Edit", key=f"ed_{index}"): st.write("Tính năng đang mở...")
        st.divider()
