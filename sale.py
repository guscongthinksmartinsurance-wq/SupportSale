import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse
import os

# --- 1. KHỞI TẠO DATABASE (CRM NỘI BỘ) ---
DB_NAME = "my_crm_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cursor = conn.cursor()
    # Tạo bảng Leads
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, crm_id TEXT, cell TEXT, work TEXT, email TEXT, state TEXT,
            status TEXT, last_interact TEXT, note TEXT
        )
    ''')
    # Tạo bảng Links
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT, title TEXT, url TEXT
        )
    ''')
    conn.commit()
    return conn

conn = init_db()

# --- 2. HÀM XỬ LÝ DỮ LIỆU ---
def save_new_note(lead_id, new_text, old_note):
    if new_text:
        now = datetime.now()
        combined = f"[{now.strftime('%m/%d')}]: {new_text}\n{old_note}"
        cursor = conn.cursor()
        cursor.execute('UPDATE leads SET last_interact = ?, note = ? WHERE id = ?', 
                     (now.strftime("%Y-%m-%d %H:%M:%S"), combined, lead_id))
        conn.commit()
        st.toast("✅ Đã lưu Note!")

# --- 3. GIAO DIỆN SIDEBAR ---
st.set_page_config(page_title="TMC Local CRM", layout="wide")

with st.sidebar:
    st.title("🛠️ Local Control")
    
    # Quản lý Links
    with st.expander("🔗 Add Link / Video"):
        with st.form("add_link"):
            cat = st.selectbox("Loại", ["Quick Link", "Sales Kit"])
            tit = st.text_input("Tên")
            url = st.text_input("URL")
            if st.form_submit_button("Lưu"):
                conn.execute('INSERT INTO links (category, title, url) VALUES (?,?,?)', (cat, tit, url))
                conn.commit(); st.rerun()

    df_links = pd.read_sql('SELECT * FROM links', conn)
    with st.expander("🚀 Quick Links", expanded=True):
        for _, l in df_links[df_links['category'] == 'Quick Link'].iterrows():
            st.markdown(f"**[{l['title']}]({l['url']})**")
    with st.expander("📚 Sales Kit", expanded=True):
        for _, v in df_links[df_links['category'] == 'Sales Kit'].iterrows():
            st.caption(v['title']); st.video(v['url'])

    st.divider()
    # Thêm Lead mới
    with st.expander("➕ Add New Lead", expanded=True):
        with st.form("new_lead"):
            n = st.text_input("Name KH"); i = st.text_input("ID"); p = st.text_input("Cell")
            w = st.text_input("Work"); e = st.text_input("Email"); s = st.text_input("State")
            if st.form_submit_button("Lưu Lead"):
                conn.execute('''INSERT INTO leads (name, crm_id, cell, work, email, state, status, last_interact, note) 
                             VALUES (?,?,?,?,?,?,?,?,?)''', (n, i, p, w, e, s, "New", "", ""))
                conn.commit(); st.rerun()

# --- MAIN VIEW ---
st.title("💼 Pipeline Processing (SQLite Speed)")

# Đọc dữ liệu
leads_df = pd.read_sql('SELECT * FROM leads ORDER BY id DESC', conn)

days = st.slider("Hiện khách chưa đụng tới quá (ngày):", 0, 90, 0)
leads_df['last_interact_dt'] = pd.to_datetime(leads_df['last_interact'], errors='coerce')
if days > 0:
    mask = (leads_df['last_interact_dt'].isna()) | ((datetime.now() - leads_df['last_interact_dt']).dt.days >= days)
    leads_df = leads_df[mask]

# Hiển thị
for _, row in leads_df.iterrows():
    with st.container():
        c1, c2, c3 = st.columns([4, 5, 1])
        
        with c1:
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

        with c2:
            st.text_area("History", value=row['note'], height=120, disabled=True, key=f"h_{row['id']}", label_visibility="collapsed")
            # Gõ Note và Enter là Rerun ngay lập tức vì Database cực nhanh
            new_note = st.text_input("Ghi chú & Enter", key=f"in_{row['id']}", label_visibility="collapsed", placeholder="Nhập note...")
            if new_note:
                save_new_note(row['id'], new_note, row['note'])
                st.rerun()

        with c3:
            with st.popover("⋮"):
                en = st.text_input("Name", value=row['name'], key=f"en_{row['id']}")
                ec = st.text_input("Cell", value=row['cell'], key=f"ec_{row['id']}")
                ew = st.text_input("Work", value=row['work'], key=f"ew_{row['id']}")
                ee = st.text_input("Email", value=row['email'], key=f"ee_{row['id']}")
                es = st.text_input("State", value=row['state'], key=f"es_{row['id']}")
                if st.button("Save Edit", key=f"sv_{row['id']}"):
                    conn.execute('UPDATE leads SET name=?, cell=?, work=?, email=?, state=? WHERE id=?', (en, ec, ew, ee, es, row['id']))
                    conn.commit(); st.rerun()
        st.divider()
