import streamlit as st
import edge_tts
import asyncio
import sqlite3
from datetime import datetime

# ==================== DATABASE SETUP ====================
def init_db():
    conn = sqlite3.connect("rst_assistant.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            user_email TEXT,
            prompt TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_chat_to_db(name, email, prompt):
    conn = sqlite3.connect("rst_assistant.db")
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO chat_logs (user_name, user_email, prompt, timestamp) VALUES (?, ?, ?, ?)",
                   (name, email, prompt, now))
    conn.commit()
    conn.close()

def fetch_all_chats():
    conn = sqlite3.connect("rst_assistant.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_name, user_email, prompt, timestamp FROM chat_logs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Database Init
init_db()

# ==================== GEMINI API SETUP ====================
HAS_GEMINI = False
client = None

if "GEMINI_API_KEY" in st.secrets:
    try:
        from google import genai
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        HAS_GEMINI = True
    except Exception as e:
        HAS_GEMINI = False

# ==================== STREAMLIT CONFIG & CSS ====================
st.set_page_config(page_title="RST ASSISTANT", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(circle at 20% 20%, rgba(255, 0, 85, 0.15), transparent 40%),
                    radial-gradient(circle at 80% 80%, rgba(0, 240, 255, 0.15), transparent 40%),
                    linear-gradient(135deg, #030008, #0a0518, #020d1a);
        background-size: 200% 200%;
        animation: cyberGlow 12s ease infinite !important;
        color: #00f0ff;
    }
    @keyframes cyberGlow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(20px) saturate(200%) !important;
        border: 1px solid rgba(0, 240, 255, 0.25) !important;
        border-radius: 20px !important;
        padding: 20px !important;
        margin-bottom: 20px !important;
    }
    .profile-box {
        float: right;
        display: flex;
        align-items: center;
        gap: 12px;
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(0, 240, 255, 0.5);
        padding: 6px 18px 6px 8px;
        border-radius: 40px;
    }
    .circle-avatar {
        width: 38px;
        height: 38px;
        background: linear-gradient(135deg, #ff0055, #7928ca);
        color: #ffffff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
    }
    .stButton>button {
        background: rgba(0, 240, 255, 0.05) !important;
        color: #00f0ff !important;
        border: 1px solid rgba(0, 240, 255, 0.4) !important;
        border-radius: 12px !important;
        font-weight: bold !important;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #ff0055, #7928ca) !important;
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== SESSION STATES ====================
if "usage_count" not in st.session_state: st.session_state.usage_count = 0
if "user_name" not in st.session_state: st.session_state.user_name = None
if "user_email" not in st.session_state: st.session_state.user_email = None
if "active_mode" not in st.session_state: st.session_state.active_mode = "chat"
if "admin_authenticated" not in st.session_state: st.session_state.admin_authenticated = False

# ==================== LOGIN PAGE ====================
def show_login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="glass-card" style="text-align:center;"><h1 style="color:#ff0055;">⚡ RST LOGIN</h1></div>', unsafe_allow_html=True)
        with st.form("login_form"):
            name_in = st.text_input("👤 Enter Your Name:")
            email_in = st.text_input("📧 Enter Your Email:")
            submit = st.form_submit_button("🚀 Unlock Access")
            if submit:
                if name_in.strip() and "@" in email_in:
                    st.session_state.user_name = name_in.strip()
                    st.session_state.user_email = email_in.strip()
                    st.success("✅ லாக் இன் வெற்றி!")
                    st.rerun()

# ==================== ADMIN DASHBOARD WITH SEARCH ====================
def show_admin_dashboard():
    st.markdown("<h1 style='text-align: center; color: #ff0055;'>👑 PERMANENT ADMIN DASHBOARD</h1>", unsafe_allow_html=True)
    
    if st.button("🚪 Exit Admin Panel"):
        st.session_state.admin_authenticated = False
        st.session_state.active_mode = "chat"
        st.rerun()

    logs = fetch_all_chats()
    
    # Analytics
    total_chats = len(logs)
    unique_users = len(set([log[1] for log in logs])) if logs else 0

    m1, m2 = st.columns(2)
    m1.metric("Total User Searches", total_chats)
    m2.metric("Total Registered Users", unique_users)

    st.subheader("🔍 Search & Filter User Activity")
    search_query = st.text_input("🔎 Search by Name or Email:")

    st.markdown("### 📜 Permanent Database Logs")
    if logs:
        for name, email, prompt, time_stamp in logs:
            if search_query.lower() in name.lower() or search_query.lower() in email.lower() or search_query.lower() in prompt.lower():
                st.markdown(f"""
                    <div class="glass-card">
                        <p style="color: #ff0055; margin:0;"><b>User:</b> {name} ({email}) | <span style="color:#8b949e; font-size:11px;">{time_stamp}</span></p>
                        <p style="color: #00f0ff; margin: 5px 0 0 0;"><b>Prompt:</b> {prompt}</p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("தரவுகள் எதுவும் இல்லை.")

# ==================== MAIN APP ====================
if st.session_state.active_mode == "admin" and st.session_state.admin_authenticated:
    show_admin_dashboard()
elif st.session_state.usage_count >= 2 and st.session_state.user_email is None:
    show_login_page()
else:
    # Profile Badge
    if st.session_state.user_email:
        st.markdown(f'''<div class="profile-box"><div class="circle-avatar">{st.session_state.user_name[0].upper()}</div><div><b>{st.session_state.user_name}</b><br><small>{st.session_state.user_email}</small></div></div><div style="clear:both;"></div>''', unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #ff0055;'>⚡ RST ASSISTANT ⚡</h1>", unsafe_allow_html=True)

    # Nav
    c1, c2, c3 = st.columns(3)
    if c1.button("🤖 AI Chat"): st.session_state.active_mode = "chat"
    if c2.button("🎙️ Voice Gen"): st.session_state.active_mode = "voice"
    if c3.button("👑 Admin"): st.session_state.active_mode = "admin"

    if st.session_state.active_mode == "chat":
        st.subheader("🤖 AI Chatbot")
        user_input = st.chat_input("Ask something...")
        if user_input:
            if st.session_state.user_email is None:
                st.session_state.usage_count += 1
                
            name = st.session_state.user_name if st.session_state.user_name else "Guest"
            email = st.session_state.user_email if st.session_state.user_email else "Guest@rst.com"
            
            # Save to Permanent SQLite DB
            save_chat_to_db(name, email, user_input)

            st.write(f"<b>You:</b> {user_input}", unsafe_allow_html=True)
            if HAS_GEMINI and client is not None:
                res = client.models.generate_content(model="gemini-3.6-flash", contents=user_input)
                st.write(f"<b>RST:</b> {res.text}", unsafe_allow_html=True)
            else:
                st.write("<b>RST:</b> வணக்கம்!")

    elif st.session_state.active_mode == "admin":
        pwd = st.text_input("Master Password:", type="password")
        if st.button("Login"):
            if pwd == "RSTA02EHYDR6":
                st.session_state.admin_authenticated = True
                st.rerun()
