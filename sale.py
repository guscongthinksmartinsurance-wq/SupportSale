import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse
import re

# --- 1. KẾT NỐI & BẢO VỆ DỮ LIỆU ĐA TẦNG ---
st.set_page_config(page_title="TMC CRM PRO V41", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    try:
        df = conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0)
        if df is not None and not df.empty:
            df = df.fillna("").astype(str)
            for col in df.columns:
                df[col] = df[col].apply(lambda x: x[:-2] if x.endswith('.0') else x)
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def save_data(df, worksheet):
    # LỚP BẢO VỆ: Không cho lưu nếu dữ liệu bị rỗng đột ngột
    if df is None or df.empty:
        st.toast("🚨 Hệ thống ngăn chặn ghi đè dữ liệu rỗng!", icon="🛑")
        return False
    try:
        conn.update(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, data=df.fillna(""))
        st.cache_data.clear()
        return True
    except:
        return False

# --- 2. HÀM HỖ TRỢ ---
def clean_phone(val):
    return re.sub(r'\D', '', str(val))

def clean_html_for_edit(raw_html):
    t = str(raw_html).replace('</div>', '\n').replace('<br>', '\n')
    return re.sub(r'<[^>]*>', '', t).strip()

# --- 3. CSS GIAO DIỆN ---
st.markdown("""
    <style>
    .history-container {
        background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px;
        padding: 12px; height: 160px; overflow-y: auto; font-size: 13px; color: #495057;
    }
    .history-entry { border-bottom: 1px solid #dee2e6; margin-bottom: 8px; padding-bottom: 4px; }
    .contact-link { text-decoration: none; color: #28a745; font-weight: bold; font-size: 18px; }
    .id-badge {
        background-color: #fce4ec; color: #d81b60; padding: 2px 8px;
        border-radius: 12px; font-weight: bold; font-size: 13px; text-decoration: none;
        border: 1px solid #f8bbd0; margin-left: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR (KHÔI PHỤC ĐẦY ĐỦ) ---
with st.sidebar:
    st.title("⚒️ CRM Tools")
    df_l = load_data("links")
    
    # 4.1 Quick Links
    with st.expander("🔗 Quick Links"):
        if not df_l.empty:
            ql = df_l[df_l['category'] == 'Quick Link']
            for idx, row in ql.iterrows():
                c1, c2 = st.columns([8, 2])
                c1.markdown(f"🚀 [{row['title']}]({row['url']})")
                if c2.button("🗑️", key=f"dql_{idx}"):
                    st.session_state[f"conf_ql_{idx}"] = True
                if st.session_state.get(f"conf_ql_{idx}"):
                    if st.button("Xóa", key=f"re_ql_{idx}", type="primary"):
                        save_data(df_l.drop(idx), "links"); del st.session_state[f"conf_ql_{idx}"]; st.rerun()
                    st.button("Hủy", key=f"can_ql_{idx}")

    # 4.2 Sales Kit (Video Youtube)
    with st.expander("📁 Sales Kit"):
        if not df_l.empty:
            sk = df_l[df_l['category'] == 'Sales Kit']
            for idx, row in sk.iterrows():
                st.markdown(f"📂 **{row['title']}**")
                if "youtu" in row['url'].lower(): st.video(row['url'])
                else: st.markdown(f"🔗 [Mở]({row['url']})")
                if st.button("🗑️ Xóa", key=f"dsk_{idx}"):
                    st.session_state[f"conf_sk_{idx}"] = True
                if st.session_state.get(f"conf_sk_{idx}"):
                    if st.button("Xác nhận", key=f"re_sk_{idx}", type="primary"):
                        save_data(df_l.drop(idx), "links"); del st.session_state[f"conf_sk_{idx}"]; st.rerun()
                    st.button("Hủy", key=f"can_sk_{idx}")
                st.divider()

    # 4.3 Form thêm Link
    with st.expander("➕ Thêm Link"):
        with st.form("f_l_add", clear_on_submit=True):
            cat=st.selectbox("Loại",["Quick Link","Sales Kit"]); tit=st.text_input("Tiêu đề"); url=st.text_input("URL")
            if st.form_submit_button("Lưu Link"):
                save_data(pd.concat([df_l, pd.DataFrame([{"category":cat,"title":tit,"url":url}])], ignore_index=True), "links"); st.rerun()

    st.divider()
    # 4.4 Form thêm Lead mới
    with st.expander("➕ Thêm Khách Hàng Mới"):
        with st.form("f_lead_add", clear_on_submit=True):
            fn=st.text_input("Họ tên"); fi=st.text_input("CRM ID"); fc=st.text_input("Cell"); fw=st.text_input("Work")
            fe=st.text_input("Email"); fl=st.text_input("Link CRM"); f_st=st.text_input("State"); f_ow=st.text_input("Owner")
            fs=st.selectbox("Status",["New","Contacted","Following","Closed"])
            if st.form_submit_button("Lưu Lead"):
                df_leads_all = load_data("leads")
                new_row = {"name":fn,"crm_id":fi,"cell":fc,"work":fw,"email":fe,"crm_link":fl,"status":fs,"state":f_st,"owner":f_ow,"note":"","last_interact":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                save_data(pd.concat([df_leads_all, pd.DataFrame([new_row])], ignore_index=True), "leads"); st.rerun()

# --- 5. PIPELINE & SLIDER ---
st.title("💼 Pipeline Processing")
df_main = load_data("leads")
c_sch, c_sld = st.columns([7, 3])
q = str(c_sch.text_input("🔍 Tìm Tên, ID, SĐT...", key="search_main")).lower().strip()
q_num = clean_phone(q)
days_limit = c_sld.slider("⏳ Không tương tác (ngày)", 0, 90, 90)

if not df_main.empty:
    # 5.1 Lọc theo ngày (Slider)
    now = datetime.now()
    def filter_date(row):
        try:
            if not row['last_interact']: return True
            dt = datetime.strptime(str(row['last_interact']), "%Y-%m-%d %H:%M:%S")
            return (now - dt).days <= days_limit
        except: return True
    
    filtered = df_main[df_main.apply(filter_date, axis=1)]
    
    # 5.2 Lọc theo từ khóa
    filtered = filtered[filtered.apply(lambda r: q in str(r.get('name','')).lower() or q in str(r.get('crm_id','')).lower() or (q_num != "" and q_num in clean_phone(r.get('cell',''))), axis=1)]

    for idx, row in filtered.iterrows():
        u_key = f"{idx}_{row.get('crm_id', 'id')}"
        with st.container(border=True):
            ci, cn, ce = st.columns([4, 5.5, 0.5])
            with ci:
                st.markdown(f"<div><h4 style='margin:0;'>{row['name']}</h4><a href='{row['crm_link']}' target='_blank' class='id-badge'>🆔 {row['crm_id']}</a></div>", unsafe_allow_html=True)
                cell = row['cell']; n_e = urllib.parse.quote(str(row['name']))
                st.markdown(f"<div style='display:flex; gap:15px; margin-top:10px;'>📱 <a href='tel:{cell}' class='contact-link'>{cell}</a> <a href='rcmobile://sms?number={cell}'>💬</a> <a href='mailto:{row['email']}'>📧</a> <a href='https://calendar.google.com/calendar/r/eventedit?text=Meeting_{n_e}' target='_blank'>📅</a></div>", unsafe_allow_html=True)
                st.caption(f"🏷️ {row['status']} | 📍 {row.get('state','-')} | 👤 {row.get('owner','-')}")
            
            with cn:
                note_h = str(row.get('note', ''))
                st.markdown(f'<div class="history-container">{note_h}</div>', unsafe_allow_html=True)
                col_n1, col_n2 = st.columns([8.5, 1.5])
                with col_n1:
                    with st.form(key=f"fn_f_{u_key}", clear_on_submit=True):
                        ni = st.text_input("Ghi nhanh...", label_visibility="collapsed")
                        if st.form_submit_button("Lưu"):
                            if ni.strip():
                                fresh = load_data("leads")
                                if not fresh.empty:
                                    entry = f"<div class='history-entry'><b>{datetime.now().strftime('[%m/%d %H:%M]')}</b> {ni}</div>"
                                    fresh.at[idx, 'note'] = entry + str(fresh.at[idx, 'note'])
                                    fresh.at[idx, 'last_interact'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    save_data(fresh, "leads"); st.rerun()
                with col_n2:
                    with st.popover("📝"):
                        en = st.text_area("Sửa Note", value=clean_html_for_edit(note_h), height=200, key=f"ed_a_{u_key}")
                        if st.button("Cập nhật", key=f"ed_b_{u_key}"):
                            fresh = load_data("leads")
                            if not fresh.empty:
                                fmt = "".join([f"<div class='history-entry'>{line}</div>" for line in en.split('\n') if line.strip()])
                                fresh.at[idx, 'note'] = fmt
                                save_data(fresh, "leads"); st.rerun()

            with ce:
                with st.popover("⚙️"):
                    with st.form(f"ed_lead_{u_key}"):
                        un=st.text_input("Tên",value=row['name']); ui=st.text_input("ID",value=row['crm_id'])
                        uc=st.text_input("Cell",value=row['cell']); uem=st.text_input("Email",value=row['email'])
                        ust=st.text_input("State",value=row.get('state','')); uow=st.text_input("Owner",value=row.get('owner',''))
                        if st.form_submit_button("Lưu thay đổi"):
                            f=load_data("leads")
                            if not f.empty:
                                f.loc[idx,['name','crm_id','cell','email','state','owner']]=[un,ui,uc,uem,ust,uow]
                                save_data(f,"leads"); st.rerun()
                    if st.button("🗑️ Lead", key=f"del_{u_key}", type="primary"):
                        st.session_state[f"conf_del_{u_key}"] = True
                    if st.session_state.get(f"conf_del_{u_key}"):
                        if st.button("Vâng, Xóa", key=f"re_ok_{u_key}"):
                            f=load_data("leads"); save_data(f.drop(idx), "leads"); del st.session_state[f"conf_del_{u_key}"]; st.rerun()
                        st.button("Hủy", key=f"re_no_{u_key}")
