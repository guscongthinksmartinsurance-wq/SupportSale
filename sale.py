import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse
import re

# --- 1. KẾT NỐI DATABASE ---
st.set_page_config(page_title="TMC CRM PRO V33.2", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    try:
        df = conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0)
        return df.fillna("").astype(str) if df is not None else pd.DataFrame()
    except:
        return pd.DataFrame()

def save_data(df, worksheet):
    df_save = df.fillna("")
    conn.update(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, data=df_save)
    st.cache_data.clear()

# --- 2. CSS GIAO DIỆN ---
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
    </style>
""", unsafe_allow_html=True)

# --- 3. HÀM XỬ LÝ HỆ THỐNG ---
def format_phone(val):
    s = str(val).strip()
    return s[:-2] if s.endswith('.0') else s

def clean_html_for_edit(raw_html):
    t = str(raw_html).replace('</div>', '\n')
    return re.sub(r'<[^>]*>', '', t).strip()

def is_youtube(url):
    return "youtube.com" in str(url).lower() or "youtu.be" in str(url).lower()

def save_note_v33(idx, current_note, note_key):
    new_txt = st.session_state.get(note_key, "")
    if new_txt and new_txt.strip():
        now = datetime.now()
        entry = f"<div class='history-entry'><span class='timestamp'>[{now.strftime('%m/%d %H:%M')}]</span>{new_txt}</div>"
        combined = entry + str(current_note)
        df = load_data("leads")
        if not df.empty:
            df.at[idx, 'note'] = combined
            df.at[idx, 'last_interact'] = now.strftime("%Y-%m-%d %H:%M:%S")
            save_data(df, "leads")
            st.session_state[note_key] = "" 
            st.rerun()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("⚒️ CRM Tools")
    df_links = load_data("links")
    
    # 4.1 QUICK LINKS
    with st.expander("🔗 Quick Links"):
        if not df_links.empty:
            ql = df_links[df_links['category'] == 'Quick Link']
            for idx, row in ql.iterrows():
                c1, c2 = st.columns([8, 2])
                c1.markdown(f"🚀 [{row['title']}]({row['url']})")
                if c2.button("🗑️", key=f"del_ql_{idx}"):
                    st.session_state[f"conf_ql_{idx}"] = True
                
                if st.session_state.get(f"conf_ql_{idx}"):
                    st.warning("Xóa link?")
                    col_ok, col_no = st.columns(2)
                    if col_ok.button("Xóa", key=f"re_ql_{idx}", type="primary"):
                        save_data(df_links.drop(idx), "links")
                        del st.session_state[f"conf_ql_{idx}"]; st.rerun()
                    if col_no.button("Hủy", key=f"can_ql_{idx}"):
                        del st.session_state[f"conf_ql_{idx}"]; st.rerun() # LỆNH RERUN ĐỂ ĐÓNG KHUNG

    # 4.2 SALES KIT
    with st.expander("📁 Sales Kit"):
        if not df_links.empty:
            sk = df_links[df_links['category'] == 'Sales Kit']
            for idx, row in sk.iterrows():
                st.markdown(f"📂 **{row['title']}**")
                if is_youtube(row['url']): st.video(row['url'])
                else: st.markdown(f"🔗 [Mở tài liệu]({row['url']})")
                
                if st.button("🗑️ Xóa tài liệu", key=f"del_sk_{idx}"):
                    st.session_state[f"conf_sk_{idx}"] = True
                
                if st.session_state.get(f"conf_sk_{idx}"):
                    st.warning("Xác nhận xóa?")
                    col_ok, col_no = st.columns(2)
                    if col_ok.button("Vâng", key=f"re_sk_{idx}", type="primary"):
                        save_data(df_links.drop(idx), "links")
                        del st.session_state[f"conf_sk_{idx}"]; st.rerun()
                    if col_no.button("Không", key=f"can_sk_{idx}"):
                        del st.session_state[f"conf_sk_{idx}"]; st.rerun() # LỆNH RERUN ĐỂ ĐÓNG KHUNG
                st.divider()

    with st.expander("➕ Thêm Link / Sales Kit"):
        with st.form("f_link"):
            c=st.selectbox("Loại",["Quick Link","Sales Kit"]); t=st.text_input("Tiêu đề"); u=st.text_input("URL")
            if st.form_submit_button("Lưu"):
                save_data(pd.concat([df_links, pd.DataFrame([{"category":c,"title":t,"url":u}])], ignore_index=True), "links"); st.rerun()

# --- 5. PIPELINE ---
st.title("💼 Pipeline Processing")
leads_df = load_data("leads")
c_sch, c_sld = st.columns([7, 3])
q = str(c_sch.text_input("🔍 Tìm theo Tên, ID, SĐT...", key="search_main")).lower().strip()
days_limit = c_sld.slider("⏳ Không tương tác", 0, 90, 90)

if not leads_df.empty:
    filtered = leads_df[leads_df.apply(lambda r: q in r.get('name','').lower() or q in r.get('crm_id','').lower() or q in r.get('cell','').lower() or q in r.get('work','').lower(), axis=1)]

    for idx, row in filtered.iterrows():
        note_h = str(row.get('note', ''))
        cell = format_phone(row.get('cell', ''))
        work = format_phone(row.get('work', ''))
        
        with st.container(border=True):
            ci, cn, ce = st.columns([4.5, 5, 0.5])
            with ci:
                st.markdown(f"<div style='display:flex;align-items:center;'><h4 style='margin:0;'>{row.get('name','')}</h4><a href='{row.get('crm_link','#')}' target='_blank' class='id-badge'>🆔 {row.get('crm_id','')}</a></div>", unsafe_allow_html=True)
                n_e = urllib.parse.quote(str(row.get('name','')))
                st.markdown(f"<div style='margin-top:8px;display:flex;align-items:center;gap:10px;'>📱 Cell: <a href='tel:{cell}' class='contact-link'>{cell}</a><a href='rcmobile://sms?number={cell}'>💬</a><a href='mailto:{row.get('email','')}'>📧</a><a href='https://calendar.google.com/calendar/r/eventedit?text=Meeting_{n_e}' target='_blank'>📅</a></div>", unsafe_allow_html=True)
                st.markdown(f"📞 Work: <a href='tel:{work}' class='contact-link'>{work}</a>", unsafe_allow_html=True)
                st.caption(f"🏷️ Status: {row.get('status','New')}")
            
            with cn:
                st.markdown(f'<div class="history-container">{note_h}</div>', unsafe_allow_html=True)
                cn1, cn2 = st.columns([8.5, 1.5])
                with cn1: st.text_input("Note nhanh...", key=f"n_{idx}", on_change=save_note_v33, args=(idx, note_h, f"n_{idx}"), label_visibility="collapsed")
                with cn2:
                    with st.popover("📝"):
                        cl_h = clean_html_for_edit(note_h)
                        new_h = st.text_area("Sửa Note", value=cl_h, height=250)
                        if st.button("Cập nhật", key=f"sn_{idx}"):
                            ls = new_h.split('\n')
                            f_h = "".join([f"<div class='history-entry'>{line}</div>" for line in ls if line.strip()])
                            f_df = load_data("leads"); f_df.at[idx, 'note'] = f_h; save_data(f_df, "leads"); st.rerun()
            
            with ce:
                with st.popover("⚙️"):
                    with st.form(f"ed_{idx}"):
                        un=st.text_input("Tên",value=row.get('name','')); ui=st.text_input("ID",value=row.get('crm_id',''))
                        uc=st.text_input("Cell",value=cell); uw=st.text_input("Work",value=work)
                        uem=st.text_input("Email",value=row.get('email','')); ul=st.text_input("Link CRM",value=row.get('crm_link',''))
                        us=st.selectbox("Status",["New","Contacted","Following","Closed"])
                        if st.form_submit_button("Cập nhật"):
                            f=load_data("leads"); f.loc[idx,['name','crm_id','cell','work','email','crm_link','status']]=[un,ui,uc,uw,uem,ul,us]
                            save_data(f,"leads"); st.rerun()
                    
                    if st.button("🗑️ Xóa Lead", key=f"d_{idx}", type="primary"):
                        st.session_state[f"confirm_del_{idx}"] = True
                    if st.session_state.get(f"confirm_del_{idx}"):
                        st.error("Xóa khách này?")
                        col_y, col_n = st.columns(2)
                        if col_y.button("Vâng", key=f"re_d_{idx}", type="primary"):
                            f=load_data("leads"); save_data(f.drop(idx),"leads")
                            del st.session_state[f"confirm_del_{idx}"]; st.rerun()
                        if col_n.button("Hủy", key=f"can_d_{idx}"):
                            del st.session_state[f"confirm_del_{idx}"]; st.rerun() # LỆNH RERUN ĐỂ ĐÓNG KHUNG
