import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse

# --- 1. KẾT NỐI DATABASE CLOUD (GOOGLE SHEETS) ---
st.set_page_config(page_title="TMC CRM PRO V24.4", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    try:
        return conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0).dropna(how='all')
    except:
        if worksheet == "leads":
            return pd.DataFrame(columns=["id", "name", "crm_id", "cell", "work", "email", "state", "status", "last_interact", "note", "crm_link"])
        return pd.DataFrame(columns=["id", "category", "title", "url"])

def save_data(df, worksheet):
    df = df.fillna("")
    conn.update(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, data=df)
    st.cache_data.clear()

# --- 2. CẤU HÌNH GIAO DIỆN ---
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

# --- 3. LOGIC XỬ LÝ NOTE ---
def save_note_v24(idx, current_note, note_key):
    new_txt = st.session_state[note_key]
    if new_txt and new_txt.strip():
        now = datetime.now()
        entry = f"<div class='history-entry'><span class='timestamp'>[{now.strftime('%m/%d %H:%M')}]</span>{new_txt}</div>"
        combined = entry + current_note
        
        df_leads_full = load_data("leads")
        df_leads_full.at[idx, 'note'] = combined
        df_leads_full.at[idx, 'last_interact'] = now.strftime("%Y-%m-%d %H:%M:%S")
        save_data(df_leads_full, "leads")
        st.session_state[note_key] = ""
        st.rerun()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🛠️ CRM Tools")
    df_links = load_data("links")
    
    with st.expander("🔗 Add Link / Sales Kit"):
        with st.form("add_l", clear_on_submit=True):
            c = st.selectbox("Loại", ["Quick Link", "Sales Kit"]); t = st.text_input("Tên"); u = st.text_input("URL")
            if st.form_submit_button("Lưu"):
                new_l = pd.DataFrame([{"id": len(df_links)+1, "category": c, "title": t, "url": u}])
                save_data(pd.concat([df_links, new_l], ignore_index=True), "links")
                st.rerun()

    with st.expander("🚀 Quick Links", expanded=True):
        for idx, l in df_links[df_links['category'] == 'Quick Link'].iterrows():
            c1, c2 = st.columns([8, 2])
            c1.markdown(f"**[{l['title']}]({l['url']})**")
            with c2.popover("🗑️"):
                if st.button("Confirm", key=f"dl_{idx}"):
                    save_data(df_links.drop(idx), "links"); st.rerun()

    with st.expander("📚 Sales Kit", expanded=True):
        for idx, v in df_links[df_links['category'] == 'Sales Kit'].iterrows():
            st.caption(v['title']); st.video(v['url'])
            with st.popover("Xóa 🗑️"):
                if st.button("Confirm Delete", key=f"dv_{idx}"):
                    save_data(df_links.drop(idx), "links"); st.rerun()
    
    st.divider()
    with st.expander("➕ Add New Lead"):
        with st.form("new_lead", clear_on_submit=True):
            n = st.text_input("Name"); i = st.text_input("ID"); p = st.text_input("Cell"); w = st.text_input("Work"); e = st.text_input("Email"); s = st.text_input("State"); cl = st.text_input("Link CRM")
            if st.form_submit_button("Lưu Lead"):
                df_leads_all = load_data("leads")
                new_row = {"id": len(df_leads_all)+1, "name": n, "crm_id": i, "cell": p, "work": w, "email": e, "state": s, "status": "New", "last_interact": "", "note": "", "crm_link": cl}
                save_data(pd.concat([df_leads_all, pd.DataFrame([new_row])], ignore_index=True), "leads")
                st.rerun()

# --- 5. BỘ LỌC & TÌM KIẾM ---
st.title("💼 Pipeline Processing")
c_search, c_slider = st.columns([7, 3])
with c_search:
    query = st.text_input("🔍 Tìm kiếm nhanh (Tên, ID, SĐT...):", placeholder="Nhập tên, ID hoặc số điện thoại để lọc...")
with c_slider:
    days = st.slider("Khách chưa đụng tới quá (ngày):", 0, 90, 0)

leads_df = load_data("leads")

if not leads_df.empty:
    if days > 0:
        leads_df['last_interact_dt'] = pd.to_datetime(leads_df['last_interact'], errors='coerce')
        mask = (leads_df['last_interact_dt'].isna()) | ((datetime.now() - leads_df['last_interact_dt']).dt.days >= days)
        leads_df = leads_df[mask]
    if query:
        q = query.lower()
        leads_df = leads_df[leads_df.apply(lambda row: q in str(row).lower(), axis=1)]

st.divider()

# --- 6. RENDER DỮ LIỆU ---
for idx, row in leads_df.iterrows():
    curr_h = row['note'] if row['note'] else ""; crm_url = row['crm_link'] if row['crm_link'] else "#"
    with st.container(border=True):
        c_info, c_note, c_edit = st.columns([4, 5, 1])
        with c_info:
            st.markdown(f"#### {row['name']}")
            rid = str(row['crm_id']).strip()
            st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;"><span style="background:#7d3c98;color:white;padding:1px 4px;border-radius:3px;font-size:10px;">ID</span><a href="{crm_url}" target="_blank" style="color:#e83e8c;text-decoration:none;font-weight:bold;background:#fef1f6;padding:2px 6px;border-radius:4px;border:1px solid #fce4ec;">🔗 {rid}</a></div>""", unsafe_allow_html=True)
            p_c = str(row['cell']).strip(); p_w = str(row['work']).strip(); em = str(row['email']).strip()
            n_e = urllib.parse.quote(str(row['name'])); m_e = urllib.parse.quote(f"Chao {row['name']}...")
            st.markdown(f"""<div style="display:flex;gap:15px;align-items:center;"><span>📱 <a href="tel:{p_c}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_c}</a></span><a href="rcmobile://sms?number={p_c}&body={m_e}">💬</a><a href="mailto:{em}?body={m_e}">📧</a><a href="https://calendar.google.com/calendar/r/eventedit?text=TMC_{n_e}" target="_blank">📅</a></div>""", unsafe_allow_html=True)
            if p_w and p_w not in ['0', '']: st.markdown(f'📞 Work: <a href="tel:{p_w}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_w}</a>', unsafe_allow_html=True)

        with c_note:
            st.markdown(f'<div class="history-container">{curr_h}</div>', unsafe_allow_html=True)
            st.text_input("Note & Enter", key=f"note_{idx}", on_change=save_note_v24, args=(idx, curr_h, f"note_{idx}"), label_visibility="collapsed", placeholder="Note nhanh...")

        with c_edit:
            with st.popover("⋮"):
                en = st.text_input("Name", value=row['name'], key=f"en_{idx}")
                ei = st.text_input("ID", value=row['crm_id'], key=f"ei_{idx}")
                ec = st.text_input("Cell", value=row['cell'], key=f"ec_{idx}")
                if st.button("Save ✅", key=f"sv_{idx}"):
                    full_df = load_data("leads")
                    full_df.loc[idx, ['name','crm_id','cell']] = [en, ei, ec]
                    save_data(full_df, "leads"); st.rerun()
                if st.button("Xóa khách", key=f"del_{idx}", type="primary"):
                    full_df = load_data("leads")
                    save_data(full_df.drop(idx), "leads"); st.rerun()
        st.divider()
