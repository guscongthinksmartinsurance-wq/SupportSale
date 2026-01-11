import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse
import re

# --- 1. KẾT NỐI & BẢO VỆ DỮ LIỆU CẤP ĐỘ CAO ---
st.set_page_config(page_title="TMC CRM PRO V38", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_load(worksheet):
    """Load dữ liệu và đảm bảo không trả về rỗng nếu có lỗi mạng"""
    try:
        df = conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0)
        if df is not None and not df.empty:
            df = df.fillna("").astype(str)
            for col in df.columns:
                df[col] = df[col].apply(lambda x: x[:-2] if x.endswith('.0') else x)
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def safe_save(df, worksheet):
    """Lớp bảo mật: Chặn ghi đè dữ liệu rỗng lên Google Sheets"""
    if df is None or len(df) == 0:
        st.error(f"🚨 HỆ THỐNG CHẶN LƯU: Phát hiện dữ liệu {worksheet} bị trống bất thường!")
        return False
    
    # Kiểm tra chéo: Đọc lại bản gốc, nếu bản gốc có dữ liệu mà bản mới rỗng -> Chặn
    try:
        check_df = conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0)
        if check_df is not None and len(check_df) > 0 and len(df) == 0:
            st.error("🚨 CẢNH BÁO: Lệnh lưu có thể làm mất dữ liệu. Đã hủy thao tác!")
            return False
    except:
        pass

    try:
        conn.update(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, data=df.fillna(""))
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Lỗi kết nối Sheets: {e}")
        return False

# --- 2. XỬ LÝ TEXT ---
def clean_phone(val):
    return re.sub(r'\D', '', str(val))

def clean_html_for_edit(raw_html):
    t = str(raw_html).replace('</div>', '\n').replace('<br>', '\n')
    return re.sub(r'<[^>]*>', '', t).strip()

# --- 3. CSS GIAO DIỆN ---
st.markdown("""
    <style>
    .history-container {
        background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px;
        padding: 12px; height: 160px; overflow-y: auto; font-size: 13px; color: #495057;
    }
    .history-entry { border-bottom: 1px solid #dee2e6; margin-bottom: 8px; padding-bottom: 4px; }
    .contact-link { text-decoration: none; color: #28a745; font-weight: bold; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR (QUẢN LÝ LINKS) ---
with st.sidebar:
    st.title("⚒️ CRM Tools")
    df_links = safe_load("links")
    
    with st.expander("🔗 Quick Links"):
        if not df_links.empty:
            for idx, row in df_links[df_links['category'] == 'Quick Link'].iterrows():
                c1, c2 = st.columns([8, 2])
                c1.markdown(f"🚀 [{row['title']}]({row['url']})")
                if c2.button("🗑️", key=f"dl_{idx}"):
                    if safe_save(df_links.drop(idx), "links"): st.rerun()

    with st.expander("📁 Sales Kit"):
        if not df_links.empty:
            for idx, row in df_links[df_links['category'] == 'Sales Kit'].iterrows():
                st.markdown(f"📂 **{row['title']}**")
                if "youtu" in row['url'].lower(): st.video(row['url'])
                else: st.markdown(f"🔗 [Mở]({row['url']})")
                if st.button("🗑️ Xóa", key=f"ds_{idx}"):
                    if safe_save(df_links.drop(idx), "links"): st.rerun()

    with st.expander("➕ Thêm Link"):
        with st.form("f_l", clear_on_submit=True):
            cat=st.selectbox("Loại",["Quick Link","Sales Kit"]); tit=st.text_input("Tiêu đề"); url=st.text_input("URL")
            if st.form_submit_button("Lưu"):
                if tit and url:
                    safe_save
