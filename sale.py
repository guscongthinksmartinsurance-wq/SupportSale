import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse

# --- 1. KHỞI TẠO DATABASE (CRM LOCAL) ---
DB_NAME = "tmc_crm_v16.db"

def init_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS leads 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, crm_id TEXT, cell TEXT, 
         work TEXT, email TEXT, state TEXT, status TEXT, last_interact TEXT, note TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS links 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, title TEXT, url TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- 2. GIAO DIỆN ---
st.set_page_config(page_title="TMC CRM Pro", layout="wide")

# Sidebar
with st.sidebar:
    st.title("🛠️ Local CRM")
    with st.expander("➕ Add New Lead", expanded=True):
        with st.form("new_l", clear_on_submit=True):
            n = st.text_input("Name"); i = st.text_input("ID"); p = st.text_input("Cell"); w = st.text_input("Work")
            if st.form_submit_button("Save"):
                conn.execute('INSERT INTO leads (name, crm_id, cell, work, status, last_interact, note) VALUES (?,?,?,?,?,?,?)', (n, i, p, w, "New", "", ""))
                conn.commit(); st.rerun()

# --- MAIN VIEW ---
st.title("💼 Pipeline Processing")

# Đọc dữ liệu mới nhất
leads_df = pd.read_sql('SELECT * FROM leads ORDER BY id DESC', conn)

for _, row in leads_df.iterrows():
    lid = row['id']
    curr_h = row['note'] if row['note'] else ""
    input_key = f"in_{lid}"

    with st.container():
        c1, c2, c3 = st.columns([4, 5, 1])
        with c1:
            st.markdown(f"#### {row['name']}")
            rid = str(row['crm_id']).strip().replace('#', '').lower()
            st.markdown(f"""<div style="margin-bottom:8px;"><span style="background:#7d3c98;color:white;padding:1px 4px;border-radius:3px;font-size:10px;">ID</span> <code style="color:#e83e8c;">{rid}</code></div>""", unsafe_allow_html=True)
            
            p_c = str(row['cell']).strip(); n_e = urllib.parse.quote(str(row['name'])); m_e = urllib.parse.quote(f"Chao {row['name']}...")
            
            # Đầy đủ Icon CRM
            st.markdown(f"""<div style="display:flex;gap:15px;align-items:center;">
                <span>📱 <a href="tel:{p_c}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_c}</a></span>
                <a href="rcmobile://sms?number={p_c}&body={m_e}">💬</a>
                <a href="mailto:?body={m_e}">📧</a>
                <a href="https://calendar.google.com/calendar/r/eventedit?text=TMC_{n_e}" target="_blank">📅</a>
            </div>""", unsafe_allow_html=True)
        
        with c2:
            st.text_area("History", value=curr_h, height=120, disabled=True, key=f"view_{lid}", label_visibility="collapsed")
            
            # XỬ LÝ NHẬP NOTE - DÙNG LOGIC KIỂM TRA TRỰC TIẾP
            new_note = st.text_input("Ghi chú mới & Enter", key=input_key, label_visibility="collapsed", placeholder="Nhập note...")
            
            if new_note: # Khi anh vừa nhấn Enter xong
                now = datetime.now()
                combined = f"[{now.strftime('%m/%d')}]: {new_note}\n{curr_h}"
                # 1. Ghi Database
                conn.execute('UPDATE leads SET last_interact = ?, note = ? WHERE id = ?', 
                             (now.strftime("%Y-%m-%d %H:%M:%S"), combined, lid))
                conn.commit()
                # 2. Xóa ô nhập trong RAM
                st.session_state[input_key] = ""
                # 3. ÉP LÀM MỚI TRANG NGAY LẬP TỨC
                st.rerun()

        with c3:
            if st.button("🗑️", key=f"del_{lid}"):
                conn.execute('DELETE FROM leads WHERE id=?', (lid,)); conn.commit(); st.rerun()
        st.divider()
