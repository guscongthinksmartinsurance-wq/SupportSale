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

# --- 2. HÀM BỔ TRỢ ---
@st.cache_resource
def get_gs_client():
    creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

def load_data():
    client = get_gs_client()
    sh = client.open_by_url(SPREADSHEET_URL)
    ws = sh.get_worksheet(0)
    data = ws.get_all_records()
    return pd.DataFrame(data)

# --- 3. GIAO DIỆN ---
st.set_page_config(page_title="TMC Pipeline V3", layout="wide")
st.title("💼 TMC Pipeline Dashboard")

df = load_data()

# --- 4. RENDER PIPELINE DẠNG THẺ ---
for index, row in df.iterrows():
    sheet_row = index + 2
    with st.container():
        # Cấu trúc 4 cột chuẩn Pipeline
        c_info, c_comm, c_note, c_action = st.columns([2.2, 3.8, 3.2, 0.8])
        
        with c_info:
            st.markdown(f"#### {row['Name KH']}")
            
            # --- FIX DỨT ĐIỂM LINK ID ---
            # Làm sạch ID và bọc trong thẻ HTML <a> để ép trình duyệt mở tab sạch
            raw_id = str(row['ID']).strip().replace('#', '').lower()
            crm_url = f"https://www.7xcrm.com/lead-management/lead-details/{raw_id}/overview"
            
            id_html = f'''
                <a href="{crm_url}" target="_blank" style="color: #007bff; text-decoration: bold;">
                    🆔 ID: #{raw_id[:8]}...
                </a>
            '''
            st.markdown(id_html, unsafe_allow_html=True)
            st.caption(f"📍 State: {row.get('State','N/A')}")

        with c_comm:
            p = str(row['Cellphone']).strip()
            n_enc = urllib.parse.quote(str(row['Name KH']))
            m_enc = urllib.parse.quote(f"Chao {row['Name KH']}, em goi tu TMC...")
            
            st.write(f"📱 {p}")
            # KHÔI PHỤC BỘ 4 NÚT: GỌI | SMS | MAIL | CALENDAR (HẸN)
            b1, b2, b3, b4 = st.columns(4)
            b1.markdown(f'<a href="tel:{p}" target="_self" style="text-decoration:none;"><div style="background-color:#28a745;color:white;padding:8px 0;border-radius:5px;text-align:center;font-weight:bold;font-size:11px;">📞 GỌI</div></a>', unsafe_allow_html=True)
            b2.markdown(f'<a href="rcmobile://sms?number={p}&body={m_enc}" target="_self" style="text-decoration:none;"><div style="background-color:#17a2b8;color:white;padding:8px 0;border-radius:5px;text-align:center;font-weight:bold;font-size:11px;">💬 SMS</div></a>', unsafe_allow_html=True)
            b3.markdown(f'<a href="mailto:{row.get("Email","")}?subject=TMC&body={m_enc}" target="_self" style="text-decoration:none;"><div style="background-color:#fd7e14;color:white;padding:8px 0;border-radius:5px;text-align:center;font-weight:bold;font-size:11px;">📧 MAIL</div></a>', unsafe_allow_html=True)
            # NÚT HẸN (CALENDAR)
            b4.markdown(f'<a href="https://calendar.google.com/calendar/r/eventedit?text=TMC_Meeting_{n_enc}" target="_blank" style="text-decoration:none;"><div style="background-color:#f4b400;color:white;padding:8px 0;border-radius:5px;text-align:center;font-weight:bold;font-size:11px;">📅 HẸN</div></a>', unsafe_allow_html=True)

        with c_note:
            st.caption("📝 Ghi chú cộng dồn:")
            st.text_area("History", value=row.get('Note',''), height=70, disabled=True, key=f"h_{index}")
            new_n = st.text_input("Note mới...", key=f"in_{index}")
            if st.button("XONG ✅", key=f"done_{index}", use_container_width=True):
                client = get_gs_client()
                ws_u = client.open_by_url(SPREADSHEET_URL).get_worksheet(0)
                now = datetime.now()
                ws_u.update_cell(sheet_row, 8, now.strftime("%Y-%m-%d %H:%M:%S"))
                if new_n:
                    combined = f"[{now.strftime('%m/%d')}]: {new_n}\n{row.get('Note','')}"
                    ws_u.update_cell(sheet_row, 9, combined[:5000])
                st.rerun()

        with c_action:
            st.write("")
            with st.popover("⋮"):
                if st.button("Xóa dòng này", key=f"del_{index}"):
                    # Logic xóa nếu cần
                    pass
        st.divider()

# --- 5. VIDEO SALES KIT (KHÔI PHỤC) ---
st.markdown("---")
st.subheader("🎬 Video Sales Kit")
v1, v2 = st.columns(2)
v1.video("https://www.youtube.com/watch?v=HHfsKefOwA4")
v2.video("https://www.youtube.com/watch?v=OJruIuIs_Ag")
