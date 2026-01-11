import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse
import re

# --- 1. KẾT NỐI & BẢO VỆ DỮ LIỆU ---
st.set_page_config(page_title="TMC CRM PRO V37", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    try:
        df = conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0)
        if df is not None and not df.empty:
            df = df.fillna("").astype(str)
            # Dọn dẹp .0 cho ID và Phone
            for col in df.columns:
                df[col] = df[col].apply(lambda x: x[:-2] if x.endswith('.0') else x)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.sidebar.error(f"Lỗi tải {worksheet}: {e}")
        return pd.DataFrame()

def save_data(df, worksheet):
    # LỚP BẢO VỆ CỨNG: Nếu DataFrame định lưu không có dòng nào, báo lỗi và dừng ngay
    if df is None or len(df) == 0:
        st.toast("🚨 CẢNH BÁO: Dữ liệu trống, đã chặn lệnh lưu để bảo vệ database!", icon="🛑")
        return False
    
    try:
        conn.update(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, data=df.fillna(""))
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Lỗi ghi dữ liệu: {e}")
        return False

# --- 2. XỬ LÝ TEXT ---
def clean_phone_search(val):
    return re.sub(r'\D', '', str(val))

def clean_html_for_edit(raw_html):
    t = str(raw_html).replace('</div>', '\n').replace('<br>', '\n')
    return re.sub(r'<[^>]*>', '', t).strip()

# --- 3. CSS ---
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
                if c2.button("🗑️", key=f"del_ql_{idx}"): st.session_state[f"conf_ql_{idx}"] = True
                if st.session_state.get(f"conf_ql_{idx}"):
                    ok, no = st.columns(2)
                    if ok.button("Xóa", key=f"re_ql_{idx}", type="primary"):
                        if save_data(df_links.drop(idx), "links"):
                            del st.session_state[f"conf_ql_{idx}"]; st.rerun()
                    if no.button("Hủy", key=f"can_ql_{idx}"):
                        del st.session_state[f"conf_ql_{idx}"]; st.rerun()

    with st.expander("📁 Sales Kit"):
        if not df_links.empty:
            sk = df_links[df_links['category'] == 'Sales Kit']
            for idx, row in sk.iterrows():
                st.markdown(f"📂 **{row['title']}**")
                if "youtube.com" in row['url'].lower() or "youtu.be" in row['url'].lower(): st.video(row['url'])
                else: st.markdown(f"🔗 [Mở tài liệu]({row['url']})")
                if st.button("🗑️ Xóa", key=f"del_sk_{idx}"): st.session_state[f"conf_sk_{idx}"] = True
                if st.session_state.get(f"conf_sk_{idx}"):
                    ok, no = st.columns(2)
                    if ok.button("Xóa", key=f"re_sk_{idx}", type="primary"):
                        if save_data(df_links.drop(idx), "links"):
                            del st.session_state[f"conf_sk_{idx}"]; st.rerun()
                    if no.button("Hủy", key=f"can_sk_{idx}"):
                        del st.session_state[f"conf_sk_{idx}"]; st.rerun()
                st.divider()

    with st.expander("➕ Thêm Link"):
        with st.form("f_link", clear_on_submit=True):
            cat_l=st.selectbox("Loại",["Quick Link","Sales Kit"]); tit_l=st.text_input("Tiêu đề"); url_l=st.text_input("URL")
            if st.form_submit_button("Lưu"):
                if tit_l and url_l:
                    new_l = pd.concat([df_links, pd.DataFrame([{"category":cat_l,"title":tit_l,"url":url_l}])], ignore_index=True)
                    save_data(new_l, "links"); st.rerun()

    st.divider()
    with st.expander("➕ Thêm Khách Hàng"):
        with st.form("f_lead", clear_on_submit=True):
            fn=st.text_input("Họ tên"); fi=st.text_input("CRM ID"); fc=st.text_input("Cell"); fw=st.text_input("Work")
            fe=st.text_input("Email"); fl=st.text_input("Link CRM"); fst=st.text_input("State"); fow=st.text_input("Owner")
            fs=st.selectbox("Status",["New","Contacted","Following","Closed"])
            if st.form_submit_button("Lưu Lead"):
                df_leads_all = load_data("leads")
                new_lead = pd.DataFrame([{"name":fn,"crm_id":fi,"cell":fc,"work":fw,"email":fe,"crm_link":fl,"status":fs,"state":fst,"owner":fow,"note":"","last_interact":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])
                save_data(pd.concat([df_leads_all, new_lead], ignore_index=True), "leads"); st.rerun()

# --- 5. PIPELINE ---
st.title("💼 Pipeline Processing")
leads_df = load_data("leads")
c_sch, c_sld = st.columns([7, 3])
q = str(c_sch.text_input("🔍 Tìm Tên, ID, SĐT...", key="search_main")).lower().strip()
q_num = clean_phone_search(q)
days_limit = c_sld.slider("⏳ Không tương tác (ngày)", 0, 90, 90)

if not leads_df.empty:
    # Lọc tìm kiếm
    filtered = leads_df[leads_df.apply(lambda r: q in str(r.get('name','')).lower() or q in str(r.get('crm_id','')).lower() or (q_num != "" and q_num in clean_phone_search(r.get('cell',''))), axis=1)]

    for idx, row in filtered.iterrows():
        with st.container(border=True):
            ci, cn, ce = st.columns([4, 5.5, 0.5])
            with ci:
                st.markdown(f"<div><h4 style='margin:0;'>{row['name']}</h4><a href='{row['crm_link']}' target='_blank' class='id-badge'>🆔 {row['crm_id']}</a></div>", unsafe_allow_html=True)
                st.markdown(f"<span style='color:grey; font-size:12px;'>📍 State: {row.get('state','-')} | 👤 Owner: {row.get('owner','-')}</span>", unsafe_allow_html=True)
                cell = row['cell']; n_e = urllib.parse.quote(str(row['name']))
                st.markdown(f"<div style='display:flex; gap:15px; margin-top:10px;'>📱 <a href='tel:{cell}' class='contact-link'>{cell}</a><a href='rcmobile://sms?number={cell}'>💬</a><a href='mailto:{row['email']}'>📧</a><a href='https://calendar.google.com/calendar/r/eventedit?text=Meeting_{n_e}' target='_blank'>📅</a></div>", unsafe_allow_html=True)
                st.caption(f"🏷️ Status: {row['status']}")
            
            with cn:
                note_h = str(row.get('note', ''))
                st.markdown(f'<div class="history-container">{note_h}</div>', unsafe_allow_html=True)
                col_n1, col_n2 = st.columns([8.5, 1.5])
                with col_n1:
                    with st.form(key=f"form_n_{idx}", clear_on_submit=True):
                        ni = st.text_input("Ghi nhanh...", label_visibility="collapsed")
                        if st.form_submit_button("Lưu"):
                            if ni.strip():
                                # Load lại dữ liệu tại thời điểm lưu để đảm bảo không mất dòng nào
                                fresh_df = load_data("leads")
                                if not fresh_df.empty:
                                    now = datetime.now().strftime("[%m/%d %H:%M]")
                                    entry = f"<div class='history-entry'><span style='color:#007bff;font-weight:bold;'>{now}</span> {ni}</div>"
                                    fresh_df.at[idx, 'note'] = entry + str(fresh_df.at[idx, 'note'])
                                    fresh_df.at[idx, 'last_interact'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    save_data(fresh_df, "leads"); st.rerun()
                with col_n2:
                    with st.popover("📝"):
                        en = st.text_area("Sửa Note", value=clean_html_for_edit(note_h), height=200)
                        if st.button("Cập nhật", key=f"up_{idx}"):
                            fmt = "".join([f"<div class='history-entry'>{line}</div>" for line in en.split('\n') if line.strip()])
                            fresh_df = load_data("leads")
                            if not fresh_df.empty:
                                fresh_df.at[idx, 'note'] = fmt
                                save_data(fresh_df, "leads"); st.rerun()

            with ce:
                with st.popover("⚙️"):
                    with st.form(f"ed_{idx}"):
                        un=st.text_input("Tên",value=row['name']); ui=st.text_input("ID",value=row['crm_id'])
                        uc=st.text_input("Cell",value=row['cell']); uw=st.text_input("Work",value=row['work'])
                        ust=st.text_input("State",value=row.get('state','')); uow=st.text_input("Owner",value=row.get('owner',''))
                        uem=st.text_input("Email",value=row['email']); ul=st.text_input("Link CRM",value=row['crm_link'])
                        us=st.selectbox("Status",["New","Contacted","Following","Closed"], index=["New","Contacted","Following","Closed"].index(row['status']) if row['status'] in ["New","Contacted","Following","Closed"] else 0)
                        if st.form_submit_button("Cập nhật Lead"):
                            f=load_data("leads")
                            if not f.empty:
                                f.loc[idx,['name','crm_id','cell','work','email','crm_link','state','owner','status']]=[un,ui,uc,uw,uem,ul,ust,uow,us]
                                save_data(f,"leads"); st.rerun()
                    if st.button("🗑️ Xóa", key=f"d_{idx}"): st.session_state[f"c_del_{idx}"] = True
                    if st.session_state.get(f"c_del_{idx}"):
                        ok, no = st.columns(2)
                        if ok.button("Vâng", key=f"ok_d_{idx}"):
                            f=load_data("leads")
                            if save_data(f.drop(idx), "leads"):
                                del st.session_state[f"c_del_{idx}"]; st.rerun()
                        if no.button("Hủy", key=f"no_d_{idx}"):
                            del st.session_state[f"c_del_{idx}"]; st.rerun()
