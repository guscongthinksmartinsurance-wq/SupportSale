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

# --- 2. HÀM XỬ LÝ LƯU NOTE TỨC THÌ ---
def save_note_instant(lid, old_note, note_key):
    new_text = st.session_state[note_key]
    if new_text:
        now = datetime.now()
        combined = f"[{now.strftime('%m/%d')}]: {new_text}\n{old_note}"
        
        # Bước 1: Ghi vào Database
        cursor = conn.cursor()
        cursor.execute('UPDATE leads SET last_interact = ?, note = ? WHERE id = ?', 
                     (now.strftime("%Y-%m-%d %H:%M:%S"), combined, lid))
        conn.commit()
        
        # Bước 2: ÉP HIỂN THỊ (QUAN TRỌNG) - Lưu thẳng vào bộ nhớ tạm của App
        st.session_state[f"force_view_{lid}"] = combined
        
        # Bước 3: Xóa ô nhập
        st.session_state[note_key] = ""
        st.toast("✅ Đã lưu History!")

# --- 3. GIAO DIỆN ---
st.set_page_config(page_title="TMC CRM Pro", layout="wide")

with st.sidebar:
    st.title("🛠️ Local Control")
    # Quản lý Links
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
            n = st.text_input("Name"); i = st.text_input("ID"); p = st.text_input("Cell"); w = st.text_input("Work"); e = st.text_input("Email"); s = st.text_input("State")
            if st.form_submit_button("Save"):
                conn.execute('INSERT INTO leads (name, crm_id, cell, work, email, state, status, last_interact, note) VALUES (?,?,?,?,?,?,?,?,?)', (n, i, p, w, e, s, "New", "", ""))
                conn.commit(); st.rerun()

# --- MAIN VIEW ---
st.title("💼 Pipeline Processing")
leads_df = pd.read_sql('SELECT * FROM leads ORDER BY id DESC', conn)
days = st.slider("Hiện khách chưa đụng tới quá (ngày):", 0, 90, 0)

# Render
for _, row in leads_df.iterrows():
    lid = row['id']
    # CHIẾN THUẬT CRM: Ưu tiên lấy Note từ RAM (force_view) nếu vừa gõ xong
    final_h = st.session_state.get(f"force_view_{lid}", row['note'] if row['note'] else "")

    with st.container():
        c1, c2, c3 = st.columns([4, 5, 1])
        with c1:
            st.markdown(f"#### {row['name']}")
            rid = str(row['crm_id']).strip().replace('#', '').lower()
            st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;"><span style="background:#7d3c98;color:white;padding:1px 4px;border-radius:3px;font-size:10px;">ID</span><span onclick="navigator.clipboard.writeText('{rid}');alert('Copied!')" style="color:#e83e8c;cursor:pointer;font-family:monospace;font-weight:bold;background:#f8f9fa;border:1px dashed #e83e8c;padding:2px 6px;border-radius:4px;">📋 {rid}</span></div>""", unsafe_allow_html=True)
            p_c = str(row['cell']).strip(); p_w = str(row['work']).strip()
            st.markdown(f"""<div style="display:flex;gap:15px;align-items:center;"><span>📱 <a href="tel:{p_c}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_c}</a></span></div>""", unsafe_allow_html=True)
            if p_w and p_w not in ['0', '']:
                st.markdown(f'📞 Work: <a href="tel:{p_w}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_w}</a>', unsafe_allow_html=True)

        with c2:
            # Hiển thị History lấy từ final_h (RAM)
            st.text_area("History", value=final_h, height=120, disabled=True, key=f"h_{lid}", label_visibility="collapsed")
            # GÕ VÀ ENTER
            st.text_input("Ghi chú mới & Enter", key=f"in_{lid}", on_change=save_note_instant, args=(lid, final_h, f"in_{lid}"), label_visibility="collapsed", placeholder="Nhập note...")

        with c3:
            with st.popover("⋮"):
                if st.button("Xóa Lead", key=f"del_{lid}"):
                    conn.execute('DELETE FROM leads WHERE id=?', (lid,)); conn.commit(); st.rerun()
        st.divider()
