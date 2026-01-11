import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse

# --- 1. KẾT NỐI GOOGLE API ---
st.set_page_config(page_title="TMC CRM PRO V24.4", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# ID file Sheet anh vừa gửi
SHEET_URL = "https://docs.google.com/spreadsheets/d/1QSMUSOkeazaX1bRpOQ4DVHqu0_j-uz4maG3l7Lj1c1M/edit"

def load_data(worksheet):
    # Đọc dữ liệu từ Sheet leads hoặc links 
    return conn.read(spreadsheet=SHEET_URL, worksheet=worksheet, ttl=0).dropna(how='all')

def save_data(df, worksheet):
    df = df.fillna("")
    conn.update(spreadsheet=SHEET_URL, worksheet=worksheet, data=df)
    st.cache_data.clear()

# --- 2. CSS HISTORY CHUẨN ---
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

# --- 3. LOGIC NOTE NHANH (BẢN GỐC CỦA ANH) ---
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

# --- 4. RENDER PIPELINE ---
st.title("💼 Pipeline Processing")
leads_df = load_data("leads")

if not leads_df.empty:
    for idx, row in leads_df.iterrows():
        curr_h = str(row['note']) if str(row['note']) != 'nan' else ""
        crm_url = str(row['crm_link']) if str(row['crm_link']) != 'nan' else "#"
        
        with st.container(border=True):
            c_info, c_note, c_edit = st.columns([4, 5, 1])
            with c_info:
                st.markdown(f"#### {row['name']}")
                # Hiển thị ID và các nút RingCentral chuẩn Baseline 
                st.markdown(f"ID: `{row['crm_id']}` | 📱 {row['cell']}")
                st.write(f"🔗 [Mở CRM]({crm_url})")
            
            with c_note:
                st.markdown(f'<div class="history-container">{curr_h}</div>', unsafe_allow_html=True)
                # Ô nhập note ăn ngay, không cần F5
                st.text_input("Ghi chú & Enter", key=f"note_{idx}", on_change=save_note_v24, 
                             args=(idx, curr_h, f"note_{idx}"), label_visibility="collapsed", placeholder="Note nhanh...")
