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

# 3. STREAMLIT PAGE CONFIG & STABLE EYE-FRIENDLY CSS
st.set_page_config(page_title="RST ASSISTANT", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    /* Eye-Friendly Slate Dark Background */
    .stApp {
        background-color: #0b0f19 !important;
        color: #e2e8f0 !important;
    }

    /* Soft Glass Card */
    .glass-card {
        background: rgba(30, 41, 59, 0.7) !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
        border-radius: 14px !important;
        padding: 16px 20px !important;
        margin-bottom: 15px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
    }

    /* Profile Box Badge */
    .profile-box {
        float: right;
        display: flex;
        align-items: center;
        gap: 10px;
        background: #1e293b;
        border: 1px solid #38bdf8;
        padding: 6px 16px;
        border-radius: 30px;
    }

    .circle-avatar {
        width: 34px;
        height: 34px;
        background: linear-gradient(135deg, #6366f1, #3b82f6);
        color: #ffffff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 15px;
    }

    /* Styled Buttons */
    .stButton>button {
        background: #1e293b !important;
        color: #38bdf8 !important;
        border: 1px solid rgba(56, 189, 248, 0.4) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        width: 100% !important;
        padding: 8px 12px !important;
        transition: 0.2s !important;
    }

    .stButton>button:hover {
        background: #38bdf8 !important;
        color: #0f172a !important;
        border-color: #38bdf8 !important;
    }

    h1, h2, h3 {
        color: #38bdf8 !important;
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
        st.markdown('<div class="glass-card" style="text-align:center;"><h2>⚡ RST LOGIN</h2><p style="color:#94a3b8;">இலவச பயன்பாடு முடிந்தது! தொடர லாக் இன் செய்யவும்.</p></div>', unsafe_allow_html=True)
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
    st.markdown("<h1 style='text-align: center;'>👑 OWNER ADMIN DASHBOARD</h1>", unsafe_allow_html=True)
    
    if st.button("🚪 Exit Admin Panel"):
        st.session_state.admin_authenticated = False
        st.session_state.active_mode = "chat"
        st.rerun()

    logs = fetch_all_chats()
    total_chats = len(logs)
    unique_users = len(set([log[1] for log in logs])) if logs else 0

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(f'<div class="glass-card" style="text-align:center;"><h3>{total_chats}</h3><p style="color:#94a3b8; margin:0;">Total Searches Logged</p></div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown(f'<div class="glass-card" style="text-align:center;"><h3>{unique_users}</h3><p style="color:#94a3b8; margin:0;">Total Registered Users</p></div>', unsafe_allow_html=True)

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

    # Header
    st.markdown("<h1 style='text-align: center; font-size:36px;'>⚡ RST ASSISTANT ⚡</h1>", unsafe_allow_html=True)
    st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 10px !important; max-width: 500px; margin: 0 auto 15px auto;">
            <b>SYSTEM OWNER:</b> <span style="color:#38bdf8;">MOHAMMED RASITH</span>
        </div>
    """, unsafe_allow_html=True)

    # Navigation
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
