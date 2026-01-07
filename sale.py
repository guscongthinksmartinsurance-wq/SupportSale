import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime

# --- 1. CẤU HÌNH (DÙNG JSON CỦA ANH) ---
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

# --- 2. HÀM TẢI DỮ LIỆU CỰC KỲ AN TOÀN ---
@st.cache_resource # Dùng cache_resource để giữ kết nối không bị khởi tạo lại
def get_gsheet_client():
    return gspread.authorize(creds)

def load_data_from_google():
    gc = get_gsheet_client()
    sh = gc.open_by_url(SPREADSHEET_URL)
    ws = sh.get_worksheet(0)
    df = pd.DataFrame(ws.get_all_records())
    df.columns = [str(col).strip() for col in df.columns]
    return df, ws

# --- 3. GIAO DIỆN ---
st.set_page_config(page_title="TMC Sales Assistant", layout="wide")
st.title("🚀 TMC Sales Assistant Tool")

# Khởi tạo session state để tránh load lại khi chỉnh slider
if 'df' not in st.session_state:
    with st.spinner('Đang kết nối dữ liệu an toàn...'):
        df_load, ws_load = load_data_from_google()
        st.session_state.df = df_load
        st.session_state.ws = ws_load

df = st.session_state.df
ws = st.session_state.ws

# SideBar: Thêm khách
with st.sidebar:
    st.header("➕ Thêm Khách Hàng")
    n_name = st.text_input("Name KH")
    n_cell = st.text_input("Cellphone")
    n_status = st.selectbox("Status", ["New", "Potential", "Follow-up", "Hot"])
    if st.button("Lưu khách hàng"):
        ws.append_row([n_name, "", n_cell, "", n_status, "", ""])
        st.success("Đã thêm! Hãy nhấn 'Refresh' để cập nhật.")

# Thanh trượt lọc
st.subheader("🔍 Bộ lọc thông minh")
c_s1, c_s2, c_refresh = st.columns([2, 1, 1])
with c_s1:
    days = st.slider("Chưa tương tác quá (ngày):", 1, 60, 1)
with c_s2:
    status_sel = st.multiselect("Lọc trạng thái:", df['Status'].unique(), default=df['Status'].unique())
with c_refresh:
    if st.button("🔄 Refresh Data"):
        del st.session_state.df # Xóa để load lại
        st.rerun()

# Logic lọc (Chạy local trên RAM máy tính)
df['Last_Interact_DT'] = pd.to_datetime(df['Last_Interact'], errors='coerce')
mask = (df['Last_Interact_DT'].isna()) | ((datetime.now() - df['Last_Interact_DT']).dt.days >= days)
df_filtered = df[mask & df['Status'].isin(status_sel)]

st.subheader(f"📋 Danh sách ({len(df_filtered)} khách)")

# --- HIỂN THỊ DANH SÁCH ---
for index, row in df_filtered.iterrows():
    with st.container():
        col_info, col_call, col_sms, col_mail, col_cal, col_done = st.columns([2.5, 1, 1, 1, 1, 1])
        
        with col_info:
            tag = "🟢 NEW" if pd.isna(row['Last_Interact_DT']) else ""
            st.markdown(f"**{row['Name KH']}** {tag}")
            st.caption(f"📞 {row['Cellphone']}")

        p = str(row['Cellphone']).strip()
        name_enc = urllib.parse.quote(str(row['Name KH']))
        m_enc = urllib.parse.quote(f"Chào {row['Name KH']}, em từ TMC...")

        # --- NÚT GỌI/SMS ĐƯỢC FIX LỖI BẰNG HTML TAG THUẦN ---
        # Đây là cách duy nhất để trình duyệt thấy link và cho phép mở App
        col_call.markdown(f'<a href="rcapp://call?number={p}" target="_blank" style="text-decoration:none;"><div style="background-color:#28a745;color:white;padding:8px;border-radius:5px;text-align:center;font-weight:bold;">📞 GỌI</div></a>', unsafe_allow_html=True)
        col_sms.markdown(f'<a href="rcapp://sms?number={p}&body={m_enc}" target="_blank" style="text-decoration:none;"><div style="background-color:#17a2b8;color:white;padding:8px;border-radius:5px;text-align:center;font-weight:bold;">💬 SMS</div></a>', unsafe_allow_html=True)
        col_mail.markdown(f'<a href="mailto:?subject=TMC&body={m_enc}" target="_blank" style="text-decoration:none;"><div style="background-color:#fd7e14;color:white;padding:8px;border-radius:5px;text-align:center;font-weight:bold;">📧 MAIL</div></a>', unsafe_allow_html=True)
        
        gcal_link = f"https://calendar.google.com/calendar/r/eventedit?text=Hen_TMC_{name_enc}"
        col_cal.markdown(f'<a href="{gcal_link}" target="_blank" style="text-decoration:none;"><div style="background-color:#f4b400;color:white;padding:8px;border-radius:5px;text-align:center;font-weight:bold;">📅 HẸN</div></a>', unsafe_allow_html=True)

        if col_done.button("Xong", key=f"d_{index}"):
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ws.update_cell(index + 2, 6, now_str)
            st.info("Đã cập nhật lên Sheets. Hãy nhấn Refresh để tải lại.")
        st.divider()

st.video("https://youtu.be/HHfsKefOwA4")
