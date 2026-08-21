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

# 3. STREAMLIT PAGE CONFIG & DARK MATTE DASHBOARD UI CSS
st.set_page_config(page_title="RST AI ASSISTANT", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    /* Dark Matte Background matching the UI design */
    .stApp {
        background-color: #0b0e14 !important;
        color: #e2e8f0 !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    }

    /* Matte UI Card Styling */
    .matte-card {
        background: #161b22 !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 18px !important;
        padding: 20px !important;
        margin-bottom: 16px !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5) !important;
    }

    /* Logo Emblem with Emerald/Mint Accent */
    .rst-emblem-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 10px;
        margin-bottom: 12px;
    }

    .rst-emblem-box {
        padding: 10px 32px;
        background: #161b22;
        border-radius: 20px;
        border: 1px solid #00bfa5;
        box-shadow: 0 0 20px rgba(0, 191, 165, 0.2);
    }

    .rst-emblem-text {
        font-size: 48px;
        font-weight: 900;
        letter-spacing: 6px;
        color: #00e676;
        text-shadow: 0 0 15px rgba(0, 230, 118, 0.4);
        margin: 0;
        line-height: 1;
    }

    .rst-title-text {
        font-size: 22px !important;
        font-weight: 700 !important;
        text-align: center !important;
        letter-spacing: 3px;
        color: #ffffff;
        margin-bottom: 6px !important;
    }

    .owner-badge {
        background: #161b22;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 6px 16px;
        width: fit-content;
        margin: 0 auto 24px auto;
        font-size: 11px;
        letter-spacing: 1px;
        color: #94a3b8;
    }

    /* Minimalist Profile Chip */
    .profile-box {
        float: right;
        display: flex;
        align-items: center;
        gap: 12px;
        background: #161b22;
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 6px 16px;
        border-radius: 24px;
    }

    .circle-avatar {
        width: 32px;
        height: 32px;
        background: #00bfa5;
        color: #0b0e14;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 14px;
    }

    /* Dark Matte Buttons with Teal Accent */
    .stButton>button {
        background: #161b22 !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        width: 100% !important;
        padding: 10px 20px !important;
        transition: all 0.2s ease-in-out !important;
    }

    .stButton>button:hover {
        background: #00bfa5 !important;
        color: #0b0e14 !important;
        border-color: #00bfa5 !important;
        box-shadow: 0 4px 15px rgba(0, 191, 165, 0.3) !important;
    }

    /* Admin Button Distinct Gold-Amber Style */
    div[data-testid="stColumn"]:first-child .stButton>button {
        background: #1c1917 !important;
        color: #f59e0b !important;
        border: 1px solid rgba(245, 158, 11, 0.3) !important;
        border-radius: 14px !important;
    }

    div[data-testid="stColumn"]:first-child .stButton>button:hover {
        background: #f59e0b !important;
        color: #0b0e14 !important;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4) !important;
    }

    /* Inputs Styling */
    .stTextInput input, .stTextArea textarea, .stSelectbox > div {
        background-color: #161b22 !important;
        color: #f8fafc !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
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
        st.markdown("""
            <div class="matte-card" style="text-align:center;">
                <div class="rst-emblem-container">
                    <div class="rst-emblem-box">
                        <div class="rst-emblem-text">RST</div>
                    </div>
                </div>
                <div class="rst-title-text">LOGIN</div>
                <p style="color:#94a3b8; font-size:13px; margin-top:8px;">இலவச பயன்பாடு முடிந்தது! தொடர லாக் இன் செய்யவும்.</p>
            </div>
        """, unsafe_allow_html=True)
        with st.form("login_form"):
            name_in = st.text_input("👤 Enter Your Name:")
            email_in = st.text_input("📧 Enter Your Email:")
            submit = st.form_submit_button("🚀 Access AI Assistant")
            if submit:
                if name_in.strip() and "@" in email_in:
                    st.session_state.user_name = name_in.strip()
                    st.session_state.user_email = email_in.strip()
                    st.success("✅ லாக் இன் வெற்றி!")
                    st.rerun()

# 6. ADMIN DASHBOARD
def show_admin_dashboard():
    st.markdown("""
        <div class="rst-emblem-container">
            <div class="rst-emblem-box">
                <div class="rst-emblem-text">RST</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="rst-title-text">OWNER ADMIN DASHBOARD</div>', unsafe_allow_html=True)
    
    if st.button("🚪 Exit Admin Panel"):
        st.session_state.admin_authenticated = False
        st.session_state.active_mode = "chat"
        st.rerun()

    logs = fetch_all_chats()
    total_chats = len(logs)
    unique_users = len(set([log[1] for log in logs])) if logs else 0

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(f'<div class="matte-card" style="text-align:center;"><h2 style="color:#00e676; margin:0;">{total_chats}</h2><p style="color:#94a3b8; margin:0;">Total Searches Logged</p></div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown(f'<div class="matte-card" style="text-align:center;"><h2 style="color:#00bfa5; margin:0;">{unique_users}</h2><p style="color:#94a3b8; margin:0;">Total Registered Users</p></div>', unsafe_allow_html=True)

    st.subheader("🔍 Search User Activity")
    search_query = st.text_input("🔎 Filter by Name, Email or Prompt Keyword:")

    st.markdown("### 📜 Permanent Chat History")
    if logs:
        for name, email, prompt, time_stamp in logs:
            if search_query.lower() in name.lower() or search_query.lower() in email.lower() or search_query.lower() in prompt.lower():
                st.markdown(f"""
                    <div class="matte-card">
                        <p style="color: #00bfa5; margin:0;"><b>User:</b> {name} ({email}) | <span style="color:#94a3b8; font-size:11px;">{time_stamp}</span></p>
                        <p style="color: #e2e8f0; margin: 5px 0 0 0;"><b>Prompt:</b> {prompt}</p>
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
    # TOP HEADER ROW
    top_col_left, top_col_right = st.columns([1, 1])
    
    with top_col_left:
        if st.button("👑 Admin"): 
            st.session_state.active_mode = "admin"

    with top_col_right:
        if st.session_state.user_email:
            avatar_letter = st.session_state.user_name[0].upper()
            st.markdown(f"""
                <div class="profile-box">
                    <div class="circle-avatar">{avatar_letter}</div>
                    <div>
                        <div style="color:#ffffff; font-weight:bold; font-size:13px;">{st.session_state.user_name}</div>
                        <div style="color:#00bfa5; font-size:10px;">{st.session_state.user_email}</div>
                    </div>
                </div>
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
            """, unsafe_allow_html=True)

    # Header Emblem Banner
    st.markdown("""
        <div class="rst-emblem-container">
            <div class="rst-emblem-box">
                <div class="rst-emblem-text">RST</div>
            </div>
        </div>
        <div class="rst-title-text">⚡ ASSISTANT ⚡</div>
        <div class="owner-badge">
            SYSTEM ARCHITECT: <span style="color:#00e676; font-weight:bold;">MOHAMMED RASITH</span>
        </div>
    """, unsafe_allow_html=True)

    # MATTE NAVIGATION BUTTONS
    c_space_left, c_btn1, c_btn2, c_space_right = st.columns([2, 1.5, 1.5, 2])
    
    with c_btn1:
        if st.button("🤖 AI Chat"): st.session_state.active_mode = "chat"
    with c_btn2:
        if st.button("🎙️ Voice Gen"): st.session_state.active_mode = "voice"

    st.markdown("<hr style='border: 0.5px solid rgba(255,255,255,0.05); margin: 20px 0;'>", unsafe_allow_html=True)

    # 1. AI CHAT MODE
    if st.session_state.active_mode == "chat":
        st.subheader("🤖 RST Smart AI Assistant")

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

    # 2. VOICE GENERATION MODE
    elif st.session_state.active_mode == "voice":
        st.subheader("🎙️ RST Voice Generator")
        v_text = st.text_area("பேச்சாக மாற்ற வேண்டிய உரை:", "வணக்கம்! நான் RST AI Assistant.")
        voice_opt = st.selectbox("குரலைத் தேர்ந்தெடுக்கவும்:", ["ta-IN-ValluvarNeural (Tamil Male)", "ta-IN-PallaviNeural (Tamil Female)"])
        voice_code = "ta-IN-ValluvarNeural" if "Valluvar" in voice_opt else "ta-IN-PallaviNeural"
        
        if st.button("Generate Voice"):
            if v_text:
                async def make_voice():
                    comm = edge_tts.Communicate(v_text, voice_code)
                    await comm.save("voice.mp3")
                asyncio.run(make_voice())
                st.audio("voice.mp3")

    # 3. ADMIN LOGIN MODE
    elif st.session_state.active_mode == "admin":
        st.subheader("👑 Admin Authentication")
        pwd = st.text_input("Enter Master Password:", type="password")
        if st.button("Access Admin Console"):
            if pwd == "RSTA02EHYDR6":
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Incorrect Password!")
