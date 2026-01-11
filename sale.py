import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse
import re

# --- 1. KẾT NỐI DATABASE ---
st.set_page_config(page_title="TMC CRM PRO V35", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    try:
        df = conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0)
        if df is not None:
            # Ép tất cả thành string và xử lý triệt để đuôi .0 ngay khi load
            df = df.fillna("").astype(str)
            for col in df.columns:
                df[col] = df[col].apply(lambda x: x[:-2] if x.endswith('.0') else x)
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def save_data(df, worksheet):
    conn.update(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, data=df.fillna(""))
    st.cache_data.clear()

# --- 2. HÀM HỖ TRỢ (TÌM KIẾM THÔNG MINH) ---
def clean_phone_to_int(phone_str):
    # Chỉ giữ lại các chữ số để so sánh tìm kiếm
    return re.sub(r'\D', '', str(phone_str))

def clean_html_for_edit(raw_html):
    t = str(raw_html).replace('</div>', '\n')
    return re.sub(r'<[^>]*>', '', t).strip()

def is_youtube(url):
    return "youtube.com" in str(url).lower() or "youtu.be" in str(url).lower()

# --- 3. CSS GIAO DIỆN ---
st.markdown("""
    <style>
    .history-container {
        background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px;
        padding: 12px; height: 160px; overflow-y: auto; font-size: 13px; color: #495057;
    }
    .history-entry { border-bottom: 1px solid #dee2e6; margin-bottom: 8px; padding-bottom: 4px; }
    .contact-link { text-decoration: none; color: #28a745; font-weight: bold; }
    .id-badge {
        background-color: #fce4ec; color: #d81b60; padding: 2px 8px;
        border-radius: 12px; font-weight: bold; font-size: 13px; text-decoration: none;
        border: 1px solid #f8bbd0; margin-left: 10px;
    }
    .owner-tag { color: #6c757d; font-size: 12px; font-style: italic; }
    </style>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("⚒️ CRM Tools")
    df_links = load_data("links")
    
    with st.expander("🔗 Quick Links"):
        if not df_links.empty:
            ql = df_links[df_links['category'] == 'Quick Link']
            for idx, row in ql.iterrows():
                c1, c2 = st.columns([8, 2])
                c1.markdown(f"🚀 [{row['title']}]({row['url']})")
                if c2.button("🗑️", key=f"del_ql_{idx}"):
                    st.session_state[f"conf_ql_{idx}"] = True
                if st.session_state.get(f"conf_ql_{idx}"):
                    st.warning("Xóa?")
                    ok, no = st.columns(2)
                    if ok.button("Xóa", key=f"re_ql_{idx}", type="primary"):
                        save_data(df_links.drop(idx), "links"); del st.session_state[f"conf_ql_{idx}"]; st.rerun()
                    if no.button("Hủy", key=f"can_ql_{idx}"):
                        del st.session_state[f"conf_ql_{idx}"]; st.rerun()

    with st.expander("📁 Sales Kit"):
        if not df_links.empty:
            sk = df_links[df_links['category'] == 'Sales Kit']
            for idx, row in sk.iterrows():
                st.markdown(f"📂 **{row['title']}**")
                if is_youtube(row['url']): st.video(row['url'])
                else: st.markdown(f"🔗 [Mở tài liệu]({row['url']})")
                if st.button("🗑️ Xóa", key=f"del_sk_{idx}"): st.session_state[f"conf_sk_{idx}"] = True
                if st.session_state.get(f"conf_sk_{idx}"):
                    ok, no = st.columns(2)
                    if ok.button("Xóa", key=f"re_sk_{idx}", type="primary"):
                        save_data(df_links.drop(idx), "links"); del st.session_state[f"conf_sk_{idx}"]; st.rerun()
                    if no.button("Hủy", key=f"can_sk_{idx}"): del st.session_state[f"conf_sk_{idx}"]; st.rerun()
                st.divider()

    with st.expander("➕ Thêm Link"):
        with st.form("f_link"):
            c=st.selectbox("Loại",["Quick Link","Sales Kit"]); t=st.text_input("Tiêu đề"); u=st.text_input("URL")
            if st.form_submit_button("Lưu"):
                save_data(pd.concat([df_links, pd.DataFrame([{"category":c,"title":t,"url":u}])], ignore_index=True), "links"); st.rerun()

    st.divider()
    with st.expander("➕ Thêm Khách Hàng Mới"):
        with st.form("f_lead"):
            fn=st.text_input("Họ tên"); fi=st.text_input("CRM ID")
            fc=st.text_input("Cell"); fw=st.text_input("Work")
            fe=st.text_input("Email"); fl=st.text_input("Link CRM")
            f_st=st.text_input("State"); f_ow=st.text_input("Owner")
            fs=st.selectbox("Status",["New","Contacted","Following","Closed"])
            if st.form_submit_button("Lưu Lead"):
                df_all = load_data("leads")
                new_row = {"name":fn,"crm_id":fi,"cell":fc,"work":fw,"email":fe,"crm_link":fl,"status":fs,"state":f_st,"owner":f_ow,"note":"","last_interact":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                save_data(pd.concat([df_all, pd.DataFrame([new_row])], ignore_index=True), "leads"); st.rerun()

# --- 5. PIPELINE & FILTER ---
st.title("💼 Pipeline Processing")
leads_df = load_data("leads")
c_sch, c_sld = st.columns([7, 3])
search_raw = c_sch.text_input("🔍 Tìm Tên, ID, SĐT (nhập số liền nhau vẫn ra)...", key="search_main")
q = str(search_raw).lower().strip()
q_numeric = clean_phone_to_int(q) # Chuỗi số để tìm kiếm thông minh
days_limit = c_sld.slider("⏳ Không tương tác (ngày)", 0, 90, 90)

if not leads_df.empty:
    # Lọc tìm kiếm thông minh
    def smart_filter(r):
        name_match = q in str(r.get('name','')).lower()
        id_match = q in str(r.get('crm_id','')).lower()
        # So sánh số điện thoại bằng cách loại bỏ các ký tự đặc biệt
        cell_clean = clean_phone_to_int(r.get('cell',''))
        work_clean = clean_phone_to_int(r.get('work',''))
        phone_match = (q_numeric != "" and (q_numeric in cell_clean or q_numeric in work_clean))
        return name_match or id_match or phone_match

    filtered = leads_df[leads_df.apply(smart_filter, axis=1)]

    for idx, row in filtered.iterrows():
        with st.container(border=True):
            ci, cn, ce = st.columns([4.5, 5, 0.5])
            with ci:
                st.markdown(f"<div style='display:flex;align-items:center;'><h4 style='margin:0;'>{row['name']}</h4><a href='{row['crm_link']}' target='_blank' class='id-badge'>🆔 {row['crm_id']}</a></div>", unsafe_allow_html=True)
                st.markdown(f"<span class='owner-tag'>📍 State: {row.get('state','-')} | 👤 Owner: {row.get('owner','-')}</span>", unsafe_allow_html=True)
                
                cell = row['cell']; work = row['work']
                st.markdown(f"<div style='margin-top:8px;display:flex;align-items:center;gap:10px;'>📱 Cell: <a href='tel:{cell}' class='contact-link'>{cell}</a><a href='rcmobile://sms?number={cell}'>💬</a><a href='mailto:{row['email']}'>📧</a></div>", unsafe_allow_html=True)
                if work: st.markdown(f"📞 Work: <a href='tel:{work}' class='contact-link'>{work}</a>", unsafe_allow_html=True)
                st.caption(f"🏷️ Status: {row['status']}")
            
            with cn:
                note_h = str(row.get('note', ''))
                st.markdown(f'<div class="history-container">{note_h}</div>', unsafe_allow_html=True)
                n_input = st.text_input("Note nhanh...", key=f"n_{idx}", label_visibility="collapsed")
                if n_input: # Logic lưu note nhanh
                    now_str = datetime.now().strftime("[%m/%d %H:%M]")
                    new_entry = f"<div class='history-entry'><span style='color:#007bff;font-weight:bold;'>{now_str}</span> {n_input}</div>"
                    full_note = new_entry + note_h
                    leads_df.at[idx, 'note'] = full_note
                    leads_df.at[idx, 'last_interact'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    save_data(leads_df, "leads"); st.rerun()
            
            with ce:
                with st.popover("⚙️"):
                    with st.form(f"ed_{idx}"):
                        un=st.text_input("Tên",value=row['name']); ui=st.text_input("ID",value=row['crm_id'])
                        uc=st.text_input("Cell",value=row['cell']); uw=st.text_input("Work",value=row['work'])
                        uem=st.text_input("Email",value=row['email']); ul=st.text_input("Link CRM",value=row['crm_link'])
                        ust=st.text_input("State",value=row.get('state','')); uow=st.text_input("Owner",value=row.get('owner',''))
                        us=st.selectbox("Status",["New","Contacted","Following","Closed"])
                        if st.form_submit_button("Lưu"):
                            f=load_data("leads"); f.loc[idx,['name','crm_id','cell','work','email','crm_link','state','owner','status']]=[un,ui,uc,uw,uem,ul,ust,uow,us]
                            save_data(f,"leads"); st.rerun()
                    if st.button("🗑️ Xóa", key=f"d_{idx}", type="primary"):
                        st.session_state[f"c_del_{idx}"] = True
                    if st.session_state.get(f"c_del_{idx}"):
                        st.error("Xóa khách này?")
                        ok, no = st.columns(2)
                        if ok.button("Vâng", key=f"ok_d_{idx}"):
                            f=load_data("leads"); save_data(f.drop(idx),"leads"); del st.session_state[f"c_del_{idx}"]; st.rerun()
                        if no.button("Hủy", key=f"no_d_{idx}"): del st.session_state[f"c_del_{idx}"]; st.rerun()
