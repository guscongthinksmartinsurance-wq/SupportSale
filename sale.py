import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse
import re
import time

# --- 1. KẾT NỐI & CẤU HÌNH BẢO MẬT ---
st.set_page_config(page_title="TMC CRM PRO V37.5", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    try:
        # Tăng cường độ ổn định khi load
        df = conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0)
        if df is not None and not df.empty:
            df = df.fillna("").astype(str)
            for col in df.columns:
                df[col] = df[col].apply(lambda x: x[:-2] if x.endswith('.0') else x)
            return df
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def save_data(df, worksheet):
    # LỚP BẢO VỆ 1: Kiểm tra DataFrame có tồn tại không
    if df is None or df.empty:
        st.error("🚨 LỖI HỆ THỐNG: Dữ liệu tải lên bị trống. Đã chặn ghi đè để bảo vệ danh sách khách hàng!")
        return False
    
    # LỚP BẢO VỆ 2: Kiểm tra chéo với dữ liệu cũ (Nếu mất đột ngột hơn 50% số dòng là bất thường)
    try:
        old_df = conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0)
        if old_df is not None and len(old_df) > 0:
            if len(df) < len(old_df) * 0.5: # Ví dụ đang có 10 khách mà lưu chỉ còn 2 khách là lỗi
                st.error("🚨 CẢNH BÁO: Số lượng khách hàng sụt giảm bất thường. Lệnh lưu bị từ chối để tránh mất data!")
                return False
    except:
        pass # Nếu không đọc được bản cũ thì bỏ qua bước check chéo

    # LỚP BẢO VỆ 3: Thực hiện ghi dữ liệu
    try:
        conn.update(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, data=df.fillna(""))
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Lỗi đường truyền: {e}")
        return False

# --- 2. HÀM HỖ TRỢ ---
def clean_phone(val):
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

# --- 4. SIDEBAR (DỮ LIỆU LINK) ---
with st.sidebar:
    st.title("⚒️ CRM Tools")
    df_links = load_data("links")
    
    with st.expander("🔗 Quick Links"):
        if not df_links.empty:
            for idx, row in df_links[df_links['category'] == 'Quick Link'].iterrows():
                c1, c2 = st.columns([8, 2])
                c1.markdown(f"🚀 [{row['title']}]({row['url']})")
                if c2.button("🗑️", key=f"dql_{idx}"):
                    if save_data(df_links.drop(idx), "links"): st.rerun()

    with st.expander("📁 Sales Kit"):
        if not df_links.empty:
            for idx, row in df_links[df_links['category'] == 'Sales Kit'].iterrows():
                st.markdown(f"📂 **{row['title']}**")
                if "youtu" in row['url'].lower(): st.video(row['url'])
                else: st.markdown(f"🔗 [Mở]({row['url']})")
                if st.button("🗑️ Xóa", key=f"dsk_{idx}"):
                    if save_data(df_links.drop(idx), "links"): st.rerun()

    with st.expander("➕ Thêm Link"):
        with st.form("f_l", clear_on_submit=True):
            cat=st.selectbox("Loại",["Quick Link","Sales Kit"]); tit=st.text_input("Tiêu đề"); url=st.text_input("URL")
            if st.form_submit_button("Lưu"):
                save_data(pd.concat([df_links, pd.DataFrame([{"category":cat,"title":tit,"url":url}])], ignore_index=True), "links"); st.rerun()

# --- 5. PIPELINE (DỮ LIỆU KHÁCH HÀNG) ---
st.title("💼 Pipeline Processing")
leads_df = load_data("leads")

c_sch, c_sld = st.columns([7, 3])
q = str(c_sch.text_input("🔍 Tìm Tên, ID, SĐT...", key="search_main")).lower().strip()
q_num = clean_phone(q)

if not leads_df.empty:
    filtered = leads_df[leads_df.apply(lambda r: q in str(r.get('name','')).lower() or q in str(r.get('crm_id','')).lower() or (q_num != "" and q_num in clean_phone(r.get('cell',''))), axis=1)]

    for idx, row in filtered.iterrows():
        with st.container(border=True):
            ci, cn, ce = st.columns([4, 5.5, 0.5])
            with ci:
                st.markdown(f"<div><h4 style='margin:0;'>{row['name']}</h4><a href='{row['crm_link']}' target='_blank' class='id-badge'>🆔 {row['crm_id']}</a></div>", unsafe_allow_html=True)
                cell = row['cell']; n_e = urllib.parse.quote(str(row['name']))
                st.markdown(f"<div style='display:flex; gap:15px; margin-top:10px;'>📱 <a href='tel:{cell}' class='contact-link'>{cell}</a> <a href='rcmobile://sms?number={cell}'>💬</a> <a href='mailto:{row['email']}'>📧</a> <a href='https://calendar.google.com/calendar/r/eventedit?text=Meeting_{n_e}' target='_blank'>📅</a></div>", unsafe_allow_html=True)
                st.caption(f"🏷️ Status: {row['status']} | 📍 State: {row.get('state','-')}")
            
            with cn:
                note_h = str(row.get('note', ''))
                st.markdown(f'<div class="history-container">{note_h}</div>', unsafe_allow_html=True)
                
                col_n1, col_n2 = st.columns([8.5, 1.5])
                with col_n1:
                    with st.form(key=f"fn_{idx}", clear_on_submit=True):
                        ni = st.text_input("Ghi nhanh...", label_visibility="collapsed")
                        if st.form_submit_button("Lưu Note"):
                            if ni.strip():
                                # QUY TRÌNH LƯU AN TOÀN TUYỆT ĐỐI
                                current_leads = load_data("leads")
                                if not current_leads.empty and idx in current_leads.index:
                                    now = datetime.now().strftime("[%m/%d %H:%M]")
                                    new_entry = f"<div class='history-entry'><span style='color:#007bff;font-weight:bold;'>{now}</span> {ni}</div>"
                                    current_leads.at[idx, 'note'] = new_entry + str(current_leads.at[idx, 'note'])
                                    current_leads.at[idx, 'last_interact'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    if save_data(current_leads, "leads"):
                                        st.rerun()
                with col_n2:
                    with st.popover("📝"):
                        en = st.text_area("Sửa nội dung", value=clean_html_for_edit(note_h), height=200)
                        if st.button("Cập nhật", key=f"up_{idx}"):
                            current_leads = load_data("leads")
                            if not current_leads.empty and idx in current_leads.index:
                                fmt = "".join([f"<div class='history-entry'>{line}</div>" for line in en.split('\n') if line.strip()])
                                current_leads.at[idx, 'note'] = fmt
                                if save_data(current_leads, "leads"): st.rerun()

            with ce:
                with st.popover("⚙️"):
                    with st.form(f"ed_{idx}"):
                        un=st.text_input("Tên",value=row['name']); ui=st.text_input("ID",value=row['crm_id'])
                        uc=st.text_input("Cell",value=row['cell']); uem=st.text_input("Email",value=row['email'])
                        us=st.selectbox("Status",["New","Contacted","Following","Closed"], index=0)
                        if st.form_submit_button("Sửa"):
                            f=load_data("leads")
                            if not f.empty:
                                f.loc[idx,['name','crm_id','cell','email','status']]=[un,ui,uc,uem,us]
                                save_data(f,"leads"); st.rerun()
                    if st.button("🗑️ Lead", key=f"d_{idx}"):
                        f=load_data("leads")
                        if save_data(f.drop(idx), "leads"): st.rerun()
