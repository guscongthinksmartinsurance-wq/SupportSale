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

# --- 2. CSS CHUẨN ---
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

# --- 3. LOGIC NOTE ---
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

# --- 4. SIDEBAR (GỌN GÀNG VỚI SELECTBOX) ---
with st.sidebar:
    st.title("🛠️ CRM Tools")
    df_links = load_data("links")
    
    # Quick Links dạng Selectbox
    links_list = df_links[df_links['category'] == 'Quick Link']
    if not links_list.empty:
        st.subheader("🔗 Quick Links")
        selected_link = st.selectbox("Chọn liên kết nhanh:", ["-- Chọn Link --"] + links_list['title'].tolist())
        if selected_link != "-- Chọn Link --":
            url = links_list[links_list['title'] == selected_link]['url'].values[0]
            st.markdown(f"🚀 **[Mở: {selected_link}]({url})**")

    # Sales Kit dạng Selectbox
    sk_list = df_links[df_links['category'] == 'Sales Kit']
    if not sk_list.empty:
        st.subheader("📚 Sales Kit")
        selected_sk = st.selectbox("Chọn tài liệu:", ["-- Chọn tài liệu --"] + sk_list['title'].tolist())
        if selected_sk != "-- Chọn tài liệu --":
            url_sk = sk_list[sk_list['title'] == selected_sk]['url'].values[0]
            st.markdown(f"📁 **[Xem tài liệu: {selected_sk}]({url_sk})**")
            if "youtube.com" in url_sk or "youtu.be" in url_sk:
                st.video(url_sk)

    st.divider()
    # Các form Add vẫn giữ trong Expander cho gọn
    with st.expander("➕ Thêm Link / Sales Kit"):
        with st.form("add_l"):
            c = st.selectbox("Loại", ["Quick Link", "Sales Kit"]); t = st.text_input("Tên"); u = st.text_input("URL")
            if st.form_submit_button("Lưu"):
                save_data(pd.concat([df_links, pd.DataFrame([{"category":c,"title":t,"url":u}])], ignore_index=True), "links"); st.rerun()

    with st.expander("➕ Thêm Khách Hàng"):
        with st.form("add_lead"):
            n = st.text_input("Name"); i = st.text_input("ID"); c = st.text_input("Cell"); w = st.text_input("Work")
            if st.form_submit_button("Lưu"):
                df_leads = load_data("leads")
                save_data(pd.concat([df_leads, pd.DataFrame([{"name":n,"crm_id":i,"cell":c,"work":w,"status":"New","note":""}])], ignore_index=True), "leads"); st.rerun()

# --- 5. PIPELINE PROCESSING ---
st.title("💼 Pipeline Processing")
leads_df = load_data("leads")

c_search, c_filter = st.columns([7, 3])
with c_search:
    query = st.text_input("🔍 Tìm kiếm nhanh (Name, ID, Cell, Work)...").lower()
with c_filter:
    days = st.slider("⏳ Không tương tác (ngày)", 0, 90, 90)

if not leads_df.empty:
    filtered_df = leads_df[leads_df.apply(lambda r: query in str(r['name']).lower() or query in str(r['crm_id']).lower() or query in str(r['cell']).lower() or query in str(r['work']).lower(), axis=1)]

    for idx, row in filtered_df.iterrows():
        curr_h = str(row['note']) if str(row['note']) != 'nan' else ""
        with st.container(border=True):
            c_info, c_note, c_edit = st.columns([4, 5, 1])
            with c_info:
                st.markdown(f"#### {row['name']}")
                st.markdown(f"""<div style="display:flex;gap:8px;margin-bottom:8px;"><span style="background:#7d3c98;color:white;padding:1px 4px;border-radius:3px;font-size:10px;">ID</span><a href="{row.get('crm_link','#')}" target="_blank" style="color:#e83e8c;text-decoration:none;font-weight:bold;background:#fef1f6;padding:2px 6px;border-radius:4px;border:1px solid #fce4ec;">🔗 {row['crm_id']}</a></div>""", unsafe_allow_html=True)
                
                # Bốn Icon và Workphone có link tel:
                cell = str(row['cell']).strip(); work = str(row['work']).strip()
                n_e = urllib.parse.quote(str(row['name']))
                st.markdown(f"""<div style="display:flex;gap:15px;font-size:20px;">
                    <a href="tel:{cell}">📱</a> <a href="rcmobile://sms?number={cell}">💬</a>
                    <a href="mailto:{row.get('email','')}">📧</a> <a href="https://calendar.google.com/calendar/r/eventedit?text=Meeting_{n_e}" target="_blank">📅</a>
                </div>""", unsafe_allow_html=True)
                st.markdown(f"📱 Cell: **[{cell}](tel:{cell})**")
                st.markdown(f"📞 Work: **[{work}](tel:{work})**")
                st.write(f"🏷️ Status: {row['status']}")

            with c_note:
                st.markdown(f'<div class="history-container">{curr_h}</div>', unsafe_allow_html=True)
                cn1, cn2 = st.columns([8, 2])
                with cn1: st.text_input("Note...", key=f"n_{idx}", on_change=save_note_v24, args=(idx, curr_h, f"n_{idx}"), label_visibility="collapsed")
                with cn2:
                    with st.popover("📝 Sửa"):
                        ed_h = st.text_area("Sửa Note", value=curr_h, height=150)
                        if st.button("Lưu", key=f"s_n_{idx}"):
                            full = load_data("leads"); full.at[idx, 'note'] = ed_h; save_data(full, "leads"); st.rerun()

            with c_edit:
                with st.popover("⚙️"):
                    with st.form(f"ed_{idx}"):
                        un = st.text_input("Name", value=row['name']); ui = st.text_input("ID", value=row['crm_id'])
                        uc = st.text_input("Cell", value=row['cell']); uw = st.text_input("Work", value=row['work'])
                        ue = st.text_input("Email", value=row.get('email','')); ul = st.text_input("Link CRM", value=row.get('crm_link',''))
                        us = st.selectbox("Status", ["New", "Contacted", "Following", "Closed"])
                        if st.form_submit_button("Cập nhật"):
                            f = load_data("leads"); f.loc[idx,['name','crm_id','cell','work','email','crm_link','status']]=[un,ui,uc,uw,ue,ul,us]; save_data(f, "leads"); st.rerun()
