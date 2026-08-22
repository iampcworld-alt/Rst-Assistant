import streamlit as st
import edge_tts
import asyncio
import sqlite3
import random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import time

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

# 2. REAL EMAIL OTP SENDER FUNCTION VIA GMAIL SMTP
def send_otp_email(receiver_email, otp_code):
    try:
        sender_email = st.secrets.get("EMAIL_USER", "")
        sender_password = st.secrets.get("EMAIL_PASS", "")
        
        if not sender_email or not sender_password:
            return False, "Email secrets not configured in Streamlit."

        msg = MIMEText(f"Your RST AI Assistant Verification Code is: {otp_code}\nThis code is valid for single use.")
        msg['Subject'] = "RST AI Assistant - Account Verification OTP"
        msg['From'] = sender_email
        msg['To'] = receiver_email

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        return True, "Success"
    except Exception as e:
        return False, str(e)

# 3. GEMINI SETUP
HAS_GEMINI = False
client = None
try:
    from google import genai
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
        HAS_GEMINI = True
except Exception as e:
    HAS_GEMINI = False

# 5. STREAMLIT CONFIG & HIGH UI STYLING
st.set_page_config(page_title="RST AI ASSISTANT", page_icon="⚡", layout="wide")

is_dark = st.session_state.theme == "dark"

bg_app = "#05070b" if is_dark else "#f8fafc"
text_primary = "#ffffff" if is_dark else "#0f172a"
text_secondary = "#94a3b8" if is_dark else "#475569"
card_bg = "#0f172a" if is_dark else "#ffffff"
card_border = "rgba(56, 189, 248, 0.3)" if is_dark else "rgba(203, 213, 225, 0.8)"
btn_bg = "#0f172a" if is_dark else "#ffffff"
btn_text = "#38bdf8" if is_dark else "#0284c7"
btn_border = "#38bdf8" if is_dark else "#0284c7"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800;900&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"], .stApp, div[data-testid="stAppViewContainer"], div[data-testid="stHeader"] {{
        background-color: {bg_app} !important;
        color: {text_primary} !important;
        font-family: 'Inter', sans-serif !important;
    }}

    p, span, label, h1, h2, h3, div[data-testid="stMarkdownContainer"] {{
        color: {text_primary} !important;
    }}

    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 900px !important;
        background-color: {bg_app} !important;
    }}

    @keyframes floatLogo {{
        0% {{ transform: translateY(0px); filter: drop-shadow(0 0 12px rgba(139, 92, 246, 0.5)); }}
        50% {{ transform: translateY(-6px); filter: drop-shadow(0 0 22px rgba(56, 189, 248, 0.8)); }}
        100% {{ transform: translateY(0px); filter: drop-shadow(0 0 12px rgba(139, 92, 246, 0.5)); }}
    }}

    @keyframes eyeBlink {{
        0%, 90%, 100% {{ opacity: 1; }}
        95% {{ opacity: 0.2; }}
    }}

    @keyframes goldGlow {{
        0% {{ border-color: #ffd700; box-shadow: 0 0 6px rgba(255, 215, 0, 0.5); }}
        50% {{ border-color: #ffae00; box-shadow: 0 0 14px rgba(255, 174, 0, 0.9); }}
        100% {{ border-color: #ffd700; box-shadow: 0 0 6px rgba(255, 215, 0, 0.5); }}
    }}

    .gold-animated-btn button {{
        animation: goldGlow 2.5s infinite ease-in-out !important;
        color: #ffd700 !important;
        font-weight: 800 !important;
        background: {card_bg} !important;
        width: 85px !important;
        height: 26px !important;
        font-size: 8px !important;
        border-radius: 20px !important;
    }}

    .absolute-header-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        width: 100%;
        margin-bottom: 4px;
    }}

    .left-corner-box {{
        display: flex;
        flex-direction: column;
        gap: 3px;
        align-items: flex-start;
        width: 90px;
    }}

    .right-corner-box {{
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        width: 100%;
    }}

    .rst-logo-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 2px;
        animation: floatLogo 4s ease-in-out infinite;
    }}

    .robot-head {{
        position: relative;
        width: 65px;
        height: 65px;
        border: 3px solid transparent;
        border-radius: 50%;
        background: linear-gradient({bg_app}, {bg_app}) padding-box,
                    linear-gradient(135deg, #ec4899, #8b5cf6, #38bdf8) border-box;
        display: flex;
        align-items: center;
        justify-content: center;
    }}

    .robot-ear-left, .robot-ear-right {{
        position: absolute;
        width: 6px;
        height: 16px;
        background: linear-gradient(to bottom, #ec4899, #8b5cf6);
        border-radius: 3px;
    }}
    .robot-ear-left {{ left: -6px; }}
    .robot-ear-right {{ right: -6px; }}

    .robot-visor {{
        width: 36px;
        height: 18px;
        border: 2px solid #38bdf8;
        border-radius: 9px;
        display: flex;
        align-items: center;
        justify-content: space-around;
        padding: 0 3px;
        background: rgba(56, 189, 248, 0.15);
        box-shadow: inset 0 0 8px rgba(56, 189, 248, 0.6);
    }}

    .robot-eye {{
        width: 5px;
        height: 5px;
        background: #38bdf8;
        border-radius: 50%;
        box-shadow: 0 0 8px #38bdf8;
        animation: eyeBlink 3s infinite;
    }}

    .rst-title-text {{
        font-family: 'Poppins', sans-serif !important;
        font-size: 13px !important;
        font-weight: 800 !important;
        text-align: center !important;
        letter-spacing: 3px;
        background: linear-gradient(90deg, #ec4899, #38bdf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: 6px !important;
        margin-bottom: 3px !important;
    }}

    .owner-badge {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 20px;
        padding: 2px 10px;
        width: fit-content;
        margin: 0 auto 5px auto;
        font-size: 7px;
        letter-spacing: 1px;
        color: {text_secondary};
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
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
    }}

    .custom-top-btn button {{
        font-family: 'Poppins', sans-serif !important;
        background: {btn_bg} !important;
        color: {btn_text} !important;
        border: 1px solid {btn_border} !important;
        border-radius: 20px !important;
        font-weight: 700 !important;
        font-size: 8px !important;
        width: 85px !important;
        height: 26px !important;
        padding: 0px !important;
        transition: all 0.25s ease !important;
    }}

    .custom-top-btn button:hover {{
        background: {btn_text} !important;
        color: #ffffff !important;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
    }}

    .rst-card {{
        background: {card_bg} !important;
        border: 1px solid {card_border} !important;
        border-radius: 12px !important;
        padding: 12px !important;
        margin-bottom: 10px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.25);
    }}

    .custom-subheader {{
        font-size: 11px !important;
        font-weight: 700 !important;
        color: {btn_text} !important;
        margin-bottom: 4px !important;
        margin-top: 6px !important;
    }}
    </style>
""", unsafe_allow_html=True)

# 6. LOGIN & SECURE OTP VERIFICATION WITH CENTERED ALIGNMENT
def show_login_page():
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; width: 100%;">
            <div style="width: 100%; max-width: 450px;">
                <div class="rst-card" style="text-align:center;">
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
                    <div class="rst-title-text">ACCOUNT VERIFICATION</div>
                    <p style="color:{text_secondary}; font-size:11px;">தொடர உங்கள் மின்னஞ்சலைச் சரிபார்க்கவும்.</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if not st.session_state.otp_sent:
            with st.form("details_form"):
                name_in = st.text_input("👤 Enter Your Name:")
                email_in = st.text_input("📧 Enter Your Email:")
                submit_details = st.form_submit_button("📩 Send Verification OTP")
                
                if submit_details:
                    if not name_in.strip() or "@" not in email_in or "." not in email_in:
                        st.error("சரியான பெயர் மற்றும் மின்னஞ்சலை உள்ளிடவும்!")
                    else:
                        otp = str(random.randint(100000, 999999))
                        st.session_state.generated_otp = otp
                        st.session_state.temp_name = name_in.strip()
                        st.session_state.temp_email = email_in.strip()
                        st.session_state.otp_timer = time.time() + 60  # 1 Minute Cooldown
                        
                        with st.spinner("⚡ Sending secure OTP to your email..."):
                            success, err_msg = send_otp_email(email_in.strip(), otp)
                        
                        if success:
                            st.session_state.otp_sent = True
                            st.success("OTP successfully sent to your email!")
                            st.rerun()
                        else:
                            st.error(f"Email failed: {err_msg}.")
        else:
            with st.form("otp_form"):
                st.info(f"OTP sent to: {st.session_state.temp_email}")
                entered_otp = st.text_input("🔑 Enter 6-Digit OTP Code:")
                verify_submit = st.form_submit_button("✅ Verify & Enter AI")
                
                if verify_submit:
                    if entered_otp.strip() == st.session_state.generated_otp:
                        st.session_state.user_name = st.session_state.temp_name
                        st.session_state.user_email = st.session_state.temp_email
                        st.session_state.otp_sent = False
                        st.success("Verification Successful!")
                        st.rerun()
                    else:
                        st.error("Invalid OTP Code! Please try again.")

            current_time = time.time()
            if current_time < st.session_state.otp_timer:
                remaining = int(st.session_state.otp_timer - current_time)
                st.warning(f"⏳ Resend available in {remaining} seconds...")
            else:
                if st.button("🔄 Resend OTP Code"):
                    otp = str(random.randint(100000, 999999))
                    st.session_state.generated_otp = otp
                    st.session_state.otp_timer = time.time() + 60
                    with st.spinner("Resending OTP..."):
                        success, err_msg = send_otp_email(st.session_state.temp_email, otp)
                    if success:
                        st.success("New OTP sent successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to resend email.")

# 7. ADMIN DASHBOARD WITH DELETE SYSTEM
def show_admin_dashboard():
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div class="rst-title-text" style="text-align:center;">👑 OWNER ADMIN DASHBOARD</div>', unsafe_allow_html=True)
    
    col_exit, col_clear = st.columns([1, 1])
    with col_exit:
        if st.button("🚪 Exit Admin Panel"):
            st.session_state.admin_authenticated = False
            st.session_state.active_mode = "chat"
            st.rerun()
    with col_clear:
        if st.button("🗑️ Clear All Logs"):
            clear_all_chat_logs()
            st.success("All logs cleared successfully!")
            st.rerun()

    logs = fetch_all_chats()
    st.markdown(f"<h3 style='color:{text_primary}; font-size:15px;'>Total Saved Logs: {len(logs)}</h3>", unsafe_allow_html=True)
    search_query = st.text_input("🔎 Search Logs:")
    
    if logs:
        for log_id, name, email, prompt, time_stamp in logs:
            if search_query.lower() in name.lower() or search_query.lower() in prompt.lower() or search_query.lower() in email.lower():
                col_info, col_del = st.columns([6, 1])
                with col_info:
                    st.markdown(f"""
                        <div class="rst-card" style="margin-bottom: 5px; padding: 8px;">
                            <p style="color:{btn_text}; margin:0; font-size:10px;"><b>ID: {log_id} | {name}</b> (<span style="color:#38bdf8;">{email}</span>) - {time_stamp}</p>
                            <p style="color:{text_primary}; margin:3px 0 0 0; font-size:11px;">{prompt}</p>
                        </div>
                    """, unsafe_allow_html=True)
                with col_del:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("❌", key=f"del_{log_id}"):
                        delete_chat_log(log_id)
                        st.rerun()

# 8. MAIN APP ROUTING
if st.session_state.active_mode == "admin" and st.session_state.admin_authenticated:
    show_admin_dashboard()
elif st.session_state.usage_count >= 2 and st.session_state.user_email is None:
    show_login_page()
else:
    st.markdown('<div class="absolute-header-grid">', unsafe_allow_html=True)
    
    # LEFT CORNER
    st.markdown('<div class="left-corner-box">', unsafe_allow_html=True)
    st.markdown('<div class="gold-animated-btn custom-top-btn">', unsafe_allow_html=True)
    if st.button("👑 Admin"): 
        st.session_state.active_mode = "admin"
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="gold-animated-btn custom-top-btn">', unsafe_allow_html=True)
    theme_icon = "☀️ Light" if is_dark else "🌙 Dark"
    if st.button(f"{theme_icon}"):
        st.session_state.theme = "light" if is_dark else "dark"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # RIGHT CORNER
    st.markdown('<div class="right-corner-box">', unsafe_allow_html=True)
    if st.session_state.user_email:
        st.markdown(f"""
            <div class="profile-box" style="margin-left: auto;">
                <div class="circle-avatar">{st.session_state.user_name[0].upper()}</div>
                <span style="font-size:7px; font-weight:600; color:{text_primary}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{st.session_state.user_name}</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="profile-box" style="margin-left: auto;">
                <div class="circle-avatar">G</div>
                <span style="font-size:7px; color:#e11d48; font-weight:600; white-space:nowrap;">Guest({2 - st.session_state.usage_count})</span>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # CENTER ANIMATED LOGO & BRANDING
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
        <div class="rst-title-text">RST AI CHATBOT</div>
        <div class="owner-badge">
            SYSTEM ARCHITECT: <span style="color:{btn_text};">MOHAMMED RASITH</span>
        </div>
    """, unsafe_allow_html=True)

    # MODE SWITCHERS
    btn_chat_col, btn_voice_col = st.columns(2)
    with btn_chat_col:
        st.markdown('<div class="custom-top-btn">', unsafe_allow_html=True)
        if st.button("🤖 AI Chat"): 
            st.session_state.active_mode = "chat"
        st.markdown('</div>', unsafe_allow_html=True)
    with btn_voice_col:
        st.markdown('<div class="custom-top-btn">', unsafe_allow_html=True)
        if st.button("🎙️ Voice Gen"): 
            st.session_state.active_mode = "voice"
        st.markdown('</div>', unsafe_allow_html=True)

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

            with st.status("⚡ RST AI is thinking...", expanded=False) as status:
                if HAS_GEMINI and client is not None:
                    try:
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=f"You are RST ASSISTANT built by Mohammed Rasith. Reply to: {user_input}",
                        )
                        reply = response.text
                    except Exception as e:
                        reply = f"Error: {str(e)}"
                else:
                    reply = "⚠️ Gemini API Key not configured or connection failed."
                status.update(label="✨ RST Response Ready!", state="complete", expanded=False)

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
