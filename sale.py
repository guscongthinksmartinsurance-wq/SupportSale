import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse

# --- 1. KHỞI TẠO DATABASE ---
DB_NAME = "tmc_crm_v20.db"

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
st.set_page_config(page_title="TMC CRM FRAGMENT V20", layout="wide")

# CSS cho History Box
st.markdown("""
    <style>
    .history-box {
        background-color: #f1f3f5;
        border-radius: 8px;
        padding: 12px;
        height: 130px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        color: #2c3e50;
        border-left: 4px solid #7d3c98;
        white-space: pre-wrap;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR (GIỮ NGUYÊN TÍNH NĂNG) ---
with st.sidebar:
    st.title("🛠️ CRM Control")
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
            st.markdown(f"**[{l['Title'] if 'Title' in l else l['title']}]({l['URL'] if 'URL' in l else l['url']})**")
    with st.expander("📚 Sales Kit", expanded=True):
        for _, v in df_links[df_links['category'] == 'Sales Kit'].iterrows():
            st.caption(v['title'] if 'title' in v else v['Title'])
            st.video(v['url'] if 'url' in v else v['URL'])
    
    st.divider()
    with st.expander("➕ Add New Lead", expanded=True):
        with st.form("new_lead"):
            n = st.text_input("Name"); i = st.text_input("ID"); p = st.text_input("Cell")
            w = st.text_input("Work"); e = st.text_input("Email"); s = st.text_input("State")
            if st.form_submit_button("Lưu Lead"):
                conn.execute('INSERT INTO leads (name, crm_id, cell, work, email, state, status, last_interact, note) VALUES (?,?,?,?,?,?,?,?,?)', (n, i, p, w, e, s, "New", "", ""))
                conn.commit(); st.rerun()

# --- 4. HÀM CÔNG NGHỆ FRAGMENT (QUAN TRỌNG NHẤT) ---
@st.fragment
def lead_row_fragment(row):
    lid = row['id']
    curr_h = row['note'] if row['note'] else ""
    
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
        # Hiển thị History dạng Timeline sạch sẽ
        st.markdown(f'<div class="history-box">{curr_h}</div>', unsafe_allow_html=True)
        
        # Nhập Note mới
        new_note = st.text_input("Ghi chú & Enter", key=f"note_in_{lid}", label_visibility="collapsed", placeholder="Nhập note...")
        
        if new_note:
            now = datetime.now()
            combined = f"[{now.strftime('%m/%d')}]: {new_note}\n{curr_h}"
            # Lưu DB
            local_conn = sqlite3.connect(DB_NAME)
            local_conn.execute('UPDATE leads SET last_interact = ?, note = ? WHERE id = ?', 
                               (now.strftime("%Y-%m-%d %H:%M:%S"), combined, lid))
            local_conn.commit()
            local_conn.close()
            # TỰ REFRESH CHỈ RIÊNG PHÂN ĐOẠN NÀY (Hết lỗi vàng)
            st.rerun()

    with c_edit:
        with st.popover("⋮"):
            if st.button("Delete Lead", key=f"del_{lid}", type="primary"):
                conn.execute('DELETE FROM leads WHERE id=?', (lid,)); conn.commit(); st.rerun()
            st.caption("Để sửa ID/Email, dùng sidebar hoặc bản Admin.")

# --- MAIN RENDER ---
st.title("💼 Pipeline Processing")
leads_df = pd.read_sql('SELECT * FROM leads ORDER BY id DESC', conn)

for _, row in leads_df.iterrows():
    lead_row_fragment(row)
    st.divider()
