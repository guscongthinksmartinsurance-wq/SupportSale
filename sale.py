import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse
import re

# --- 1. KẾT NỐI DATABASE ---
st.set_page_config(page_title="TMC CRM PRO V31", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    return conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0).dropna(how='all')

def save_data(df, worksheet):
    df = df.fillna("")
    conn.update(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, data=df)
    st.cache_data.clear()

# --- 2. CSS GIAO DIỆN ---
st.markdown("""
    <style>
    .history-container {
        background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px;
        padding: 12px; height: 160px; overflow-y: auto; font-size: 13px; color: #495057;
    }
    .history-entry { border-bottom: 1px solid #dee2e6; margin-bottom: 8px; padding-bottom: 4px; }
    .timestamp { color: #007bff; font-weight: bold; margin-right: 8px; }
    .contact-link { text-decoration: none; color: #28a745; font-weight: bold; }
    .id-badge {
        background-color: #fce4ec; color: #d81b60; padding: 2px 8px;
        border-radius: 12px; font-weight: bold; font-size: 13px; text-decoration: none;
        border: 1px solid #f8bbd0; margin-left: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC LỌC HTML CHO PHẦN SỬA NOTE ---
def clean_html(raw_html):
    # Xóa các thẻ div, span để lấy text thuần cho ô Sửa Note
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', str(raw_html))
    return cleantext

# --- 4. LOGIC LƯU NOTE ---
def save_note_v31(idx, current_note, note_key):
    new_txt = st.session_state[note_key]
    if new_txt and new_txt.strip():
        now = datetime.now()
        entry = f"<div class='history-entry'><span class='timestamp'>[{now.strftime('%m/%d %H:%M')}]</span>{new_txt}</div>"
        combined = entry + str(current_note)
        df = load_data("leads")
        df.at[idx, 'note'] = combined
        df.at[idx, 'last_interact'] = now.strftime("%Y-%m-%d %H:%M:%S")
        save_data(df, "leads")
        st.session_state[note_key] = ""; st.rerun()

# --- 5. SIDEBAR (GIỮ NGUYÊN 100% THEO Ý ANH) ---
with st.sidebar:
    st.title("⚒️ CRM Tools")
    df_links = load_data("links")
    with st.expander("🔗 Danh sách Quick Links"):
        list_links = df_links[df_links['category'] == 'Quick Link']
        sel_l = st.selectbox("Chọn Link:", ["-- Chọn --"] + list_links['title'].tolist(), key="sb_l")
        if sel_l != "-- Chọn --":
            st.markdown(f"🚀 [Mở ngay: {sel_l}]({list_links[list_links['title'] == sel_l]['url'].values[0]})")
    with st.expander("📁 Danh sách Sales Kit"):
        list_sk = df_links[df_links['category'] == 'Sales Kit']
        sel_sk = st.selectbox("Chọn tài liệu:", ["-- Chọn --"] + list_sk['title'].tolist(), key="sb_sk")
        if sel_sk != "-- Chọn --":
            st.markdown(f"📂 [Xem: {sel_sk}]({list_sk[list_sk['title'] == sel_sk]['url'].values[0]})")
    with st.expander("➕ Thêm Link / Sales Kit mới"):
        with st.form("form_add_link"):
            cat_l = st.selectbox("Loại", ["Quick Link", "Sales Kit"]); tit_l = st.text_input("Tiêu đề"); url_l = st.text_input("URL")
            if st.form_submit_button("Lưu Link"):
                save_data(pd.concat([df_links, pd.DataFrame([{"category":cat_l, "title":tit_l, "url":url_l}])], ignore_index=True), "links"); st.rerun()
    st.divider()
    with st.expander("➕ Thêm Khách Hàng Mới"):
        with st.form("form_add_lead"):
            f_n = st.text_input("Họ tên"); f_id = st.text_input("CRM ID"); f_c = st.text_input("Cellphone"); f_w = st.text_input("Workphone")
            f_e = st.text_input("Email"); f_l = st.text_input("Link CRM"); f_s = st.selectbox("Status", ["New", "Contacted", "Following", "Closed"])
            if st.form_submit_button("Lưu Lead"):
                df_all = load_data("leads")
                save_data(pd.concat([df_all, pd.DataFrame([{"name":f_n, "crm_id":f_id, "cell":f_c, "work":f_w, "email":f_e, "crm_link":f_l, "status":f_s, "note":""}])], ignore_index=True), "leads"); st.rerun()

# --- 6. PIPELINE PROCESSING ---
st.title("💼 Pipeline Processing")
leads_df = load_data("leads")
c1, c2 = st.columns([7, 3])
q = c1.text_input("🔍 Tìm theo Tên, ID, SĐT...", placeholder="Nhập từ khóa...")
days_filter = c2.slider("⏳ Không tương tác (ngày)", 0, 90, 90)

if not leads_df.empty:
    filtered = leads_df[leads_df.apply(lambda r: q.lower() in str(r['name']).lower() or q.lower() in str(r['crm_id']).lower() or q.lower() in str(r['cell']).lower() or q.lower() in str(r['work']).lower(), axis=1)]

    for idx, row in filtered.iterrows():
        curr_h = str(row['note']) if str(row['note']) != 'nan' else ""
        # FIX TRIỆT ĐỂ WORKPHONE: Ép kiểu string và xóa phần .0 nếu có
        work = str(row['work']).replace('.0', '').strip() if str(row['work']) != 'nan' else ""
        cell = str(row['cell']).replace('.0', '').strip() if str(row['cell']) != 'nan' else ""
        
        with st.container(border=True):
            ci, cn, ce = st.columns([4.5, 5, 0.5])
            with ci:
                st.markdown(f"<div style='display:flex;align-items:center;'><h4 style='margin:0;'>{row['name']}</h4><a href='{row.get('crm_link','#')}' target='_blank' class='id-badge'>🆔 {row['crm_id']}</a></div>", unsafe_allow_html=True)
                n_e = urllib.parse.quote(str(row['name']))
                st.markdown(f"<div style='margin-top:8px;display:flex;align-items:center;gap:10px;'>📱 Cell: <a href='tel:{cell}' class='contact-link'>{cell}</a><a href='rcmobile://sms?number={cell}'>💬</a><a href='mailto:{row.get('email','')}'>📧</a><a href='https://calendar.google.com/calendar/r/eventedit?text=Meeting_{n_e}' target='_blank'>📅</a></div>", unsafe_allow_html=True)
                st.markdown(f"📞 Work: <a href='tel:{work}' class='contact-link'>{work}</a>", unsafe_allow_html=True)
                st.caption(f"🏷️ Status: {row['status']}")

            with cn:
                st.markdown(f'<div class="history-container">{curr_h}</div>', unsafe_allow_html=True)
                col_n1, col_n2 = st.columns([8.5, 1.5])
                with col_n1: st.text_input("Note nhanh...", key=f"n_{idx}", on_change=save_note_v31, args=(idx, curr_h, f"n_{idx}"), label_visibility="collapsed")
                with col_n2:
                    with st.popover("📝"):
                        # FIX NOTE: Làm sạch HTML trước khi cho vào ô sửa
                        clean_history = clean_html(curr_h)
                        new_h = st.text_area("Sửa lịch sử (Text thuần)", value=clean_history, height=250)
                        if st.button("Cập nhật Note", key=f"sn_{idx}"):
                            # Khi lưu lại, ta bao bọc lại bằng thẻ div để hiển thị đúng định dạng cũ
                            formatted_h = f"<div class='history-entry'>{new_h}</div>"
                            f_df = load_data("leads"); f_df.at[idx, 'note'] = formatted_h; save_data(f_df, "leads"); st.rerun()

            with ce:
                with st.popover("⚙️"):
                    with st.form(f"ed_{idx}"):
                        un=st.text_input("Tên",value=row['name']); ui=st.text_input("ID",value=row['crm_id'])
                        uc=st.text_input("Cell",value=cell); uw=st.text_input("Work",value=work)
                        uem=st.text_input("Email",value=row.get('email','')); ul=st.text_input("Link CRM",value=row.get('crm_link',''))
                        us=st.selectbox("Status",["New","Contacted","Following","Closed"], index=0)
                        if st.form_submit_button("Cập nhật"):
                            f=load_data("leads"); f.loc[idx,['name','crm_id','cell','work','email','crm_link','status']]=[un,ui,uc,uw,uem,ul,us]
                            save_data(f,"leads"); st.rerun()
                    if st.button("🗑️ Xóa", key=f"d_{idx}", type="primary"):
                        f=load_data("leads"); save_data(f.drop(idx),"leads"); st.rerun()
