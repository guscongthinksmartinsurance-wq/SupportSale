import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse
import re

# --- 1. KẾT NỐI & BẢO VỆ DỮ LIỆU ĐA TẦNG ---
st.set_page_config(page_title="TMC CRM PRO V40", layout="wide")
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
    # CHỐT CHẶN 1: Tuyệt đối không lưu nếu DataFrame rỗng
    if df is None or df.empty:
        st.toast("🚨 Hệ thống chặn lưu dữ liệu rỗng!", icon="🛑")
        return False
    
    # CHỐT CHẶN 2: Kiểm tra chéo với thực tế trên Sheets trước khi ghi đè
    try:
        actual_df = conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0)
        if actual_df is not None and len(actual_df) > 0 and len(df) == 0:
            st.error("🚨 CẢNH BÁO: Phát hiện nguy cơ mất dữ liệu. Đã ngắt kết nối lưu!")
            return False
    except:
        pass

    try:
        conn.update(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, data=df.fillna(""))
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Lỗi ghi đè: {e}")
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

# --- 4. SIDEBAR (LINKS) ---
with st.sidebar:
    st.title("⚒️ CRM Tools")
    df_l = load_data("links")
    
    with st.expander("🔗 Quick Links"):
        if not df_l.empty:
            for idx, row in df_l[df_l['category'] == 'Quick Link'].iterrows():
                c1, c2 = st.columns([8, 2])
                c1.markdown(f"🚀 [{row['title']}]({row['url']})")
                if c2.button("🗑️", key=f"dql_{idx}"):
                    if save_data(df_l.drop(idx), "links"): st.rerun()

    with st.expander("📁 Sales Kit"):
        if not df_l.empty:
            for idx, row in df_l[df_l['category'] == 'Sales Kit'].iterrows():
                st.markdown(f"📂 **{row['title']}**")
                if "youtu" in row['url'].lower(): st.video(row['url'])
                else: st.markdown(f"🔗 [Mở]({row['url']})")
                if st.button("🗑️ Xóa", key=f"dsk_{idx}"):
                    if save_data(df_l.drop(idx), "links"): st.rerun()

    with st.expander("➕ Thêm Link"):
        with st.form("f_l", clear_on_submit=True):
            cat=st.selectbox("Loại",["Quick Link","Sales Kit"]); tit=st.text_input("Tiêu đề"); url=st.text_input("URL")
            if st.form_submit_button("Lưu"):
                save_data(pd.concat([df_l, pd.DataFrame([{"category":cat,"title":tit,"url":url}])], ignore_index=True), "links"); st.rerun()

# --- 5. PIPELINE (LEADS) ---
st.title("💼 Pipeline Processing")
df_main = load_data("leads")

q = str(st.text_input("🔍 Tìm Tên, ID, SĐT...", key="search_main")).lower().strip()
q_num = clean_phone(q)

if not df_main.empty:
    filtered = df_main[df_main.apply(lambda r: q in str(r.get('name','')).lower() or q in str(r.get('crm_id','')).lower() or (q_num != "" and q_num in clean_phone(r.get('cell',''))), axis=1)]

    for idx, row in filtered.iterrows():
        # Định danh an toàn cho từng khách
        u_key = f"{idx}_{row.get('crm_id', 'id')}"
        
        with st.container(border=True):
            ci, cn, ce = st.columns([4, 5.5, 0.5])
            with ci:
                st.markdown(f"<div><h4 style='margin:0;'>{row['name']}</h4><a href='{row['crm_link']}' target='_blank' class='id-badge'>🆔 {row['crm_id']}</a></div>", unsafe_allow_html=True)
                cell = row['cell']; n_e = urllib.parse.quote(str(row['name']))
                st.markdown(f"<div style='display:flex; gap:15px; margin-top:10px;'>📱 <a href='tel:{cell}' class='contact-link'>{cell}</a> <a href='rcmobile://sms?number={cell}'>💬</a> <a href='mailto:{row['email']}'>📧</a> <a href='https://calendar.google.com/calendar/r/eventedit?text=Meeting_{n_e}' target='_blank'>📅</a></div>", unsafe_allow_html=True)
                st.caption(f"🏷️ {row['status']} | 📍 {row.get('state','-')}")
            
            with cn:
                note_h = str(row.get('note', ''))
                st.markdown(f'<div class="history-container">{note_h}</div>', unsafe_allow_html=True)
                
                col_n1, col_n2 = st.columns([8.5, 1.5])
                with col_n1:
                    with st.form(key=f"fn_f_{u_key}", clear_on_submit=True):
                        ni = st.text_input("Note nhanh...", key=f"ni_i_{u_key}", label_visibility="collapsed")
                        if st.form_submit_button("Lưu"):
                            if ni.strip():
                                # Load lại tại chỗ để đảm bảo dữ liệu mới nhất trước khi chèn
                                fresh_leads = load_data("leads")
                                if not fresh_leads.empty:
                                    now = datetime.now().strftime("[%m/%d %H:%M]")
                                    entry = f"<div class='history-entry'><b>{now}</b> {ni}</div>"
                                    fresh_leads.at[idx, 'note'] = entry + str(fresh_leads.at[idx, 'note'])
                                    if save_data(fresh_leads, "leads"): st.rerun()
                with col_n2:
                    with st.popover("📝"):
                        en = st.text_area("Sửa Note", value=clean_html_for_edit(note_h), height=200, key=f"ed_a_{u_key}")
                        if st.button("Cập nhật", key=f"ed_b_{u_key}"):
                            fresh_leads = load_data("leads")
                            if not fresh_leads.empty:
                                fmt = "".join([f"<div class='history-entry'>{line}</div>" for line in en.split('\n') if line.strip()])
                                fresh_leads.at[idx, 'note'] = fmt
                                if save_data(fresh_leads, "leads"): st.rerun()

            with ce:
                with st.popover("⚙️"):
                    if st.button("🗑️ Xóa Lead", key=f"del_{u_key}", type="primary"):
                        f = load_data("leads")
                        if save_data(f.drop(idx), "leads"): st.rerun()
