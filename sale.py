import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse
import re
import time

# --- 1. KẾT NỐI & BẢO VỆ DỮ LIỆU TỐI CAO ---
st.set_page_config(page_title="TMC CRM PRO V39", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    try:
        df = conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0)
        if df is not None and len(df) > 0:
            df = df.fillna("").astype(str)
            # Triệt tiêu đuôi .0 cho ID và Phone ngay từ đầu
            for col in df.columns:
                df[col] = df[col].apply(lambda x: x[:-2] if x.endswith('.0') else x)
            return df
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def save_data(df, worksheet):
    # CHỐT CHẶN CUỐI: Tuyệt đối không lưu nếu DataFrame rỗng hoặc mất quá nhiều dòng
    if df is None or df.empty:
        st.toast("🚨 Lỗi: Dữ liệu trống, đã chặn ghi đè!", icon="🛑")
        return False
    
    try:
        conn.update(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, data=df.fillna(""))
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Lỗi đường truyền Sheets: {e}")
        return False

# --- 2. HÀM HỖ TRỢ ---
def clean_phone_search(val):
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

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("⚒️ CRM Tools")
    links_all = load_data("links")
    
    with st.expander("🔗 Quick Links"):
        if not links_all.empty:
            ql = links_all[links_all['category'] == 'Quick Link']
            for idx, row in ql.iterrows():
                c1, c2 = st.columns([8, 2])
                c1.markdown(f"🚀 [{row['title']}]({row['url']})")
                if c2.button("🗑️", key=f"dql_{idx}"):
                    if save_data(links_all.drop(idx), "links"): st.rerun()

    with st.expander("📁 Sales Kit"):
        if not links_all.empty:
            sk = links_all[links_all['category'] == 'Sales Kit']
            for idx, row in sk.iterrows():
                st.markdown(f"📂 **{row['title']}**")
                if "youtu" in row['url'].lower(): st.video(row['url'])
                else: st.markdown(f"🔗 [Mở tài liệu]({row['url']})")
                if st.button("🗑️ Xóa", key=f"dsk_{idx}"):
                    if save_data(links_all.drop(idx), "links"): st.rerun()
                st.divider()

    with st.expander("➕ Thêm Link"):
        with st.form("f_l", clear_on_submit=True):
            cat=st.selectbox("Loại",["Quick Link","Sales Kit"]); tit=st.text_input("Tiêu đề"); url=st.text_input("URL")
            if st.form_submit_button("Lưu"):
                if tit and url:
                    new_l = pd.concat([links_all, pd.DataFrame([{"category":cat,"title":tit,"url":url}])], ignore_index=True)
                    save_data(new_l, "links"); st.rerun()

    st.divider()
    with st.expander("➕ Thêm Khách Hàng"):
        with st.form("f_lead", clear_on_submit=True):
            fn=st.text_input("Họ tên"); fi=st.text_input("CRM ID"); fc=st.text_input("Cell"); fw=st.text_input("Work")
            fe=st.text_input("Email"); fl=st.text_input("Link CRM"); fst=st.text_input("State"); fow=st.text_input("Owner")
            fs=st.selectbox("Status",["New","Contacted","Following","Closed"])
            if st.form_submit_button("Lưu Lead"):
                leads_all = load_data("leads")
                new_row = {"name":fn,"crm_id":fi,"cell":fc,"work":fw,"email":fe,"crm_link":fl,"status":fs,"state":fst,"owner":fow,"note":"","last_interact":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                save_data(pd.concat([leads_all, pd.DataFrame([new_row])], ignore_index=True), "leads"); st.rerun()

# --- 5. PIPELINE PROCESSING ---
st.title("💼 Pipeline Processing")
leads_main = load_data("leads")

c_sch, c_sld = st.columns([7, 3])
q = str(c_sch.text_input("🔍 Tìm Tên, ID, SĐT...", key="search_main")).lower().strip()
q_num = clean_phone_search(q)
days_limit = c_sld.slider("⏳ Không tương tác (ngày)", 0, 90, 90)

if not leads_main.empty:
    # Lọc tìm kiếm thông minh
    filtered = leads_main[leads_main.apply(lambda r: q in str(r.get('name','')).lower() or q in str(r.get('crm_id','')).lower() or (q_num != "" and q_num in clean_phone_search(r.get('cell',''))), axis=1)]

    for idx, row in filtered.iterrows():
        # Tạo Key duy nhất cho từng khách để tránh lỗi Duplicate ID
        u_key = f"{row.get('crm_id', idx)}"
        
        with st.container(border=True):
            ci, cn, ce = st.columns([4, 5.5, 0.5])
            with ci:
                st.markdown(f"<div><h4 style='margin:0;'>{row['name']}</h4><a href='{row['crm_link']}' target='_blank' class='id-badge'>🆔 {row['crm_id']}</a></div>", unsafe_allow_html=True)
                st.markdown(f"<span style='color:grey; font-size:12px;'>📍 {row.get('state','-')} | 👤 {row.get('owner','-')}</span>", unsafe_allow_html=True)
                cell = row['cell']; n_e = urllib.parse.quote(str(row['name']))
                st.markdown(f"<div style='display:flex; gap:15px; margin-top:10px;'>📱 <a href='tel:{cell}' class='contact-link'>{cell}</a> <a href='rcmobile://sms?number={cell}'>💬</a> <a href='mailto:{row['email']}'>📧</a> <a href='https://calendar.google.com/calendar/r/eventedit?text=Meeting_{n_e}' target='_blank'>📅</a></div>", unsafe_allow_html=True)
                st.caption(f"🏷️ {row['status']}")
            
            with cn:
                note_h = str(row.get('note', ''))
                st.markdown(f'<div class="history-container">{note_h}</div>', unsafe_allow_html=True)
                
                # FORM NHẬP NOTE NHANH VỚI KEY DUY NHẤT
                with st.form(key=f"fn_form_{u_key}", clear_on_submit=True):
                    ni = st.text_input("Ghi nhanh...", key=f"ni_input_{u_key}", label_visibility="collapsed")
                    if st.form_submit_button("Lưu Note"):
                        if ni.strip():
                            # Chống ghi đè bảng trống bằng cách load lại ngay lập tức
                            fresh_leads = load_data("leads")
                            if not fresh_leads.empty:
                                now = datetime.now().strftime("[%m/%d %H:%M]")
                                entry = f"<div class='history-entry'><span style='color:#007bff;font-weight:bold;'>{now}</span> {ni}</div>"
                                fresh_leads.at[idx, 'note'] = entry + str(fresh_leads.at[idx, 'note'])
                                fresh_leads.at[idx, 'last_interact'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                if save_data(fresh_leads, "leads"): st.rerun()
                
                with st.popover("📝 Chỉnh sửa"):
                    en = st.text_area("Nội dung Note", value=clean_html_for_edit(note_h), height=200, key=f"edit_area_{u_key}")
                    if st.button("Cập nhật lịch sử", key=f"up_btn_{u_key}"):
                        fresh_leads = load_data("leads")
                        if not fresh_leads.empty:
                            fmt = "".join([f"<div class='history-entry'>{line}</div>" for line in en.split('\n') if line.strip()])
                            fresh_leads.at[idx, 'note'] = fmt
                            if save_data(fresh_leads, "leads"): st.rerun()

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
                    if st.button("🗑️ Xóa Lead", key=f"del_lead_{u_key}", type="primary"):
                        st.session_state[f"conf_del_{u_key}"] = True
                    if st.session_state.get(f"conf_del_{u_key}"):
                        ok, no = st.columns(2)
                        if ok.button("Vâng", key=f"re_ok_{u_key}"):
                            f=load_data("leads")
                            if save_data(f.drop(idx), "leads"):
                                del st.session_state[f"conf_del_{u_key}"]; st.rerun()
                        if no.button("Hủy", key=f"re_no_{u_key}"):
                            del st.session_state[f"conf_del_{u_key}"]; st.rerun()
else:
    st.info("Hệ thống đang tải dữ liệu hoặc database đang trống. Nếu dữ liệu không hiện, anh hãy thử tải lại trang nhé.")
