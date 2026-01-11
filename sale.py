import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import urllib.parse

# --- 1. KẾT NỐI DATABASE ---
st.set_page_config(page_title="TMC CRM PRO V24.4", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    return conn.read(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, ttl=0).dropna(how='all')

def save_data(df, worksheet):
    df = df.fillna("")
    conn.update(spreadsheet=st.secrets["spreadsheet"], worksheet=worksheet, data=df)
    st.cache_data.clear()

# --- 2. CSS CHUẨN ---
st.markdown("""
    <style>
    .history-container {
        background-color: #ffffff; border: 1px solid #e1e4e8; border-radius: 6px;
        padding: 10px; height: 160px; overflow-y: auto; font-family: sans-serif;
        font-size: 13px; color: #24292e;
    }
    .history-entry { border-bottom: 1px dashed #eee; margin-bottom: 5px; padding-bottom: 2px; }
    .timestamp { color: #0366d6; font-weight: bold; margin-right: 5px; }
    .stButton>button { width: 100%; border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC LƯU NOTE ---
def save_note_v24(idx, current_note, note_key):
    new_txt = st.session_state[note_key]
    if new_txt and new_txt.strip():
        now = datetime.now()
        entry = f"<div class='history-entry'><span class='timestamp'>[{now.strftime('%m/%d %H:%M')}]</span>{new_txt}</div>"
        combined = entry + str(current_note)
        df_full = load_data("leads")
        df_full.at[idx, 'note'] = combined
        df_full.at[idx, 'last_interact'] = now.strftime("%Y-%m-%d %H:%M:%S")
        save_data(df_full, "leads")
        st.session_state[note_key] = ""
        st.rerun()

# --- 4. SIDEBAR (QUICK LINKS & SALES KIT & ADD NEW) ---
with st.sidebar:
    st.title("🛠️ CRM Tools")
    
    # --- PHẦN LINKS & SALES KIT ---
    df_links = load_data("links")
    col_l, col_s = st.columns(2)
    with col_l:
        st.subheader("🔗 Links")
        for _, l in df_links[df_links['category'] == 'Quick Link'].iterrows():
            st.markdown(f"**[{l['title']}]({l['url']})**")
    with col_s:
        st.subheader("📁 Sales Kit")
        for _, l in df_links[df_links['category'] == 'Sales Kit'].iterrows():
            st.markdown(f"**[{l['title']}]({l['url']})**")

    st.divider()
    
    # --- PHẦN THÊM KHÁCH HÀNG MỚI (ĐỦ TRƯỜNG) ---
    with st.expander("➕ Thêm Khách Hàng Mới", expanded=False):
        with st.form("new_lead_form", clear_on_submit=True):
            f_name = st.text_input("Họ tên *")
            f_id = st.text_input("CRM ID *")
            f_cell = st.text_input("Số điện thoại (Cell)")
            f_email = st.text_input("Email")
            f_source = st.selectbox("Nguồn", ["Facebook", "Zalo", "Hotline", "Web", "Khác"])
            f_budget = st.text_input("Ngân sách")
            if st.form_submit_button("Lưu hệ thống"):
                if f_name and f_id:
                    df_leads_all = load_data("leads")
                    new_row = {
                        "name": f_name, "crm_id": f_id, "cell": f_cell, "email": f_email,
                        "source": f_source, "budget": f_budget, "status": "New", 
                        "last_interact": datetime.now().strftime("%Y-%m-%d %H:%M"), "note": ""
                    }
                    save_data(pd.concat([df_leads_all, pd.DataFrame([new_row])], ignore_index=True), "leads")
                    st.success("Đã thêm!"); st.rerun()

# --- 5. GIAO DIỆN CHÍNH ---
st.title("💼 Pipeline Processing")
leads_df = load_data("leads")

if not leads_df.empty:
    for idx, row in leads_df.iterrows():
        curr_h = str(row['note']) if str(row['note']) != 'nan' else ""
        crm_url = str(row['crm_link']) if 'crm_link' in row and str(row['crm_link']) != 'nan' else "#"
        
        with st.container(border=True):
            c_info, c_note, c_edit = st.columns([4, 5, 1])
            
            with c_info:
                st.markdown(f"#### {row['name']}")
                # Badge ID & Link
                st.markdown(f"""<div style="display:flex;gap:8px;margin-bottom:8px;"><span style="background:#7d3c98;color:white;padding:1px 4px;border-radius:3px;font-size:10px;">ID</span><a href="{crm_url}" target="_blank" style="color:#e83e8c;text-decoration:none;font-weight:bold;background:#fef1f6;padding:2px 6px;border-radius:4px;border:1px solid #fce4ec;">🔗 {row['crm_id']}</a></div>""", unsafe_allow_html=True)
                
                # Liên lạc Icons
                p_c = str(row['cell']).strip(); n_e = urllib.parse.quote(str(row['name']))
                st.markdown(f"""<div style="display:flex;gap:15px;align-items:center;"><span>📱 <a href="tel:{p_c}" style="color:#28a745;font-weight:bold;text-decoration:none;">{p_c}</a></span><a href="rcmobile://sms?number={p_c}">💬</a><a href="mailto:{row.get('email','')}">📧</a></div>""", unsafe_allow_html=True)
                
                # Thông tin bổ sung
                st.caption(f"📍 Nguồn: {row.get('source','-')} | 💰 Ngân sách: {row.get('budget','-')}")

            with c_note:
                st.markdown(f'<div class="history-container">{curr_h}</div>', unsafe_allow_html=True)
                st.text_input("Ghi chú...", key=f"note_{idx}", on_change=save_note_v24, args=(idx, curr_h, f"note_{idx}"), label_visibility="collapsed")

            with c_edit:
                with st.popover("⚙️"):
                    st.markdown("**Chỉnh sửa thông tin**")
                    with st.form(f"edit_{idx}"):
                        u_name = st.text_input("Tên", value=row['name'])
                        u_status = st.selectbox("Trạng thái", ["New", "Contacted", "Following", "Closed"], index=0)
                        u_budget = st.text_input("Ngân sách", value=row.get('budget',''))
                        if st.form_submit_button("Cập nhật"):
                            full_df = load_data("leads")
                            full_df.at[idx, 'name'] = u_name
                            full_df.at[idx, 'status'] = u_status
                            full_df.at[idx, 'budget'] = u_budget
                            save_data(full_df, "leads"); st.rerun()
                    
                    if st.button("🗑️ Xóa khách", key=f"del_{idx}", type="primary"):
                        full_df = load_data("leads")
                        save_data(full_df.drop(idx), "leads"); st.rerun()
        st.divider()
