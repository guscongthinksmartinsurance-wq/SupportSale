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

# --- 3. GIAO DIỆN CHÍNH ---
st.set_page_config(page_title="TMC Pipeline V2", layout="wide")
st.title("💼 TMC Sales Pipeline Dashboard")

# --- SIDEBAR: THÊM KHÁCH HÀNG MỚI (CẬP NHẬT TRƯỜNG MỚI) ---
with st.sidebar:
    st.header("➕ Add New Lead")
    with st.form("add_form", clear_on_submit=True):
        f_name = st.text_input("Name KH")
        f_id = st.text_input("CRM Lead ID (Mã chuỗi)")
        f_cell = st.text_input("Cellphone")
        f_work = st.text_input("Workphone")
        f_email = st.text_input("Email")
        f_state = st.text_input("State")
        f_status = st.selectbox("Status", ["New", "Potential", "Follow-up", "Hot"])
        f_note = st.text_area("Initial Note")
        if st.form_submit_button("Save Lead"):
            client = get_gs_client()
            ws = client.open_by_url(SPREADSHEET_URL).get_worksheet(0)
            # Thứ tự: Name, ID, Cell, Work, Email, State, Status, Last_Interact, Note, Sales
            ws.append_row([f_name, f_id, f_cell, f_work, f_email, f_state, f_status, "", f_note, ""])
            st.success("Lead added successfully!")
            st.cache_data.clear()
            st.rerun()

# --- BỘ LỌC & REFRESH ---
df = load_data()
col_f1, col_f2 = st.columns([3, 1])
with col_f1:
    days = st.slider("Chưa tương tác quá (ngày):", 0, 60, 1)
with col_f2:
    if st.button("🔄 Refresh Pipeline"):
        st.cache_data.clear()
        st.rerun()

# Logic lọc
df['Last_Interact_DT'] = pd.to_datetime(df['Last_Interact'], errors='coerce')
mask = (df['Last_Interact_DT'].isna()) | ((datetime.now() - df['Last_Interact_DT']).dt.days >= days)
df_display = df[mask]

# --- 4. HIỂN THỊ PIPELINE (GIAO DIỆN CARD MỚI) ---
st.subheader(f"📋 Working List ({len(df_display)} leads)")

for index, row in df_display.iterrows():
    # ID thật để tìm trên Sheet (index + 2 vì dòng 1 là Header và index bắt đầu từ 0)
    sheet_row = index + 2
    
    with st.container():
        # Chia layout: Info | Comms | Note & Action | Menu
        c_info, c_comm, c_note, c_action = st.columns([2.5, 3, 3, 0.5])
        
        # 1. CỘT THÔNG TIN & LINK CRM
        with c_info:
            st.markdown(f"### {row['Name KH']}")
            crm_link = f"https://www.7xcrm.com/lead-management/lead-details/{row['ID']}/overview"
            st.markdown(f"🆔 ID: [`{row['ID'][:8]}...`]({crm_link})", help="Click to open CRM")
            st.caption(f"📍 State: {row.get('State','N/A')} | 👤 {row.get('Sales Assigned','')}")

        # 2. CỘT LIÊN LẠC (Giao thức Baseline chuẩn)
        with c_comm:
            p_cell = str(row['Cellphone']).strip()
            p_work = str(row['Workphone']).strip()
            m_enc = urllib.parse.quote(f"Chao {row['Name KH']}, em goi tu TMC...")
            
            # Cụm Cellphone
            st.write(f"📱 **Cell:** {p_cell}")
            b1, b2, b3 = st.columns(3)
            b1.markdown(f'<a href="tel:{p_cell}" target="_self" style="text-decoration:none;"><div style="background-color:#28a745;color:white;padding:5px;border-radius:5px;text-align:center;font-size:12px;">📞 CALL</div></a>', unsafe_allow_html=True)
            b2.markdown(f'<a href="rcmobile://sms?number={p_cell}&body={m_enc}" target="_self" style="text-decoration:none;"><div style="background-color:#17a2b8;color:white;padding:5px;border-radius:5px;text-align:center;font-size:12px;">💬 SMS</div></a>', unsafe_allow_html=True)
            
            # Cụm Workphone & Mail
            st.write(f"📞 **Work:** {p_work}")
            b4, b5, b6 = st.columns(3)
            b4.markdown(f'<a href="tel:{p_work}" target="_self" style="text-decoration:none;"><div style="background-color:#28a745;color:white;padding:5px;border-radius:5px;text-align:center;font-size:12px;">📞 CALL</div></a>', unsafe_allow_html=True)
            if row.get('Email'):
                b5.markdown(f'<a href="mailto:{row["Email"]}?subject=TMC&body={m_enc}" target="_self" style="text-decoration:none;"><div style="background-color:#fd7e14;color:white;padding:5px;border-radius:5px;text-align:center;font-size:12px;">📧 MAIL</div></a>', unsafe_allow_html=True)

        # 3. CỘT NOTE & DONE
        with c_note:
            st.caption("📝 Ghi chú hiện tại:")
            st.info(row.get('Note', 'Chưa có ghi chú'))
            new_note = st.text_input("Nhập ghi chú mới...", key=f"note_{index}")
            
            if st.button("DONE ✅", key=f"done_{index}", use_container_width=True):
                client = get_gs_client()
                ws_u = client.open_by_url(SPREADSHEET_URL).get_worksheet(0)
                
                # Cập nhật thời gian tương tác (Cột H - 8)
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ws_u.update_cell(sheet_row, 8, now_str)
                
                # Cập nhật Note cộng dồn (Cột I - 9)
                if new_note:
                    timestamp = datetime.now().strftime("%m/%d")
                    updated_note = f"[{timestamp}]: {new_note} \n {row.get('Note','')}"
                    ws_u.update_cell(sheet_row, 9, updated_note)
                
                st.cache_data.clear()
                st.rerun()

        # 4. NÚT 3 CHẤM (MENU EDIT)
        with c_action:
            with st.popover("⋮"):
                st.write("✏️ Edit Lead Info")
                e_name = st.text_input("Name", value=row['Name KH'], key=f"e_n_{index}")
                e_cell = st.text_input("Cell", value=row['Cellphone'], key=f"e_c_{index}")
                e_email = st.text_input("Email", value=row.get('Email',''), key=f"e_e_{index}")
                e_state = st.text_input("State", value=row.get('State',''), key=f"e_s_{index}")
                
                if st.button("Save Changes", key=f"save_{index}"):
                    client = get_gs_client()
                    ws_edit = client.open_by_url(SPREADSHEET_URL).get_worksheet(0)
                    # Cập nhật các cột tương ứng
                    ws_edit.update_cell(sheet_row, 1, e_name)
                    ws_edit.update_cell(sheet_row, 3, e_cell)
                    ws_edit.update_cell(sheet_row, 5, e_email)
                    ws_edit.update_cell(sheet_row, 6, e_state)
                    st.success("Updated!")
                    st.cache_data.clear()
                    st.rerun()

        st.divider()
