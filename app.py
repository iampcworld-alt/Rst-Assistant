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

# 3. STREAMLIT PAGE CONFIG & ADVANCED CSS
st.set_page_config(page_title="RST ASSISTANT", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    /* Full Page Background Animation */
    .stApp {
        background: radial-gradient(circle at 20% 20%, rgba(255, 0, 85, 0.2), transparent 40%),
                    radial-gradient(circle at 80% 80%, rgba(0, 240, 255, 0.2), transparent 40%),
                    linear-gradient(135deg, #030008, #0a0518, #020d1a) !important;
        background-size: 200% 200% !important;
        animation: cyberGlow 12s ease infinite !important;
        color: #00f0ff !important;
    }

    @keyframes cyberGlow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Transparent Glass Card */
    .glass-card {
        background: rgba(255, 255, 255, 0.04) !important;
        backdrop-filter: blur(20px) saturate(200%) !important;
        -webkit-backdrop-filter: blur(20px) saturate(200%) !important;
        border: 1px solid rgba(0, 240, 255, 0.3) !important;
        border-radius: 20px !important;
        padding: 20px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6) !important;
    }

    /* Top Right Profile Badge */
    .profile-box {
        float: right;
        display: flex;
        align-items: center;
        gap: 12px;
        background: rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(0, 240, 255, 0.5);
        padding: 6px 18px 6px 8px;
        border-radius: 40px;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.3);
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
        font-size: 17px;
        box-shadow: 0 0 10px #ff0055;
    }

    /* Neon Styled Buttons */
    .stButton>button {
        background: rgba(0, 240, 255, 0.08) !important;
        color: #00f0ff !important;
        border: 1px solid rgba(0, 240, 255, 0.4) !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        padding: 10px 20px !important;
        transition: all 0.3s ease-in-out !important;
    }

    .stButton>button:hover {
        background: linear-gradient(135deg, #ff0055, #7928ca) !important;
        color: #ffffff !important;
        border-color: #ff0055 !important;
        box-shadow: 0 0 20px rgba(255, 0, 85, 0.8) !important;
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
        st.markdown('<div class="glass-card" style="text-align:center;"><h1 style="color:#ff0055;">⚡ RST LOGIN</h1><p style="color:#8b949e;">இலவச பயன்பாடு முடிந்தது! தொடர லாக் இன் செய்யவும்.</p></div>', unsafe_allow_html=True)
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
    st.markdown("<h1 style='text-align: center; color: #ff0055; text-shadow: 0 0 25px #ff0055;'>👑 OWNER ADMIN DASHBOARD</h1>", unsafe_allow_html=True)
    
    if st.button("🚪 Exit Admin Panel"):
        st.session_state.admin_authenticated = False
        st.session_state.active_mode = "chat"
        st.rerun()

    logs = fetch_all_chats()
    
    total_chats = len(logs)
    unique_users = len(set([log[1] for log in logs])) if logs else 0

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(f'<div class="glass-card" style="text-align:center;"><h3>{total_chats}</h3><p>Total Searches Logged</p></div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown(f'<div class="glass-card" style="text-align:center;"><h3>{unique_users}</h3><p>Total Registered Users</p></div>', unsafe_allow_html=True)

    st.subheader("🔍 Search User Activity")
    search_query = st.text_input("🔎 Filter by Name, Email or Prompt Keyword:")

    st.markdown("### 📜 Permanent Chat History")
    if logs:
        for name, email, prompt, time_stamp in logs:
            if search_query.lower() in name.lower() or search_query.lower() in email.lower() or search_query.lower() in prompt.lower():
                st.markdown(f"""
                    <div class="glass-card" style="padding: 12px 20px !important;">
                        <p style="color: #ff0055; margin:0;"><b>User:</b> {name} ({email}) | <span style="color:#8b949e; font-size:11px;">{time_stamp}</span></p>
                        <p style="color: #00f0ff; margin: 5px 0 0 0;"><b>Prompt:</b> {prompt}</p>
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
                    <div style="color:#00f0ff; font-size:10px;">{st.session_state.user_email}</div>
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
                    <div style="color:#ff0055; font-size:10px;">{left} Uses Left</div>
                </div>
            </div>
            <div style="clear:both;"></div>
        """, unsafe_allow_html=True)

    # Header
    st.markdown("<h1 style='text-align: center; color: #ff0055; text-shadow: 0 0 25px #ff0055;'>⚡ RST ASSISTANT ⚡</h1>", unsafe_allow_html=True)
    st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 10px !important; max-width: 600px; margin: 0 auto 20px auto;">
            <b>SYSTEM OWNER:</b> <span style="color:#00f0ff;">MOHAMMED RASITH</span>
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

    st.markdown("<hr style='border: 0.5px solid rgba(0,240,255,0.2); margin: 15px 0;'>", unsafe_allow_html=True)

    # Chat Mode
    if st.session_state.active_mode == "chat":
        st.subheader("🤖 RST Interactive Smart Chatbot")

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_input = st.chat_input("Ask RST Assistant...")

        if user_input:
            if st.session_state.user_email is None:
                st.session_state.usage_count += 1

            name = st.session_state.user_name if st.session_state.user_name else "Guest User"
            email = st.session_state.user_email if st.session_state.user_email else "Guest"

            # Database Save
            save_chat_to_db(name, email, user_input)

            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.spinner("⚡ RST Thinking..."):
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
