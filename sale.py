import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse
import re

# --- 1. KẾT NỐI DATABASE ---
st.set_page_config(page_title="TMC CRM PRO V32.9", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    try:
        df = conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0)
        if df is not None:
            return df.fillna("").astype(str)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def save_data(df, worksheet):
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
    .contact-link { text-decoration: none; color: #28a745; font-weight: bold; }
    .id-badge {
        background-color: #fce4ec; color: #d81b60; padding: 2px 8px;
        border-radius: 12px; font-weight: bold; font-size: 13px; text-decoration: none;
        border: 1px solid #f8bbd0; margin-left: 10px;
    }
    .link-display { font-size: 11px; color: #6c757d; display: block; margin-top: -5px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. HÀM XỬ LÝ ---
def format_phone(val):
    s = str(val).strip()
    return s[:-2] if s.endswith('.0') else s

def clean_html_for_edit(raw_html):
    t = str(raw_html).replace('</div>', '\n')
    return re.sub(r'<[^>]*>', '', t).strip()

def save_note_v32(idx, current_note, note_key):
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
            st.session_state[note_key] = ""; st.rerun()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("⚒️ CRM Tools")
    df_links = load_data("links")
    
    # HIỂN THỊ LINK VỚI URL YOUTUBE & NÚT XÓA CÓ XÁC NHẬN
    def show_link_category(cat, label, key_prefix):
        with st.expander(label):
            if not df_links.empty:
                items = df_links[df_links['category'] == cat]
                for l_idx, l_row in items.iterrows():
                    c_link, c_del = st.columns([8, 2])
                    with c_link:
                        st.markdown(f"🚀 [{l_row['title']}]({l_row['url']})")
                        st.markdown(f"<span class='link-display'>{l_row['url']}</span>", unsafe_allow_html=True)
                    with c_del:
                        if st.button("🗑️", key=f"del_l_{key_prefix}_{l_idx}"):
                            st.session_state[f"confirm_del_l_{l_idx}"] = True
                    
                    if st.session_state.get(f"confirm_del_l_{l_idx}"):
                        st.warning(f"Xóa link này?")
                        if st.button("Xác nhận xóa", key=f"re_del_l_{l_idx}"):
                            new_df = df_links.drop(l_idx)
                            save_data(new_df, "links")
                            del st.session_state[f"confirm_del_l_{l_idx}"]
                            st.rerun()
                        if st.button("Hủy", key=f"can_del_l_{l_idx}"):
                            del st.session_state[f"confirm_del_l_{l_idx}"]
                            st.rerun()

    show_link_category("Quick Link", "🔗 Danh sách Quick Links", "ql")
    show_link_category("Sales Kit", "📁 Danh sách Sales Kit", "sk")

    with st.expander("➕ Thêm Link / Sales Kit"):
        with st.form("f_link"):
            c=st.selectbox("Loại",["Quick Link","Sales Kit"]); t=st.text_input("Tiêu đề"); u=st.text_input("URL")
            if st.form_submit_button("Lưu"):
                save_data(pd.concat([df_links, pd.DataFrame([{"category":c,"title":t,"url":u}])], ignore_index=True), "links"); st.rerun()

    st.divider()
    with st.expander("➕ Thêm Khách Hàng Mới"):
        with st.form("f_lead"):
            fn=st.text_input("Họ tên"); fi=st.text_input("CRM ID"); fc=st.text_input("Cell"); fw=st.text_input("Work")
            fe=st.text_input("Email"); fl=st.text_input("Link CRM"); fs=st.selectbox("Status",["New","Contacted","Following","Closed"])
            if st.form_submit_button("Lưu"):
                df_all = load_data("leads")
                save_data(pd.concat([df_all, pd.DataFrame([{"name":fn,"crm_id":fi,"cell":fc,"work":fw,"email":fe,"crm_link":fl,"status":fs,"note":""}])], ignore_index=True), "leads"); st.rerun()

# --- 5. PIPELINE ---
st.title("💼 Pipeline Processing")
leads_df = load_data("leads")
c1, c2 = st.columns([7, 3])
search_val = c1.text_input("🔍 Tìm theo Tên, ID, SĐT...", key="search_main")
q = str(search_val).lower().strip()
days_f = c2.slider("⏳ Không tương tác", 0, 90, 90)

if not leads_df.empty:
    filtered = leads_df[leads_df.apply(lambda r: q in r.get('name','').lower() or q in r.get('crm_id','').lower() or q in r.get('cell','').lower() or q in r.get('work','').lower(), axis=1)]

    for idx, row in filtered.iterrows():
        note_h = str(row.get('note', ''))
        cell = format_phone(row.get('cell', ''))
        work = format_phone(row.get('work', ''))
        
        with st.container(border=True):
            ci, cn, ce = st.columns([4.5, 5, 0.5])
            with ci:
                st.markdown(f"<div style='display:flex;align-items:center;'><h4 style='margin:0;'>{row.get('name','N/A')}</h4><a href='{row.get('crm_link','#')}' target='_blank' class='id-badge'>🆔 {row.get('crm_id','-')}</a></div>", unsafe_allow_html=True)
                n_e = urllib.parse.quote(str(row.get('name','')))
                st.markdown(f"<div style='margin-top:8px;display:flex;align-items:center;gap:10px;'>📱 Cell: <a href='tel:{cell}' class='contact-link'>{cell}</a><a href='rcmobile://sms?number={cell}'>💬</a><a href='mailto:{row.get('email','')}'>📧</a><a href='https://calendar.google.com/calendar/r/eventedit?text=Meeting_{n_e}' target='_blank'>📅</a></div>", unsafe_allow_html=True)
                st.markdown(f"📞 Work: <a href='tel:{work}' class='contact-link'>{work}</a>", unsafe_allow_html=True)
                st.caption(f"🏷️ Status: {row.get('status','New')}")
            with cn:
                st.markdown(f'<div class="history-container">{note_h}</div>', unsafe_allow_html=True)
                cn1, cn2 = st.columns([8.5, 1.5])
                with cn1: st.text_input("Note nhanh...", key=f"n_{idx}", on_change=save_note_v32, args=(idx, note_h, f"n_{idx}"), label_visibility="collapsed")
                with cn2:
                    with st.popover("📝"):
                        cl_h = clean_html_for_edit(note_h)
                        new_h = st.text_area("Sửa lịch sử", value=cl_h, height=250)
                        if st.button("Lưu", key=f"sn_{idx}"):
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
                    
                    # NÚT XÓA KHÁCH HÀNG CÓ XÁC NHẬN
                    if st.button("🗑️ Xóa Lead", key=f"d_{idx}", type="primary"):
                        st.session_state[f"confirm_del_{idx}"] = True
                    
                    if st.session_state.get(f"confirm_del_{idx}"):
                        st.error("Bạn có chắc chắn muốn xóa khách hàng này?")
                        if st.button("Vâng, Xóa ngay", key=f"re_d_{idx}"):
                            f=load_data("leads"); save_data(f.drop(idx),"leads")
                            del st.session_state[f"confirm_del_{idx}"]; st.rerun()
                        if st.button("Hủy bỏ", key=f"can_d_{idx}"):
                            del st.session_state[f"confirm_del_{idx}"]; st.rerun()
