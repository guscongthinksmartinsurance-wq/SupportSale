import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime
import streamlit.components.v1 as components

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
  "token_uri": "https://oauth2.googleapis.com/token",
}

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1QSMUSOkeazaX1bRpOQ4DVHqu0_j-uz4maG3l7Lj1c1M/edit?gid=0#gid=0"

scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(info, scopes=scopes)
client = gspread.authorize(creds)

def load_data():
    try:
        sh = client.open_by_url(SPREADSHEET_URL)
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        df.columns = [str(col).strip() for col in df.columns]
        return df, worksheet
    except Exception as e:
        st.error(f"Lỗi: {e}")
        return pd.DataFrame(), None

# --- 2. HÀM TẠO NÚT BẤM JAVASCRIPT ---
def custom_button(label, link, color):
    # Dùng JS window.location.assign để ép mở App
    html_code = f"""
    <button onclick="window.location.assign('{link}')" style="
        width: 100%;
        background-color: {color};
        color: white;
        border: none;
        padding: 10px;
        border-radius: 5px;
        cursor: pointer;
        font-weight: bold;
    ">{label}</button>
    """
    components.html(html_code, height=45)

# --- 3. GIAO DIỆN ---
st.set_page_config(page_title="TMC Sales Assistant Tool", layout="wide")
st.title("🚀 TMC Sales Assistant Tool")

df, ws = load_data()

# Sidebar Thêm Khách
with st.sidebar:
    st.header("➕ Thêm Khách Hàng Mới")
    n_name = st.text_input("Name KH")
    n_id = st.text_input("ID")
    n_cell = st.text_input("Cellphone")
    n_work = st.text_input("Workphone")
    n_status = st.selectbox("Status", ["New", "Potential", "Follow-up", "Hot"])
    n_sales = st.text_input("Sales Assigned")
    
    if st.button("Lưu vào Google Sheets"):
        if n_name and n_cell and ws:
            ws.append_row([n_name, n_id, n_cell, n_work, n_status, "", n_sales])
            st.success("Đã thêm khách mới!")
            st.rerun()

if not df.empty:
    st.subheader("🔍 Bộ lọc tương tác")
    c_s1, c_s2 = st.columns([2, 1])
    
    status_col = 'Status' if 'Status' in df.columns else df.columns[4]
    interact_col = 'Last_Interact' if 'Last_Interact' in df.columns else df.columns[5]

    with c_s1:
        days_slider = st.slider("Chưa tương tác quá (ngày):", 1, 60, 1)
    with c_s2:
        st_unique = df[status_col].unique()
        status_sel = st.multiselect("Lọc trạng thái:", st_unique, default=st_unique)

    df[interact_col] = pd.to_datetime(df[interact_col], errors='coerce')
    today = datetime.now()
    mask = (df[interact_col].isna()) | ((today - df[interact_col]).dt.days >= days_slider)
    df_display = df[mask & df[status_col].isin(status_sel)]

    st.subheader(f"📋 Danh sách ({len(df_display)} khách)")
    
    for index, row in df_display.iterrows():
        with st.container():
            col_info, col_call, col_sms, col_mail, col_cal, col_done = st.columns([3, 1, 1, 1, 1, 1])
            
            with col_info:
                tag = "🟢 NEW" if pd.isna(row[interact_col]) else ""
                st.markdown(f"**{row['Name KH']}** {tag}")
                st.caption(f"ID: {row['ID']} | 📞 {row['Cellphone']}")

            phone = str(row['Cellphone']).strip()
            name_enc = urllib.parse.quote(str(row['Name KH']))
            msg_enc = urllib.parse.quote(f"Chào {row['Name KH']}, em từ TMC...")

            # Nút bằng JavaScript để kích hoạt App
            with col_call:
                custom_button("📞 GỌI", f"rcapp://call?number={phone}", "#28a745")
            with col_sms:
                custom_button("💬 SMS", f"rcapp://sms?number={phone}&body={msg_enc}", "#17a2b8")
            with col_mail:
                custom_button("📧 MAIL", f"mailto:?subject=TMC_Support&body={msg_enc}", "#fd7e14")
            with col_cal:
                custom_button("📅 HẸN", f"https://www.google.com/calendar/render?action=TEMPLATE&text=Hen_TMC_{name_enc}", "#f4b400")

            if col_done.button("Xong", key=f"x_{index}"):
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ws.update_cell(index + 2, 6, now)
                st.rerun()
            st.divider()

# Kho Video
st.markdown("---")
st.subheader("🎬 Kho Video Sales Kit")
v1, v2 = st.columns(2)
v1.video("https://youtu.be/HHfsKefOwA4")
v2.video("https://youtu.be/OJruIuIs_Ag")
