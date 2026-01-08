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

# --- 2. HÀM XỬ LÝ CRM (LƯU & KÍCH HOẠT LÀM MỚI) ---
def save_note_realtime(lid, note_key, old_h):
    text = st.session_state[note_key]
    if text:
        now = datetime.now()
        combined = f"[{now.strftime('%m/%d')}]: {text}\n{old_h}"
        # Ghi Database
        cursor = conn.cursor()
        cursor.execute('UPDATE leads SET last_interact = ?, note = ? WHERE id = ?', 
                     (now.strftime("%Y-%m-%d %H:%M:%S"), combined, lid))
        conn.commit()
        # Xóa ô nhập và Bật công tắc làm mới
        st.session_state[note_key] = ""
        st.session_state["refresh_signal"] = True

# --- 3. GIAO DIỆN ---
st.set_page_config(page_title="TMC CRM Pro", layout="wide")

# BỘ CẢM BIẾN TỰ ĐỘNG LÀM MỚI (TRÁNH F5)
if st.session_state.get("refresh_signal"):
    st.session_state["refresh_signal"] = False
    st.rerun()

with st.sidebar:
    st.title("🛠️ CRM Control")
    with st.expander("➕ Add New Lead", expanded=True):
        with st.form("new_l", clear_on_submit=True):
            n = st.text_input("Name KH"); i = st.text_input("ID"); p = st.text_input("Cell"); w = st.text_input("Work")
            if st.form_submit_button("Save"):
                conn.execute('INSERT INTO leads (name, crm_id, cell, work, status, last_interact, note) VALUES (?,?,?,?,?,?,?)', (n, i, p, w, "New", "", ""))
                conn.commit(); st.rerun()
    
    st.divider()
    df_links = pd.read_sql('SELECT * FROM links', conn)
    with st.expander("🚀 Quick Links", expanded=True):
        for _, l in df_links.iterrows(): st.markdown(f"**[{l['title']}]({l['url']})**")

# --- MAIN VIEW ---
st.title("💼 Pipeline Processing")

# Đọc dữ liệu (Luôn là bản mới nhất sau khi Rerun)
leads_df = pd.read_sql('SELECT * FROM leads ORDER BY id DESC', conn)

for _, row in leads_df.iterrows():
    lid = row['id']
    input_key = f"in_{lid}"
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
            # ENTER LÀM MỚI TỨC THÌ QUA CALLBACK
            st.text_input("Ghi chú mới & Enter", key=input_key, on_change=save_note_realtime, args=(lid, input_key, curr_h), label_visibility="collapsed", placeholder="Nhập note...")

        with c3:
            if st.button("🗑️", key=f"del_{lid}"):
                conn.execute('DELETE FROM leads WHERE id=?', (lid,)); conn.commit(); st.rerun()
        st.divider()
