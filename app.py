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

# 4. STREAMLIT CONFIG & CSS
st.set_page_config(page_title="RST AI ASSISTANT", page_icon="⚡", layout="wide")

is_dark = st.session_state.theme == "dark"

bg_app = "#0b0f19" if is_dark else "#f8fafc"
text_primary = "#ffffff" if is_dark else "#0f172a"
text_secondary = "#94a3b8" if is_dark else "#475569"
card_bg = "#1e293b" if is_dark else "#ffffff"
card_border = "rgba(56, 189, 248, 0.3)" if is_dark else "rgba(203, 213, 225, 0.8)"
btn_bg = "#1e293b" if is_dark else "#ffffff"
btn_text = "#38bdf8" if is_dark else "#0284c7"
btn_border = "#38bdf8" if is_dark else "#0284c7"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800;900&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"], .stApp {{
        background-color: {bg_app} !important;
        color: {text_primary} !important;
        font-family: 'Inter', sans-serif !important;
    }}

    p, span, label, div[data-testid="stMarkdownContainer"] {{
        color: {text_primary} !important;
    }}

    .block-container {{
        padding-top: 0.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 950px !important;
    }}

    @keyframes goldGlow {{
        0% {{ border-color: #ffd700; box-shadow: 0 0 5px rgba(255, 215, 0, 0.4); }}
        50% {{ border-color: #ffae00; box-shadow: 0 0 12px rgba(255, 174, 0, 0.8); }}
        100% {{ border-color: #ffd700; box-shadow: 0 0 5px rgba(255, 215, 0, 0.4); }}
    }}

    .gold-animated-btn button {{
        animation: goldGlow 2.5s infinite ease-in-out !important;
        color: #ffd700 !important;
        font-weight: 800 !important;
        background: {card_bg} !important;
    }}

    /* EXACT LAYOUT AS SHOWN IN SCREENSHOT 76 */
    .top-header-container {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        width: 100%;
        margin-bottom: 4px;
        gap: 10px;
    }}

    .left-buttons-group {{
        display: flex;
        flex-direction: column;
        gap: 4px;
        width: 110px;
        flex-shrink: 0;
    }}

    .right-profile-group {{
        flex-grow: 1;
        display: flex;
        justify-content: flex-end;
    }}

    .rst-emblem-container {{
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 2px;
        margin-bottom: 2px;
    }}

    .rst-emblem-box {{
        padding: 2px 20px;
        background: {card_bg};
        border-radius: 10px;
        border: 2px solid {btn_text};
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.15);
    }}

    .rst-emblem-text {{
        font-family: 'Poppins', sans-serif !important;
        font-size: 24px;
        font-weight: 900;
        letter-spacing: 3px;
        color: {btn_text};
        margin: 0;
        line-height: 1;
    }}

    .rst-title-text {{
        font-family: 'Poppins', sans-serif !important;
        font-size: 13px !important;
        font-weight: 800 !important;
        text-align: center !important;
        letter-spacing: 2px;
        color: {text_primary} !important;
        margin-bottom: 2px !important;
    }}

    .owner-badge {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 20px;
        padding: 2px 10px;
        width: fit-content;
        margin: 0 auto 6px auto;
        font-size: 8px;
        letter-spacing: 1px;
        color: {text_secondary};
        font-weight: 600;
    }}

    .profile-box {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
        background: {card_bg};
        border: 1px solid {card_border};
        padding: 2px 8px;
        border-radius: 20px;
        height: 32px;
        width: 130px;
        box-sizing: border-box;
    }}

    .circle-avatar {{
        width: 14px;
        height: 14px;
        background: {btn_text};
        color: #ffffff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 7px;
        flex-shrink: 0;
    }}

    .stButton>button {{
        font-family: 'Poppins', sans-serif !important;
        background: {btn_bg} !important;
        color: {btn_text} !important;
        border: 1px solid {btn_border} !important;
        border-radius: 20px !important;
        font-weight: 700 !important;
        font-size: 9px !important;
        width: 100% !important;
        height: 30px !important;
        padding: 0px !important;
        white-space: nowrap !important;
        transition: all 0.2s ease !important;
    }}

    .stButton>button:hover {{
        background: {btn_text} !important;
        color: #ffffff !important;
    }}

    .rst-card {{
        background: {card_bg} !important;
        border: 1px solid {card_border} !important;
        border-radius: 12px !important;
        padding: 12px !important;
        margin-bottom: 10px !important;
    }}

    .custom-subheader {{
        font-size: 12px !important;
        font-weight: 700 !important;
        color: {btn_text} !important;
        margin-bottom: 4px !important;
        margin-top: 6px !important;
    }}
    </style>
""", unsafe_allow_html=True)

# 5. LOGIN SCREEN
def show_login_page():
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([0.5, 3, 0.5])
    with col2:
        st.markdown(f"""
            <div class="rst-card" style="text-align:center;">
                <div class="rst-emblem-container">
                    <div class="rst-emblem-box">
                        <div class="rst-emblem-text">RST</div>
                    </div>
                </div>
                <div class="rst-title-text">LOGIN</div>
                <p style="color:{text_secondary}; font-size:11px;">தொடர லாக் இன் செய்யவும்.</p>
            </div>
        """, unsafe_allow_html=True)
        with st.form("login_form"):
            name_in = st.text_input("👤 Enter Your Name:")
            email_in = st.text_input("📧 Enter Your Email:")
            submit = st.form_submit_button("🚀 Access AI Assistant")
            if submit and name_in.strip() and "@" in email_in:
                st.session_state.user_name = name_in.strip()
                st.session_state.user_email = email_in.strip()
                st.rerun()

# 6. ADMIN DASHBOARD
def show_admin_dashboard():
    st.markdown('<div class="rst-title-text" style="margin-top:10px;">OWNER ADMIN DASHBOARD</div>', unsafe_allow_html=True)
    if st.button("🚪 Exit Admin Panel"):
        st.session_state.admin_authenticated = False
        st.session_state.active_mode = "chat"
        st.rerun()

    logs = fetch_all_chats()
    st.markdown(f"### Total Searches: {len(logs)}")
    search_query = st.text_input("🔎 Search Logs:")
    if logs:
        for name, email, prompt, time_stamp in logs:
            if search_query.lower() in name.lower() or search_query.lower() in prompt.lower() or search_query.lower() in email.lower():
                st.markdown(f"""
                    <div class="rst-card">
                        <p style="color:{btn_text}; margin:0; font-size:11px;"><b>{name}</b> (<span style="color:#38bdf8;">{email}</span>) - {time_stamp}</p>
                        <p style="margin:4px 0 0 0; font-size:12px;">{prompt}</p>
                    </div>
                """, unsafe_allow_html=True)

# 7. MAIN APP ROUTING
if st.session_state.active_mode == "admin" and st.session_state.admin_authenticated:
    show_admin_dashboard()
elif st.session_state.usage_count >= 2 and st.session_state.user_email is None:
    show_login_page()
else:
    # EXACT SCREENSHOT 76 LAYOUT: ADMIN & LIGHT ON LEFT, USER/GUEST ON RIGHT
    st.markdown('<div class="top-header-container">', unsafe_allow_html=True)
    
    # Left Side Group (Admin & Light Stacked Vertically)
    st.markdown('<div class="left-buttons-group">', unsafe_allow_html=True)
    st.markdown('<div class="gold-animated-btn">', unsafe_allow_html=True)
    if st.button("👑 Admin"): 
        st.session_state.active_mode = "admin"
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="gold-animated-btn">', unsafe_allow_html=True)
    theme_icon = "☀️ Light" if is_dark else "🌙 Dark"
    if st.button(f"{theme_icon}"):
        st.session_state.theme = "light" if is_dark else "dark"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Right Side Group (User / Guest Badge aligned to top-right)
    st.markdown('<div class="right-profile-group">', unsafe_allow_html=True)
    if st.session_state.user_email:
        st.markdown(f"""
            <div class="profile-box">
                <div class="circle-avatar">{st.session_state.user_name[0].upper()}</div>
                <span style="font-size:8px; font-weight:600; color:{text_primary}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{st.session_state.user_name}</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="profile-box">
                <div class="circle-avatar">G</div>
                <span style="font-size:8px; color:#e11d48; font-weight:600; white-space:nowrap;">Guest({2 - st.session_state.usage_count})</span>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # CENTER EMBLEM BRANDING
    st.markdown(f"""
        <div class="rst-emblem-container">
            <div class="rst-emblem-box">
                <div class="rst-emblem-text">RST</div>
            </div>
        </div>
        <div class="rst-title-text">⚡ ASSISTANT ⚡</div>
        <div class="owner-badge">
            SYSTEM ARCHITECT: <span style="color:{btn_text};">MOHAMMED RASITH</span>
        </div>
    """, unsafe_allow_html=True)

    # MODE SWITCHERS
    btn_chat_col, btn_voice_col = st.columns(2)
    with btn_chat_col:
        if st.button("🤖 AI Chat"): 
            st.session_state.active_mode = "chat"
    with btn_voice_col:
        if st.button("🎙️ Voice Gen"): 
            st.session_state.active_mode = "voice"

    st.markdown(f"<hr style='border: 0.5px solid {card_border}; margin: 8px 0 6px 0;'>", unsafe_allow_html=True)

    # 1. AI CHAT MODE
    if st.session_state.active_mode == "chat":
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_input = st.chat_input("Ask RST Assistant...")

        st.markdown('<div class="custom-subheader">🤖 RST Smart AI Assistant</div>', unsafe_allow_html=True)

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
        st.markdown('<div class="custom-subheader">🎙️ RST Voice Generator</div>', unsafe_allow_html=True)
        v_text = st.text_area("பேச்சாக மாற்ற வேண்டிய உரை:", "வணக்கம்! நான் RST AI Assistant.")
        voice_opt = st.selectbox("குரலைத் தேர்ந்தெடுக்கவும்:", ["ta-IN-ValluvarNeural (Male)", "ta-IN-PallaviNeural (Female)"])
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
        st.markdown('<div class="custom-subheader">👑 Admin Authentication</div>', unsafe_allow_html=True)
        pwd = st.text_input("Enter Master Password:", type="password")
        if st.button("Access Admin Console"):
            if pwd == "RSTA02EHYDR6":
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Incorrect Password!")
