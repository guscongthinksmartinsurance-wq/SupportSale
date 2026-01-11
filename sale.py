import streamlit as st
import pandas as pd
from gspread_pandas import Spread, Client
import urllib.parse
from datetime import datetime
import json

# --- 1. CẤU HÌNH KẾT NỐI GOOGLE SHEETS ---
# Em dán trực tiếp JSON của anh vào đây để anh dễ dùng
credentials_dict = {
  "type": "service_account",
  "project_id": "caramel-hallway-481517-q8",
  "private_key_id": "b4f20621f80d644d23e3ee6fe898acd7b955bf3e",
  "private_key": st.secrets.get("private_key", "Dán_Private_Key_Vào_Đây_Hoặc_Dùng_Secrets"),
  "client_email": "tmc-assistant@caramel-hallway-481517-q8.iam.gserviceaccount.com",
  "token_uri": "https://oauth2.googleapis.com/token",
}
# Lưu ý: Khi đưa lên Streamlit Cloud, anh nên đưa Private Key vào phần Secrets để bảo mật.

# --- 2. KHO VIDEO SALES KIT ---
video_kit = [
    {"title": "Review khách hàng A", "url": "https://youtu.be/HHfsKefOwA4", "msg": "Dạ em gửi anh xem clip thực tế khách dùng máy bên em ạ:"},
    {"title": "Showroom TMC thực tế", "url": "https://youtu.be/OJruIuIs_Ag", "msg": "Mời anh tham quan showroom qua video ngắn này nhé:"},
]

# --- 3. CÁC HÀM XỬ LÝ ---
def render_button(label, link, icon="🚀", color="#007bff"):
    st.markdown(f"""<a href="{link}" target="_self" style="text-decoration: none;">
        <div style="background-color: {color}; color: white; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; margin-bottom: 5px;">
            {icon} {label}</div></a>""", unsafe_allow_html=True)

# --- GIAO DIỆN CHÍNH ---
st.set_page_config(page_title="TMC Sales Assistant", layout="wide")
st.title("🚀 TMC Sales Assistant Tool")

# Sidebar: Thêm khách hàng mới
with st.sidebar:
    st.header("➕ Thêm Khách Hàng Mới")
    new_name = st.text_input("Name KH")
    new_id = st.text_input("ID")
    new_cell = st.text_input("Cellphone")
    new_work = st.text_input("Workphone")
    new_status = st.selectbox("Status", ["New", "Potential", "Follow-up", "Hot"])
    new_sales = st.text_input("Sales Assigned")
    
    if st.button("Lưu vào Google Sheets"):
        # Logic gửi dữ liệu lên Google Sheets sẽ nằm ở đây
        st.success(f"Đã thêm khách hàng: {new_name}")

# Khu vực lọc (Thanh kéo 1-60 ngày)
st.subheader("🔍 Bộ lọc tương tác")
col_s1, col_s2 = st.columns([2, 1])
with col_s1:
    days = st.slider("Khách hàng chưa tương tác quá (ngày):", 1, 60, 7)
with col_s2:
    status_filter = st.multiselect("Lọc theo trạng thái:", ["New", "Potential", "Follow-up", "Hot"])

# Giả lập bảng dữ liệu (Khi anh chạy thật, nó sẽ kéo từ Google Sheets)
st.markdown("---")
st.subheader("📋 Danh sách cần chăm sóc")

# Demo một dòng khách hàng
c_name, c_id, c_phone, c_actions = st.columns([2, 1, 2, 4])
c_name.write("**Nguyễn Văn A**")
c_id.write("ID: 12345")
c_phone.write("📞 0901234567")

with c_actions:
    msg = "Chào anh, em gọi từ TMC..."
    rc_call = f"rcapp://call?number=0901234567"
    rc_sms = f"rcapp://sms?number=0901234567&body={urllib.parse.quote(msg)}"
    out_link = f"mailto:test@gmail.com?subject=TMC&body={urllib.parse.quote(msg)}"
    
    act1, act2, act3 = st.columns(3)
    with act1: render_button("GỌI", rc_call, "📞", "#28a745")
    with act2: render_button("SMS", rc_sms, "💬", "#17a2b8")
    with act3: render_button("MAIL", out_link, "📧", "#0078d4")

# Kho Video
st.markdown("---")
st.subheader("🎬 Kho Video Sales Kit")
v1, v2 = st.columns(2)
for i, vid in enumerate(video_kit):
    with (v1 if i==0 else v2):
        st.video(vid['url'])
        st.caption(vid['title'])
        st.code(f"{vid['msg']} {vid['url']}")
