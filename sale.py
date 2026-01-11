import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse

# --- 1. KẾT NỐI DATABASE ---
st.set_page_config(page_title="TMC CRM PRO V24.4", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    # ttl=0 đảm bảo dữ liệu luôn mới nhất
    return conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0).dropna(how='all')

def save_data(df, worksheet):
    df = df.fillna("")
    conn.update(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, data=df)
    st.cache_data.clear()

# --- 2. CSS HISTORY ---
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

# --- 3. LOGIC NOTE NHANH ---
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

# --- 4. RENDER GIAO DIỆN ---
st.title("💼 Pipeline Processing")
try:
    leads_df = load_data("leads")
    if not leads_df.empty:
        for idx, row in leads_df.iterrows():
            curr_h = str(row['note']) if str(row['note']) != 'nan' else ""
            with st.container(border=True):
                c1, c2, c3 = st.columns([4, 5, 1])
                with c1:
                    st.markdown(f"#### {row['name']}")
                    st.write(f"ID: `{row['crm_id']}` | 📱 {row['cell']}")
                with c2:
                    st.markdown(f'<div class="history-container">{curr_h}</div>', unsafe_allow_html=True)
                    st.text_input("Ghi chú & Enter", key=f"note_{idx}", on_change=save_note_v24, 
                                 args=(idx, curr_h, f"note_{idx}"), label_visibility="collapsed")
except Exception as e:
    st.error(f"Đang chờ kết nối dữ liệu chuẩn... (Lỗi: {e})")
