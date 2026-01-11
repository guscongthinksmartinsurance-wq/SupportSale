import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import urllib.parse

# --- 1. CẤU HÌNH & KẾT NỐI ---
st.set_page_config(page_title="TMC CRM CLOUD V26.3", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    return conn.read(spreadsheet=st.secrets["gsheet_url"], worksheet=worksheet, ttl=0)

def save_data(df, worksheet):
    # Xử lý xóa bỏ các cột rác hoặc cột tạm trước khi lưu
    if 'dt_obj' in df.columns: df = df.drop(columns=['dt_obj'])
    conn.update(spreadsheet=st.secrets["gsheet_url"], worksheet=worksheet, data=df)
    st.cache_data.clear()

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("🛠️ TMC Cloud Tools")
    
    # --- QUẢN LÝ LINKS ---
    try:
        df_links = load_data("links").dropna(how='all')
    except:
        df_links = pd.DataFrame(columns=["category", "title", "url"])

    with st.expander("🔗 Add Link / Sales Kit"):
        with st.form("add_l", clear_on_submit=True):
            c = st.selectbox("Loại", ["Quick Link", "Sales Kit"])
            t = st.text_input("Tên")
            u = st.text_input("URL")
            if st.form_submit_button("Lưu"):
                if t and u:
                    new_l = pd.DataFrame([{"category": c, "title": t, "url": u}])
                    df_links = pd.concat([df_links, new_l], ignore_index=True)
                    save_data(df_links, "links")
                    st.success("Đã lưu!")
                    st.rerun()
                else:
                    st.error("Vui lòng điền đủ tên và link!")

    if not df_links.empty:
        # Render Quick Links
        ql = df_links[df_links['category'] == 'Quick Link']
        if not ql.empty:
            st.subheader("🚀 Quick Links")
            for idx, l in ql.iterrows():
                col1, col2 = st.columns([8, 2])
                col1.markdown(f"**[{l['title']}]({l['url']})**")
                if col2.button("🗑️", key=f"dl_{idx}"):
                    df_links = df_links.drop(idx)
                    save_data(df_links, "links")
                    st.rerun()

        # Render Sales Kit (Video)
        sk = df_links[df_links['category'] == 'Sales Kit']
        if not sk.empty:
            st.subheader("📚 Sales Kit")
            for idx, v in sk.iterrows():
                st.caption(v['title'])
                st.video(v['url'])
                if st.button("Xóa Video", key=f"dv_{idx}"):
                    df_links = df_links.drop(idx)
                    save_data(df_links, "links")
                    st.rerun()
    
    st.divider()
    
    # --- THÊM KHÁCH HÀNG ---
    with st.expander("➕ Add New Lead"):
        with st.form("new_lead", clear_on_submit=True):
            n = st.text_input("Name"); i = st.text_input("ID"); p = st.text_input("Cell")
            w = st.text_input("Work"); e = st.text_input("Email"); s = st.text_input("State")
            cl = st.text_input("Link CRM")
            if st.form_submit_button("Lưu Lead"):
                try: df_leads = load_data("leads").dropna(how='all')
                except: df_leads = pd.DataFrame(columns=["name", "crm_id", "cell", "work", "email", "state", "status", "last_interact", "note", "crm_link"])
                new_row = {"name":n, "crm_id":i, "cell":p, "work":w, "email":e, "state":s, "status":"New", "last_interact":"", "note":"", "crm_link":cl}
                df_leads = pd.concat([df_leads, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df_leads, "leads")
                st.rerun()

# --- PHẦN TIẾP THEO (TÌM KIẾM & DANH SÁCH) GIỮ NGUYÊN NHƯ BẢN V26.2 ---
# (Anh copy tiếp phần code render leads từ bản V26.2 vào đây nhé)
