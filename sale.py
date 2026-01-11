import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import urllib.parse

# --- CONFIG ---
st.set_page_config(page_title="TMC CRM CLOUD V26", layout="wide")

# --- KẾT NỐI GOOGLE SHEETS ---
# Sử dụng thư viện chuyên dụng để tốc độ nhanh nhất
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    return conn.read(spreadsheet=st.secrets["gsheet_url"], worksheet=worksheet, ttl=0)

# --- XỬ LÝ LƯU DỮ LIỆU ---
def save_data(df, worksheet):
    conn.update(spreadsheet=st.secrets["gsheet_url"], worksheet=worksheet, data=df)
    st.cache_data.clear() # Ép App xóa bộ nhớ đệm để hiện Note ngay lập tức

# --- GIAO DIỆN ---
st.markdown("""
    <style>
    .history-container {
        background-color: #ffffff; border: 1px solid #e1e4e8; border-radius: 6px;
        padding: 10px; height: 150px; overflow-y: auto; font-family: sans-serif; font-size: 13px;
    }
    .history-entry { border-bottom: 1px dashed #eee; margin-bottom: 5px; padding-bottom: 2px; }
    .timestamp { color: #0366d6; font-weight: bold; margin-right: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 1. SIDEBAR (LINKS & ADD LEAD) ---
with st.sidebar:
    st.title("🛠️ Google Cloud Tools")
    # Load Links
    try:
        df_links = load_data("links")
    except:
        df_links = pd.DataFrame(columns=["category", "title", "url"])

    with st.expander("🔗 Add Link"):
        with st.form("add_l", clear_on_submit=True):
            c = st.selectbox("Loại", ["Quick Link", "Sales Kit"]); t = st.text_input("Tên"); u = st.text_input("URL")
            if st.form_submit_button("Lưu"):
                new_l = pd.DataFrame([{"category": c, "title": t, "url": u}])
                df_links = pd.concat([df_links, new_l], ignore_index=True)
                save_data(df_links, "links")
                st.rerun()

    # Render Links
    if not df_links.empty:
        for _, l in df_links[df_links['category'] == 'Quick Link'].iterrows():
            st.markdown(f"**[{l['title']}]({l['url']})**")
    
    st.divider()
    with st.expander("➕ Add New Lead"):
        with st.form("new_l", clear_on_submit=True):
            n = st.text_input("Name"); i = st.text_input("ID"); p = st.text_input("Cell"); cl = st.text_input("Link CRM")
            if st.form_submit_button("Lưu Lead"):
                df_leads = load_data("leads")
                new_lead = pd.DataFrame([{"name":n, "crm_id":i, "cell":p, "status":"New", "last_interact":"", "note":"", "crm_link":cl}])
                df_leads = pd.concat([df_leads, new_lead], ignore_index=True)
                save_data(df_leads, "leads")
                st.rerun()

# --- 2. MAIN APP ---
st.title("💼 Pipeline Processing")
query = st.text_input("🔍 Tìm kiếm:", placeholder="Nhập tên hoặc số điện thoại...")

# Load Leads
try:
    df_leads = load_data("leads")
except:
    df_leads = pd.DataFrame(columns=["name", "crm_id", "cell", "status", "last_interact", "note", "crm_link"])

if query and not df_leads.empty:
    df_leads = df_leads[df_leads['name'].str.contains(query, case=False, na=False) | df_leads['cell'].str.contains(query, na=False)]

# --- RENDER LEADS ---
for idx, row in df_leads.iterrows():
    with st.container(border=True):
        c1, c2, c3 = st.columns([4, 5, 1])
        with c1:
            st.markdown(f"#### {row['name']}")
            st.caption(f"ID: {row['crm_id']} | Cell: {row['cell']}")
            st.link_button("Mở CRM", row['crm_link'] if str(row['crm_link']) != 'nan' else "#")

        with c2:
            st.markdown(f'<div class="history-container">{row["note"]}</div>', unsafe_allow_html=True)
            # Ô nhập note
            new_note = st.text_input("Note & Enter", key=f"in_{idx}", placeholder="Ghi chú mới...")
            if new_note:
                now = datetime.now().strftime('%m/%d %H:%M')
                entry = f"<div class='history-entry'><span class='timestamp'>[{now}]</span>{new_note}</div>"
                df_leads.at[idx, 'note'] = entry + str(row['note'])
                df_leads.at[idx, 'last_interact'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                save_data(df_leads, "leads")
                st.rerun()

        with c3:
            if st.button("🗑️", key=f"del_{idx}"):
                df_leads = df_leads.drop(idx)
                save_data(df_leads, "leads")
                st.rerun()
