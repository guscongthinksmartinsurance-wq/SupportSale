import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import urllib.parse

# --- 1. KẾT NỐI VÀ CẤU TRÚC ---
st.set_page_config(page_title="TMC CRM CLOUD V26.5", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    try:
        return conn.read(spreadsheet=st.secrets["gsheet_url"], worksheet=worksheet, ttl=0).dropna(how='all')
    except:
        if worksheet == "leads":
            return pd.DataFrame(columns=["name", "crm_id", "cell", "work", "email", "state", "status", "last_interact", "note", "crm_link"])
        return pd.DataFrame(columns=["category", "title", "url"])

def save_and_refresh(df, worksheet):
    # Xử lý sạch dữ liệu trước khi lưu
    if 'dt_obj' in df.columns: df = df.drop(columns=['dt_obj'])
    df = df.fillna("")
    conn.update(spreadsheet=st.secrets["gsheet_url"], worksheet=worksheet, data=df)
    st.cache_data.clear()
    st.rerun() # Ép App load lại để thấy Note ngay lập tức

# --- 2. CSS HISTORY CHUẨN ---
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

# --- 3. SIDEBAR: LINK & ADD LEAD (LÀM TẠI CHỖ) ---
with st.sidebar:
    st.title("🛠️ TMC Cloud Tools")
    df_links = load_data("links")

    with st.expander("🔗 Add Link / Sales Kit"):
        with st.form("add_l", clear_on_submit=True):
            c = st.selectbox("Loại", ["Quick Link", "Sales Kit"])
            t = st.text_input("Tên")
            u = st.text_input("URL")
            if st.form_submit_button("Lưu"):
                new_l = pd.DataFrame([{"category": c, "title": t, "url": u}])
                save_and_refresh(pd.concat([df_links, new_l], ignore_index=True), "links")

    if not df_links.empty:
        with st.expander("🚀 Quick Links", expanded=True):
            for idx, l in df_links[df_links['category'] == 'Quick Link'].iterrows():
                c1, c2 = st.columns([8, 2])
                c1.markdown(f"**[{l['title']}]({l['url']})**")
                if c2.button("🗑️", key=f"dl_{idx}"):
                    save_and_refresh(df_links.drop(idx), "links")

        with st.expander("📚 Sales Kit", expanded=True):
            for idx, v in df_links[df_links['category'] == 'Sales Kit'].iterrows():
                st.caption(v['title'])
                st.video(v['url'])
                if st.button("Xóa Video", key=f"dv_{idx}"):
                    save_and_refresh(df_links.drop(idx), "links")
    
    st.divider()
    with st.expander("➕ Add New Lead"):
        with st.form("new_lead", clear_on_submit=True):
            n = st.text_input("Name"); i = st.text_input("ID"); p = st.text_input("Cell")
            w = st.text_input("Work"); e = st.text_input("Email"); s = st.text_input("State")
            cl = st.text_input("Link CRM")
            if st.form_submit_button("Lưu Lead"):
                df_leads_all = load_data("leads")
                new_row = {"name":n, "crm_id":i, "cell":p, "work":w, "email":e, "state":s, "status":"New", "last_interact":"", "note":"", "crm_link":cl}
                save_and_refresh(pd.concat([df_leads_all, pd.DataFrame([new_row])], ignore_index=True), "leads")

# --- 4. PIPELINE: FILTER & SEARCH ---
st.title("💼 Pipeline Processing")
c_search, c_slider = st.columns([7, 3])
with c_search:
    query = st.text_input("🔍 Tìm kiếm:", placeholder="Tên, ID hoặc SĐT...")
with c_slider:
    days_limit = st.slider("Khách chưa đụng tới (ngày):", 0, 90, 0)

df_leads = load_data("leads")

if not df_leads.empty:
    df_leads['last_interact'] = df_leads['last_interact'].astype(str).replace('nan', '')
    if days_limit > 0:
        df_leads['dt_obj'] = pd.to_datetime(df_leads['last_interact'], errors='coerce')
        mask = (df_leads['dt_obj'].isna()) | ((datetime.now() - df_leads['dt_obj']).dt.days >= days_limit)
        df_leads = df_leads[mask]
    if query:
        q = query.lower()
        df_leads = df_leads[df_leads.apply(lambda row: q in str(row).lower(), axis=1)]

# --- 5. RENDER LIST (ICON & RINGCENTRAL CHUẨN) ---
for idx, row in df_leads.iterrows():
    curr_h = str(row['note']) if str(row['note']) != 'nan' else ""
    crm_url = str(row['crm_link']) if str(row['crm_link']) != 'nan' else "#"
    
    with st.container(border=True):
        c_info, c_note, c_edit = st.columns([4, 5, 1])
        with c_info:
            st.markdown(f"#### {row['name']}")
            rid = str(row['crm_id']).strip()
            st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;"><span style="background:#7d3c98;color:white;padding:1px 4px;border-radius:3px;font-size:10px;">ID</span><a href="{crm_url}" target="_blank" style="color:#e83e8c;text-decoration:none;font-weight:bold;background:#fef1f6;padding:2px 6px;border-radius:4px;border:1px solid #fce4ec;">🔗 {rid}</a></div>""", unsafe_allow_html=True)
            
            p_c = str(row['cell']).strip(); p_w = str(row['work']).strip(); em = str(row['email']).strip()
            n_e = urllib.parse.quote(str(row['name'])); m_e = urllib.parse.quote(f"Chao {row['name']}...")
            st.markdown(f"""<div style="display:flex;gap:15px;align-items:center;"><span>📱 <a href="tel:{p_c}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_c}</a></span><a href="rcmobile://sms?number={p_c}&body={m_e}">💬</a><a href="mailto:{em}?body={m_e}">📧</a><a href="https://calendar.google.com/calendar/r/eventedit?text=TMC_{n_e}" target="_blank">📅</a></div>""", unsafe_allow_html=True)
            if p_w and p_w not in ['0', 'nan', '']: st.markdown(f'📞 Work: <a href="tel:{p_w}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_w}</a>', unsafe_allow_html=True)

        with c_note:
            st.markdown(f'<div class="history-container">{curr_h}</div>', unsafe_allow_html=True)
            # NHẬP LÀ ĂN NGAY
            new_txt = st.text_input("Note & Enter", key=f"n_{idx}", placeholder="Ghi chú...", label_visibility="collapsed")
            if new_txt:
                now = datetime.now()
                entry = f"<div class='history-entry'><span class='timestamp'>[{now.strftime('%m/%d %H:%M')}]</span>{new_txt}</div>"
                full_df = load_data("leads")
                full_df.at[idx, 'note'] = entry + curr_h
                full_df.at[idx, 'last_interact'] = now.strftime("%Y-%m-%d %H:%M:%S")
                save_and_refresh(full_df, "leads")

        with c_edit:
            with st.popover("⋮"):
                en = st.text_input("Name", value=row['name'], key=f"en_{idx}")
                ei = st.text_input("ID", value=row['crm_id'], key=f"ei_{idx}")
                ec = st.text_input("Cell", value=row['cell'], key=f"ec_{idx}")
                ew = st.text_input("Work", value=row['work'], key=f"ew_{idx}")
                ee = st.text_input("Email", value=row['email'], key=f"ee_{idx}")
                es = st.text_input("State", value=row['state'], key=f"es_{idx}")
                el = st.text_input("Link CRM", value=row['crm_link'], key=f"el_{idx}")
                if st.button("Save ✅", key=f"sv_{idx}", use_container_width=True):
                    full_df = load_data("leads")
                    full_df.loc[idx, ['name','crm_id','cell','work','email','state','crm_link']] = [en, ei, ec, ew, ee, es, el]
                    save_and_refresh(full_df, "leads")
                st.divider()
                if st.button("Xóa", key=f"del_{idx}", type="primary", use_container_width=True):
                    full_df = load_data("leads")
                    save_and_refresh(full_df.drop(idx), "leads")
