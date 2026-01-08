import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse

# --- 1. KHỞI TẠO DATABASE ---
DB_NAME = "tmc_crm_v10.db"

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

# --- 2. HÀM XỬ LÝ LƯU NOTE & TỰ ĐỘNG REFRESH ---
def handle_note_sync(lead_id, note_key, old_note):
    new_text = st.session_state[note_key]
    if new_text:
        now = datetime.now()
        combined = f"[{now.strftime('%m/%d')}]: {new_text}\n{old_note}"
        # Cập nhật Database
        cursor = conn.cursor()
        cursor.execute('UPDATE leads SET last_interact = ?, note = ? WHERE id = ?', 
                     (now.strftime("%Y-%m-%d %H:%M:%S"), combined, lead_id))
        conn.commit()
        # Xóa nội dung trong ô nhập sau khi lưu
        st.session_state[note_key] = ""
        # Lệnh quan trọng: Tự động chạy lại App để cập nhật History ngay lập tức
        st.rerun()

# --- 3. GIAO DIỆN ---
st.set_page_config(page_title="TMC SQLite CRM", layout="wide")

with st.sidebar:
    st.title("🛠️ Local Control")
    with st.expander("🔗 Add Link / Video"):
        with st.form("add_l"):
            c = st.selectbox("Loại", ["Quick Link", "Sales Kit"]); t = st.text_input("Tên"); u = st.text_input("URL")
            if st.form_submit_button("Lưu"):
                conn.execute('INSERT INTO links (category, title, url) VALUES (?,?,?)', (c, t, u)); conn.commit(); st.rerun()

    df_links = pd.read_sql('SELECT * FROM links', conn)
    with st.expander("🚀 Quick Links", expanded=True):
        for _, l in df_links[df_links['category'] == 'Quick Link'].iterrows(): st.markdown(f"**[{l['title']}]({l['url']})**")
    with st.expander("📚 Sales Kit", expanded=True):
        for _, v in df_links[df_links['category'] == 'Sales Kit'].iterrows(): st.caption(v['title']); st.video(v['URL'])
    
    st.divider()
    with st.expander("➕ Add New Lead", expanded=True):
        with st.form("new_l"):
            n = st.text_input("Name"); i = st.text_input("ID"); p = st.text_input("Cell"); w = st.text_input("Work"); e = st.text_input("Email"); s = st.text_input("State")
            if st.form_submit_button("Save Lead"):
                conn.execute('INSERT INTO leads (name, crm_id, cell, work, email, state, status, last_interact, note) VALUES (?,?,?,?,?,?,?,?,?)', (n, i, p, w, e, s, "New", "", ""))
                conn.commit(); st.rerun()

# --- MAIN VIEW ---
st.title("💼 Pipeline Processing")
leads_df = pd.read_sql('SELECT * FROM leads ORDER BY id DESC', conn)
days = st.slider("Hiện khách chưa đụng tới quá (ngày):", 0, 90, 0)

# Lọc ngày
leads_df['last_interact_dt'] = pd.to_datetime(leads_df['last_interact'], errors='coerce')
if days > 0:
    mask = (leads_df['last_interact_dt'].isna()) | ((datetime.now() - leads_df['last_interact_dt']).dt.days >= days)
    leads_df = leads_df[mask]

# --- RENDER PIPELINE ---
for _, row in leads_df.iterrows():
    lid = row['id']
    k_in = f"in_{lid}"
    curr_note = row['note'] if row['note'] else ""

    with st.container():
        c1, c2, c3 = st.columns([4, 5, 1])
        with c1:
            st.markdown(f"#### {row['name']}")
            clean_id = str(row['crm_id']).strip().replace('#', '').lower()
            st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;"><span style="background:#7d3c98;color:white;padding:1px 4px;border-radius:3px;font-size:10px;">ID</span><span onclick="navigator.clipboard.writeText('{clean_id}');alert('Copied!')" style="color:#e83e8c;cursor:pointer;font-family:monospace;font-weight:bold;background:#f8f9fa;border:1px dashed #e83e8c;padding:2px 6px;border-radius:4px;">📋 {clean_id}</span></div>""", unsafe_allow_html=True)
            p_c = str(row['cell']).strip(); p_w = str(row['work']).strip(); n_e = urllib.parse.quote(str(row['name'])); m_e = urllib.parse.quote(f"Chao {row['name']}...")
            st.markdown(f"""<div style="display:flex;gap:15px;align-items:center;"><span>📱 <a href="tel:{p_c}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_c}</a></span><a href="rcmobile://sms?number={p_c}&body={m_e}">💬</a><a href="mailto:{row['email']}?body={m_e}">📧</a><a href="https://calendar.google.com/calendar/r/eventedit?text=TMC_{n_e}" target="_blank">📅</a></div>""", unsafe_allow_html=True)
            if p_w and p_w not in ['0', '']:
                st.markdown(f'📞 Work: <a href="tel:{p_w}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_w}</a>', unsafe_allow_html=True)
        
        with c2:
            st.text_area("History", value=curr_note, height=120, disabled=True, key=f"h_{lid}", label_visibility="collapsed")
            # KHI NHẤN ENTER: handle_note_sync sẽ được gọi và tự st.rerun()
            st.text_input("Ghi chú mới & Enter", key=k_in, on_change=handle_note_sync, args=(lid, k_in, curr_note), label_visibility="collapsed", placeholder="Nhập note...")

        with c3:
            with st.popover("⋮"):
                en = st.text_input("Name", value=row['name'], key=f"en_{lid}")
                ec = st.text_input("Cell", value=row['cell'], key=f"ec_{lid}")
                ew = st.text_input("Work", value=row['work'], key=f"ew_{lid}")
                if st.button("Save Edit", key=f"sv_{lid}"):
                    conn.execute('UPDATE leads SET name=?, cell=?, work=? WHERE id=?', (en, ec, ew, lid))
                    conn.commit(); st.rerun()
        st.divider()
