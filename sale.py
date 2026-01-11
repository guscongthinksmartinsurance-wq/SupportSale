import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse

# --- 1. CẤU HÌNH & KẾT NỐI ---
st.set_page_config(page_title="TMC CRM PRO V24.4", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    return conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0).dropna(how='all')

def save_data(df, worksheet):
    df = df.fillna("")
    conn.update(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, data=df)
    st.cache_data.clear()

# --- 2. CSS CHUẨN (GIAO DIỆN CŨ) ---
st.markdown("""
    <style>
    .history-container {
        background-color: #ffffff; border: 1px solid #e1e4e8; border-radius: 6px;
        padding: 10px; height: 160px; overflow-y: auto; font-family: sans-serif;
        font-size: 13px; color: #24292e; margin-bottom: 5px;
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
        combined = entry + str(current_note)
        df_full = load_data("leads")
        df_full.at[idx, 'note'] = combined
        df_full.at[idx, 'last_interact'] = now.strftime("%Y-%m-%d %H:%M:%S")
        save_data(df_full, "leads")
        st.session_state[note_key] = ""
        st.rerun()

# --- 4. SIDEBAR (LINKS, SALES KIT, ADD NEW) ---
with st.sidebar:
    st.title("🛠️ CRM Tools")
    df_links = load_data("links")
    
    # Quick Links & Sales Kit
    col_l, col_s = st.columns(2)
    with col_l:
        st.subheader("🔗 Links")
        for _, l in df_links[df_links['category'] == 'Quick Link'].iterrows():
            st.markdown(f"**[{l['title']}]({l['url']})**")
    with col_s:
        st.subheader("📁 Sales Kit")
        for _, l in df_links[df_links['category'] == 'Sales Kit'].iterrows():
            st.markdown(f"**[{l['title']}]({l['url']})**")
    
    # Add Link/Sales Kit trực tiếp
    with st.expander("➕ Thêm Link / Sales Kit"):
        with st.form("add_link_form", clear_on_submit=True):
            cat = st.selectbox("Loại", ["Quick Link", "Sales Kit"])
            tit = st.text_input("Tiêu đề"); url = st.text_input("Link URL")
            if st.form_submit_button("Lưu Link"):
                new_l = pd.DataFrame([{"category": cat, "title": tit, "url": url}])
                save_data(pd.concat([df_links, new_l], ignore_index=True), "links"); st.rerun()

    st.divider()
    # Add New Lead (Đầy đủ trường)
    with st.expander("➕ Thêm Khách Hàng Mới"):
        with st.form("new_lead_form", clear_on_submit=True):
            n = st.text_input("Họ tên *"); i = st.text_input("CRM ID *")
            c = st.text_input("Cellphone"); w = st.text_input("Workphone")
            e = st.text_input("Email"); l = st.text_input("Link CRM")
            if st.form_submit_button("Lưu Khách Hàng"):
                df_all = load_data("leads")
                new_r = {"name":n, "crm_id":i, "cell":c, "work":w, "email":e, "crm_link":l, "status":"New", "note":""}
                save_data(pd.concat([df_all, pd.DataFrame([new_r])], ignore_index=True), "leads"); st.rerun()

# --- 5. BỘ LỌC & TÌM KIẾM ---
st.title("💼 Pipeline Processing")
leads_df = load_data("leads")

c_search, c_filter = st.columns([7, 3])
with c_search:
    search_query = st.text_input("🔍 Tìm kiếm nhanh (Name, ID, Cell, Work)...").lower()
with c_filter:
    days_limit = st.slider("⏳ Không tương tác (ngày)", 0, 90, 90)

# Logic lọc dữ liệu
if not leads_df.empty:
    # Lọc theo tìm kiếm
    filtered_df = leads_df[
        leads_df.apply(lambda r: search_query in str(r['name']).lower() or 
                                search_query in str(r['crm_id']).lower() or 
                                search_query in str(r['cell']).lower() or 
                                search_query in str(r['work']).lower(), axis=1)
    ]
    # Lọc theo ngày không tương tác (giả định có cột last_interact)
    # (Phần này có thể bổ sung thêm logic datetime tùy theo định dạng của anh)

# --- 6. RENDER PIPELINE ---
    for idx, row in filtered_df.iterrows():
        curr_h = str(row['note']) if str(row['note']) != 'nan' else ""
        with st.container(border=True):
            c_info, c_note, c_edit = st.columns([4, 5, 1])
            
            with c_info:
                st.markdown(f"#### {row['name']}")
                # Badge ID & Link CRM
                st.markdown(f"""<div style="display:flex;gap:8px;margin-bottom:8px;"><span style="background:#7d3c98;color:white;padding:1px 4px;border-radius:3px;font-size:10px;">ID</span><a href="{row.get('crm_link','#')}" target="_blank" style="color:#e83e8c;text-decoration:none;font-weight:bold;background:#fef1f6;padding:2px 6px;border-radius:4px;border:1px solid #fce4ec;">🔗 {row['crm_id']}</a></div>""", unsafe_allow_html=True)
                
                # Bộ 4 Icon Tương Tác
                cell = str(row['cell']).strip(); work = str(row['work']).strip()
                n_e = urllib.parse.quote(str(row['name']))
                st.markdown(f"""<div style="display:flex;gap:15px;font-size:20px;">
                    <a href="tel:{cell}">📱</a> <a href="rcmobile://sms?number={cell}">💬</a>
                    <a href="mailto:{row.get('email','')}">📧</a> <a href="https://calendar.google.com/calendar/r/eventedit?text=Meeting_{n_e}" target="_blank">📅</a>
                </div>""", unsafe_allow_html=True)
                st.write(f"📞 Cell: {cell} | ☎️ Work: {work}")
                st.write(f"🏷️ Status: **{row['status']}**")

            with c_note:
                st.markdown(f'<div class="history-container">{curr_h}</div>', unsafe_allow_html=True)
                col_n1, col_n2 = st.columns([8, 2])
                with col_n1:
                    st.text_input("Note nhanh...", key=f"n_{idx}", on_change=save_note_v24, args=(idx, curr_h, f"n_{idx}"), label_visibility="collapsed")
                with col_n2:
                    with st.popover("📝 Sửa"):
                        edited_history = st.text_area("Chỉnh sửa toàn bộ Note", value=curr_h, height=200)
                        if st.button("Lưu lại", key=f"save_ed_{idx}"):
                            full_df = load_data("leads")
                            full_df.at[idx, 'note'] = edited_history
                            save_data(full_df, "leads"); st.rerun()

            with c_edit:
                with st.popover("⚙️"):
                    with st.form(f"f_ed_{idx}"):
                        u_name = st.text_input("Name", value=row['name'])
                        u_id = st.text_input("ID", value=row['crm_id'])
                        u_cell = st.text_input("Cell", value=row['cell'])
                        u_work = st.text_input("Work", value=row['work'])
                        u_email = st.text_input("Email", value=row.get('email',''))
                        u_link = st.text_input("Link CRM", value=row.get('crm_link',''))
                        u_status = st.selectbox("Status", ["New", "Contacted", "Following", "Closed"], index=0)
                        if st.form_submit_button("Cập nhật"):
                            f_df = load_data("leads")
                            f_df.loc[idx, ['name','crm_id','cell','work','email','crm_link','status']] = [u_name, u_id, u_cell, u_work, u_email, u_link, u_status]
                            save_data(f_df, "leads"); st.rerun()
                    if st.button("🗑️ Xóa", key=f"d_{idx}", type="primary"):
                        f_df = load_data("leads"); save_data(f_df.drop(idx), "leads"); st.rerun()
