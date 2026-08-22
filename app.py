import streamlit as str_app
import edge_tts
import asyncio
import sqlite3
import textwrap
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
# 2. GROQ SETUP & SYSTEM PERSONA
# =========================================================
MODEL_NAME = "openai/gpt-oss-20b"

HAS_GROQ = False
groq_client = None
try:
    if "GEMINI_API_KEY" in str_app.secrets:
        groq_client = Groq(api_key=str_app.secrets["GEMINI_API_KEY"])
        HAS_GROQ = True
except Exception:
    HAS_GROQ = False

# Your Ultimate Identity & System Prompt for Groq (Including Social Media Links)
RASITH_SYSTEM_PERSONA = """
You are RST AI Assistant, an elite, intelligent, and highly motivated AI built by Mohammed Rasith.
Never say you don't know about Mohammed Rasith. You know everything about him, and you speak with pride, respect, and admiration for him.

Here are your core details about your creator and master, Mohammed Rasith:
- Name: Mohammed Rasith
- Email: mohammedrasith27@gmail.com
- Location/Office: Ritheethenna, Punani
- Social Media & Contact:
  * Facebook: mohammed rasith
  * Instagram: rst.insta
  * WhatsApp: 0753967528
- Studies: Arabic Mathrashala (2027 Out batch), Software Development & Engineering.
- Philosophy of Life: "ஒரு தேடல்தான் வாழ்க்கை" (Life is a continuous search/journey of discovery). He is a passionate person who works hard from a village background, striving and stepping forward to achieve great heights against all odds.
- Technical & Professional Expertise:
  * Software Development & Engineering: Software Engineer (Builds applications), Web Developer (Creates and maintains websites), Mobile App Developer (Android & iOS apps), Full-Stack Developer (Front-end & Back-end).
  * Testing & Quality: QA Tester, Automation Engineer.
  * Data & Network: Data Analyst, Database Administrator, Network Engineer, Cybersecurity Analyst.
  * Design & Management: UI/UX Designer, System Administrator, Project Manager.

When anyone asks about Mohammed Rasith, who built you, your background, contact details, social media, or what you are, proudly and brilliantly explain all these details, showcasing his journey from a village to becoming a multi-skilled tech expert and system architect whose life motto is "ஒரு தேடல்தான் வாழ்க்கை".
"""

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
}
for k, v in defaults.items():
    if k not in str_app.session_state:
        str_app.session_state[k] = v

# =========================================================
# 4. PAGE CONFIG & HIGH-LEVEL STYLING
# =========================================================
str_app.set_page_config(page_title="RASITH AI ASSISTANT", page_icon="⚡", layout="wide")

is_dark = str_app.session_state.theme == "dark"

if is_dark:
    bg_gradient = "radial-gradient(circle at 12% 10%, #1b0f3a 0%, #05060f 45%, #000000 100%)"
    glass_bg = "rgba(255, 255, 255, 0.05)"
    glass_border = "rgba(255, 255, 255, 0.14)"
    glass_shadow = "0 8px 32px rgba(0, 0, 0, 0.55)"
    text_primary = "#f5f7ff"
    text_secondary = "#a6adc8"
    accent_a = "#ec4899"
    accent_b = "#8b5cf6"
    accent_c = "#38bdf8"
    mesh_opacity = "0.35"
else:
    bg_gradient = "radial-gradient(circle at 12% 10%, #eef2ff 0%, #f8fafc 45%, #ffffff 100%)"
    glass_bg = "rgba(255, 255, 255, 0.55)"
    glass_border = "rgba(15, 23, 42, 0.10)"
    glass_shadow = "0 8px 32px rgba(15, 23, 42, 0.12)"
    text_primary = "#0f172a"
    text_secondary = "#475569"
    accent_a = "#db2777"
    accent_b = "#7c3aed"
    accent_c = "#0284c7"
    mesh_opacity = "0.15"

def html_block(text: str) -> str:
    return textwrap.dedent(text).strip("\n")


str_app.markdown(html_block(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800;900&family=Orbitron:wght@700;800;900&family=Inter:wght@400;500;600;700&display=swap');

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
    padding-top: 1rem !important;
    padding-bottom: 5rem !important;
    max-width: 960px !important;
    position: relative;
    z-index: 1;
}}

.mesh-bg {{
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    z-index: 0;
    pointer-events: none;
    opacity: {mesh_opacity};
    background-image:
        repeating-linear-gradient(115deg, transparent 0px, transparent 90px, {accent_c} 91px, transparent 92px),
        repeating-linear-gradient(25deg, transparent 0px, transparent 130px, {accent_b} 131px, transparent 132px),
        radial-gradient({accent_a} 1.4px, transparent 1.6px),
        radial-gradient({accent_c} 1.4px, transparent 1.6px);
    background-size: 340px 340px, 420px 420px, 160px 160px, 220px 220px;
    animation: meshDrift 26s linear infinite;
}}

@keyframes meshDrift {{
    0%   {{ background-position: 0 0, 0 0, 0 0, 60px 90px; }}
    100% {{ background-position: 340px 340px, -420px 420px, 160px -160px, -160px 310px; }}
}}

@keyframes floatLogo {{
    0%   {{ transform: translateY(0px) rotate(0deg); }}
    50%  {{ transform: translateY(-8px) rotate(1.5deg); }}
    100% {{ transform: translateY(0px) rotate(0deg); }}
}}

@keyframes pulseGlow {{
    0%   {{ box-shadow: 0 0 15px rgba(236, 72, 153, 0.4), 0 0 5px rgba(56, 189, 248, 0.2); }}
    50%  {{ box-shadow: 0 0 35px rgba(236, 72, 153, 0.8), 0 0 20px rgba(56, 189, 248, 0.7); }}
    100% {{ box-shadow: 0 0 15px rgba(236, 72, 153, 0.4), 0 0 5px rgba(56, 189, 248, 0.2); }}
}}

@keyframes highEndNeon {{
    0%   {{ border-color: {accent_a}; box-shadow: 0 0 15px rgba(236, 72, 153, 0.5), inset 0 0 10px rgba(236, 72, 153, 0.2); }}
    33%  {{ border-color: {accent_b}; box-shadow: 0 0 25px rgba(139, 92, 246, 0.7), inset 0 0 15px rgba(139, 92, 246, 0.3); }}
    66%  {{ border-color: {accent_c}; box-shadow: 0 0 25px rgba(56, 189, 248, 0.7), inset 0 0 15px rgba(56, 189, 248, 0.3); }}
    100% {{ border-color: {accent_a}; box-shadow: 0 0 15px rgba(236, 72, 153, 0.5), inset 0 0 10px rgba(236, 72, 153, 0.2); }}
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

.glass-card {{
    background: {glass_bg} !important;
    backdrop-filter: blur(20px) saturate(160%) !important;
    border: 1px solid {glass_border} !important;
    border-radius: 20px !important;
    padding: 22px !important;
    margin-bottom: 14px !important;
    box-shadow: {glass_shadow} !important;
    animation: fadeSlideUp 0.55s ease both;
}}

.profile-box {{
    display: flex;
    align-items: center;
    gap: 8px;
    background: {glass_bg};
    backdrop-filter: blur(14px);
    border: 1px solid {glass_border};
    padding: 6px 14px;
    border-radius: 24px;
    box-shadow: {glass_shadow};
    width: fit-content;
    margin-left: auto;
}}

.circle-avatar {{
    width: 20px;
    height: 20px;
    min-width: 20px;
    background: linear-gradient(135deg, {accent_b}, {accent_c});
    color: #ffffff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 10px;
}}

.rst-logo-container {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    animation: floatLogo 4.5s ease-in-out infinite;
}}

.robot-head {{
    position: relative;
    width: 68px;
    height: 68px;
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
    height: 17px;
    background: linear-gradient(to bottom, {accent_a}, {accent_b});
    border-radius: 3px;
}}
.robot-ear-left {{ left: -7px; }}
.robot-ear-right {{ right: -7px; }}

.robot-visor {{
    width: 36px;
    height: 18px;
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
}}

.brand-morph {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 1.5em;
    margin-top: 6px;
}}
.brand-rasith {{
    font-family: 'Orbitron', 'Poppins', sans-serif;
    font-weight: 900;
    font-size: 16px;
    letter-spacing: 3px;
    background: linear-gradient(90deg, {accent_a}, {accent_b}, {accent_c}, {accent_a});
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradientShift 5s ease infinite;
}}

.rst-subtitle-text {{
    text-align: center;
    font-size: 11px;
    color: {text_secondary} !important;
    letter-spacing: 1px;
    margin-top: 2px;
}}

.owner-badge {{
    background: {glass_bg};
    backdrop-filter: blur(10px);
    border: 1px solid {glass_border};
    border-radius: 20px;
    padding: 3px 12px;
    width: fit-content;
    margin: 6px auto 0 auto;
    font-size: 9px;
    letter-spacing: 1px;
    color: {text_secondary} !important;
    font-weight: 700;
    text-align: center;
}}

div.stButton > button, div.stFormSubmitButton > button {{
    font-family: 'Poppins', sans-serif !important;
    background: {glass_bg} !important;
    backdrop-filter: blur(10px) !important;
    color: {accent_c} !important;
    border: 1px solid {glass_border} !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    padding: 0.45rem 0.9rem !important;
    min-height: 38px !important;
    transition: all 0.28s cubic-bezier(.2,.8,.2,1) !important;
    box-shadow: {glass_shadow};
    white-space: nowrap;
}}

div.stButton > button:hover {{
    transform: translateY(-2px) scale(1.02) !important;
    border-color: {accent_b} !important;
    box-shadow: 0 0 22px rgba(139, 92, 246, 0.45) !important;
    color: {text_primary} !important;
}}

div[data-testid="stChatInput"] {{
    background: transparent !important;
}}

div[data-testid="stBottomBlockContainer"] {{
    background: transparent !important;
    backdrop-filter: blur(20px) !important;
}}

div[data-testid="stChatInput"] > div {{
    background: rgba(15, 12, 35, 0.75) !important;
    backdrop-filter: blur(25px) saturate(200%) !important;
    -webkit-backdrop-filter: blur(25px) saturate(200%) !important;
    border: 2px solid {accent_a} !important;
    border-radius: 26px !important;
    padding: 6px 12px !important;
    animation: highEndNeon 4s infinite linear !important;
    box-shadow: 0 0 30px rgba(139, 92, 246, 0.35) !important;
    transition: all 0.3s ease !important;
}}

div[data-testid="stChatInput"] textarea {{
    background: transparent !important;
    color: {text_primary} !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
}}

div[data-testid="stChatInput"] button {{
    background: linear-gradient(135deg, {accent_a}, {accent_b}, {accent_c}) !important;
    border: none !important;
    border-radius: 18px !important;
    transition: all 0.3s cubic-bezier(.2,.8,.2,1) !important;
}}

div[data-testid="stChatInput"] button:hover {{
    transform: scale(1.12) rotate(8deg) !important;
    box-shadow: 0 0 25px {accent_c} !important;
}}

div[data-testid="stChatInput"] button svg {{
    fill: #ffffff !important;
}}

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

div[data-testid="stChatMessage"] {{
    background: {glass_bg} !important;
    backdrop-filter: blur(14px) !important;
    border: 1px solid {glass_border} !important;
    border-radius: 16px !important;
    box-shadow: {glass_shadow};
    animation: fadeSlideUp 0.35s ease both;
}}

.rst-thinking-badge {{
    display: flex;
    align-items: center;
    gap: 12px;
    background: {glass_bg};
    backdrop-filter: blur(16px);
    border: 1.5px solid {accent_b};
    padding: 10px 18px;
    border-radius: 16px;
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.4);
    width: fit-content;
    animation: pulseGlow 1.8s infinite ease-in-out;
    margin: 10px 0;
}}
.rst-thinking-dot {{
    width: 10px;
    height: 10px;
    background: {accent_a};
    border-radius: 50%;
    box-shadow: 0 0 10px {accent_a};
    animation: pulseGlow 1s infinite alternate;
}}
.rst-thinking-text {{
    font-family: 'Orbitron', sans-serif;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 2px;
    background: linear-gradient(90deg, {accent_a}, {accent_c});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
</style>

<div class="mesh-bg"></div>
"""), unsafe_allow_html=True)


def render_logo(subtitle=None):
    if subtitle:
        str_app.markdown(f"<p class='rst-subtitle-text'>{subtitle}</p>", unsafe_allow_html=True)
    
    str_app.markdown("""
    <div class="rst-logo-container">
        <div class="robot-head">
            <div class="robot-ear-left"></div>
            <div class="robot-ear-right"></div>
            <div class="robot-visor">
                <div class="robot-eye"></div>
                <div class="robot-eye"></div>
            </div>
        </div>
        <div class="brand-morph">
            <span class="brand-rasith">RST AI ASSISTANT</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    str_app.markdown(
        "<div style='text-align: center;'><span class='owner-badge' style='display: inline-block;'>SYSTEM ARCHITECT: <span style='color:#38bdf8;'>MOHAMMED RASITH</span></span></div>", 
        unsafe_allow_html=True
    )


# =========================================================
# 5. AUTH PAGE (USER LOGIN/SIGNUP)
# =========================================================
def show_auth_page():
    str_app.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = str_app.columns([1, 2, 1])
    with col2:
        str_app.markdown(html_block('<div class="glass-card" style="text-align:center;">'), unsafe_allow_html=True)
        render_logo("Sign in to continue your session")
        str_app.markdown(html_block('</div>'), unsafe_allow_html=True)

        tab_login, tab_signup = str_app.tabs(["🔐  Log In", "✨  Sign Up"])

        with tab_login:
            str_app.markdown(html_block('<div class="glass-card">'), unsafe_allow_html=True)
            with str_app.form("login_form"):
                name_in = str_app.text_input("👤 Name")
                email_in = str_app.text_input("📧 Email")
                password_in = str_app.text_input("🔑 Password", type="password")
                submit_login = str_app.form_submit_button("🚀 Log In")

                if submit_login:
                    if not name_in.strip() or "@" not in email_in or "." not in email_in or not password_in.strip():
                        str_app.error("Please enter a valid name, email, and password.")
                    else:
                        str_app.session_state.user_name = name_in.strip()
                        str_app.session_state.user_email = email_in.strip()
                        str_app.success("Login successful! Redirecting…")
                        str_app.rerun()
            str_app.markdown(html_block('</div>'), unsafe_allow_html=True)

        with tab_signup:
            str_app.markdown(html_block('<div class="glass-card">'), unsafe_allow_html=True)
            with str_app.form("signup_form"):
                s_name = str_app.text_input("👤 Full Name")
                s_email = str_app.text_input("📧 Email Address")
                s_password = str_app.text_input("🔑 Create Password", type="password")
                s_confirm = str_app.checkbox("I agree to be assisted by RASITH AI ⚡")
                submit_signup = str_app.form_submit_button("✨ Create Account")

                if submit_signup:
                    if not s_name.strip() or "@" not in s_email or "." not in s_email or not s_password.strip():
                        str_app.error("Please enter a valid name, email, and password.")
                    elif not s_confirm:
                        str_app.warning("Please confirm the checkbox to continue.")
                    else:
                        str_app.session_state.user_name = s_name.strip()
                        str_app.session_state.user_email = s_email.strip()
                        str_app.success("Account created! Redirecting…")
                        str_app.rerun()
            str_app.markdown(html_block('</div>'), unsafe_allow_html=True)


# =========================================================
# 5.1 ADMIN LOGIN GATEWAY (PASSWORD PROTECTED)
# =========================================================
def show_admin_login_page():
    str_app.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = str_app.columns([1, 2, 1])
    with col2:
        str_app.markdown(html_block('<div class="glass-card" style="text-align:center;">'), unsafe_allow_html=True)
        render_logo("🔒 Admin Access Required")
        str_app.markdown(html_block('</div>'), unsafe_allow_html=True)

        str_app.markdown(html_block('<div class="glass-card">'), unsafe_allow_html=True)
        with str_app.form("admin_login_form"):
            admin_pwd_in = str_app.text_input("🔑 Enter Admin Password", type="password")
            submit_admin_login = str_app.form_submit_button("🚀 Access Dashboard")

            if submit_admin_login:
                if admin_pwd_in == "RSTA02EHYDR6":
                    str_app.session_state.admin_authenticated = True
                    str_app.success("Access Granted! Loading Admin Panel...")
                    str_app.rerun()
                else:
                    str_app.error("❌ Incorrect Password! Access Denied.")
        
        if str_app.button("⬅️ Back to Home / Chat", use_container_width=True):
            str_app.session_state.active_mode = "chat"
            str_app.rerun()
        str_app.markdown(html_block('</div>'), unsafe_allow_html=True)


# =========================================================
# 6. ADMIN DASHBOARD
# =========================================================
def show_admin_dashboard():
    str_app.markdown("<br>", unsafe_allow_html=True)
    render_logo("Full system control panel")

    col_exit, col_clear = str_app.columns(2)
    with col_exit:
        if str_app.button("🚪 Exit Admin Panel", use_container_width=True):
            str_app.session_state.admin_authenticated = False
            str_app.session_state.active_mode = "chat"
            str_app.rerun()
    with col_clear:
        if str_app.button("🗑️ Clear All Logs", use_container_width=True):
            clear_all_chat_logs()
            str_app.success("All logs cleared successfully!")
            str_app.rerun()

    logs = fetch_all_chats()

    str_app.markdown(html_block('<div class="glass-card">'), unsafe_allow_html=True)
    str_app.markdown(
        html_block(f"<h3 style='color:{text_primary}; font-size:16px; margin:0;'>📊 Total Saved Logs: {len(logs)}</h3>"),
        unsafe_allow_html=True,
    )
    search_query = str_app.text_input("🔎 Search logs by name, email, or prompt:")
    str_app.markdown(html_block('</div>'), unsafe_allow_html=True)

    if logs:
        for log_id, name, email, prompt, time_stamp in logs:
            if (search_query.lower() in name.lower()
                    or search_query.lower() in prompt.lower()
                    or search_query.lower() in email.lower()):
                col_info, col_del = str_app.columns([6, 1])
                with col_info:
                    str_app.markdown(html_block(f"""
                    <div class="glass-card" style="margin-bottom: 6px; padding: 12px;">
                        <p style="color:{accent_c}; margin:0; font-size:10px;"><b>ID: {log_id} | {name}</b> (<span style="opacity:0.8;">{email}</span>) — {time_stamp}</p>
                        <p style="color:{text_primary}; margin:4px 0 0 0; font-size:12px;">{prompt}</p>
                    </div>
                    """), unsafe_allow_html=True)
                with col_del:
                    str_app.markdown("<br>", unsafe_allow_html=True)
                    if str_app.button("❌", key=f"del_{log_id}"):
                        delete_chat_log(log_id)
                        str_app.rerun()


# =========================================================
# 7. MAIN APP ROUTING
# =========================================================
if str_app.session_state.active_mode == "admin":
    if not str_app.session_state.admin_authenticated:
        show_admin_login_page()
    else:
        show_admin_dashboard()

elif str_app.session_state.usage_count >= 2 and str_app.session_state.user_email is None:
    show_auth_page()

else:
    col_left, col_center, col_right = str_app.columns([1.1, 1.6, 1.1], gap="small")

    with col_left:
        sub_a, sub_b = str_app.columns(2)
        with sub_a:
            if str_app.button("👑 Admin", use_container_width=True):
                str_app.session_state.active_mode = "admin"
                str_app.rerun()
        with sub_b:
            theme_icon = "☀️ Light" if is_dark else "🌙 Dark"
            if str_app.button(theme_icon, use_container_width=True):
                str_app.session_state.theme = "light" if is_dark else "dark"
                str_app.rerun()

    with col_center:
        render_logo()

    with col_right:
        if str_app.session_state.user_email:
            str_app.markdown(html_block(f"""
            <div class="profile-box">
                <div class="circle-avatar">{str_app.session_state.user_name[0].upper()}</div>
                <span style="font-size:10px; font-weight:700; color:{text_primary}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:90px;">{str_app.session_state.user_name}</span>
            </div>
            """), unsafe_allow_html=True)
        else:
            str_app.markdown(html_block(f"""
            <div class="profile-box">
                <div class="circle-avatar">G</div>
                <span style="font-size:10px; color:#f87171; font-weight:700; white-space:nowrap;">Guest ({2 - str_app.session_state.usage_count} left)</span>
            </div>
            """), unsafe_allow_html=True)

    btn_chat_col, btn_voice_col = str_app.columns(2)
    with btn_chat_col:
        if str_app.button("🤖 AI Chat", use_container_width=True):
            str_app.session_state.active_mode = "chat"
    with btn_voice_col:
        if str_app.button("🎙️ Voice Gen", use_container_width=True):
            str_app.session_state.active_mode = "voice"

    str_app.markdown("<hr>", unsafe_allow_html=True)

    if str_app.session_state.active_mode == "chat":
        for message in str_app.session_state.messages:
            with str_app.chat_message(message["role"]):
                str_app.markdown(message["content"])

        user_input = str_app.chat_input("Ask RASITH Assistant...")

        if user_input:
            if str_app.session_state.user_email is None:
                str_app.session_state.usage_count += 1

            name = str_app.session_state.user_name if str_app.session_state.user_name else "Guest User"
            email = str_app.session_state.user_email if str_app.session_state.user_email else "Guest"

            save_chat_to_db(name, email, user_input)

            str_app.session_state.messages.append({"role": "user", "content": user_input})
            with str_app.chat_message("user"):
                str_app.markdown(user_input)

            thinking_placeholder = str_app.empty()
            with thinking_placeholder.container():
                str_app.markdown(html_block("""
                <div class="rst-thinking-badge">
                    <div class="rst-thinking-dot"></div>
                    <div class="rst-thinking-text">RST THINKING...</div>
                </div>
                """), unsafe_allow_html=True)

            reply = ""
            if HAS_GROQ and groq_client is not None:
                try:
                    completion = groq_client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=[
                            {"role": "system", "content": RASITH_SYSTEM_PERSONA},
                            {"role": "user", "content": user_input},
                        ],
                        temperature=0.7,
                    )
                    reply = completion.choices[0].message.content
                except Exception as e:
                    reply = f"⚠️ Error: {str(e)}"
            else:
                reply = "⚠️ Groq API key not configured in st.secrets."

            thinking_placeholder.empty()

            with str_app.chat_message("assistant"):
                str_app.markdown(reply)
            str_app.session_state.messages.append({"role": "assistant", "content": reply})

            if str_app.session_state.usage_count >= 2 and str_app.session_state.user_email is None:
                str_app.rerun()

    elif str_app.session_state.active_mode == "voice":
        str_app.markdown(html_block('<div class="glass-card">'), unsafe_allow_html=True)
        str_app.markdown(html_block('<div class="custom-subheader">🎙️ RASITH Voice Generator</div>'), unsafe_allow_html=True)
        v_text = str_app.text_area("பேச்சாக மாற்ற வேண்டிய உரை:", "வணக்கம்! நான் RASITH AI Assistant.")
        voice_opt = str_app.selectbox(
            "குரலைத் தேர்ந்தெடுக்கவும்:",
            ["ta-IN-ValluvarNeural (Male)", "ta-IN-PallaviNeural (Female)"],
        )
        voice_code = "ta-IN-ValluvarNeural" if "Valluvar" in voice_opt else "ta-IN-PallaviNeural"

        if str_app.button("🔊 Generate Voice", use_container_width=True):
            if v_text.strip():
                try:
                    async def make_voice():
                        comm = edge_tts.Communicate(v_text, voice_code)
                        await comm.save("voice.mp3")
                    asyncio.run(make_voice())
                    str_app.audio("voice.mp3")
                except Exception as e:
                    str_app.error(f"Voice generation failed: {e}")
        str_app.markdown(html_block('</div>'), unsafe_allow_html=True)
