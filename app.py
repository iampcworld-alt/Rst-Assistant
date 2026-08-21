import streamlit as st
import edge_tts
import asyncio
import sqlite3
from datetime import datetime

# 1. DATABASE SETUP
def init_db():
    conn = sqlite3.connect("rst_assistant.db", check_same_thread=False)
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
    conn = sqlite3.connect("rst_assistant.db", check_same_thread=False)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO chat_logs (user_name, user_email, prompt, timestamp) VALUES (?, ?, ?, ?)",
                   (name, email, prompt, now))
    conn.commit()
    conn.close()

def fetch_all_chats():
    conn = sqlite3.connect("rst_assistant.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT user_name, user_email, prompt, timestamp FROM chat_logs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

init_db()

# 2. GEMINI SETUP
HAS_GEMINI = False
client = None

if "GEMINI_API_KEY" in st.secrets:
    try:
        from google import genai
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        HAS_GEMINI = True
    except Exception:
        HAS_GEMINI = False

# 3. STREAMLIT PAGE CONFIG & HIGH-LEVEL ANIMATED CSS
st.set_page_config(page_title="RST ASSISTANT", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    /* Smooth Animated Dark Background */
    .stApp {
        background: linear-gradient(-45deg, #0f172a, #0b0f19, #1e1b4b, #0f172a) !important;
        background-size: 400% 400% !important;
        animation: gradientBG 15s ease infinite !important;
        color: #f1f5f9 !important;
    }

    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Animated RST Logo Title */
    .rst-logo-title {
        font-size: 42px !important;
        font-weight: 900 !important;
        text-align: center !important;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc, #38bdf8);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 4s linear infinite, logoPulse 3s ease-in-out infinite alternate;
        margin-bottom: 5px !important;
    }

    @keyframes shine {
        to { background-position: 200% center; }
    }

    @keyframes logoPulse {
        0% { filter: drop-shadow(0 0 5px rgba(56, 189, 248, 0.3)); }
        100% { filter: drop-shadow(0 0 20px rgba(129, 140, 248, 0.7)); }
    }

    /* Glassmorphic Card with Smooth Hover Lift */
    .glass-card {
        background: rgba(30, 41, 59, 0.6) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
        border-radius: 16px !important;
        padding: 18px 22px !important;
        margin-bottom: 15px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        transition: all 0.3s ease-in-out !important;
    }

    .glass-card:hover {
        transform: translateY(-4px) !important;
        border-color: rgba(56, 189, 248, 0.5) !important;
        box-shadow: 0 12px 40px 0 rgba(56, 189, 248, 0.15) !important;
    }

    /* Profile Badge */
    .profile-box {
        float: right;
        display: flex;
        align-items: center;
        gap: 12px;
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(56, 189, 248, 0.4);
        padding: 6px 16px;
        border-radius: 30px;
        box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);
    }

    .circle-avatar {
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, #6366f1, #38bdf8);
        color: #ffffff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 16px;
        box-shadow: 0 0 10px rgba(99, 102, 241, 0.5);
    }

    /* Modern Responsive Interactive Buttons */
    .stButton>button {
        background: rgba(30, 41, 59, 0.8) !important;
        color: #38bdf8 !important;
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        width: 100% !important;
        padding: 10px 14px !important;
        transition: all 0.3s ease !important;
    }

    .stButton>button:hover {
        background: linear-gradient(135deg, #38bdf8, #6366f1) !important;
        color: #ffffff !important;
        border-color: #38bdf8 !important;
        box-shadow: 0 0 18px rgba(56, 189, 248, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    </style>
""", unsafe_allow_html=True)

# 4. SESSION STATES
if "usage_count" not in st.session_state: st.session_state.usage_count = 0
if "user_name" not in st.session_state: st.session_state.user_name = None
if "user_email" not in st.session_state: st.session_state.user_email = None
if "active_mode" not in st.session_state: st.session_state.active_mode = "chat"
if "admin_authenticated" not in st.session_state: st.session_state.admin_authenticated = False
if "messages" not in st.session_state: st.session_state.messages = []

# 5. LOGIN SCREEN
def show_login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="glass-card" style="text-align:center;"><div class="rst-logo-title">⚡ RST LOGIN</div><p style="color:#94a3b8;">இலவச பயன்பாடு முடிந்தது! தொடர லாக் இன் செய்யவும்.</p></div>', unsafe_allow_html=True)
        with st.form("login_form"):
            name_in = st.text_input("👤 Enter Your Name:")
            email_in = st.text_input("📧 Enter Your Email:")
            submit = st.form_submit_button("🚀 Unlock Unlimited Access")
            if submit:
                if name_in.strip() and "@" in email_in:
                    st.session_state.user_name = name_in.strip()
                    st.session_state.user_email = email_in.strip()
                    st.success("✅ லாக் இன் வெற்றி!")
                    st.rerun()

# 6. ADMIN DASHBOARD
def show_admin_dashboard():
    st.markdown('<div class="rst-logo-title">👑 OWNER ADMIN DASHBOARD</div>', unsafe_allow_html=True)
    
    if st.button("🚪 Exit Admin Panel"):
        st.session_state.admin_authenticated = False
        st.session_state.active_mode = "chat"
        st.rerun()

    logs = fetch_all_chats()
    total_chats = len(logs)
    unique_users = len(set([log[1] for log in logs])) if logs else 0

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(f'<div class="glass-card" style="text-align:center;"><h2 style="color:#38bdf8; margin:0;">{total_chats}</h2><p style="color:#94a3b8; margin:0;">Total Searches Logged</p></div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown(f'<div class="glass-card" style="text-align:center;"><h2 style="color:#818cf8; margin:0;">{unique_users}</h2><p style="color:#94a3b8; margin:0;">Total Registered Users</p></div>', unsafe_allow_html=True)

    st.subheader("🔍 Search User Activity")
    search_query = st.text_input("🔎 Filter by Name, Email or Prompt Keyword:")

    st.markdown("### 📜 Permanent Chat History")
    if logs:
        for name, email, prompt, time_stamp in logs:
            if search_query.lower() in name.lower() or search_query.lower() in email.lower() or search_query.lower() in prompt.lower():
                st.markdown(f"""
                    <div class="glass-card">
                        <p style="color: #818cf8; margin:0;"><b>User:</b> {name} ({email}) | <span style="color:#94a3b8; font-size:11px;">{time_stamp}</span></p>
                        <p style="color: #38bdf8; margin: 5px 0 0 0;"><b>Prompt:</b> {prompt}</p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("தரவுகள் எதுவும் இல்லை.")

# 7. MAIN APP ROUTING
if st.session_state.active_mode == "admin" and st.session_state.admin_authenticated:
    show_admin_dashboard()
elif st.session_state.usage_count >= 2 and st.session_state.user_email is None:
    show_login_page()
else:
    # Profile Badge
    if st.session_state.user_email:
        avatar_letter = st.session_state.user_name[0].upper()
        st.markdown(f"""
            <div class="profile-box">
                <div class="circle-avatar">{avatar_letter}</div>
                <div>
                    <div style="color:#ffffff; font-weight:bold; font-size:13px;">{st.session_state.user_name}</div>
                    <div style="color:#38bdf8; font-size:10px;">{st.session_state.user_email}</div>
                </div>
            </div>
            <div style="clear:both;"></div>
        """, unsafe_allow_html=True)
    else:
        left = 2 - st.session_state.usage_count
        st.markdown(f"""
            <div class="profile-box">
                <div class="circle-avatar">G</div>
                <div>
                    <div style="color:#ffffff; font-weight:bold; font-size:13px;">Guest User</div>
                    <div style="color:#f43f5e; font-size:10px;">{left} Uses Left</div>
                </div>
            </div>
            <div style="clear:both;"></div>
        """, unsafe_allow_html=True)

    # Animated Logo Header
    st.markdown('<div class="rst-logo-title">⚡ RST ASSISTANT ⚡</div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 8px 15px !important; max-width: 450px; margin: 0 auto 15px auto;">
            <b>SYSTEM OWNER:</b> <span style="color:#38bdf8;">MOHAMMED RASITH</span>
        </div>
    """, unsafe_allow_html=True)

    # Navigation Buttons
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        if st.button("🤖 AI Chat"): st.session_state.active_mode = "chat"
    with c2:
        if st.button("🎨 Image Gen"): st.session_state.active_mode = "image"
    with c3:
        if st.button("🎬 Video Gen"): st.session_state.active_mode = "video"
    with c4:
        if st.button("🎙️ Voice Gen"): st.session_state.active_mode = "voice"
    with c5:
        if st.button("🚀 Photo Edit"): st.session_state.active_mode = "edit"
    with c6:
        if st.button("👑 Admin"): st.session_state.active_mode = "admin"

    st.markdown("<hr style='border: 0.5px solid rgba(56,189,248,0.2); margin: 15px 0;'>", unsafe_allow_html=True)

    # Chat Mode
    if st.session_state.active_mode == "chat":
        st.subheader("🤖 RST Smart Assistant")

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_input = st.chat_input("Ask RST Assistant...")

        if user_input:
            if st.session_state.user_email is None:
                st.session_state.usage_count += 1

            name = st.session_state.user_name if st.session_state.user_name else "Guest User"
            email = st.session_state.user_email if st.session_state.user_email else "Guest"

            save_chat_to_db(name, email, user_input)

            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.spinner("⚡ RST Processing..."):
                if HAS_GEMINI and client is not None:
                    try:
                        response = client.models.generate_content(
                            model="gemini-3.6-flash",
                            contents=f"You are RST ASSISTANT built by Mohammed Rasith. Reply to: {user_input}"
                        )
                        reply = response.text
                    except Exception as e:
                        reply = f"Error: {str(e)}"
                else:
                    reply = "வணக்கம்! நான் RST AI Assistant."

            with st.chat_message("assistant"):
                st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

            if st.session_state.usage_count >= 2 and st.session_state.user_email is None:
                st.rerun()

    # Voice Mode
    elif st.session_state.active_mode == "voice":
        st.subheader("🎙️ RST Voice Generator")
        v_text = st.text_area("பேச்சாக மாற்ற வேண்டிய உரை:", "வணக்கம்!")
        if st.button("Generate Voice"):
            if v_text:
                async def make_voice():
                    comm = edge_tts.Communicate(v_text, "ta-IN-ValluvarNeural")
                    await comm.save("voice.mp3")
                asyncio.run(make_voice())
                st.audio("voice.mp3")

    # Admin Login Mode
    elif st.session_state.active_mode == "admin":
        st.subheader("👑 Admin Authentication")
        pwd = st.text_input("Enter Master Password:", type="password")
        if st.button("Access Admin Console"):
            if pwd == "RSTA02EHYDR6":
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Incorrect Password!")
