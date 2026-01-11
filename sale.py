import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
from sqlalchemy import text # Thêm thư viện này để fix lỗi image_32036b

# --- 1. KẾT NỐI DATABASE ONLINE (SUPABASE) ---
conn = st.connection("postgresql", type="sql")

def init_db():
    with conn.session as s:
        # Bọc câu lệnh trong text() để Postgres hiểu
        s.execute(text('''CREATE TABLE IF NOT EXISTS leads 
            (id SERIAL PRIMARY KEY, name TEXT, crm_id TEXT, cell TEXT, 
             work TEXT, email TEXT, state TEXT, status TEXT, last_interact TEXT, note TEXT, crm_link TEXT)'''))
        s.execute(text('''CREATE TABLE IF NOT EXISTS links 
            (id SERIAL PRIMARY KEY, category TEXT, title TEXT, url TEXT)'''))
        s.commit()

init_db()

# --- 2. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="TMC CRM CLOUD V25.1", layout="wide")

st.markdown("""
    <style>
    .history-container {
        background-color: #ffffff; border: 1px solid #e1e4e8; border-radius: 6px;
        padding: 10px; height: 150px; overflow-y: auto; font-family: sans-serif;
        font-size: 13px; color: #24292e;
    }
    .history-entry { border-bottom: 1px dashed #eee; margin-bottom: 5px; padding-bottom: 2px; }
    .timestamp { color: #0366d6; font-weight: bold; margin-right: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC XỬ LÝ ---
if st.session_state.get("needs_refresh"):
    st.session_state["needs_refresh"] = False
    st.rerun()

def save_note_v25(lid, current_note, note_key):
    new_txt = st.session_state[note_key]
    if new_txt and new_txt.strip():
        now = datetime.now()
        entry = f"<div class='history-entry'><span class='timestamp'>[{now.strftime('%m/%d %H:%M')}]</span>{new_txt}</div>"
        combined = entry + (current_note if current_note else "")
        
        with conn.session as s:
            s.execute(
                text("UPDATE leads SET last_interact = :t, note = :n WHERE id = :id"),
                {"t": now.strftime("%Y-%m-%d %H:%M:%S"), "n": combined, "id": lid}
            )
            s.commit()
        st.session_state[note_key] = ""
        st.session_state["needs_refresh"] = True

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🛠️ Cloud CRM Tools")
    with st.expander("🔗 Add Link / Sales Kit"):
        with st.form("add_l", clear_on_submit=True):
            c = st.selectbox("Loại", ["Quick Link", "Sales Kit"]); t = st.text_input("Tên"); u = st.text_input("URL")
            if st.form_submit_button("Lưu"):
                with conn.session as s:
                    s.execute(text("INSERT INTO links (category, title, url) VALUES (:c, :t, :u)"), {"c": c, "t": t, "u": u})
                    s.commit()
                st.rerun()

    df_links = conn.query("SELECT * FROM links", ttl=0)
    if not df_links.empty:
        with st.expander("🚀 Quick Links", expanded=True):
            for _, l in df_links[df_links['category'] == 'Quick Link'].iterrows():
                c1, c2 = st.columns([8, 2])
                c1.markdown(f"**[{l['title']}]({l['url']})**")
                with c2.popover("🗑️"):
                    if st.button("Confirm", key=f"dl_{l['id']}"):
                        with conn.session as s:
                            s.execute(text("DELETE FROM links WHERE id = :id"), {"id": l['id']})
                            s.commit()
                        st.rerun()

        with st.expander("📚 Sales Kit", expanded=True):
            for _, v in df_links[df_links['category'] == 'Sales Kit'].iterrows():
                st.caption(v['title']); st.video(v['url'])
                with st.popover("Xóa 🗑️"):
                    if st.button("Confirm Delete", key=f"dv_{v['id']}"):
                        with conn.session as s:
                            s.execute(text("DELETE FROM links WHERE id = :id"), {"id": v['id']})
                            s.commit()
                        st.rerun()
                st.divider()
    
    st.divider()
    with st.expander("➕ Add New Lead"):
        with st.form("new_lead", clear_on_submit=True):
            n = st.text_input("Name"); i = st.text_input("ID"); p = st.text_input("Cell"); w = st.text_input("Work"); e = st.text_input("Email"); s = st.text_input("State"); cl = st.text_input("Link CRM")
            if st.form_submit_button("Lưu Lead"):
                with conn.session as s:
                    s.execute(text("""INSERT INTO leads (name, crm_id, cell, work, email, state, status, last_interact, note, crm_link) 
                              VALUES (:n, :i, :p, :w, :e, :s, 'New', '', '', :cl)"""), 
                              {"n": n, "i": i, "p": p, "w": w, "e": e, "s": s, "cl": cl})
                    s.commit()
                st.rerun()

# --- 5. BỘ LỌC & TÌM KIẾM ---
st.title("💼 Pipeline Processing")

c_search, c_slider = st.columns([7, 3])
with c_search:
    query = st.text_input("🔍 Tìm kiếm nhanh:", placeholder="Nhập tên, ID hoặc số điện thoại...")

with c_slider:
    days_limit = st.slider("Khách chưa đụng tới quá (ngày):", 0, 90, 0)

# Đọc dữ liệu từ Postgres
leads_df = conn.query("SELECT * FROM leads ORDER BY id DESC", ttl=0)

# Lọc dữ liệu
if not leads_df.empty:
    if days_limit > 0:
        leads_df['last_interact_dt'] = pd.to_datetime(leads_df['last_interact'], errors='coerce')
        mask = (leads_df['last_interact_dt'].isna()) | ((datetime.now() - leads_df['last_interact_dt']).dt.days >= days_limit)
        leads_df = leads_df[mask]

    if query:
        q = query.lower()
        leads_df = leads_df[
            leads_df['name'].astype(str).str.lower().str.contains(q) | 
            leads_df['crm_id'].astype(str).str.lower().str.contains(q) | 
            leads_df['cell'].astype(str).str.contains(q)
        ]

st.divider()

# --- 6. RENDER DỮ LIỆU ---
for _, row in leads_df.iterrows():
    lid = row['id']; curr_h = row['note'] if row['note'] else ""; crm_url = row['crm_link'] if row['crm_link'] else "#"
    
    with st.container(border=True):
        c_info, c_note, c_edit = st.columns([4, 5, 1])
        with c_info:
            st.markdown(f"#### {row['name']}")
            rid = str(row['crm_id']).strip()
            st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;"><span style="background:#7d3c98;color:white;padding:1px 4px;border-radius:3px;font-size:10px;">ID</span><a href="{crm_url}" target="_blank" style="color:#e83e8c;text-decoration:none;font-weight:bold;background:#fef1f6;padding:2px 6px;border-radius:4px;border:1px solid #fce4ec;">🔗 {rid}</a><span onclick="navigator.clipboard.writeText('{rid}');alert('Copied ID!')" style="cursor:pointer;font-size:14px;">📋</span></div>""", unsafe_allow_html=True)
            p_c = str(row['cell']).strip(); p_w = str(row['work']).strip(); em = str(row['email']).strip(); n_e = urllib.parse.quote(str(row['name'])); m_e = urllib.parse.quote(f"Chao {row['name']}...")
            st.markdown(f"""<div style="display:flex;gap:15px;align-items:center;"><span>📱 <a href="tel:{p_c}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_c}</a></span><a href="rcmobile://sms?number={p_c}&body={m_e}">💬</a><a href="mailto:{em}?body={m_e}">📧</a><a href="https://calendar.google.com/calendar/r/eventedit?text=TMC_{n_e}" target="_blank">📅</a></div>""", unsafe_allow_html=True)
            if p_w and p_w not in ['0', '']: st.markdown(f'📞 Work: <a href="tel:{p_w}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_w}</a>', unsafe_allow_html=True)

        with c_note:
            st.markdown(f'<div class="history-container">{curr_h}</div>', unsafe_allow_html=True)
            st.text_input("Ghi chú & Enter", key=f"note_{lid}", on_change=save_note_v25, args=(lid, curr_h, f"note_{lid}"), label_visibility="collapsed", placeholder="Note nhanh...")

        with c_edit:
            with st.popover("⋮"):
                en = st.text_input("Name", value=row['name'], key=f"en_{lid}")
                ei = st.text_input("ID", value=row['crm_id'], key=f"ei_{lid}")
                ec = st.text_input("Cell", value=row['cell'], key=f"ec_{lid}")
                ew = st.text_input("Work", value=row['work'], key=f"ew_{lid}")
                ee = st.text_input("Email", value=row['email'], key=f"ee_{lid}")
                es = st.text_input("State", value=row['state'], key=f"es_{lid}")
                el = st.text_input("Link CRM", value=row['crm_link'] if row['crm_link'] else "", key=f"el_{lid}")
                if st.button("Save ✅", key=f"sv_{lid}", use_container_width=True):
                    with conn.session as s:
                        s.execute(text("""UPDATE leads SET name=:n, crm_id=:i, cell=:c, work=:w, email=:e, state=:s, crm_link=:cl WHERE id=:id"""), 
                                  {"n": en, "i": ei, "c": ec, "w": ew, "e": ee, "s": es, "cl": el, "id": lid})
                        s.commit()
                    st.rerun()
                st.divider()
                with st.expander("Xóa khách hàng 🗑️"):
                    if st.button("Xác nhận xóa", key=f"conf_del_{lid}", type="primary", use_container_width=True):
                        with conn.session as s:
                            s.execute(text("DELETE FROM leads WHERE id = :id"), {"id": lid})
                            s.commit()
                        st.rerun()
        st.divider()
