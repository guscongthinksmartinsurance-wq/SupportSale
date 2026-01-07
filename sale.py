import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime

# --- 1. CẤU HÌNH KẾT NỐI (JSON ANH CUNG CẤP) ---
credentials_info = {
  "type": "service_account",
  "project_id": "caramel-hallway-481517-q8",
  "private_key_id": "b4f20621f80d644d23e3ee6fe898acd7b955bf3e",
  "private_key": """-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC+8HRC1BZcrafY\nyI+MlMqX3tJ0Rt5FuDdJlew0kZggLJpr0z1OshwSOJ8++8lgyPkvkZumb3CLZkB1\n3PVprn3Qw7YkPcBBosq6J4VTNWazgx0OMZUi/sJJbWoKu3Z2BAk/7nFkBqESO7/F\n2OSandv+8FFen8B9Ie5SBXRHLMOMMbkkqPKBU76tT1yhMFtDRZWNWFb0wJoJ2XRm\nWCGj6taTMZy0aOw+jVB4DjTAuJN3gUv5tALbGX/C9HE39vl098stNRrKmQ4CcvYs\nZAvqyye9GoI1KEI6OEXCA86aFYVfjDeIh3VLlQC5feWqPWHSv3mOktZHoVt+b1Gu\nsPKM49GjAgMBAAECggEAG4KklZ5eLHM+zD61ZBFqETCjDOrLCquMl7cYpchWbUhP\n5Xo1ipmh7sQmuZnofV/ne0GU9gl3YzZT0keIOnZQHVydaSJWiX5tjB22mXMHvZSG\nAq4FKVogXxj7Htm8qytQs9vkjX9hBLIEIvrpkRdug5BXgPUudDkHz9yGUNzzvcaK\nOpGr3fVwLwal/FYx0XLy5Hpdl5zkVsiuK4Q7IBvketKZg3Sy9xYnhPqOdkvIoIr6\ncVXVE+hCVYt6+FtLmuOBQO5EfTiXY+S/CP/qUsNYz0J6pPsTxQAdRYHwoVFP117t\nhlQ/dnWT1hg8wDWXZR/EwLI8H4mP2vPNqmG9f0CZiQKBgQD0NGkEqISRa1ac32Lt\n2U1HSkjoGa0d2ZATdfMWJyz/IUFiDEhgY02eauPm2QJCcMXg3qJieRnsNKh5fy7I\n2PHSXzW+AQCUcx0g/HIEyLccCRoTZJcrVuvZ5UAxpepAeQDmCHyNfp1I7SjnBd0J\nPbLBOLJFHziXF/x/uY0DRVI9CwKBgQDIKWq9ZSutX7euZH5TVC27r5Eh4wwcsoCi\nEanEwf9QOIcYZmBGIa5gDJgGqQKfseXA2c3ZpjcYGHY4cPhXQ/LhrisHEyyHDFsp\nf01RJIAK0bHI/RBwUB0QVKwhfqfsYG4YVCRJlgnqUNLgnhq1GCESD9JPsJlCSrkF\np3R8cvwsyQKBgQDVjYuU/kVH4eURNCyQMOpqgGS3S9Te+KYMzqWwZrvrtEo4EuOs\nHsr+0RzRgE6AiZwRpL++e4aW0AnQjc785vK59HbL3JaEOxJrCTgwRNIUG0WJVfr4\ndH+1wcvcXuo2TVrizuMU3XdwEa0mMjN0ZFcQr6L93WqgfuJZU4skJBfhtwKBgGp4\nxYObhmFB8iX85MmUlIMqv8vDx5SYSx5qwOCdxR66AvqysnF7xxLmgBPC4VdrPOiZ\swschF/32yLozOE2jsMHb3Hi/COWKgPn6IvKG6Ylpylfm9fydZNTRwDGK7LsFIQy\ndd8CxaFzfsjmsRQ1kpnV+qxTJyMBNmxQiAEO9R8pAoGBAJDB8lvIXnAkRQZ/cWDg\nzoHC+8FyTIEkkcD7/7KZD25DjD7FW247Mx7OfMGwqs9Wj67+ec5mTHco1TFrs15F\nMWcgHed08BRLsxm5PETmUQhciTQ3yHuFkIqbND9V8XRA+YuBMCcJcpoU+WrExB3N\nUvNQNXmUy4VQRI8i9CHtAZdp\n-----END PRIVATE KEY-----\n""",
  "client_email": "tmc-assistant@caramel-hallway-481517-q8.iam.gserviceaccount.com",
}

# --- ANH DÁN LINK FILE GOOGLE SHEETS CỦA ANH VÀO ĐÂY ---
SPREADSHEET_URL = "DÁN_LINK_FILE_CỦA_ANH_VÀO_ĐÂY"

scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(credentials_info, scopes=scopes)
client = gspread.authorize(creds)

# --- 2. HÀM TƯƠNG TÁC DỮ LIỆU ---
def load_data():
    try:
        sh = client.open_by_url(SPREADSHEET_URL)
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()
        return pd.DataFrame(data), worksheet
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}. Anh nhớ Share file Sheets cho Email service account nhé!")
        return pd.DataFrame(), None

# --- 3. GIAO DIỆN ---
st.set_page_config(page_title="TMC Sales Assistant Tool", layout="wide")
st.title("🚀 TMC Sales Assistant Tool")

# Sidebar: Thêm khách hàng mới
with st.sidebar:
    st.header("➕ Thêm Khách Hàng Mới")
    n_name = st.text_input("Name KH")
    n_id = st.text_input("ID")
    n_cell = st.text_input("Cellphone")
    n_work = st.text_input("Workphone")
    n_status = st.selectbox("Status", ["New", "Potential", "Follow-up", "Hot"])
    n_sales = st.text_input("Sales Assigned")
    
    if st.button("Lưu vào Google Sheets"):
        df, ws = load_data()
        if n_name and n_cell and ws:
            ws.append_row([n_name, n_id, n_cell, n_work, n_status, "", n_sales])
            st.success("Đã thêm khách mới thành công!")
            st.rerun()

df, ws = load_data()

if not df.empty:
    # Thanh kéo & Lọc
    st.subheader("🔍 Bộ lọc tương tác")
    c1, c2 = st.columns([2, 1])
    with c1:
        days_slider = st.slider("Khách hàng chưa tương tác quá (ngày):", 1, 60, 7)
    with c2:
        all_status = df['Status'].unique().tolist()
        status_sel = st.multiselect("Lọc theo trạng thái:", all_status, default=all_status)

    # Xử lý ngày tháng và lọc
    df['Last_Interact'] = pd.to_datetime(df['Last_Interact'], errors='coerce')
    today = datetime.now()
    mask = (df['Last_Interact'].isna()) | ((today - df['Last_Interact']).dt.days >= days_slider)
    df_display = df[mask & df['Status'].isin(status_sel)]

    st.subheader("📋 Danh sách cần chăm sóc")
    
    for index, row in df_display.iterrows():
        with st.container():
            col_info, col_call, col_sms, col_mail, col_done = st.columns([3, 1, 1, 1, 1])
            
            with col_info:
                new_tag = "🟢 [NEW]" if pd.isna(row['Last_Interact']) else ""
                st.write(f"**{row['Name KH']}** {new_tag}")
                st.caption(f"ID: {row['ID']} | 📞 {row['Cellphone']}")

            # Link cho các nút bấm
            msg_enc = urllib.parse.quote(f"Chào {row['Name KH']}, em gọi từ TMC...")
            rc_call = f"rcapp://call?number={row['Cellphone']}"
            rc_sms = f"rcapp://sms?number={row['Cellphone']}&body={msg_enc}"
            out_mail = f"mailto:?subject=TMC%20Support&body={msg_enc}"

            col_call.markdown(f'[:green[📞 GỌI]]({rc_call})')
            col_sms.markdown(f'[:blue[💬 SMS]]({rc_sms})')
            col_mail.markdown(f'[:orange[📧 MAIL]]({out_mail})')

            if col_done.button("Xong", key=f"btn_{index}"):
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Cập nhật cột F (số 6) trên Sheets
                ws.update_cell(index + 2, 6, now_str)
                st.rerun()
            st.divider()

# Kho Video Sales Kit
st.markdown("---")
st.subheader("🎬 Kho Video Sales Kit")
v_col1, v_col2 = st.columns(2)
with v_col1:
    st.video("https://youtu.be/HHfsKefOwA4")
    st.caption("Review khách hàng A")
with v_col2:
    st.video("https://youtu.be/OJruIuIs_Ag")
    st.caption("TMC Show Room Corporate Video")
