import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse

# --- 1. KHỞI TẠO DATABASE ---
DB_NAME = "tmc_crm_v15.db"

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

with st.sidebar:
    st.title("🛠️ Local CRM Control")
    with st.expander("➕ Add New Lead", expanded=True):
        with st.form("new_lead_form", clear_on_submit=True):
            n = st.text_input("Name KH"); i = st.text_input("ID"); p = st.text_input("Cell"); w = st.text_input("Work")
            if st.form_submit_button("Lưu Lead"):
                conn.execute('INSERT INTO leads (name, crm_id, cell, work, status, last_interact, note) VALUES (?,?,?,?,?,?,?)', (n, i, p, w, "New", "", ""))
                conn.commit(); st.rerun()
    
    st.divider()
    df_links = pd.read_sql('SELECT * FROM links', conn)
    with st.expander("🚀 Quick Links", expanded=True):
        for _, l in df_links.iterrows(): st.markdown(f"**[{l['title']}]({l['url']})**")

# --- MAIN VIEW ---
st.title("💼 Pipeline Processing")

# Đọc dữ liệu mới nhất
leads_df = pd.read_sql('SELECT * FROM leads ORDER BY id DESC', conn)

for _, row in leads_df.iterrows():
    lid = row['id']
    curr_h = row['note'] if row['note'] else ""

    with st.container():
        c1, c2, c3 = st.columns([4, 5, 1])
        with c1:
            st.markdown(f"#### {row['name']}")
            rid = str(row['crm_id']).strip().replace('#', '').lower()
            st.markdown(f"""<div style="margin-bottom:8px;"><span style="background:#7d3c98;color:white;padding:1px 4px;border-radius:3px;font-size:10px;">ID</span> <code style="color:#e83e8c;">{rid}</code></div>""", unsafe_allow_html=True)
            
            p_c = str(row['cell']).strip(); n_e = urllib.parse.quote(str(row['name'])); m_e = urllib.parse.quote(f"Chao {row['name']}...")
            
            # FULL ICONS: Call, SMS, Email, Calendar
            st.markdown(f"""<div style="display:flex;gap:15px;align-items:center;">
                <span>📱 <a href="tel:{p_c}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_c}</a></span>
                <a href="rcmobile://sms?number={p_c}&body={m_e}">💬</a>
                <a href="mailto:?body={m_e}">📧</a>
                <a href="https://calendar.google.com/calendar/r/eventedit?text=TMC_{n_e}" target="_blank">📅</a>
            </div>""", unsafe_allow_html=True)
            if row['work']: st.markdown(f'📞 Work: <a href="tel:{row["work"]}" style="color:#28a745;font-weight:bold;text-decoration:none;">{row["work"]}</a>', unsafe_allow_html=True)
        
        with c2:
            st.text_area("History", value=curr_h, height=120, disabled=True, key=f"view_{lid}", label_visibility="collapsed")
            
            # GIẢI PHÁP CRM: Dùng mini-form để Enter là Rerun ngay lập tức
            with st.form(key=f"note_form_{lid}", clear_on_submit=True):
                new_msg = st.text_input("Ghi chú mới", label_visibility="collapsed", placeholder="Nhập ghi chú & Enter...")
                if st.form_submit_button("Lưu Note", help="Nhấn Enter để lưu nhanh"):
                    if new_msg:
                        now = datetime.now()
                        combined = f"[{now.strftime('%m/%d')}]: {new_msg}\n{curr_h}"
                        conn.execute('UPDATE leads SET last_interact = ?, note = ? WHERE id = ?', 
                                     (now.strftime("%Y-%m-%d %H:%M:%S"), combined, lid))
                        conn.commit()
                        st.rerun() # Form Submit Button ép App phải tải lại dữ liệu mới nhất

        with c3:
            if st.button("🗑️", key=f"del_{lid}"):
                conn.execute('DELETE FROM leads WHERE id=?', (lid,)); conn.commit(); st.rerun()
        st.divider()
