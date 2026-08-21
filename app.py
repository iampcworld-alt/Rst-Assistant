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

# 3. SESSION STATES
if "theme" not in st.session_state: st.session_state.theme = "dark"
if "usage_count" not in st.session_state: st.session_state.usage_count = 0
if "user_name" not in st.session_state: st.session_state.user_name = None
if "user_email" not in st.session_state: st.session_state.user_email = None
if "active_mode" not in st.session_state: st.session_state.active_mode = "chat"
if "admin_authenticated" not in st.session_state: st.session_state.admin_authenticated = False
if "messages" not in st.session_state: st.session_state.messages = []

# 4. STREAMLIT CONFIG & PERFECT ALIGNMENT CSS
st.set_page_config(page_title="RST AI ASSISTANT", page_icon="⚡", layout="wide")

is_dark = st.session_state.theme == "dark"

bg_app = "#0b0f19" if is_dark else "#f1f5f9"
text_primary = "#f8fafc" if is_dark else "#0f172a"
text_secondary = "#94a3b8" if is_dark else "#64748b"
card_bg = "#1e293b" if is_dark else "#ffffff"
card_border = "rgba(56, 189, 248, 0.2)" if is_dark else "rgba(148, 163, 184, 0.3)"
btn_bg = "#1e293b" if is_dark else "#ffffff"
btn_text = "#38bdf8" if is_dark else "#0284c7"
btn_border = "rgba(56, 189, 248, 0.4)" if is_dark else "rgba(2, 132, 199, 0.3)"

st.markdown(f"""
    <style>
    /* Global Reset & Base */
    .stApp {{
        background-color: {bg_app} !important;
        color: {text_primary} !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    }}

    /* Container Padding Adjustment */
    .block-container {{
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px !important;
    }}

    /* Card Box */
    .rst-card {{
        background: {card_bg} !important;
        border: 1px solid {card_border} !important;
        border-radius: 16px !important;
        padding: 20px !important;
        margin-bottom: 16px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    }}

    /* Banner Logo Section */
    .rst-emblem-container {{
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 10px;
        margin-bottom: 8px;
    }}

    .rst-emblem-box {{
        padding: 8px 30px;
        background: {card_bg};
        border-radius: 18px;
        border: 2px solid {btn_border};
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.15);
    }}

    .rst-emblem-text {{
        font-size: 42px;
        font-weight: 900;
        letter-spacing: 5px;
        color: {btn_text};
        margin: 0;
        line-height: 1;
    }}

    .rst-title-text {{
        font-size: 20px !important;
        font-weight: 800 !important;
        text-align: center !important;
        letter-spacing: 3px;
        color: {text_primary} !important;
        margin-bottom: 6px !important;
    }}

    .owner-badge {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 20px;
        padding: 4px 16px;
        width: fit-content;
        margin: 0 auto 18px auto;
        font-size: 11px;
        letter-spacing: 1px;
        color: {text_secondary};
    }}

    /* Profile Badge Alignment */
    .profile-box {{
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 10px;
        background: {card_bg};
        border: 1px solid {card_border};
        padding: 5px 14px;
        border-radius: 24px;
        height: 42px;
    }}

    .circle-avatar {{
        width: 28px;
        height: 28px;
        background: {btn_text};
        color: #ffffff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 13px;
    }}

    /* Universal Button Style */
    .stButton>button {{
        background: {btn_bg} !important;
        color: {btn_text} !important;
        border: 1px solid {btn_border} !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        width: 100% !important;
        height: 42px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease !important;
    }}

    .stButton>button:hover {{
        background: {btn_text} !important;
        color: #ffffff !important;
    }}

    /* Admin Button Highlight */
    .admin-btn-col .stButton>button {{
        color: #d97706 !important;
        border: 1px solid rgba(217, 119, 6, 0.4) !important;
    }}

    .admin-btn-col .stButton>button:hover {{
        background: #d97706 !important;
        color: #ffffff !important;
    }}

    /* Inputs */
    .stTextInput input, .stTextArea textarea, .stSelectbox > div {{
        background-color: {card_bg} !important;
        color: {text_primary} !important;
        border: 1px solid {card_border} !important;
        border-radius: 12px !important;
    }}
    </style>
""", unsafe_allow_html=True)

# 5. LOGIN SCREEN
def show_login_page():
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown(f"""
            <div class="rst-card" style="text-align:center;">
                <div class="rst-emblem-container">
                    <div class="rst-emblem-box">
                        <div class="rst-emblem-text">RST</div>
                    </div>
                </div>
                <div class="rst-title-text">LOGIN</div>
                <p style="color:{text_secondary}; font-size:12px; margin-top:4px;">இலவச பயன்பாடு முடிந்தது! தொடர லாக் இன் செய்யவும்.</p>
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
        st.markdown(f'<div class="rst-card" style="text-align:center;"><h2 style="color:{btn_text}; margin:0;">{total_chats}</h2><p style="color:{text_secondary}; margin:0; font-size:12px;">Total Searches Logged</p></div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown(f'<div class="rst-card" style="text-align:center;"><h2 style="color:{btn_text}; margin:0;">{unique_users}</h2><p style="color:{text_secondary}; margin:0; font-size:12px;">Total Registered Users</p></div>', unsafe_allow_html=True)

    st.subheader("🔍 Search User Activity")
    search_query = st.text_input("🔎 Filter by Name, Email or Prompt Keyword:")

    st.markdown("### 📜 Permanent Chat History")
    if logs:
        for name, email, prompt, time_stamp in logs:
            if search_query.lower() in name.lower() or search_query.lower() in email.lower() or search_query.lower() in prompt.lower():
                st.markdown(f"""
                    <div class="rst-card">
                        <p style="color: {btn_text}; margin:0; font-size:13px;"><b>User:</b> {name} ({email}) | <span style="color:{text_secondary}; font-size:11px;">{time_stamp}</span></p>
                        <p style="color: {text_primary}; margin: 5px 0 0 0; font-size:14px;"><b>Prompt:</b> {prompt}</p>
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
    # PERFECT ALIGNED TOP HEADER BAR
    top_col_admin, top_col_spacer, top_col_theme, top_col_user = st.columns([1.2, 3, 1.5, 2.3])
    
    with top_col_admin:
        st.markdown('<div class="admin-btn-col">', unsafe_allow_html=True)
        if st.button("👑 Admin"): 
            st.session_state.active_mode = "admin"
        st.markdown('</div>', unsafe_allow_html=True)

    with top_col_theme:
        theme_icon = "☀️ Light" if is_dark else "🌙 Dark"
        if st.button(f"{theme_icon} Mode"):
            st.session_state.theme = "light" if is_dark else "dark"
            st.rerun()

    with top_col_user:
        if st.session_state.user_email:
            avatar_letter = st.session_state.user_name[0].upper()
            st.markdown(f"""
                <div class="profile-box">
                    <div class="circle-avatar">{avatar_letter}</div>
                    <div style="text-align:right;">
                        <div style="color:{text_primary}; font-weight:bold; font-size:12px; line-height:1.1;">{st.session_state.user_name}</div>
                        <div style="color:{btn_text}; font-size:10px;">{st.session_state.user_email}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            left = 2 - st.session_state.usage_count
            st.markdown(f"""
                <div class="profile-box">
                    <div class="circle-avatar">G</div>
                    <div style="text-align:right;">
                        <div style="color:{text_primary}; font-weight:bold; font-size:12px; line-height:1.1;">Guest User</div>
                        <div style="color:#e11d48; font-size:10px;">{left} Uses Left</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # Main Header Emblem Banner
    st.markdown(f"""
        <div class="rst-emblem-container">
            <div class="rst-emblem-box">
                <div class="rst-emblem-text">RST</div>
            </div>
        </div>
        <div class="rst-title-text">⚡ ASSISTANT ⚡</div>
        <div class="owner-badge">
            SYSTEM ARCHITECT: <span style="color:{btn_text}; font-weight:bold;">MOHAMMED RASITH</span>
        </div>
    """, unsafe_allow_html=True)

    # CENTERED NAVIGATION BUTTONS
    c_space_l, c_btn1, c_btn2, c_space_r = st.columns([2.5, 1.5, 1.5, 2.5])
    
    with c_btn1:
        if st.button("🤖 AI Chat"): st.session_state.active_mode = "chat"
    with c_btn2:
        if st.button("🎙️ Voice Gen"): st.session_state.active_mode = "voice"

    st.markdown(f"<hr style='border: 0.5px solid {card_border}; margin: 16px 0;'>", unsafe_allow_html=True)

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
