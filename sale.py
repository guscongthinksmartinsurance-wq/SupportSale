import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse
import re
import time

# --- 1. KẾT NỐI & BẢO MẬT DỮ LIỆU CẤP ĐỘ DOANH NGHIỆP ---
st.set_page_config(page_title="TMC CRM PRO V44", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(worksheet):
    """Hàm tải dữ liệu an toàn, chống trả về bảng rỗng"""
    try:
        df = conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0)
        if df is not None and len(df) > 0:
            df = df.fillna("").astype(str)
            for col in df.columns:
                df[col] = df[col].apply(lambda x: x[:-2] if x.endswith('.0') else x)
            return df
        return None # Trả về None nếu load lỗi để hệ thống biết mà giữ lại data cũ
    except:
        return None

def push_data(df, worksheet):
    """Hàm lưu dữ liệu với chốt chặn an toàn tuyệt đối"""
    if df is None or len(df) == 0:
        st.error("🚨 CHẶN GHI ĐÈ: Dữ liệu định lưu bị trống!")
        return False
    
    # Kiểm tra chéo: Chỉ lưu nếu dữ liệu trên Cloud không bị mất kết nối
    check_df = get_data(worksheet)
    if check_df is None:
        st.error("🚨 Cloud đang bận hoặc mất kết nối. Đã hủy lưu để bảo vệ dữ liệu cũ!")
        return False
        
    try:
        conn.update(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, data=df.fillna(""))
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Lỗi đường truyền: {e}")
        return False

# --- 2. QUẢN LÝ TRẠNG THÁI (SESSION STATE) ---
if 'leads' not in st.session_state:
    st.session_state.leads = get_data("leads")
if 'links' not in st.session_state:
    st.session_state.links = get_data("links")

# Cập nhật dữ liệu ngầm để đảm bảo mượt mà
tmp_leads = get_data("leads")
if tmp_leads is not None: st.session_state.leads = tmp_leads

tmp_links = get_data("links")
if tmp_links is not None: st.session_state.links = tmp_links

# --- 3. HÀM HỖ TRỢ & CSS ---
def clean_phone(val): return re.sub(r'\D', '', str(val))
def clean_html(raw): return re.sub(r'<[^>]*>', '', str(raw).replace('</div>', '\n')).strip()

st.markdown("""
    <style>
    .history-container { background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 12px; height: 160px; overflow-y: auto; font-size: 13px; }
    .history-entry { border-bottom: 1px solid #dee2e6; margin-bottom: 8px; padding-bottom: 4px; }
    .contact-link { text-decoration: none; color: #28a745; font-weight: bold; font-size: 18px; }
    .id-badge { background-color: #fce4ec; color: #d81b60; padding: 2px 8px; border-radius: 12px; font-weight: bold; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR (LINKS) ---
with st.sidebar:
    st.title("⚒️ CRM Tools")
    if st.session_state.links is not None:
        df_l = st.session_state.links
        with st.expander("🔗 Quick Links"):
            for idx, row in df_l[df_l['category'] == 'Quick Link'].iterrows():
                c1, c2 = st.columns([8, 2])
                c1.markdown(f"🚀 [{row['title']}]({row['url']})")
                if c2.button("🗑️", key=f"dl_{idx}"):
                    if push_data(df_l.drop(idx), "links"): st.rerun()

        with st.expander("📁 Sales Kit"):
            for idx, row in df_l[df_l['category'] == 'Sales Kit'].iterrows():
                st.markdown(f"📂 **{row['title']}**")
                if "youtu" in row['url'].lower(): st.video(row['url'])
                else: st.markdown(f"🔗 [Mở]({row['url']})")
                if st.button("🗑️ Xóa", key=f"ds_{idx}"):
                    if push_data(df_l.drop(idx), "links"): st.rerun()

    with st.expander("➕ Thêm Link/Lead"):
        with st.form("add_l", clear_on_submit=True):
            cat=st.selectbox("Loại",["Quick Link","Sales Kit"]); tit=st.text_input("Tiêu đề"); url=st.text_input("URL")
            if st.form_submit_button("Lưu Link"):
                new_l = pd.concat([st.session_state.links, pd.DataFrame([{"category":cat,"title":tit,"url":url}])], ignore_index=True)
                if push_data(new_l, "links"): st.rerun()

# --- 5. PIPELINE & SEARCH ---
st.title("💼 Pipeline Processing")
if st.session_state.leads is not None:
    leads_df = st.session_state.leads
    c_sch, c_sld = st.columns([7, 3])
    q = str(c_sch.text_input("🔍 Tìm Tên, ID, SĐT...", key="main_search")).lower().strip()
    q_num = clean_phone(q)
    days_limit = c_sld.slider("⏳ Không tương tác", 0, 90, 90)

    # Lọc Logic
    now = datetime.now()
    filtered = leads_df.copy()
    filtered = filtered[filtered.apply(lambda r: q in str(r.get('name','')).lower() or q in str(r.get('crm_id','')).lower() or (q_num != "" and q_num in clean_phone(r.get('cell',''))), axis=1)]

    for idx, row in filtered.iterrows():
        u_id = f"{idx}_{row.get('crm_id', 'id')}"
        with st.container(border=True):
            ci, cn, ce = st.columns([4, 5.5, 0.5])
            with ci:
                st.markdown(f"<div><h4 style='margin:0;'>{row['name']}</h4><span class='id-badge'>🆔 {row['crm_id']}</span></div>", unsafe_allow_html=True)
                cell = row['cell']; n_e = urllib.parse.quote(str(row['name']))
                st.markdown(f"📱 <a href='tel:{cell}' class='contact-link'>{cell}</a> | <a href='mailto:{row['email']}'>📧</a> | <a href='https://calendar.google.com/calendar/r/eventedit?text=Meeting_{n_e}' target='_blank'>📅</a>", unsafe_allow_html=True)
                st.caption(f"🏷️ {row['status']} | 👤 {row.get('owner','-')}")
            
            with cn:
                note_h = str(row.get('note', ''))
                st.markdown(f'<div class="history-container">{note_h}</div>', unsafe_allow_html=True)
                with st.form(key=f"f_n_{u_id}", clear_on_submit=True):
                    ni = st.text_input("Ghi nhanh...", label_visibility="collapsed")
                    if st.form_submit_button("Lưu Note"):
                        if ni.strip():
                            # Atomic Update: Load - Check - Add - Save
                            fresh_leads = get_data("leads")
                            if fresh_leads is not None:
                                entry = f"<div class='history-entry'><b>{datetime.now().strftime('[%m/%d %H:%M]')}</b> {ni}</div>"
                                fresh_leads.at[idx, 'note'] = entry + str(fresh_leads.at[idx, 'note'])
                                fresh_leads.at[idx, 'last_interact'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                if push_data(fresh_leads, "leads"): st.rerun()
            with ce:
                with st.popover("⚙️"):
                    if st.button("🗑️ Xóa Lead", key=f"del_{u_id}", type="primary"):
                        fresh = get_data("leads")
                        if fresh is not None and push_data(fresh.drop(idx), "leads"): st.rerun()
else:
    st.warning("⚠️ Đang kết nối dữ liệu an toàn. Nếu chờ lâu, anh hãy nhấn F5.")
