import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime

# --- 1. CẤU HÌNH KẾT NỐI (GIỮ NGUYÊN) ---
private_key = """-----BEGIN PRIVATE KEY-----
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
    "private_key": private_key.replace("\\n", "\n"),
    "client_email": "tmc-assistant@caramel-hallway-481517-q8.iam.gserviceaccount.com",
}

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1QSMUSOkeazaX1bRpOQ4DVHqu0_j-uz4maG3l7Lj1c1M/edit?gid=0#gid=0"
creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])

@st.cache_data(ttl=600)
def load_data_final():
    client = gspread.authorize(creds)
    sh = client.open_by_url(SPREADSHEET_URL)
    ws = sh.get_worksheet(0)
    df = pd.DataFrame(ws.get_all_records())
    df.columns = [str(col).strip() for col in df.columns]
    return df, ws

# --- 2. GIAO DIỆN CHUẨN ---
st.set_page_config(page_title="TMC Sales Assistant", layout="wide")
st.title("🚀 TMC Sales Assistant Tool")

# Sidebar: Thêm khách đầy đủ các cột
with st.sidebar:
    st.header("➕ Thêm Khách Hàng Mới")
    n_name = st.text_input("Name KH")
    n_id = st.text_input("ID")
    n_cell = st.text_input("Cellphone")
    n_work = st.text_input("Workphone")
    n_status = st.selectbox("Status", ["New", "Potential", "Follow-up", "Hot"])
    n_sales = st.text_input("Sales Assigned")
    
    if st.button("Lưu khách hàng"):
        client = gspread.authorize(creds)
        ws_append = client.open_by_url(SPREADSHEET_URL).get_worksheet(0)
        ws_append.append_row([n_name, n_id, n_cell, n_work, n_status, "", n_sales])
        st.cache_data.clear()
        st.success("Đã thêm khách mới!")
        st.rerun()

df, ws = load_data_final()

# Thanh trượt & Refresh
c_filter, c_refresh = st.columns([3, 1])
with c_filter:
    days = st.slider("Chưa tương tác quá (ngày):", 1, 60, 1)
with c_refresh:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

df['Last_Interact_DT'] = pd.to_datetime(df['Last_Interact'], errors='coerce')
mask = (df['Last_Interact_DT'].isna()) | ((datetime.now() - df['Last_Interact_DT']).dt.days >= days)
df_display = df[mask]

st.subheader(f"📋 Danh sách ({len(df_display)} khách)")

# --- HIỂN THỊ DANH SÁCH ---
for index, row in df_display.iterrows():
    with st.container():
        col_info, col_call, col_sms, col_mail, col_cal, col_done = st.columns([2.5, 1, 1, 1, 1, 1])
        
        with col_info:
            st.markdown(f"**{row['Name KH']}**")
            st.caption(f"ID: {row['ID']} | 📞 {row['Cellphone']} | {row['Status']}")

        p = str(row['Cellphone']).strip()
        n_enc = urllib.parse.quote(str(row['Name KH']))
        m_enc = urllib.parse.quote(f"Chao {row['Name KH']}, em goi tu TMC...")

        # NÚT GỌI & SMS: Dùng lại HTML <a> tag (Cách anh đã bật được Call thành công)
        # Sửa lại link SMS theo chuẩn Deep Link của RingCentral
        col_call.markdown(f'<a href="rcapp://call?number={p}" target="_self" style="text-decoration:none;"><div style="background-color:#28a745;color:white;padding:10px;border-radius:5px;text-align:center;font-weight:bold;cursor:pointer;">📞 GỌI</div></a>', unsafe_allow_html=True)
        
        col_sms.markdown(f'<a href="rcapp://sms?number={p}&body={m_enc}" target="_self" style="text-decoration:none;"><div style="background-color:#17a2b8;color:white;padding:10px;border-radius:5px;text-align:center;font-weight:bold;cursor:pointer;">💬 SMS</div></a>', unsafe_allow_html=True)
        
        col_mail.markdown(f'<a href="mailto:?subject=TMC_Support&body={m_enc}" target="_self" style="text-decoration:none;"><div style="background-color:#fd7e14;color:white;padding:10px;border-radius:5px;text-align:center;font-weight:bold;cursor:pointer;">📧 MAIL</div></a>', unsafe_allow_html=True)
        
        gcal = f"https://calendar.google.com/calendar/r/eventedit?text=Hen_TMC_{n_enc}"
        col_cal.markdown(f'<a href="{gcal}" target="_blank" style="text-decoration:none;"><div style="background-color:#f4b400;color:white;padding:10px;border-radius:5px;text-align:center;font-weight:bold;cursor:pointer;">📅 HẸN</div></a>', unsafe_allow_html=True)

        if col_done.button("Xong", key=f"d_{index}"):
            client = gspread.authorize(creds)
            ws_update = client.open_by_url(SPREADSHEET_URL).get_worksheet(0)
            ws_update.update_cell(index + 2, 6, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            st.cache_data.clear()
            st.rerun()
        st.divider()

# --- 4. KHO VIDEO SALES KIT ---
st.markdown("---")
st.subheader("🎬 Kho Video Sales Kit")
v_col1, v_col2 = st.columns(2)
with v_col1:
    st.video("https://www.youtube.com/watch?v=HHfsKefOwA4") # Anh thay link của anh vào đây
with v_col2:
    st.video("https://www.youtube.com/watch?v=OJruIuIs_Ag") # Anh thay link của anh vào đây
