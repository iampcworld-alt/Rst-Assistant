import streamlit as st
import edge_tts
import asyncio
import urllib.parse
from PIL import Image

# 1. Gemini API Setup
HAS_GEMINI = False
client = None

if "GEMINI_API_KEY" in st.secrets:
    try:
        from google import genai
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        HAS_GEMINI = True
    except Exception as e:
        HAS_GEMINI = False

# 2. Page Config
st.set_page_config(page_title="RST ASSISTANT", page_icon="⚡", layout="wide")

# 3. ULTRA GLASSMORPHISM CSS
st.markdown("""
    <style>
    /* Gradient Animated Background */
    .stApp {
        background: linear-gradient(-45deg, #05050d, #0d001a, #00121e, #05050d);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        color: #00f0ff;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Glassmorphism Container */
    .glass-box {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(16px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(16px) saturate(180%) !important;
        border: 1px solid rgba(0, 240, 255, 0.25) !important;
        border-radius: 20px !important;
        padding: 25px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 240, 255, 0.2) !important;
        margin-bottom: 20px !important;
    }

    /* Shiny Glass Buttons */
    .stButton>button {
        background: rgba(0, 240, 255, 0.08) !important;
        backdrop-filter: blur(10px) !important;
        color: #00f0ff !important;
        border: 1px solid rgba(0, 240, 255, 0.5) !important;
        border-radius: 12px !important;
        padding: 10px 20px !important;
        font-weight: bold !important;
        transition: all 0.4s ease !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5) !important;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #ff0055, #7928ca) !important;
        color: #ffffff !important;
        border: 1px solid #ff0055 !important;
        box-shadow: 0 0 20px rgba(255, 0, 85, 0.8) !important;
        transform: translateY(-3px) !important;
    }

    /* Inputs Styling */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div {
        background: rgba(0, 0, 0, 0.6) !important;
        color: #00f0ff !important;
        border: 1px solid rgba(0, 240, 255, 0.3) !important;
        border-radius: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)

# 4. Session State Setup
if "usage_count" not in st.session_state:
    st.session_state.usage_count = 0

if "user_email" not in st.session_state:
    st.session_state.user_email = None

if "chat_history_db" not in st.session_state:
    st.session_state.chat_history_db = []

if "active_mode" not in st.session_state:
    st.session_state.active_mode = "chat"

# ---------------- 5. SEPARATE LOGIN SCREEN ----------------
def show_login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
        <div class="glass-box" style="max-width: 450px; margin: 0 auto; text-align: center;">
            <h1 style="color: #ff0055; margin-bottom: 5px;">⚡ RST LOGIN</h1>
            <p style="color: #8b949e; font-size: 14px;">உங்கள் Free 2 Limits முடிந்துவிட்டது! தொடர லாக் இன் செய்யவும்.</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_screen_form"):
            email_in = st.text_input("📧 Enter Your Email Address:")
            submit = st.form_submit_button("🚀 Unlock Unlimited Access")
            
            if submit:
                if "@" in email_in and "." in email_in:
                    st.session_state.user_email = email_in
                    st.success("✅ லாக் இன் வெற்றி! சிஸ்டம் அன்லாக் செய்யப்பட்டது.")
                    st.rerun()
                else:
                    st.error("❌ சரியான Email முகவரியை டைப் செய்யவும்!")

# ---------------- 6. MAIN APP INTERFACE ----------------
# Limit Exceeded Check
if st.session_state.usage_count >= 2 and st.session_state.user_email is None:
    show_login_page()
else:
    # Header Section
    st.markdown("<h1 style='text-align: center; color: #ff0055; text-shadow: 0 0 20px #ff0055;'>⚡ RST ASSISTANT ⚡</h1>", unsafe_allow_html=True)
    
    user_status = st.session_state.user_email if st.session_state.user_email else f"Free User ({2 - st.session_state.usage_count} uses left)"
    
    st.markdown(f"""
        <div class="glass-box" style="text-align: center; max-width: 650px; margin: 0 auto 20px auto; padding: 15px !important;">
            <h4 style="color: #00f0ff; margin:0;">SYSTEM INFORMATION</h4>
            <p style="margin:5px 0; color:#ffffff; font-size:14px;"><b>OWNER:</b> MOHAMMED RASITH | <b>ACCOUNT:</b> <span style="color:#ff0055;">{user_status}</span></p>
        </div>
    """, unsafe_allow_html=True)

    # Tool Navigation Buttons
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
        if st.button("🚀 Photo Re-Imagine"): st.session_state.active_mode = "edit"
    with c6:
        if st.button("👑 Admin"): st.session_state.active_mode = "admin"

    st.markdown("<hr style='border: 0.5px solid rgba(0,240,255,0.1);'>", unsafe_allow_html=True)

    # ---------------- 1. AI CHAT MODE ----------------
    if st.session_state.active_mode == "chat":
        st.subheader("🤖 RST Interactive Smart AI Chatbot")
        
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_input = st.chat_input("Ask RST Assistant anything...")

        if user_input:
            if st.session_state.user_email is None:
                st.session_state.usage_count += 1
                
            current_user = st.session_state.user_email if st.session_state.user_email else "Guest (Free Trail)"
            
            # Save to Admin History
            st.session_state.chat_history_db.append({
                "user": current_user,
                "prompt": user_input
            })

            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.spinner("⚡ RST Thinking..."):
                if HAS_GEMINI and client is not None:
                    try:
                        p_config = "You are RST ASSISTANT created by Mohammed Rasith. Be smart, intelligent, and respond in the same language as user."
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=f"{p_config}\nUser: {user_input}"
                        )
                        reply = response.text
                    except Exception as e:
                        reply = f"Error: {str(e)}"
                else:
                    reply = "வணக்கம்! நான் RST AI Assistant. உங்களுக்கு எப்படி உதவட்டும்?"

            with st.chat_message("assistant"):
                st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            
            if st.session_state.usage_count >= 2 and st.session_state.user_email is None:
                st.rerun()

    # ---------------- 2. VOICE GEN MODE ----------------
    elif st.session_state.active_mode == "voice":
        st.subheader("🎙️ RST Voice Generator")
        
        col1, col2 = st.columns(2)
        with col1:
            voice_options = {
                "🇱🇰 Sarar (Sri Lanka Male)": ("ta-LK-KumarNeural", "+0Hz"),
                "🇱🇰 Saranya (Sri Lanka Female)": ("ta-LK-SaranyaNeural", "+0Hz"),
                "🇮🇳 Valluvar (India Male)": ("ta-IN-ValluvarNeural", "+0Hz"),
                "🇮🇳 Pallavi (India Female)": ("ta-IN-PallaviNeural", "+0Hz"),
                "🕵️‍♂️ Tamil Hacker / Cyber Voice": ("ta-IN-ValluvarNeural", "-20Hz")
            }
            selected_voice_name = st.selectbox("Select Voice Style:", list(voice_options.keys()))
            selected_voice_id, default_pitch = voice_options[selected_voice_name]

        with col2:
            speed_options = {"Normal (1.0x)": "+0%", "Fast (1.25x)": "+25%", "Slow (0.8x)": "-20%"}
            selected_speed_label = st.selectbox("Select Speed:", list(speed_options.keys()))
            selected_rate = speed_options[selected_speed_label]

        v_text = st.text_area("பேச்சாக மாற்ற வேண்டிய உரை:", "வணக்கம், RST ASSISTANT தளத்திற்கு வரவேற்கிறேன்.")
        
        if st.button("Generate Voice Now"):
            if v_text:
                if st.session_state.user_email is None:
                    st.session_state.usage_count += 1
                with st.spinner("⚡ RST Generating Voice..."):
                    async def make_custom_voice():
                        comm = edge_tts.Communicate(v_text, selected_voice_id, pitch=default_pitch, rate=selected_rate)
                        await comm.save("custom_voice.mp3")
                    asyncio.run(make_custom_voice())
                    st.audio("custom_voice.mp3")
                if st.session_state.usage_count >= 2 and st.session_state.user_email is None:
                    st.rerun()

    # ---------------- 3. ADMIN PANEL MODE ----------------
    elif st.session_state.active_mode == "admin":
        st.subheader("👑 Owner Admin Control Panel")
        admin_pass = st.text_input("Master Password:", type="password")
        
        if admin_pass == "RSTA02EHYDR6":
            st.success("அனுமதி வழங்கப்பட்டது! பயனர்களின் Chat History கீழே உள்ளது:")
            if st.session_state.chat_history_db:
                for idx, log in enumerate(reversed(st.session_state.chat_history_db)):
                    st.markdown(f"""
                        <div class="glass-box" style="padding: 10px 20px !important;">
                            <p style="color: #ff0055; margin: 0;"><b>User Email/ID:</b> {log['user']}</p>
                            <p style="color: #00f0ff; margin: 5px 0 0 0;"><b>Prompt:</b> {log['prompt']}</p>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("இன்னும் எந்த உரையாடல்களும் பதிவாகவில்லை.")
