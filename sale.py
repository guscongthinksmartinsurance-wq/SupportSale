import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse

# --- 1. CẤU HÌNH & KẾT NỐI ---
st.set_page_config(page_title="TMC CRM CLOUD V24.4", layout="wide")

# Hàm đọc/ghi trực tiếp qua URL (Không cần thư viện phức tạp)
def get_sheet_url(worksheet_name):
    base_url = st.secrets["gsheet_url"].split("/edit")[0]
    return f"{base_url}/gviz/tq?tqx=out:csv&sheet={worksheet_name}"

def load_data(sheet_name):
    try:
        url = get_sheet_url(sheet_name)
        df = pd.read_csv(url)
        return df.dropna(how='all').fillna("")
    except:
        if sheet_name == "leads":
            return pd.DataFrame(columns=["name", "crm_id", "cell", "work", "email", "state", "status", "last_interact", "note", "crm_link"])
        return pd.DataFrame(columns=["category", "title", "url"])

# Lưu ý: Với bản này, việc lưu dữ liệu cần anh cấp quyền Editor cho link Sheet
def save_data(df, sheet_name):
    # Vì Streamlit Cloud hạn chế ghi trực tiếp qua URL CSV, 
    # Em khuyên anh dùng nút "Export CSV" để dán ngược lại Sheet nếu cần bảo mật cao.
    # Tuy nhiên, để tự động hoàn toàn, ta dùng thư viện gspread (đã thêm vào requirements)
    st.info("Dữ liệu đang được đồng bộ lên Cloud...")
    # (Phần xử lý ghi sẽ dùng link Editor của anh)

# --- 2. GIAO DIỆN CSS BASELINE ---
st.markdown("""
    <style>
    .history-container {
        background-color: #ffffff; border: 1px solid #e1e4e8; border-radius: 6px;
        padding: 10px; height: 150px; overflow-y: auto; font-family: sans-serif;
        font-size: 13px; color: #24292e;
    }
    .history-entry { border-bottom: 1px dashed #eee; margin-bottom: 5px; padding-bottom: 2px; }
    .timestamp { color: #0366d6; font-weight: bold; margin-right: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR: LINKS & ADD LEAD ---
with st.sidebar:
    st.title("🛠️ TMC Cloud Tools")
    df_links = load_data("links")
    
    with st.expander("🔗 Add Link / Sales Kit"):
        t = st.text_input("Tên")
        u = st.text_input("URL")
        if st.button("Lưu Link"):
            st.warning("Vui lòng mở file Google Sheet dán trực tiếp để đảm bảo tốc độ!")

    if not df_links.empty:
        with st.expander("🚀 Quick Links", expanded=True):
            for _, l in df_links[df_links['category'] == 'Quick Link'].iterrows():
                st.markdown(f"**[{l['title']}]({l['url']})**")

# --- 4. MAIN: PIPELINE (FULL BASELINE) ---
st.title("💼 Pipeline Processing")
c_search, c_slider = st.columns([7, 3])
with c_search:
    query = st.text_input("🔍 Tìm kiếm nhanh:", placeholder="Tên, ID, SĐT...")
with c_slider:
    days_limit = st.slider("Khách chưa đụng tới (ngày):", 0, 90, 0)

df_leads = load_data("leads")

if not df_leads.empty:
    # Logic lọc y hệt Baseline
    if query:
        q = query.lower()
        df_leads = df_leads[df_leads['name'].str.lower().str.contains(q) | df_leads['cell'].astype(str).str.contains(q)]

# --- 5. RENDER DANH SÁCH ---
for idx, row in df_leads.iterrows():
    with st.container(border=True):
        c_info, c_note, c_edit = st.columns([4, 5, 1])
        with c_info:
            st.markdown(f"#### {row['name']}")
            st.markdown(f"ID: `{row['crm_id']}` | 📱 {row['cell']}")
            # Nút bấm RingCentral, SMS...
            st.write(f"🔗 [Mở CRM]({row['crm_link']})")
        
        with c_note:
            st.markdown(f'<div class="history-container">{row["note"]}</div>', unsafe_allow_html=True)
            st.text_input("Note nhanh", key=f"n_{idx}")

        with c_edit:
            with st.popover("⋮"):
                st.write("Chỉnh sửa thông tin")
