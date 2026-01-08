import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse

# --- 1. KHỞI TẠO DATABASE ---
DB_NAME = "tmc_crm_v18.db"

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
st.set_page_config(page_title="TMC CRM MASTER V18", layout="wide")

# Hàm xử lý lưu note tách biệt để tránh lỗi đỏ
def update_note_db(lid, new_msg, old_h):
    if new_msg:
        now = datetime.now()
        combined = f"[{now.strftime('%m/%d')}]: {new_msg}\n{old_h}"
        c = conn.cursor()
        c.execute('UPDATE leads SET last_interact = ?, note = ? WHERE id = ?', 
                  (now.strftime("%Y-%m-%d %H:%M:%S"), combined, lid))
        conn.commit()
        return combined
    return old_h

with st.sidebar:
    st.title("🛠️ Control Center")
    with st.expander("🔗 Add Link / Sales Kit"):
        with st.form("add_l", clear_on_submit=True):
            c_type = st.selectbox("Loại", ["Quick Link", "Sales Kit"])
            t_title = st.text_input("Tên")
            u_url = st.text_input("URL")
            if st.form_submit_button("Lưu"):
                conn.execute('INSERT INTO links (category, title, url) VALUES (?,?,?)', (c_type, t_title, u_url))
                conn.commit(); st.rerun()

    df_links = pd.read_sql('SELECT * FROM links', conn)
    with st.expander("🚀 Quick Links", expanded=True):
        for _, l in df_links[df_links['category'] == 'Quick Link'].iterrows():
            st.markdown(f"**[{l['title']}]({l['url']})**")
    with st.expander("📚 Sales Kit", expanded=True):
        for _, v in df_links[df_links['category'] == 'Sales Kit'].iterrows():
            st.caption(v['title']); st.video(v['url'])
    
    st.divider()
    with st.expander("➕ Add New Lead", expanded=True):
        with st.form("new_lead", clear_on_submit=True):
            n = st.text_input("Name"); i = st.text_input("ID"); p = st.text_input("Cell")
            w = st.text_input("Work"); e = st.text_input("Email"); s = st.text_input("State")
            if st.form_submit_button("Save Lead"):
                conn.execute('INSERT INTO leads (name, crm_id, cell, work, email, state, status, last_interact, note) VALUES (?,?,?,?,?,?,?,?,?)', (n, i, p, w, e, s, "New", "", ""))
                conn.commit(); st.rerun()

# --- MAIN VIEW ---
st.title("💼 Pipeline Processing")

# Đọc dữ liệu
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
            
            p_cell = str(row['cell']).strip(); p_work = str(row['work']).strip()
            n_enc = urllib.parse.quote(str(row['name'])); m_enc = urllib.parse.quote(f"Chao {row['name']}...")
            
            st.markdown(f"""<div style="display:flex;gap:15px;align-items:center;">
                <span>📱 <a href="tel:{p_cell}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_cell}</a></span>
                <a href="rcmobile://sms?number={p_cell}&body={m_enc}">💬</a>
                <a href="mailto:{row['email']}?body={m_enc}">📧</a>
                <a href="https://calendar.google.com/calendar/r/eventedit?text=TMC_{n_enc}" target="_blank">📅</a>
            </div>""", unsafe_allow_html=True)
            if p_work and p_work not in ['0', '']:
                st.markdown(f'📞 Work: <a href="tel:{p_work}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_work}</a>', unsafe_allow_html=True)
            st.caption(f"📍 State: {row['state']}")

        with c_note:
            # Dùng st.empty để cập nhật nội dung ô History mà không bị gạch chéo
            history_placeholder = st.empty()
            history_placeholder.text_area("History", value=curr_h, height=120, disabled=True, key=f"v_{lid}", label_visibility="collapsed")
            
            # Ô NHẬP NOTE - Dùng form nhỏ để Enter ổn định 100%
            with st.form(key=f"fn_{lid}", clear_on_submit=True):
                msg = st.text_input("Note", label_visibility="collapsed", placeholder="Nhập note...")
                if st.form_submit_button("Update"):
                    if msg:
                        new_h = update_note_db(lid, msg, curr_h)
                        # Ép ô History hiện Note mới ngay lập tức
                        history_placeholder.text_area("History", value=new_h, height=120, disabled=True, key=f"v2_{lid}", label_visibility="collapsed")
                        st.toast("✅ Đã lưu!")
                        st.rerun()

        with c_edit:
            with st.popover("⋮"):
                en = st.text_input("Name", value=row['name'], key=f"en_{lid}")
                ei = st.text_input("ID", value=row['crm_id'], key=f"ei_{lid}")
                ec = st.text_input("Cell", value=row['cell'], key=f"ec_{lid}")
                ew = st.text_input("Work", value=row['work'], key=f"ew_{lid}")
                ee = st.text_input("Email", value=row['email'], key=f"ee_{lid}")
                es = st.text_input("State", value=row['state'], key=f"es_{lid}")
                if st.button("Save Edit", key=f"sv_{lid}"):
                    conn.execute('UPDATE leads SET name=?, crm_id=?, cell=?, work=?, email=?, state=? WHERE id=?', (en, ei, ec, ew, ee, es, lid))
                    conn.commit(); st.rerun()
                if st.button("Delete", key=f"del_{lid}", type="primary"):
                    conn.execute('DELETE FROM leads WHERE id=?', (lid,)); conn.commit(); st.rerun()
        st.divider()
