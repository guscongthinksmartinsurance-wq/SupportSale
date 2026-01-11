import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse

# --- 1. KẾT NỐI GOOGLE API (KHỚP VỚI SECRET ANH VỪA DÁN) ---
st.set_page_config(page_title="TMC CRM PRO V24.4", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# Link Sheet anh vừa đưa
SHEET_URL = "https://docs.google.com/spreadsheets/d/1QSMUSOkeazaX1bRpOQ4DVHqu0_j-uz4maG3l7Lj1c1M/edit"

def load_data(worksheet):
    # ttl=0 để nhập Note là nó hiện lên ngay, không bị trễ
    return conn.read(spreadsheet=SHEET_URL, worksheet=worksheet, ttl=0).dropna(how='all')

def save_data(df, worksheet):
    df = df.fillna("")
    conn.update(spreadsheet=SHEET_URL, worksheet=worksheet, data=df)
    st.cache_data.clear()

# --- 2. CSS HISTORY CHUẨN (GIỮ NGUYÊN BẢN GỐC) ---
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

# --- 3. LOGIC LƯU NOTE NHANH (BẢN GỐC NHẤN ENTER ĂN NGAY) ---
def save_note_v24(idx, current_note, note_key):
    new_txt = st.session_state[note_key]
    if new_txt and new_txt.strip():
        now = datetime.now()
        entry = f"<div class='history-entry'><span class='timestamp'>[{now.strftime('%m/%d %H:%M')}]</span>{new_txt}</div>"
        combined = entry + str(current_note)
        
        # Đọc và ghi thẳng lên Google Sheet
        df_full = load_data("leads")
        df_full.at[idx, 'note'] = combined
        df_full.at[idx, 'last_interact'] = now.strftime("%Y-%m-%d %H:%M:%S")
        save_data(df_full, "leads")
        
        st.session_state[note_key] = ""
        st.rerun()

# --- 4. GIAO DIỆN CHÍNH (SIDEBAR & PIPELINE) ---
with st.sidebar:
    st.title("🛠️ CRM Tools")
    df_links = load_data("links")
    # Hiển thị các link nhanh của anh
    for idx, l in df_links[df_links['category'] == 'Quick Link'].iterrows():
        st.markdown(f"**[{l['title']}]({l['url']})**")

st.title("💼 Pipeline Processing")
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
                # Ô nhập Note chuẩn của anh
                st.text_input("Ghi chú & Enter", key=f"note_{idx}", on_change=save_note_v24, 
                             args=(idx, curr_h, f"note_{idx}"), label_visibility="collapsed")
