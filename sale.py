import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse

# --- 1. KHỞI TẠO DATABASE (THAY THẾ GOOGLE SHEET) ---
def init_db():
    conn = sqlite3.connect('crm_data.db', check_same_thread=False)
    cursor = conn.cursor()
    # Tạo bảng Leads nếu chưa có
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, crm_id TEXT, cell TEXT, work TEXT, email TEXT, state TEXT,
            status TEXT, last_interact TEXT, note TEXT
        )
    ''')
    # Tạo bảng Links nếu chưa có
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
def get_leads():
    return pd.read_sql('SELECT * FROM leads ORDER BY id DESC', conn)

def get_links():
    return pd.read_sql('SELECT * FROM links', conn)

# --- 3. GIAO DIỆN ---
st.set_page_config(page_title="TMC Pro CRM (No-Sheet)", layout="wide")

with st.sidebar:
    st.title("🛠️ CRM Database")
    
    # Thêm Link mới
    with st.expander("🔗 Add Link / Video"):
        with st.form("add_link"):
            cat = st.selectbox("Loại", ["Quick Link", "Sales Kit"])
            tit = st.text_input("Tiêu đề")
            url = st.text_input("URL")
            if st.form_submit_button("Lưu Link"):
                conn.execute('INSERT INTO links (category, title, url) VALUES (?,?,?)', (cat, tit, url))
                conn.commit(); st.rerun()

    # Hiển thị Links
    links_df = get_links()
    with st.expander("🚀 Quick Links", expanded=True):
        for _, l in links_df[links_df['category'] == 'Quick Link'].iterrows():
            st.markdown(f"**[{l['title']}]({l['url']})**")
    with st.expander("📚 Sales Kit", expanded=True):
        for _, v in links_df[links_df['category'] == 'Sales Kit'].iterrows():
            st.caption(v['title']); st.video(v['url'])

    st.divider()
    # Thêm Lead mới
    with st.expander("➕ Add New Lead", expanded=True):
        with st.form("add_lead"):
            n = st.text_input("Name"); i = st.text_input("ID"); p = st.text_input("Cell")
            w = st.text_input("Work"); e = st.text_input("Email"); s = st.text_input("State")
            if st.form_submit_button("Lưu Lead"):
                conn.execute('''INSERT INTO leads (name, crm_id, cell, work, email, state, status, last_interact, note) 
                             VALUES (?,?,?,?,?,?,?,?,?)''', (n, i, p, w, e, s, "New", "", ""))
                conn.commit(); st.rerun()

# --- MAIN VIEW ---
st.title("💼 Pipeline Processing (Real-time)")

leads_df = get_leads()
# Slider 0-90 ngày
days = st.slider("Hiện khách chưa đụng tới quá (ngày):", 0, 90, 0)

# Logic lọc ngày
leads_df['last_interact_dt'] = pd.to_datetime(leads_df['last_interact'], errors='coerce')
if days > 0:
    mask = (leads_df['last_interact_dt'].isna()) | ((datetime.now() - leads_df['last_interact_dt']).dt.days >= days)
    leads_df = leads_df[mask]

# --- RENDER PIPELINE ---
for idx, row in leads_df.iterrows():
    with st.container():
        c1, c2, c3 = st.columns([4, 5, 1])
        
        with c1:
            st.markdown(f"#### {row['name']}")
            rid = str(row['crm_id']).strip().replace('#', '').lower()
            st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;"><span style="background:#7d3c98;color:white;padding:1px 4px;border-radius:3px;font-size:10px;">ID</span><span onclick="navigator.clipboard.writeText('{rid}');alert('Copied ID: {rid}')" style="color:#e83e8c;cursor:pointer;font-family:monospace;font-weight:bold;background:#f8f9fa;border:1px dashed #e83e8c;padding:2px 6px;border-radius:4px;">📋 {rid}</span></div>""", unsafe_allow_html=True)
            
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
            st.text_area("History", value=row['note'], height=120, disabled=True, key=f"h_{idx}", label_visibility="collapsed")
            # NHẬP VÀ ENTER - LƯU TỨC THÌ
            new_note = st.text_input("Ghi chú & Enter", key=f"in_{idx}", label_visibility="collapsed", placeholder="Nhập note mới...")
            if new_note:
                now = datetime.now()
                combined = f"[{now.strftime('%m/%d')}]: {new_note}\n{row['note']}"
                conn.execute('UPDATE leads SET last_interact = ?, note = ? WHERE id = ?', 
                             (now.strftime("%Y-%m-%d %H:%M:%S"), combined, row['id']))
                conn.commit()
                st.rerun() # Tải lại cực nhanh vì không phụ thuộc Sheet

        with c3:
            with st.popover("⋮"):
                en = st.text_input("Name", value=row['name'], key=f"en_{idx}")
                ec = st.text_input("Cell", value=row['cell'], key=f"ec_{idx}")
                ew = st.text_input("Work", value=row['work'], key=f"ew_{idx}")
                if st.button("Save", key=f"sv_{idx}"):
                    conn.execute('UPDATE leads SET name=?, cell=?, work=? WHERE id=?', (en, ec, ew, row['id']))
                    conn.commit(); st.rerun()
        st.divider()
