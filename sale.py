import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse

# --- 1. KHỞI TẠO DATABASE ---
DB_NAME = "tmc_crm_v17.db"

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
st.set_page_config(page_title="TMC CRM PRO V17", layout="wide")

with st.sidebar:
    st.title("🛠️ Control Center")
    # 🔗 QUẢN LÝ LINKS & SALES KIT
    with st.expander("🔗 Add Link / Sales Kit"):
        with st.form("add_l", clear_on_submit=True):
            c = st.selectbox("Loại", ["Quick Link", "Sales Kit"])
            t = st.text_input("Tên/Tiêu đề")
            u = st.text_input("URL (Link hoặc Link Video)")
            if st.form_submit_button("Lưu"):
                conn.execute('INSERT INTO links (category, title, url) VALUES (?,?,?)', (c, t, u))
                conn.commit(); st.rerun()

    df_links = pd.read_sql('SELECT * FROM links', conn)
    with st.expander("🚀 Quick Links", expanded=True):
        for _, l in df_links[df_links['category'] == 'Quick Link'].iterrows():
            st.markdown(f"**[{l['title']}]({l['url']})**")
    with st.expander("📚 Sales Kit (Videos)", expanded=True):
        for _, v in df_links[df_links['category'] == 'Sales Kit'].iterrows():
            st.caption(v['title']); st.video(v['url'])
    
    st.divider()
    # ➕ THÊM LEAD MỚI FULL TRƯỜNG
    with st.expander("➕ Add New Lead", expanded=True):
        with st.form("new_lead", clear_on_submit=True):
            n = st.text_input("Name KH"); i = st.text_input("ID"); p = st.text_input("Cell")
            w = st.text_input("Workphone"); e = st.text_input("Email"); s = st.text_input("State")
            if st.form_submit_button("Save Lead"):
                conn.execute('''INSERT INTO leads (name, crm_id, cell, work, email, state, status, last_interact, note) 
                             VALUES (?,?,?,?,?,?,?,?,?)''', (n, i, p, w, e, s, "New", "", ""))
                conn.commit(); st.rerun()

# --- MAIN VIEW ---
st.title("💼 Pipeline Processing")

# Đọc dữ liệu mới nhất
leads_df = pd.read_sql('SELECT * FROM leads ORDER BY id DESC', conn)
days = st.slider("Hiện khách chưa đụng tới quá (ngày):", 0, 90, 0)

# Render Lead Pipeline
for _, row in leads_df.iterrows():
    lid = row['id']
    curr_h = row['note'] if row['note'] else ""

    with st.container():
        c_info, c_note, c_edit = st.columns([4, 5, 1])
        
        with c_info:
            st.markdown(f"#### {row['name']}")
            rid = str(row['crm_id']).strip().replace('#', '').lower()
            st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;"><span style="background:#7d3c98;color:white;padding:1px 4px;border-radius:3px;font-size:10px;">ID</span><span onclick="navigator.clipboard.writeText('{rid}');alert('Copied!')" style="color:#e83e8c;cursor:pointer;font-family:monospace;font-weight:bold;background:#f8f9fa;border:1px dashed #e83e8c;padding:2px 6px;border-radius:4px;">📋 {rid}</span></div>""", unsafe_allow_html=True)
            
            p_c = str(row['cell']).strip(); p_w = str(row['work']).strip()
            n_e = urllib.parse.quote(str(row['name'])); m_e = urllib.parse.quote(f"Chao {row['name']}...")
            
            # BỘ 4 ICON THẦN THÁNH
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
            st.text_area("History", value=curr_h, height=120, disabled=True, key=f"v_{lid}", label_visibility="collapsed")
            # ENTER LÀ HIỆN NGAY (Dùng logic Rerun chuẩn)
            new_note = st.text_input("Ghi chú mới & Enter", key=f"in_{lid}", label_visibility="collapsed", placeholder="Nhập note...")
            if new_note:
                now = datetime.now()
                combined = f"[{now.strftime('%m/%d')}]: {new_note}\n{curr_h}"
                conn.execute('UPDATE leads SET last_interact = ?, note = ? WHERE id = ?', (now.strftime("%Y-%m-%d %H:%M:%S"), combined, lid))
                conn.commit()
                st.session_state[f"in_{lid}"] = "" # Clear ô nhập
                st.rerun()

        with c_edit:
            with st.popover("⋮"):
                en = st.text_input("Name", value=row['name'], key=f"en_{lid}")
                ei = st.text_input("ID", value=row['crm_id'], key=f"ei_{lid}")
                ec = st.text_input("Cell", value=row['cell'], key=f"ec_{lid}")
                ew = st.text_input("Work", value=row['work'], key=f"ew_{lid}")
                ee = st.text_input("Email", value=row['email'], key=f"ee_{lid}")
                es = st.text_input("State", value=row['state'], key=f"es_{lid}")
                if st.button("Save Changes", key=f"sv_{lid}"):
                    conn.execute('UPDATE leads SET name=?, crm_id=?, cell=?, work=?, email=?, state=? WHERE id=?', (en, ei, ec, ew, ee, es, lid))
                    conn.commit(); st.rerun()
                if st.button("Delete Lead", key=f"del_{lid}", type="primary"):
                    conn.execute('DELETE FROM leads WHERE id=?', (lid,)); conn.commit(); st.rerun()
        st.divider()
