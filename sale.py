import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse

# --- 1. KẾT NỐI DATABASE ---
DB_NAME = "tmc_crm_v21.db"

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

# --- 2. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="TMC CRM V21", layout="wide")

# CSS cho History Timeline chuyên nghiệp
st.markdown("""
    <style>
    .history-container {
        background-color: #ffffff;
        border: 1px solid #e1e4e8;
        border-radius: 6px;
        padding: 10px;
        height: 150px;
        overflow-y: auto;
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
        line-height: 1.6;
        color: #24292e;
    }
    .history-entry {
        border-bottom: 1px dashed #eee;
        margin-bottom: 5px;
        padding-bottom: 2px;
    }
    .timestamp { color: #0366d6; font-weight: bold; margin-right: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR (QUẢN LÝ TÍNH NĂNG PHỤ) ---
with st.sidebar:
    st.title("🛠️ CRM Tools")
    with st.expander("🔗 Add Link / Sales Kit"):
        with st.form("add_l", clear_on_submit=True):
            c = st.selectbox("Loại", ["Quick Link", "Sales Kit"])
            t = st.text_input("Tên"); u = st.text_input("URL")
            if st.form_submit_button("Lưu"):
                conn.execute('INSERT INTO links (category, title, url) VALUES (?,?,?)', (c, t, u))
                conn.commit(); st.rerun()

    df_links = pd.read_sql('SELECT * FROM links', conn)
    with st.expander("🚀 Quick Links", expanded=True):
        for _, l in df_links[df_links['category'] == 'Quick Link'].iterrows():
            st.markdown(f"**[{l['title']}]({l['url']})**")
    
    st.divider()
    with st.expander("➕ Add New Lead", expanded=True):
        with st.form("new_lead", clear_on_submit=True):
            n = st.text_input("Name"); i = st.text_input("ID"); p = st.text_input("Cell"); w = st.text_input("Work"); e = st.text_input("Email"); s = st.text_input("State")
            if st.form_submit_button("Lưu Lead"):
                conn.execute('INSERT INTO leads (name, crm_id, cell, work, email, state, status, last_interact, note) VALUES (?,?,?,?,?,?,?,?,?)', (n, i, p, w, e, s, "New", "", ""))
                conn.commit(); st.rerun()

# --- 4. HÀM XỬ LÝ LƯU NOTE CHỐNG NHÂN BẢN ---
def save_note_v21(lid, current_note, note_key):
    new_txt = st.session_state[note_key]
    if new_txt and new_txt.strip():
        now = datetime.now()
        # Định dạng Note: Mỗi dòng là một Entry riêng biệt
        entry = f"<div class='history-entry'><span class='timestamp'>[{now.strftime('%m/%d %H:%M')}]</span>{new_txt}</div>"
        combined = entry + current_note
        
        # Ghi DB
        db = sqlite3.connect(DB_NAME)
        db.execute('UPDATE leads SET last_interact = ?, note = ? WHERE id = ?', 
                  (now.strftime("%Y-%m-%d %H:%M:%S"), combined, lid))
        db.commit()
        db.close()
        
        # XÓA TRẠNG THÁI Ô NHẬP NGAY LẬP TỨC ĐỂ CHỐNG LẶP
        st.session_state[note_key] = ""
        st.rerun()

# --- 5. MAIN VIEW ---
st.title("💼 Pipeline Processing (Stable)")
leads_df = pd.read_sql('SELECT * FROM leads ORDER BY id DESC', conn)

for _, row in leads_df.iterrows():
    lid = row['id']
    curr_h = row['note'] if row['note'] else ""
    
    with st.container(border=True):
        c_info, c_note, c_edit = st.columns([4, 5, 1])
        
        with c_info:
            st.markdown(f"#### {row['name']}")
            rid = str(row['crm_id']).strip().replace('#', '').lower()
            st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;"><span style="background:#7d3c98;color:white;padding:1px 4px;border-radius:3px;font-size:10px;">ID</span><span onclick="navigator.clipboard.writeText('{rid}');alert('Copied!')" style="color:#e83e8c;cursor:pointer;font-family:monospace;font-weight:bold;background:#f8f9fa;border:1px dashed #e83e8c;padding:2px 6px;border-radius:4px;">📋 {rid}</span></div>""", unsafe_allow_html=True)
            
            p_c = str(row['cell']).strip(); p_w = str(row['work']).strip()
            n_e = urllib.parse.quote(str(row['name'])); m_e = urllib.parse.quote(f"Chao {row['name']}...")
            
            st.markdown(f"""<div style="display:flex;gap:15px;align-items:center;">
                <span>📱 <a href="tel:{p_c}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_c}</a></span>
                <a href="rcmobile://sms?number={p_c}&body={m_e}">💬</a>
                <a href="mailto:{row['email']}?body={m_e}">📧</a>
                <a href="https://calendar.google.com/calendar/r/eventedit?text=TMC_{n_e}" target="_blank">📅</a>
            </div>""", unsafe_allow_html=True)
            if p_w and p_w not in ['0', '']:
                st.markdown(f'📞 Work: <a href="tel:{p_w}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_w}</a>', unsafe_allow_html=True)
            st.caption(f"📍 State: {row['state']}")

        with c_note:
            # Hiển thị dạng Timeline - Không lo bị gạch chéo icon tròn
            st.markdown(f'<div class="history-container">{curr_h}</div>', unsafe_allow_html=True)
            # Nhập note
            st.text_input("Ghi chú & Enter", key=f"note_{lid}", on_change=save_note_v21, args=(lid, curr_h, f"note_{lid}"), label_visibility="collapsed", placeholder="Note nhanh...")

        with c_edit:
            # PHỤC HỒI PHẦN EDIT LEAD
            with st.popover("⋮"):
                st.subheader("Edit Lead")
                en = st.text_input("Name", value=row['name'], key=f"en_{lid}")
                ei = st.text_input("ID", value=row['crm_id'], key=f"ei_{lid}")
                ec = st.text_input("Cell", value=row['cell'], key=f"ec_{lid}")
                ew = st.text_input("Work", value=row['work'], key=f"ew_{lid}")
                ee = st.text_input("Email", value=row['email'], key=f"ee_{lid}")
                es = st.text_input("State", value=row['state'], key=f"es_{lid}")
                
                c1, c2 = st.columns(2)
                if c1.button("Save ✅", key=f"sv_{lid}"):
                    conn.execute('UPDATE leads SET name=?, crm_id=?, cell=?, work=?, email=?, state=? WHERE id=?', (en, ei, ec, ew, ee, es, lid))
                    conn.commit(); st.rerun()
                if c2.button("Del 🗑️", key=f"del_{lid}"):
                    conn.execute('DELETE FROM leads WHERE id=?', (lid,)); conn.commit(); st.rerun()
        st.divider()
