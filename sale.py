import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse

# --- 1. KẾT NỐI DATABASE CHUẨN ---
st.set_page_config(page_title="TMC CRM PRO V24.4", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    return conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0).dropna(how='all')

def save_data(df, worksheet):
    df = df.fillna("")
    conn.update(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, data=df)
    st.cache_data.clear()

# --- 2. CSS HISTORY & GIAO DIỆN GỐC ---
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

# --- 3. LOGIC LƯU NOTE ĂN NGAY ---
def save_note_v24(idx, current_note, note_key):
    new_txt = st.session_state[note_key]
    if new_txt and new_txt.strip():
        now = datetime.now()
        entry = f"<div class='history-entry'><span class='timestamp'>[{now.strftime('%m/%d %H:%M')}]</span>{new_txt}</div>"
        combined = entry + str(current_note)
        df_full = load_data("leads")
        df_full.at[idx, 'note'] = combined
        df_full.at[idx, 'last_interact'] = now.strftime("%Y-%m-%d %H:%M:%S")
        save_data(df_full, "leads")
        st.session_state[note_key] = ""
        st.rerun()

# --- 4. SIDEBAR CHUẨN (ADD NEW LEAD & LINKS) ---
with st.sidebar:
    st.title("🛠️ CRM Tools")
    df_links = load_data("links")
    with st.expander("🔗 Add Link / Sales Kit"):
        with st.form("add_l", clear_on_submit=True):
            c = st.selectbox("Loại", ["Quick Link", "Sales Kit"]); t = st.text_input("Tên"); u = st.text_input("URL")
            if st.form_submit_button("Lưu"):
                new_l = pd.DataFrame([{"category": c, "title": t, "url": u}])
                save_data(pd.concat([df_links, new_l], ignore_index=True), "links"); st.rerun()

    for idx, l in df_links[df_links['category'] == 'Quick Link'].iterrows():
        st.markdown(f"**[{l['title']}]({l['url']})**")
    
    st.divider()
    with st.expander("➕ Add New Lead"):
        with st.form("new_lead", clear_on_submit=True):
            n = st.text_input("Name"); i = st.text_input("ID"); p = st.text_input("Cell"); w = st.text_input("Work")
            if st.form_submit_button("Lưu Lead"):
                df_leads_all = load_data("leads")
                new_row = {"name":n, "crm_id":i, "cell":p, "work":w, "status":"New", "last_interact":"", "note":""}
                save_data(pd.concat([df_leads_all, pd.DataFrame([new_row])], ignore_index=True), "leads"); st.rerun()

# --- 5. PIPELINE & ICONS LIÊN LẠC ---
st.title("💼 Pipeline Processing")
leads_df = load_data("leads")

if not leads_df.empty:
    for idx, row in leads_df.iterrows():
        curr_h = str(row['note']) if str(row['note']) != 'nan' else ""
        crm_url = str(row['crm_link']) if 'crm_link' in row and str(row['crm_link']) != 'nan' else "#"
        
        with st.container(border=True):
            c_info, c_note, c_edit = st.columns([4, 5, 1])
            with c_info:
                st.markdown(f"#### {row['name']}")
                rid = str(row['crm_id']).strip()
                # Badge ID & CRM Link
                st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;"><span style="background:#7d3c98;color:white;padding:1px 4px;border-radius:3px;font-size:10px;">ID</span><a href="{crm_url}" target="_blank" style="color:#e83e8c;text-decoration:none;font-weight:bold;background:#fef1f6;padding:2px 6px;border-radius:4px;border:1px solid #fce4ec;">🔗 {rid}</a></div>""", unsafe_allow_html=True)
                
                # ICONS CHUẨN: Gọi, SMS, Mail, Calendar
                p_c = str(row['cell']).strip(); n_e = urllib.parse.quote(str(row['name'])); m_e = urllib.parse.quote(f"Chao {row['name']}...")
                st.markdown(f"""<div style="display:flex;gap:15px;align-items:center;"><span>📱 <a href="tel:{p_c}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_c}</a></span><a href="rcmobile://sms?number={p_c}&body={m_e}">💬</a><a href="mailto:{row.get('email', '')}?body={m_e}">📧</a><a href="https://calendar.google.com/calendar/r/eventedit?text=TMC_{n_e}" target="_blank">📅</a></div>""", unsafe_allow_html=True)
                if row.get('work') and str(row['work']) not in ['0', 'nan', '']: st.markdown(f'📞 Work: <a href="tel:{row["work"]}" style="color:#28a745;font-weight:bold;text-decoration:none;">{row["work"]}</a>', unsafe_allow_html=True)

            with c_note:
                st.markdown(f'<div class="history-container">{curr_h}</div>', unsafe_allow_html=True)
                st.text_input("Note & Enter", key=f"note_{idx}", on_change=save_note_v24, args=(idx, curr_h, f"note_{idx}"), label_visibility="collapsed", placeholder="Note nhanh...")

            with c_edit:
                with st.popover("⋮"):
                    if st.button("Xóa khách", key=f"del_{idx}", type="primary"):
                        full_df = load_data("leads")
                        save_data(full_df.drop(idx), "leads"); st.rerun()
        st.divider()
