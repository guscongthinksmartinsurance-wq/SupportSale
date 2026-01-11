import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse

# --- 1. KẾT NỐI & CẤU HÌNH ---
st.set_page_config(page_title="TMC CRM PRO V28", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    return conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0).dropna(how='all')

def save_data(df, worksheet):
    df = df.fillna("")
    conn.update(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, data=df)
    st.cache_data.clear()

# --- 2. CSS GIAO DIỆN CAO CẤP ---
st.markdown("""
    <style>
    .history-container {
        background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px;
        padding: 12px; height: 160px; overflow-y: auto; font-family: 'Segoe UI', sans-serif;
        font-size: 13px; color: #495057; line-height: 1.5;
    }
    .history-entry { border-bottom: 1px solid #dee2e6; margin-bottom: 8px; padding-bottom: 4px; }
    .timestamp { color: #007bff; font-weight: 600; margin-right: 8px; }
    .contact-link { text-decoration: none; color: #28a745; font-weight: bold; }
    .id-badge {
        background-color: #fce4ec; color: #d81b60; padding: 2px 8px;
        border-radius: 12px; font-weight: bold; font-size: 13px; text-decoration: none;
        border: 1px solid #f8bbd0; margin-left: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC NOTE ---
def save_note_v28(idx, current_note, note_key):
    new_txt = st.session_state[note_key]
    if new_txt and new_txt.strip():
        now = datetime.now()
        entry = f"<div class='history-entry'><span class='timestamp'>[{now.strftime('%m/%d %H:%M')}]</span>{new_txt}</div>"
        combined = entry + str(current_note)
        df = load_data("leads")
        df.at[idx, 'note'] = combined
        df.at[idx, 'last_interact'] = now.strftime("%Y-%m-%d %H:%M:%S")
        save_data(df, "leads")
        st.session_state[note_key] = ""; st.rerun()

# --- 4. SIDEBAR (SELECTBOX & ADD) ---
with st.sidebar:
    st.title("⚒️ CRM Tools")
    df_links = load_data("links")
    
    # Selectbox cho Links/Sales Kit
    for cat in ["Quick Link", "Sales Kit"]:
        list_items = df_links[df_links['category'] == cat]
        if not list_items.empty:
            sel = st.selectbox(f"📂 {cat}", ["-- Chọn --"] + list_items['title'].tolist())
            if sel != "-- Chọn --":
                url = list_items[list_items['title'] == sel]['url'].values[0]
                st.markdown(f"🔗 **[Mở tài liệu]({url})**")

    st.divider()
    with st.expander("➕ Thêm Khách Hàng Mới"):
        with st.form("add_lead"):
            n = st.text_input("Họ tên"); i = st.text_input("CRM ID")
            c = st.text_input("Cellphone"); w = st.text_input("Workphone")
            em = st.text_input("Email"); l = st.text_input("Link CRM")
            if st.form_submit_button("Lưu hệ thống"):
                df_all = load_data("leads")
                new_r = {"name":n, "crm_id":i, "cell":c, "work":w, "email":em, "crm_link":l, "status":"New"}
                save_data(pd.concat([df_all, pd.DataFrame([new_r])], ignore_index=True), "leads"); st.rerun()

# --- 5. PIPELINE PROCESSING ---
st.title("💼 Pipeline Processing")
leads_df = load_data("leads")

# Tìm kiếm & Slider
c_sch, c_sld = st.columns([7, 3])
q = c_sch.text_input("🔍 Tìm theo Tên, ID, SĐT...", placeholder="Nhập từ khóa...").lower()
days = c_sld.slider("⏳ Không tương tác", 0, 90, 90)

if not leads_df.empty:
    filtered = leads_df[leads_df.apply(lambda r: q in str(r['name']).lower() or q in str(r['crm_id']).lower() or q in str(r['cell']).lower() or q in str(r['work']).lower(), axis=1)]

    for idx, row in filtered.iterrows():
        curr_h = str(row['note']) if str(row['note']) != 'nan' else ""
        crm_url = str(row.get('crm_link', '#'))
        
        with st.container(border=True):
            c_info, c_note, c_edit = st.columns([4.5, 5, 0.5])
            
            with c_info:
                # Dòng 1: Tên và ID gắn link CRM
                st.markdown(f"""<div style='display: flex; align-items: center;'>
                    <h4 style='margin:0;'>{row['name']}</h4>
                    <a href='{crm_url}' target='_blank' class='id-badge'>🆔 {row['crm_id']}</a>
                </div>""", unsafe_allow_html=True)
                
                # Dòng 2: Cellphone + Icons
                cell = str(row['cell']).strip()
                n_e = urllib.parse.quote(str(row['name']))
                st.markdown(f"""<div style='margin-top: 10px; display: flex; align-items: center; gap: 10px;'>
                    📱 Cell: <a href='tel:{cell}' class='contact-link'>{cell}</a>
                    <a href='rcmobile://sms?number={cell}'>💬</a>
                    <a href='mailto:{row.get('email','')}'>📧</a>
                    <a href='https://calendar.google.com/calendar/r/eventedit?text=Meeting_{n_e}' target='_blank'>📅</a>
                </div>""", unsafe_allow_html=True)
                
                # Dòng 3: Workphone
                work = str(row['work']).strip()
                if work and work not in ['nan', '0', '']:
                    st.markdown(f"📞 Work: <a href='tel:{work}' class='contact-link'>{work}</a>", unsafe_allow_html=True)
                
                st.caption(f"🏷️ Trạng thái: {row['status']}")

            with c_note:
                st.markdown(f'<div class="history-container">{curr_h}</div>', unsafe_allow_html=True)
                cn1, cn2 = st.columns([8.5, 1.5])
                with cn1: st.text_input("Note nhanh...", key=f"n_{idx}", on_change=save_note_v28, args=(idx, curr_h, f"n_{idx}"), label_visibility="collapsed")
                with cn2:
                    with st.popover("📝"):
                        new_h = st.text_area("Sửa lịch sử Note", value=curr_h, height=250)
                        if st.button("Lưu thay đổi", key=f"s_{idx}"):
                            f_df = load_data("leads"); f_df.at[idx, 'note'] = new_h; save_data(f_df, "leads"); st.rerun()

            with c_edit:
                with st.popover("⚙️"):
                    with st.form(f"e_{idx}"):
                        un = st.text_input("Tên", value=row['name'])
                        ui = st.text_input("ID", value=row['crm_id'])
                        uc = st.text_input("Cell", value=row['cell'])
                        uw = st.text_input("Work", value=row['work'])
                        ul = st.text_input("Link CRM", value=row.get('crm_link',''))
                        if st.form_submit_button("Cập nhật"):
                            f = load_data("leads"); f.loc[idx,['name','crm_id','cell','work','crm_link']]=[un,ui,uc,uw,ul]; save_data(f,"leads"); st.rerun()
                    if st.button("🗑️ Xóa", key=f"d_{idx}", type="primary"):
                        f = load_data("leads"); save_data(f.drop(idx), "leads"); st.rerun()
