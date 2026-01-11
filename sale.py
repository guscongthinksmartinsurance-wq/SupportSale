import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse
import re

# --- 1. KẾT NỐI & BẢO VỆ DỮ LIỆU ---
st.set_page_config(page_title="TMC CRM PRO V39.1", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    try:
        df = conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0)
        if df is not None and len(df) > 0:
            df = df.fillna("").astype(str)
            for col in df.columns:
                df[col] = df[col].apply(lambda x: x[:-2] if x.endswith('.0') else x)
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def save_data(df, worksheet, current_len=0):
    # LỚP BẢO VỆ: Nếu số dòng mới ít hơn 50% số dòng cũ -> Chặn lưu (tránh mất data)
    if df is None or df.empty or (current_len > 0 and len(df) < current_len * 0.5):
        st.toast("🛑 Hệ thống chặn lưu để bảo vệ dữ liệu!", icon="🚨")
        return False
    try:
        conn.update(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, data=df.fillna(""))
        st.cache_data.clear()
        return True
    except:
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
            for idx, row in links_all[links_all['category'] == 'Quick Link'].iterrows():
                c1, c2 = st.columns([8, 2])
                c1.markdown(f"🚀 [{row['title']}]({row['url']})")
                if c2.button("🗑️", key=f"dql_{idx}_{row['title'][:3]}"):
                    save_data(links_all.drop(idx), "links"); st.rerun()

    with st.expander("📁 Sales Kit"):
        if not links_all.empty:
            for idx, row in links_all[links_all['category'] == 'Sales Kit'].iterrows():
                st.markdown(f"📂 **{row['title']}**")
                if "youtu" in row['url'].lower(): st.video(row['url'])
                else: st.markdown(f"🔗 [Mở]({row['url']})")
                if st.button("🗑️ Xóa", key=f"dsk_{idx}_{row['title'][:3]}"):
                    save_data(links_all.drop(idx), "links"); st.rerun()
                st.divider()

    with st.expander("➕ Thêm Link"):
        with st.form("f_l", clear_on_submit=True):
            cat=st.selectbox("Loại",["Quick Link","Sales Kit"]); tit=st.text_input("Tiêu đề"); url=st.text_input("URL")
            if st.form_submit_button("Lưu"):
                save_data(pd.concat([links_all, pd.DataFrame([{"category":cat,"title":tit,"url":url}])], ignore_index=True), "links"); st.rerun()

# --- 5. PIPELINE PROCESSING ---
st.title("💼 Pipeline Processing")
leads_main = load_data("leads")

c_sch, c_sld = st.columns([7, 3])
q = str(c_sch.text_input("🔍 Tìm kiếm...", key="search_main")).lower().strip()
q_num = clean_phone_search(q)

if not leads_main.empty:
    filtered = leads_main[leads_main.apply(lambda r: q in str(r.get('name','')).lower() or q in str(r.get('crm_id','')).lower() or (q_num != "" and q_num in clean_phone_search(r.get('cell',''))), axis=1)]

    for idx, row in filtered.iterrows():
        # KHÓA ID DUY NHẤT: Kết hợp Index và ID để không bao giờ trùng
        safe_id = f"{idx}_{row.get('crm_id', 'no_id')}"
        
        with st.container(border=True):
            ci, cn, ce = st.columns([4, 5.5, 0.5])
            with ci:
                st.markdown(f"<div><h4 style='margin:0;'>{row['name']}</h4><a href='{row['crm_link']}' target='_blank' class='id-badge'>🆔 {row['crm_id']}</a></div>", unsafe_allow_html=True)
                st.markdown(f"<span style='color:grey; font-size:12px;'>📍 {row.get('state','-')} | 👤 {row.get('owner','-')}</span>", unsafe_allow_html=True)
                cell = row['cell']; n_e = urllib.parse.quote(str(row['name']))
                st.markdown(f"<div style='display:flex; gap:15px; margin-top:10px;'>📱 <a href='tel:{cell}' class='contact-link'>{cell}</a> <a href='mailto:{row['email']}'>📧</a> <a href='https://calendar.google.com/calendar/r/eventedit?text=Meeting_{n_e}' target='_blank'>📅</a></div>", unsafe_allow_html=True)
            
            with cn:
                note_h = str(row.get('note', ''))
                st.markdown(f'<div class="history-container">{note_h}</div>', unsafe_allow_html=True)
                
                with st.form(key=f"fn_form_{safe_id}", clear_on_submit=True):
                    ni = st.text_input("Note nhanh...", key=f"ni_in_{safe_id}", label_visibility="collapsed")
                    if st.form_submit_button("Lưu"):
                        if ni.strip():
                            fresh = load_data("leads")
                            if not fresh.empty:
                                now = datetime.now().strftime("[%m/%d %H:%M]")
                                entry = f"<div class='history-entry'><b>{now}</b> {ni}</div>"
                                fresh.at[idx, 'note'] = entry + str(fresh.at[idx, 'note'])
                                save_data(fresh, "leads", current_len=len(leads_main)); st.rerun()
                
                with st.popover("📝 Sửa"):
                    en = st.text_area("Nội dung", value=clean_html_for_edit(note_h), height=200, key=f"ed_ar_{safe_id}")
                    if st.button("Cập nhật", key=f"up_bt_{safe_id}"):
                        fresh = load_data("leads")
                        if not fresh.empty:
                            fmt = "".join([f"<div class='history-entry'>{line}</div>" for line in en.split('\n') if line.strip()])
                            fresh.at[idx, 'note'] = fmt
                            save_data(fresh, "leads", current_len=len(leads_main)); st.rerun()

            with ce:
                with st.popover("⚙️"):
                    if st.button("🗑️ Xóa Lead", key=f"del_{safe_id}", type="primary"):
                        st.session_state[f"conf_{safe_id}"] = True
                    if st.session_state.get(f"conf_{safe_id}"):
                        ok, no = st.columns(2)
                        if ok.button("Vâng", key=f"y_{safe_id}"):
                            f = load_data("leads")
                            save_data(f.drop(idx), "leads", current_len=len(leads_main))
                            del st.session_state[f"conf_{safe_id}"]; st.rerun()
                        if no.button("Hủy", key=f"n_{safe_id}"):
                            del st.session_state[f"conf_{safe_id}"]; st.rerun()
else:
    st.info("Đang tải dữ liệu...")
