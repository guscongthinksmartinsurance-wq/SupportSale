import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse

# --- 1. KẾT NỐI CHUẨN GOOGLE API ---
st.set_page_config(page_title="TMC CRM PRO V24.4", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    # ttl=0 để luôn lấy data mới nhất, nhập Note là thấy ngay
    return conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0).dropna(how='all')

def save_data(df, worksheet):
    df = df.fillna("")
    conn.update(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, data=df)
    st.cache_data.clear()

# --- 2. CSS HISTORY GỐC ---
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

# --- 3. LOGIC NOTE NHANH (KHÔNG ĐỔI) ---
def save_note_v24(idx, current_note, note_key):
    new_txt = st.session_state[note_key]
    if new_txt and new_txt.strip():
        now = datetime.now()
        entry = f"<div class='history-entry'><span class='timestamp'>[{now.strftime('%m/%d %H:%M')}]</span>{new_txt}</div>"
        combined = entry + str(current_note)
        
        df_full = load_data("leads")
        df_full.at[idx, 'note'] = combined
        df_full.at[idx, 'last_interact'] = now.strftime("%Y-%m-%d %H:%M:%S")
        save_data(df_full, "leads")
        
        st.session_state[note_key] = ""
        st.rerun()

# --- 4. SIDEBAR CHUẨN ---
with st.sidebar:
    st.title("🛠️ CRM Tools")
    df_links = load_data("links")
    
    with st.expander("🔗 Add Link / Sales Kit"):
        with st.form("add_l", clear_on_submit=True):
            c = st.selectbox("Loại", ["Quick Link", "Sales Kit"]); t = st.text_input("Tên"); u = st.text_input("URL")
            if st.form_submit_button("Lưu"):
                new_l = pd.DataFrame([{"category": c, "title": t, "url": u}])
                save_data(pd.concat([df_links, new_l], ignore_index=True), "links")
                st.rerun()

    for idx, l in df_links[df_links['category'] == 'Quick Link'].iterrows():
        c1, c2 = st.columns([8, 2])
        c1.markdown(f"**[{l['title']}]({l['url']})**")
        if c2.button("🗑️", key=f"dl_{idx}"):
            save_data(df_links.drop(idx), "links"); st.rerun()

# --- 5. BỘ LỌC & PIPELINE ---
st.title("💼 Pipeline Processing")
c_search, c_slider = st.columns([7, 3])
with c_search:
    query = st.text_input("🔍 Tìm kiếm nhanh:", placeholder="Tên, ID, SĐT...")
with c_slider:
    days = st.slider("Khách chưa đụng tới quá (ngày):", 0, 90, 0)

leads_df = load_data("leads")
if not leads_df.empty:
    if query:
        q = query.lower()
        leads_df = leads_df[leads_df.apply(lambda row: q in str(row).lower(), axis=1)]

    for idx, row in leads_df.iterrows():
        curr_h = str(row['note']) if str(row['note']) != 'nan' else ""
        with st.container(border=True):
            c_info, c_note, c_edit = st.columns([4, 5, 1])
            with c_info:
                st.markdown(f"#### {row['name']}")
                st.write(f"ID: `{row['crm_id']}` | 📱 {row['cell']}")
                st.write(f"🔗 [Mở CRM]({row.get('crm_link', '#')})")
            with c_note:
                st.markdown(f'<div class="history-container">{curr_h}</div>', unsafe_allow_html=True)
                st.text_input("Note & Enter", key=f"note_{idx}", on_change=save_note_v24, args=(idx, curr_h, f"note_{idx}"), label_visibility="collapsed")
