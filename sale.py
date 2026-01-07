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
}

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1XUfU2v-vH_f2r6-L0-1K4H4yK4yK4yK4yK4yK4yK4yK/edit"
creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
client = gspread.authorize(creds)

@st.cache_data(ttl=300)
def load_data_safe():
    sh = client.open_by_url(SPREADSHEET_URL)
    worksheet = sh.get_worksheet(0)
    df = pd.DataFrame(worksheet.get_all_records())
    df.columns = [str(col).strip() for col in df.columns]
    return df, worksheet

# --- 2. HÀM TẠO NÚT BẤM SIÊU MẠNH (JS) ---
def action_button(label, link, color):
    # Dùng JS để ép trình duyệt mở protocol handler (rcapp)
    html = f"""
    <button onclick="window.top.location.href='{link}'" style="
        width: 100%; background-color: {color}; color: white; 
        border: none; padding: 8px; border-radius: 5px; 
        cursor: pointer; font-weight: bold; font-family: sans-serif;
    ">{label}</button>
    """
    components.html(html, height=45)

# --- 3. GIAO DIỆN ---
st.set_page_config(page_title="TMC Sales Assistant", layout="wide")
st.title("🚀 TMC Sales Assistant Tool")

df, ws = load_data_safe()

# Sidebar: Thêm khách
with st.sidebar:
    st.header("➕ Thêm Khách Hàng")
    n_name = st.text_input("Name KH")
    n_cell = st.text_input("Cellphone")
    n_status = st.selectbox("Status", ["New", "Potential", "Follow-up", "Hot"])
    if st.button("Lưu khách hàng"):
        ws.append_row([n_name, "", n_cell, "", n_status, "", ""])
        st.cache_data.clear()
        st.success("Đã thêm!")
        st.rerun()

# Bộ lọc thanh trượt
st.subheader("🔍 Bộ lọc")
c_s1, c_s2 = st.columns([2, 1])
with c_s1:
    days = st.slider("Chưa tương tác quá (ngày):", 1, 60, 1)
with c_s2:
    status_sel = st.multiselect("Lọc trạng thái:", df['Status'].unique(), default=df['Status'].unique())

df['Last_Interact'] = pd.to_datetime(df['Last_Interact'], errors='coerce')
mask = (df['Last_Interact'].isna()) | ((datetime.now() - df['Last_Interact']).dt.days >= days)
df_filtered = df[mask & df['Status'].isin(status_sel)]

# Danh sách hiển thị
for index, row in df_filtered.iterrows():
    with st.container():
        col_info, col_call, col_sms, col_mail, col_cal, col_done = st.columns([2.5, 1, 1, 1, 1, 1])
        
        with col_info:
            tag = "🟢 NEW" if pd.isna(row['Last_Interact']) else ""
            st.markdown(f"**{row['Name KH']}** {tag}")
            st.caption(f"📞 {row['Cellphone']}")

        p = str(row['Cellphone']).strip()
        name_enc = urllib.parse.quote(str(row['Name KH']))
        m_enc = urllib.parse.quote(f"Chào {row['Name KH']}, em từ TMC...")

        # Dùng JavaScript Button để bật App
        with col_call: action_button("📞 GỌI", f"rcapp://call?number={p}", "#28a745")
        with col_sms:  action_button("💬 SMS", f"rcapp://sms?number={p}&body={m_enc}", "#17a2b8")
        with col_mail: action_button("📧 MAIL", f"mailto:?subject=TMC&body={m_enc}", "#fd7e14")
        with col_cal:  action_button("📅 HẸN", f"https://calendar.google.com/calendar/r/eventedit?text=Hen_TMC_{name_enc}", "#f4b400")

        if col_done.button("Xong", key=f"done_{index}"):
            ws.update_cell(index + 2, 6, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            st.cache_data.clear()
            st.rerun()
        st.divider()
