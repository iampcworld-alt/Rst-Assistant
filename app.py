import streamlit as st
import edge_tts
import asyncio
import urllib.parse
from PIL import Image

# ---------------- 1. PAGE CONFIG & GLASSMORPHISM STYLING ----------------
st.set_page_config(page_title="RST ASSISTANT", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    /* Dark Futuristic Background */
    .stApp {
        background: radial-gradient(circle at top left, #0d0e15, #030308);
        color: #00f0ff;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Glassmorphism Card Style */
    .glass-card {
        background: rgba(22, 27, 34, 0.45);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 240, 255, 0.18);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 20px;
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    .glass-card:hover {
        border-color: rgba(255, 0, 85, 0.5);
        transform: translateY(-2px);
    }

    /* Glow Text */
    .glow-title {
        color: #ffffff;
        text-shadow: 0 0 10px #00f0ff, 0 0 20px #00f0ff;
        text-align: center;
        font-weight: 800;
    }

    /* Glass Buttons with Glow Hover */
    .stButton>button {
        background: rgba(0, 240, 255, 0.05);
        backdrop-filter: blur(5px);
        color: #00f0ff;
        border: 1px solid rgba(0, 240, 255, 0.4);
        border-radius: 10px;
        padding: 10px 24px;
        font-weight: bold;
        transition: all 0.3s ease-in-out;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #ff0055, #7928ca);
        color: #ffffff;
        border: 1px solid #ff0055;
        box-shadow: 0 0 15px rgba(255, 0, 85, 0.6);
    }
    
    /* Input Fields */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background: rgba(15, 23, 42, 0.6) !important;
        color: #00f0ff !important;
        border: 1px solid rgba(0, 240, 255, 0.2) !important;
        border-radius: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- 2. SESSION STATE MANAGEMENT ----------------
if "usage_count" not in st.session_state:
    st.session_state.usage_count = 0

if "user_email" not in st.session_state:
    st.session_state.user_email = None

if "chat_history_db" not in st.session_state:
    st.session_state.chat_history_db = [] # Admin logs storage

# ---------------- 3. HEADER UI ----------------
st.markdown("<h1 class='glow-title'>⚡ RST ASSISTANT ⚡</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8b949e;'>ULTRA-FUTURISTIC AI CONTROL CENTER</p>", unsafe_allow_html=True)

# System Info Glass Card
st.markdown("""
    <div class="glass-card" style="text-align: center; max-width: 600px; margin: 0 auto 20px auto;">
        <h4 style="color: #ff0055; margin: 0;">SYSTEM INFORMATION</h4>
        <p style="margin: 5px 0; color: #ffffff;"><b>OWNER:</b> MOHAMMED RASITH | <b>VERSION:</b> 3.0 Glass-SaaS</p>
    </div>
""", unsafe_allow_html=True)

# ---------------- 4. USER AUTHENTICATION & LIMIT CHECK ----------------
def check_user_access():
    # If usage exceeds 2 and user is not logged in
    if st.session_state.usage_count >= 2 and st.session_state.user_email is None:
        st.warning("⚠️ நீங்கள் உங்கள் 2 இலவச உரையாடல்களைப் பயன்படுத்திவிட்டீர்கள்! தொடர உங்கள் Email-ஐ உள்ளிடவும்.")
        
        with st.form("login_form"):
            email_input = st.text_input("Enter your Email Address to Continue:")
            submit_login = st.form_submit_button("🔑 Login / Access Unlimited")
            
            if submit_login:
                if "@" in email_input and "." in email_input:
                    st.session_state.user_email = email_input
                    st.success(f"வரவேற்கிறோம் {email_input}! வரம்பற்ற அணுகல் வழங்கப்பட்டது.")
                    st.rerun()
                else:
                    st.error("செல்லுபடியாகும் மின்னஞ்சல் முகவரியை உள்ளிடவும்!")
        return False
    return True

# ---------------- 5. MAIN NAVIGATION ----------------
c1, c2, c3, c4, c5, c6 = st.columns(6)

if "active_mode" not in st.session_state:
    st.session_state.active_mode = "chat"

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
    if st.button("👑 Admin Panel"): st.session_state.active_mode = "admin"

st.markdown("<hr style='border: 0.5px solid rgba(0,240,255,0.1);'>", unsafe_allow_html=True)

# ---------------- 6. FEATURE MODES ----------------

# MODE: AI CHAT
if st.session_state.active_mode == "chat":
    st.subheader("🤖 RST Interactive Smart AI Chatbot")
    
    if check_user_access():
        user_input = st.chat_input("Ask RST Assistant anything...")
        if user_input:
            # Increase usage count
            st.session_state.usage_count += 1
            
            user_id = st.session_state.user_email if st.session_state.user_email else "Guest (Free Usage)"
            
            # Save to Admin History Database
            st.session_state.chat_history_db.append({
                "user": user_id,
                "prompt": user_input,
                "time": "Just now"
            })
            
            st.write(f"**You ({user_id}):** {user_input}")
            st.write("**RST Assistant:** வணக்கம்! நான் உங்களுக்கு எவ்வாறு உதவட்டும்?")

# MODE: VOICE GENERATOR
elif st.session_state.active_mode == "voice":
    st.subheader("🎙️ RST Glass Voice Generator")
    if check_user_access():
        col1, col2 = st.columns(2)
        with col1:
            voice = st.selectbox("Select Voice:", [
                "🇱🇰 Sarar (Sri Lanka Male)", 
                "🇱🇰 Saranya (Sri Lanka Female)",
                "🇮🇳 Valluvar (India Male)", 
                "🕵️‍♂️ Tamil Hacker / Cyber Voice"
            ])
        with col2:
            speed = st.selectbox("Speed:", ["Normal (1.0x)", "Fast (1.25x)", "Slow (0.8x)"])
            
        v_text = st.text_area("பேச்சாக மாற்ற வேண்டிய உரை:", "வணக்கம், RST ASSISTANT-க்கு வரவேற்கிறேன்.")
        if st.button("Generate Voice"):
            st.session_state.usage_count += 1
            st.success("குரல் வெற்றிகரமாக உருவாக்கப்பட்டது!")

# MODE: ADMIN DASHBOARD (OWNER ONLY)
elif st.session_state.active_mode == "admin":
    st.subheader("👑 Owner Admin Control & User Chat History")
    admin_pass = st.text_input("Enter Master Password to view Logs:", type="password")
    
    if admin_pass == "RSTA02EHYDR6":
        st.success("அனுமதி வழங்கப்பட்டது! அனைத்து பயனர்களின் வரலாறு கீழே:")
        
        if len(st.session_state.chat_history_db) > 0:
            for idx, log in enumerate(st.session_state.chat_history_db):
                st.markdown(f"""
                <div class="glass-card">
                    <p style="color: #ff0055; margin:0;"><b>User:</b> {log['user']}</p>
                    <p style="color: #00f0ff; margin:5px 0;"><b>Prompt:</b> {log['prompt']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("இன்னும் எந்த உரையாடல்களும் பதிவாகவில்லை.")
    elif admin_pass:
        st.error("தவறான கடவுச்சொல்!")
