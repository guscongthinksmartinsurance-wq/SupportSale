import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse

# --- 1. DATABASE (Thêm cột crm_link) ---
DB_NAME = "tmc_crm_v23.db"

def init_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cursor = conn.cursor()
    # Thêm crm_link để lưu link mật mã của 7xCRM
    cursor.execute('''CREATE TABLE IF NOT EXISTS leads 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, crm_id TEXT, cell TEXT, 
         work TEXT, email TEXT, state TEXT, status TEXT, last_interact TEXT, note TEXT, crm_link TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS links 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, title TEXT, url TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- 2. CẤU HÌNH ---
st.set_page_config(page_title="TMC CRM Pro V23", layout="wide")

# Hàm lưu note sạch bóng màu vàng
def save_note_v23(lid, current_note, note_key):
    new_txt = st.session_state[note_key]
    if new_txt and new_txt.strip():
        now = datetime.now()
        entry = f"<div style='border-bottom:1px dashed #eee;margin-bottom:5px;'><span style='color:#0366d6;font-weight:bold;'>[{now.strftime('%m/%d %H:%M')}]</span> {new_txt}</div>"
        combined = entry + current_note
        db = sqlite3.connect(DB_NAME)
        db.execute('UPDATE leads SET last_interact = ?, note = ? WHERE id = ?', (now.strftime("%Y-%m-%d %H:%M:%S"), combined, lid))
        db.commit(); db.close()
        st.session_state[note_key] = ""
        st.session_state["needs_refresh"] = True

if st.session_state.get("needs_refresh"):
    st.session_state["needs_refresh"] = False
    st.rerun()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("🛠️ CRM Tools")
    with st.expander("➕ Add New Lead", expanded=True):
        with st.form("new_lead", clear_on_submit=True):
            n = st.text_input("Name"); i = st.text_input("ID Lead"); p = st.text_input("Cell"); lk = st.text_input("Dán Link CRM vào đây (Nếu có)")
            if st.form_submit_button("Save"):
                conn.execute('INSERT INTO leads (name, crm_id, cell, status, last_interact, note, crm_link) VALUES (?,?,?,?,?,?,?)', (n, i, p, "New", "", "", lk))
                conn.commit(); st.rerun()
    
    st.divider()
    df_l = pd.read_sql('SELECT * FROM links', conn)
    with st.expander("🚀 Quick Links", expanded=True):
        for _, r in df_l.iterrows(): st.markdown(f"**[{r['title']}]({r['url']})**")

# --- 4. MAIN VIEW ---
st.title("💼 Pipeline Processing")
leads_df = pd.read_sql('SELECT * FROM leads ORDER BY id DESC', conn)

for _, row in leads_df.iterrows():
    lid = row['id']; curr_h = row['note'] if row['note'] else ""
    crm_url = row['crm_link'] if row['crm_link'] else "#"
    
    with st.container(border=True):
        c1, c2, c3 = st.columns([4, 5, 1])
        with c1:
            st.markdown(f"#### {row['name']}")
            rid = str(row['crm_id']).strip()
            # NÚT BẤM THÔNG MINH: Nhấn vào số ID là mở CRM, nhấn vào Icon là Copy
            st.markdown(f"""
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                    <span style="background:#7d3c98;color:white;padding:1px 4px;border-radius:3px;font-size:10px;">ID</span>
                    <a href="{crm_url}" target="_blank" style="color:#e83e8c;text-decoration:none;font-weight:bold;background:#fef1f6;padding:2px 6px;border-radius:4px;border:1px solid #fce4ec;">🔗 {rid}</a>
                    <span onclick="navigator.clipboard.writeText('{rid}');alert('Copied ID!')" style="cursor:pointer;font-size:14px;">📋</span>
                </div>
            """, unsafe_allow_html=True)
            
            p_c = str(row['cell']).strip(); n_e = urllib.parse.quote(str(row['name'])); m_e = urllib.parse.quote(f"Chao {row['name']}...")
            st.markdown(f"""<div style="display:flex;gap:15px;align-items:center;"><span>📱 <a href="tel:{p_c}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_c}</a></span><a href="rcmobile://sms?number={p_c}&body={m_e}">💬</a><a href="https://calendar.google.com/calendar/r/eventedit?text=TMC_{n_e}" target="_blank">📅</a></div>""", unsafe_allow_html=True)
        
        with c2:
            st.markdown(f'<div style="background:white;border:1px solid #eee;border-radius:6px;padding:10px;height:120px;overflow-y:auto;font-size:13px;">{curr_h}</div>', unsafe_allow_html=True)
            st.text_input("Note & Enter", key=f"n_{lid}", on_change=save_note_v23, args=(lid, curr_h, f"n_{lid}"), label_visibility="collapsed")

        with c3:
            with st.popover("⋮"):
                new_link = st.text_input("Update CRM Link", value=row['crm_link'] if row['crm_link'] else "", key=f"lk_{lid}")
                if st.button("Save Link ✅", key=f"sl_{lid}"):
                    conn.execute('UPDATE leads SET crm_link=? WHERE id=?', (new_link, lid)); conn.commit(); st.rerun()
                if st.button("Del 🗑️", key=f"del_{lid}"):
                    conn.execute('DELETE FROM leads WHERE id=?', (lid,)); conn.commit(); st.rerun()
        st.divider()
