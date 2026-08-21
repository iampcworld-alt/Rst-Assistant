import streamlit as str_lit
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

# 2. GEMINI SETUP (USING GOOGLE-GENAI SDK & GEMINI-3.6-FLASH)
HAS_GEMINI = False
client = None

try:
    from google import genai
    if "GEMINI_API_KEY" in str_lit.secrets:
        api_key = str_lit.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
        HAS_GEMINI = True
except Exception as e:
    HAS_GEMINI = False

# 3. SESSION STATES
if "theme" not in str_lit.session_state: str_lit.session_state.theme = "dark"
if "usage_count" not in str_lit.session_state: str_lit.session_state.usage_count = 0
if "user_name" not in str_lit.session_state: str_lit.session_state.user_name = None
if "user_email" not in str_lit.session_state: str_lit.session_state.user_email = None
if "active_mode" not in str_lit.session_state: str_lit.session_state.active_mode = "chat"
if "admin_authenticated" not in str_lit.session_state: str_lit.session_state.admin_authenticated = False
if "messages" not in str_lit.session_state: str_lit.session_state.messages = []

# 4. STREAMLIT CONFIG & CSS
str_lit.set_page_config(page_title="RST AI ASSISTANT", page_icon="⚡", layout="wide")

is_dark = str_lit.session_state.theme == "dark"

bg_app = "#0b0f19" if is_dark else "#f8fafc"
text_primary = "#ffffff" if is_dark else "#0f172a"
text_secondary = "#94a3b8" if is_dark else "#475569"
card_bg = "#1e293b" if is_dark else "#ffffff"
card_border = "rgba(56, 189, 248, 0.3)" if is_dark else "rgba(203, 213, 225, 0.8)"
btn_bg = "#1e293b" if is_dark else "#ffffff"
btn_text = "#38bdf8" if is_dark else "#0284c7"
btn_border = "#38bdf8" if is_dark else "#0284c7"

str_lit.markdown(f"""
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
        padding-top: 1.5rem !important;
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
        width: 90px !important;
        height: 26px !important;
        font-size: 8px !important;
        border-radius: 20px !important;
    }}

    .absolute-header-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        width: 100%;
        margin-bottom: 5px;
    }}

    .left-corner-box {{
        display: flex;
        flex-direction: column;
        gap: 3px;
        align-items: flex-start;
        justify-content: flex-start;
        width: 90px;
    }}

    .right-corner-box {{
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        justify-content: flex-start;
        width: 100%;
    }}

    .rst-emblem-container {{
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 5px;
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
        font-size: 14px !important;
        font-weight: 800 !important;
        text-align: center !important;
        letter-spacing: 2px;
        color: {text_primary} !important;
        margin-top: 15px !important;
        margin-bottom: 10px !important;
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
        height: 26px;
        width: 105px;
        box-sizing: border-box;
    }}

    .circle-avatar {{
        width: 12px;
        height: 12px;
        background: {btn_text};
        color: #ffffff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 6px;
        flex-shrink: 0;
    }}

    .custom-top-btn button {{
        font-family: 'Poppins', sans-serif !important;
        background: {btn_bg} !important;
        color: {btn_text} !important;
        border: 1px solid {btn_border} !important;
        border-radius: 20px !important;
        font-weight: 700 !important;
        font-size: 8px !important;
        width: 90px !important;
        height: 26px !important;
        padding: 0px !important;
        transition: all 0.2s ease !important;
    }}

    .custom-top-btn button:hover {{
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
    str_lit.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = str_lit.columns([0.5, 3, 0.5])
    with col2:
        str_lit.markdown(f"""
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
        with str_lit.form("login_form"):
            name_in = str_lit.text_input("👤 Enter Your Name:")
            email_in = str_lit.text_input("📧 Enter Your Email:")
            submit = str_lit.form_submit_button("🚀 Access AI Assistant")
            if submit and name_in.strip() and "@" in email_in:
                str_lit.session_state.user_name = name_in.strip()
                str_lit.session_state.user_email = email_in.strip()
                str_lit.rerun()

# 6. ADMIN DASHBOARD
def show_admin_dashboard():
    str_lit.markdown("<br>", unsafe_allow_html=True)
    str_lit.markdown('<div class="rst-title-text">👑 OWNER ADMIN DASHBOARD</div>', unsafe_allow_html=True)
    if str_lit.button("🚪 Exit Admin Panel"):
        str_lit.session_state.admin_authenticated = False
        str_lit.session_state.active_mode = "chat"
        str_lit.rerun()

    logs = fetch_all_chats()
    str_lit.markdown(f"### Total Searches: {len(logs)}")
    search_query = str_lit.text_input("🔎 Search Logs:")
    if logs:
        for name, email, prompt, time_stamp in logs:
            if search_query.lower() in name.lower() or search_query.lower() in prompt.lower() or search_query.lower() in email.lower():
                str_lit.markdown(f"""
                    <div class="rst-card">
                        <p style="color:{btn_text}; margin:0; font-size:11px;"><b>{name}</b> (<span style="color:#38bdf8;">{email}</span>) - {time_stamp}</p>
                        <p style="margin:4px 0 0 0; font-size:12px;">{prompt}</p>
                    </div>
                """, unsafe_allow_html=True)

# 7. MAIN APP ROUTING
if str_lit.session_state.active_mode == "admin" and str_lit.session_state.admin_authenticated:
    show_admin_dashboard()
elif str_lit.session_state.usage_count >= 2 and str_lit.session_state.user_email is None:
    show_login_page()
else:
    str_lit.markdown('<div class="absolute-header-grid">', unsafe_allow_html=True)
    
    # LEFT CORNER
    str_lit.markdown('<div class="left-corner-box">', unsafe_allow_html=True)
    str_lit.markdown('<div class="gold-animated-btn custom-top-btn">', unsafe_allow_html=True)
    if str_lit.button("👑 Admin"): 
        str_lit.session_state.active_mode = "admin"
    str_lit.markdown('</div>', unsafe_allow_html=True)

    str_lit.markdown('<div class="gold-animated-btn custom-top-btn">', unsafe_allow_html=True)
    theme_icon = "☀️ Light" if is_dark else "🌙 Dark"
    if str_lit.button(f"{theme_icon}"):
        str_lit.session_state.theme = "light" if is_dark else "dark"
        str_lit.rerun()
    str_lit.markdown('</div>', unsafe_allow_html=True)
    str_lit.markdown('</div>', unsafe_allow_html=True)

    # RIGHT CORNER
    str_lit.markdown('<div class="right-corner-box">', unsafe_allow_html=True)
    if str_lit.session_state.user_email:
        str_lit.markdown(f"""
            <div class="profile-box" style="margin-left: auto;">
                <div class="circle-avatar">{str_lit.session_state.user_name[0].upper()}</div>
                <span style="font-size:7px; font-weight:600; color:{text_primary}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{str_lit.session_state.user_name}</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        str_lit.markdown(f"""
            <div class="profile-box" style="margin-left: auto;">
                <div class="circle-avatar">G</div>
                <span style="font-size:7px; color:#e11d48; font-weight:600; white-space:nowrap;">Guest({2 - str_lit.session_state.usage_count})</span>
            </div>
        """, unsafe_allow_html=True)
    str_lit.markdown('</div>', unsafe_allow_html=True)

    str_lit.markdown('</div>', unsafe_allow_html=True)

    # CENTER EMBLEM BRANDING
    str_lit.markdown(f"""
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
    btn_chat_col, btn_voice_col = str_lit.columns(2)
    with btn_chat_col:
        str_lit.markdown('<div class="custom-top-btn">', unsafe_allow_html=True)
        if str_lit.button("🤖 AI Chat"): 
            str_lit.session_state.active_mode = "chat"
        str_lit.markdown('</div>', unsafe_allow_html=True)
    with btn_voice_col:
        str_lit.markdown('<div class="custom-top-btn">', unsafe_allow_html=True)
        if str_lit.button("🎙️ Voice Gen"): 
            str_lit.session_state.active_mode = "voice"
        str_lit.markdown('</div>', unsafe_allow_html=True)

    str_lit.markdown(f"<hr style='border: 0.5px solid {card_border}; margin: 8px 0 6px 0;'>", unsafe_allow_html=True)

    # 1. AI CHAT MODE
    if str_lit.session_state.active_mode == "chat":
        for message in str_lit.session_state.messages:
            with str_lit.chat_message(message["role"]):
                str_lit.markdown(message["content"])

        user_input = str_lit.chat_input("Ask RST Assistant...")

        str_lit.markdown('<div class="custom-subheader">🤖 RST Smart AI Assistant</div>', unsafe_allow_html=True)

        if user_input:
            if str_lit.session_state.user_email is None:
                str_lit.session_state.usage_count += 1

            name = str_lit.session_state.user_name if str_lit.session_state.user_name else "Guest User"
            email = str_lit.session_state.user_email if str_lit.session_state.user_email else "Guest"

            save_chat_to_db(name, email, user_input)

            str_lit.session_state.messages.append({"role": "user", "content": user_input})
            with str_lit.chat_message("user"):
                str_lit.markdown(user_input)

            with str_lit.spinner("⚡ RST Processing..."):
                if HAS_GEMINI and client is not None:
                    try:
                        response = client.models.generate_content(
                            model="gemini-3.6-flash",
                            contents=f"You are RST ASSISTANT built by Mohammed Rasith. Reply to: {user_input}",
                        )
                        reply = response.text
                    except Exception as e:
                        reply = f"Error: {str_e}"
                else:
                    reply = "⚠️ Gemini API Key not configured or connection failed."

            with str_lit.chat_message("assistant"):
                str_lit.markdown(reply)
            str_lit.session_state.messages.append({"role": "assistant", "content": reply})

            if str_lit.session_state.usage_count >= 2 and str_lit.session_state.user_email is None:
                str_lit.rerun()

    # 2. VOICE GENERATION MODE
    elif str_lit.session_state.active_mode == "voice":
        str_lit.markdown('<div class="custom-subheader">🎙️ RST Voice Generator</div>', unsafe_allow_html=True)
        v_text = str_lit.text_area("பேச்சாக மாற்ற வேண்டிய உரை:", "வணக்கம்! நான் RST AI Assistant.")
        voice_opt = str_lit.selectbox("குரலைத் தேர்ந்தெடுக்கவும்:", ["ta-IN-ValluvarNeural (Male)", "ta-IN-PallaviNeural (Female)"])
        voice_code = "ta-IN-ValluvarNeural" if "Valluvar" in voice_opt else "ta-IN-PallaviNeural"
        
        if str_lit.button("Generate Voice"):
            if v_text:
                async def make_voice():
                    comm = edge_tts.Communicate(v_text, voice_code)
                    await comm.save("voice.mp3")
                asyncio.run(make_voice())
                str_lit.audio("voice.mp3")

    # 3. ADMIN LOGIN MODE
    elif str_lit.session_state.active_mode == "admin":
        str_lit.markdown('<div class="custom-subheader">👑 Admin Authentication</div>', unsafe_allow_html=True)
        pwd = str_lit.text_input("Enter Master Password:", type="password")
        if str_lit.button("Access Admin Console"):
            if pwd == "RSTA02EHYDR6":
                str_lit.session_state.admin_authenticated = True
                str_lit.rerun()
            else:
                str_lit.error("Incorrect Password!")
