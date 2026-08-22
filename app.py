import streamlit as st
import edge_tts
import asyncio
import sqlite3
from datetime import datetime
from groq import Groq

# =========================================================
# 1. DATABASE LAYER
# =========================================================
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
    cursor.execute(
        "INSERT INTO chat_logs (user_name, user_email, prompt, timestamp) VALUES (?, ?, ?, ?)",
        (name, email, prompt, now),
    )
    conn.commit()
    conn.close()

def fetch_all_chats():
    conn = sqlite3.connect("rst_assistant.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_name, user_email, prompt, timestamp FROM chat_logs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_chat_log(log_id):
    conn = sqlite3.connect("rst_assistant.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_logs WHERE id = ?", (log_id,))
    conn.commit()
    conn.close()

def clear_all_chat_logs():
    conn = sqlite3.connect("rst_assistant.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_logs")
    conn.commit()
    conn.close()

init_db()

# =========================================================
# 2. GROQ SETUP
# =========================================================
# NOTE ON MODEL NAME:
# Groq deprecated "llama-3.3-70b-versatile" and "llama-3.1-8b-instant" for
# free/developer tier usage. Using either of those now throws the exact
# 404 model_not_found error you were hitting. Groq's own migration guide
# points to "openai/gpt-oss-20b" as the direct replacement, so that's what
# is wired in below. If you're on an enterprise contract where the old
# Llama models are still active, just swap MODEL_NAME back.
MODEL_NAME = "openai/gpt-oss-20b"

HAS_GROQ = False
groq_client = None
try:
    if "GEMINI_API_KEY" in st.secrets:
        groq_client = Groq(api_key=st.secrets["GEMINI_API_KEY"])
        HAS_GROQ = True
except Exception:
    HAS_GROQ = False

# =========================================================
# 3. SESSION STATE
# =========================================================
defaults = {
    "theme": "dark",
    "usage_count": 0,
    "user_name": None,
    "user_email": None,
    "active_mode": "chat",
    "admin_authenticated": False,
    "messages": [],
    "auth_tab": "login",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================================================
# 4. PAGE CONFIG
# =========================================================
st.set_page_config(page_title="RST AI ASSISTANT", page_icon="⚡", layout="wide")

is_dark = st.session_state.theme == "dark"

# ---- Glassmorphism color system ----
if is_dark:
    bg_gradient = "radial-gradient(circle at 15% 15%, #1b0f3a 0%, #05060f 45%, #000000 100%)"
    glass_bg = "rgba(255, 255, 255, 0.05)"
    glass_border = "rgba(255, 255, 255, 0.14)"
    glass_shadow = "0 8px 32px rgba(0, 0, 0, 0.55)"
    text_primary = "#f5f7ff"
    text_secondary = "#a6adc8"
    accent_a = "#ec4899"
    accent_b = "#8b5cf6"
    accent_c = "#38bdf8"
    input_bg = "rgba(255,255,255,0.06)"
else:
    bg_gradient = "radial-gradient(circle at 15% 15%, #eef2ff 0%, #f8fafc 45%, #ffffff 100%)"
    glass_bg = "rgba(255, 255, 255, 0.55)"
    glass_border = "rgba(15, 23, 42, 0.10)"
    glass_shadow = "0 8px 32px rgba(15, 23, 42, 0.12)"
    text_primary = "#0f172a"
    text_secondary = "#475569"
    accent_a = "#db2777"
    accent_b = "#7c3aed"
    accent_c = "#0284c7"
    input_bg = "rgba(15,23,42,0.04)"

gradient_text = f"linear-gradient(90deg, {accent_a}, {accent_b}, {accent_c})"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');

    #MainMenu, footer, header {{ visibility: hidden; }}

    html, body, [class*="css"], .stApp {{
        background: {bg_gradient} !important;
        background-attachment: fixed !important;
        color: {text_primary} !important;
        font-family: 'Inter', sans-serif !important;
    }}

    div[data-testid="stAppViewContainer"], div[data-testid="stHeader"] {{
        background: transparent !important;
    }}

    p, span, label, h1, h2, h3, div[data-testid="stMarkdownContainer"] {{
        color: {text_primary} !important;
    }}

    .block-container {{
        padding-top: 1.2rem !important;
        padding-bottom: 3rem !important;
        max-width: 920px !important;
    }}

    /* ---------- ANIMATIONS ---------- */
    @keyframes floatLogo {{
        0%   {{ transform: translateY(0px) rotate(0deg); }}
        50%  {{ transform: translateY(-8px) rotate(1.5deg); }}
        100% {{ transform: translateY(0px) rotate(0deg); }}
    }}

    @keyframes pulseGlow {{
        0%   {{ box-shadow: 0 0 12px rgba(139, 92, 246, 0.45), 0 0 0px rgba(56, 189, 248, 0.0); }}
        50%  {{ box-shadow: 0 0 30px rgba(236, 72, 153, 0.55), 0 0 14px rgba(56, 189, 248, 0.5); }}
        100% {{ box-shadow: 0 0 12px rgba(139, 92, 246, 0.45), 0 0 0px rgba(56, 189, 248, 0.0); }}
    }}

    @keyframes eyeBlink {{
        0%, 88%, 100% {{ opacity: 1; }}
        94% {{ opacity: 0.15; }}
    }}

    @keyframes gradientShift {{
        0%   {{ background-position: 0% 50%; }}
        50%  {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}

    @keyframes fadeSlideUp {{
        0%   {{ opacity: 0; transform: translateY(14px); }}
        100% {{ opacity: 1; transform: translateY(0px); }}
    }}

    @keyframes borderGlow {{
        0%   {{ border-color: rgba(236, 72, 153, 0.55); }}
        33%  {{ border-color: rgba(139, 92, 246, 0.55); }}
        66%  {{ border-color: rgba(56, 189, 248, 0.55); }}
        100% {{ border-color: rgba(236, 72, 153, 0.55); }}
    }}

    /* ---------- GLASS CARD ---------- */
    .glass-card {{
        background: {glass_bg} !important;
        backdrop-filter: blur(16px) saturate(160%) !important;
        -webkit-backdrop-filter: blur(16px) saturate(160%) !important;
        border: 1px solid {glass_border} !important;
        border-radius: 20px !important;
        padding: 22px !important;
        margin-bottom: 14px !important;
        box-shadow: {glass_shadow} !important;
        animation: fadeSlideUp 0.55s ease both;
    }}

    .glass-card-glow {{
        animation: fadeSlideUp 0.55s ease both, borderGlow 6s linear infinite;
    }}

    /* ---------- LOGO ---------- */
    .rst-logo-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 4px;
        animation: floatLogo 4.5s ease-in-out infinite;
    }}

    .robot-head {{
        position: relative;
        width: 72px;
        height: 72px;
        border: 3px solid transparent;
        border-radius: 50%;
        background: linear-gradient({glass_bg}, {glass_bg}) padding-box,
                    linear-gradient(135deg, {accent_a}, {accent_b}, {accent_c}) border-box;
        display: flex;
        align-items: center;
        justify-content: center;
        backdrop-filter: blur(10px);
        animation: pulseGlow 3.2s ease-in-out infinite;
    }}

    .robot-ear-left, .robot-ear-right {{
        position: absolute;
        width: 6px;
        height: 18px;
        background: linear-gradient(to bottom, {accent_a}, {accent_b});
        border-radius: 3px;
    }}
    .robot-ear-left {{ left: -7px; }}
    .robot-ear-right {{ right: -7px; }}

    .robot-visor {{
        width: 38px;
        height: 19px;
        border: 2px solid {accent_c};
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: space-around;
        padding: 0 3px;
        background: rgba(56, 189, 248, 0.15);
        box-shadow: inset 0 0 10px rgba(56, 189, 248, 0.6);
    }}

    .robot-eye {{
        width: 5px;
        height: 5px;
        background: {accent_c};
        border-radius: 50%;
        box-shadow: 0 0 8px {accent_c};
        animation: eyeBlink 3s infinite;
    }}

    .rst-title-text {{
        font-family: 'Poppins', sans-serif !important;
        font-size: 15px !important;
        font-weight: 900 !important;
        text-align: center !important;
        letter-spacing: 3.5px;
        background: linear-gradient(90deg, {accent_a}, {accent_b}, {accent_c}, {accent_a});
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradientShift 5s ease infinite;
        margin-top: 8px !important;
        margin-bottom: 4px !important;
    }}

    .rst-subtitle-text {{
        text-align: center;
        font-size: 11px;
        color: {text_secondary} !important;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }}

    .owner-badge {{
        background: {glass_bg};
        backdrop-filter: blur(10px);
        border: 1px solid {glass_border};
        border-radius: 20px;
        padding: 3px 12px;
        width: fit-content;
        margin: 0 auto 6px auto;
        font-size: 7px;
        letter-spacing: 1px;
        color: {text_secondary} !important;
        font-weight: 700;
    }}

    /* ---------- HEADER CORNERS ---------- */
    .absolute-header-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        width: 100%;
        margin-bottom: 6px;
        align-items: flex-start;
    }}
    .left-corner-box {{ display: flex; gap: 6px; align-items: flex-start; }}
    .right-corner-box {{ display: flex; flex-direction: column; align-items: flex-end; width: 100%; }}

    .profile-box {{
        display: flex;
        align-items: center;
        gap: 6px;
        background: {glass_bg};
        backdrop-filter: blur(12px);
        border: 1px solid {glass_border};
        padding: 4px 12px;
        border-radius: 22px;
        box-shadow: {glass_shadow};
    }}

    .circle-avatar {{
        width: 16px;
        height: 16px;
        background: linear-gradient(135deg, {accent_b}, {accent_c});
        color: #ffffff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 8px;
    }}

    /* ---------- BUTTONS ---------- */
    div.stButton > button, div.stFormSubmitButton > button {{
        font-family: 'Poppins', sans-serif !important;
        background: {glass_bg} !important;
        backdrop-filter: blur(10px) !important;
        color: {accent_c} !important;
        border: 1px solid {glass_border} !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        transition: all 0.28s cubic-bezier(.2,.8,.2,1) !important;
        box-shadow: {glass_shadow};
    }}

    div.stButton > button:hover, div.stFormSubmitButton > button:hover {{
        transform: translateY(-2px) scale(1.02) !important;
        border-color: {accent_b} !important;
        box-shadow: 0 0 22px rgba(139, 92, 246, 0.45) !important;
        color: {text_primary} !important;
    }}

    .custom-top-btn button {{
        font-size: 9px !important;
        height: 30px !important;
        border-radius: 20px !important;
        padding: 0 14px !important;
    }}

    .gold-btn button {{
        border: 1px solid rgba(255, 215, 0, 0.55) !important;
        color: #ffd166 !important;
        animation: pulseGlow 2.6s infinite ease-in-out;
    }}

    .google-btn button {{
        width: 100% !important;
        height: 46px !important;
        font-size: 14px !important;
        border-radius: 14px !important;
        background: linear-gradient(90deg, rgba(236,72,153,0.16), rgba(139,92,246,0.16), rgba(56,189,248,0.16)) !important;
        border: 1px solid {glass_border} !important;
        letter-spacing: 0.4px;
    }}
    .google-btn button:hover {{
        box-shadow: 0 0 28px rgba(56, 189, 248, 0.45) !important;
    }}

    /* ---------- INPUTS ---------- */
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-baseweb="select"] > div {{
        background: {input_bg} !important;
        border: 1px solid {glass_border} !important;
        border-radius: 12px !important;
        color: {text_primary} !important;
    }}

    /* ---------- TABS (login/signup) ---------- */
    .auth-tab-row {{ display: flex; gap: 8px; margin-bottom: 14px; }}

    .custom-subheader {{
        font-size: 12px !important;
        font-weight: 800 !important;
        letter-spacing: 1px;
        color: {accent_c} !important;
        margin-bottom: 6px !important;
        margin-top: 8px !important;
        text-transform: uppercase;
    }}

    hr {{ border: 0.5px solid {glass_border} !important; }}

    /* Chat bubbles */
    div[data-testid="stChatMessage"] {{
        background: {glass_bg} !important;
        backdrop-filter: blur(14px) !important;
        border: 1px solid {glass_border} !important;
        border-radius: 16px !important;
        box-shadow: {glass_shadow};
        animation: fadeSlideUp 0.35s ease both;
    }}
    </style>
""", unsafe_allow_html=True)


def render_logo(title="RST AI CHATBOT", subtitle=None):
    st.markdown(f"""
        <div class="rst-logo-container">
            <div class="robot-head">
                <div class="robot-ear-left"></div>
                <div class="robot-ear-right"></div>
                <div class="robot-visor">
                    <div class="robot-eye"></div>
                    <div class="robot-eye"></div>
                </div>
            </div>
        </div>
        <div class="rst-title-text">{title}</div>
        {f'<div class="rst-subtitle-text">{subtitle}</div>' if subtitle else ''}
    """, unsafe_allow_html=True)


# =========================================================
# 5. AUTH PAGE (Login / Signup, glassmorphism modal-style)
# =========================================================
def show_auth_page():
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="glass-card glass-card-glow" style="text-align:center;">', unsafe_allow_html=True)
        render_logo("RST AI ACCESS", "Sign in to continue your session")
        st.markdown('<div class="owner-badge">SECURE • ENCRYPTED • RST NETWORK</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        tab_login, tab_signup = st.tabs(["🔐  Log In", "✨  Sign Up"])

        with tab_login:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="google-btn">', unsafe_allow_html=True)
            if st.button("🔵 Continue with Google", key="google_login_btn"):
                st.session_state.auth_tab = "google_pending_login"
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown(f"<p style='text-align:center;color:{text_secondary};font-size:11px;margin:10px 0;'>— or continue with email —</p>", unsafe_allow_html=True)

            with st.form("login_form"):
                name_in = st.text_input("👤 Name")
                email_in = st.text_input("📧 Email")
                submit_login = st.form_submit_button("🚀 Log In")

                if submit_login:
                    if not name_in.strip() or "@" not in email_in or "." not in email_in:
                        st.error("Please enter a valid name and email address.")
                    else:
                        st.session_state.user_name = name_in.strip()
                        st.session_state.user_email = email_in.strip()
                        st.success("Login successful! Redirecting…")
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with tab_signup:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="google-btn">', unsafe_allow_html=True)
            if st.button("🔵 Sign Up with Google", key="google_signup_btn"):
                st.session_state.auth_tab = "google_pending_signup"
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown(f"<p style='text-align:center;color:{text_secondary};font-size:11px;margin:10px 0;'>— or sign up with email —</p>", unsafe_allow_html=True)

            with st.form("signup_form"):
                s_name = st.text_input("👤 Full Name")
                s_email = st.text_input("📧 Email Address")
                s_confirm = st.checkbox("I agree to be assisted by a sentient robot ⚡")
                submit_signup = st.form_submit_button("✨ Create Account")

                if submit_signup:
                    if not s_name.strip() or "@" not in s_email or "." not in s_email:
                        st.error("Please enter a valid name and email address.")
                    elif not s_confirm:
                        st.warning("Please confirm the checkbox to continue.")
                    else:
                        st.session_state.user_name = s_name.strip()
                        st.session_state.user_email = s_email.strip()
                        st.success("Account created! Redirecting…")
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 6. ADMIN DASHBOARD
# =========================================================
def show_admin_dashboard():
    st.markdown("<br>", unsafe_allow_html=True)
    render_logo("OWNER DASHBOARD", "Full system control panel")

    col_exit, col_clear = st.columns(2)
    with col_exit:
        if st.button("🚪 Exit Admin Panel", use_container_width=True):
            st.session_state.admin_authenticated = False
            st.session_state.active_mode = "chat"
            st.rerun()
    with col_clear:
        if st.button("🗑️ Clear All Logs", use_container_width=True):
            clear_all_chat_logs()
            st.success("All logs cleared successfully!")
            st.rerun()

    logs = fetch_all_chats()

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown(f"<h3 style='color:{text_primary}; font-size:16px; margin:0;'>📊 Total Saved Logs: {len(logs)}</h3>", unsafe_allow_html=True)
    search_query = st.text_input("🔎 Search logs by name, email, or prompt:")
    st.markdown('</div>', unsafe_allow_html=True)

    if logs:
        for log_id, name, email, prompt, time_stamp in logs:
            if (search_query.lower() in name.lower()
                    or search_query.lower() in prompt.lower()
                    or search_query.lower() in email.lower()):
                col_info, col_del = st.columns([6, 1])
                with col_info:
                    st.markdown(f"""
                        <div class="glass-card" style="margin-bottom: 6px; padding: 12px;">
                            <p style="color:{accent_c}; margin:0; font-size:10px;"><b>ID: {log_id} | {name}</b> (<span style="opacity:0.8;">{email}</span>) — {time_stamp}</p>
                            <p style="color:{text_primary}; margin:4px 0 0 0; font-size:12px;">{prompt}</p>
                        </div>
                    """, unsafe_allow_html=True)
                with col_del:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("❌", key=f"del_{log_id}"):
                        delete_chat_log(log_id)
                        st.rerun()
    else:
        st.markdown(f"<p style='color:{text_secondary};text-align:center;'>No chat logs yet.</p>", unsafe_allow_html=True)


# =========================================================
# 7. MAIN APP ROUTING
# =========================================================
if st.session_state.active_mode == "admin" and st.session_state.admin_authenticated:
    show_admin_dashboard()

elif st.session_state.usage_count >= 2 and st.session_state.user_email is None:
    show_auth_page()

else:
    st.markdown('<div class="absolute-header-grid">', unsafe_allow_html=True)

    # LEFT CORNER
    st.markdown('<div class="left-corner-box">', unsafe_allow_html=True)
    st.markdown('<div class="gold-btn custom-top-btn">', unsafe_allow_html=True)
    if st.button("👑 Admin"):
        st.session_state.active_mode = "admin"
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="custom-top-btn">', unsafe_allow_html=True)
    theme_icon = "☀️ Light" if is_dark else "🌙 Dark"
    if st.button(theme_icon):
        st.session_state.theme = "light" if is_dark else "dark"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # RIGHT CORNER
    st.markdown('<div class="right-corner-box">', unsafe_allow_html=True)
    if st.session_state.user_email:
        st.markdown(f"""
            <div class="profile-box">
                <div class="circle-avatar">{st.session_state.user_name[0].upper()}</div>
                <span style="font-size:9px; font-weight:700; color:{text_primary}; white-space:nowrap;">{st.session_state.user_name}</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="profile-box">
                <div class="circle-avatar">G</div>
                <span style="font-size:9px; color:#f87171; font-weight:700; white-space:nowrap;">Guest ({2 - st.session_state.usage_count} left)</span>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # CENTER BRANDING
    render_logo("RST AI CHATBOT", "Your futuristic assistant, always online")
    st.markdown(f"""
        <div class="owner-badge" style="margin-top:2px;">
            SYSTEM ARCHITECT: <span style="color:{accent_c};">MOHAMMED RASITH</span>
        </div>
    """, unsafe_allow_html=True)

    # MODE SWITCHERS
    btn_chat_col, btn_voice_col = st.columns(2)
    with btn_chat_col:
        st.markdown('<div class="custom-top-btn">', unsafe_allow_html=True)
        if st.button("🤖 AI Chat", use_container_width=True):
            st.session_state.active_mode = "chat"
        st.markdown('</div>', unsafe_allow_html=True)
    with btn_voice_col:
        st.markdown('<div class="custom-top-btn">', unsafe_allow_html=True)
        if st.button("🎙️ Voice Gen", use_container_width=True):
            st.session_state.active_mode = "voice"
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ---------------- 1. AI CHAT MODE ----------------
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

            with st.status("⚡ RST AI is thinking...", expanded=False) as status:
                if HAS_GROQ and groq_client is not None:
                    try:
                        completion = groq_client.chat.completions.create(
                            model=MODEL_NAME,
                            messages=[
                                {"role": "system", "content": "You are RST ASSISTANT built by Mohammed Rasith."},
                                {"role": "user", "content": user_input},
                            ],
                            temperature=0.7,
                        )
                        reply = completion.choices[0].message.content
                        status.update(label="✨ RST Response Ready!", state="complete", expanded=False)
                    except Exception as e:
                        err_text = str(e)
                        if "model_not_found" in err_text or "does not exist" in err_text:
                            reply = (
                                "⚠️ The configured Groq model is unavailable "
                                "(it may have been deprecated or renamed). "
                                "Please update `MODEL_NAME` in app.py to a currently "
                                "active model from the Groq console."
                            )
                        elif "authentication" in err_text.lower() or "api key" in err_text.lower():
                            reply = "⚠️ Groq authentication failed. Please check that your API key in `st.secrets` is a valid Groq key."
                        elif "rate limit" in err_text.lower():
                            reply = "⚠️ Groq rate limit reached. Please wait a moment and try again."
                        else:
                            reply = f"⚠️ Something went wrong talking to Groq: {err_text}"
                        status.update(label="⚠️ Error occurred", state="error", expanded=False)
                else:
                    reply = "⚠️ Groq API key not configured. Please add it to `st.secrets`."
                    status.update(label="⚠️ Not configured", state="error", expanded=False)

            with st.chat_message("assistant"):
                st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

            if st.session_state.usage_count >= 2 and st.session_state.user_email is None:
                st.rerun()

    # ---------------- 2. VOICE GENERATION MODE ----------------
    elif st.session_state.active_mode == "voice":
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="custom-subheader">🎙️ RST Voice Generator</div>', unsafe_allow_html=True)
        v_text = st.text_area("பேச்சாக மாற்ற வேண்டிய உரை:", "வணக்கம்! நான் RST AI Assistant.")
        voice_opt = st.selectbox(
            "குரலைத் தேர்ந்தெடுக்கவும்:",
            ["ta-IN-ValluvarNeural (Male)", "ta-IN-PallaviNeural (Female)"],
        )
        voice_code = "ta-IN-ValluvarNeural" if "Valluvar" in voice_opt else "ta-IN-PallaviNeural"

        if st.button("🔊 Generate Voice", use_container_width=True):
            if v_text.strip():
                try:
                    async def make_voice():
                        comm = edge_tts.Communicate(v_text, voice_code)
                        await comm.save("voice.mp3")
                    asyncio.run(make_voice())
                    st.audio("voice.mp3")
                except Exception as e:
                    st.error(f"Voice generation failed: {str(e)}")
            else:
                st.warning("Please enter some text first.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- 3. ADMIN LOGIN MODE ----------------
    elif st.session_state.active_mode == "admin":
        st.markdown('<div class="glass-card" style="max-width:420px;margin:0 auto;">', unsafe_allow_html=True)
        st.markdown('<div class="custom-subheader">👑 Admin Authentication</div>', unsafe_allow_html=True)
        pwd = st.text_input("Enter Master Password:", type="password")
        if st.button("🔓 Access Admin Console", use_container_width=True):
            if pwd == "RSTA02EHYDR6":
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Incorrect Password!")
        st.markdown('</div>', unsafe_allow_html=True)
