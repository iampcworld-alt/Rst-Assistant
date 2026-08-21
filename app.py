import streamlit as st
import edge_tts
import asyncio

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

# 3. DIRECT WORKING ANIMATED BACKGROUND & CIRCLE BADGE CSS
st.markdown("""
    <style>
    /* Full Page Background Gradient Animation */
    .stApp {
        background: linear-gradient(-45deg, #05050f, #0d1b2a, #1b263b, #000814);
        background-size: 400% 400%;
        animation: gradientBg 10s ease infinite !important;
        color: #00f0ff;
    }

    @keyframes gradientBg {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Glass Container */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 240, 255, 0.3);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
    }

    /* Circle Profile Badge at Top Right */
    .profile-box {
        float: right;
        display: flex;
        align-items: center;
        gap: 12px;
        background: rgba(0, 240, 255, 0.1);
        border: 1px solid #00f0ff;
        padding: 6px 15px;
        border-radius: 50px;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.3);
    }

    .circle-avatar {
        width: 35px;
        height: 35px;
        background: linear-gradient(135deg, #ff0055, #7928ca);
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 16px;
    }

    /* Button Customization */
    .stButton>button {
        background: rgba(0, 240, 255, 0.1) !important;
        color: #00f0ff !important;
        border: 1px solid #00f0ff !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        transition: 0.3s !important;
    }

    .stButton>button:hover {
        background: #ff0055 !important;
        color: white !important;
        border-color: #ff0055 !important;
        box-shadow: 0 0 15px #ff0055 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 4. Session States
if "usage_count" not in st.session_state:
    st.session_state.usage_count = 0
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "chat_history_db" not in st.session_state:
    st.session_state.chat_history_db = []
if "active_mode" not in st.session_state:
    st.session_state.active_mode = "chat"

# 5. LOGIN PAGE
def show_login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="glass-card"><h2 style="text-align:center; color:#ff0055;">⚡ RST LOGIN</h2></div>', unsafe_allow_html=True)
        with st.form("login_form"):
            name_in = st.text_input("👤 Name:")
            email_in = st.text_input("📧 Email:")
            submit = st.form_submit_button("🚀 Submit")
            if submit:
                if name_in.strip() and "@" in email_in:
                    st.session_state.user_name = name_in.strip()
                    st.session_state.user_email = email_in.strip()
                    st.success("வெற்றி!")
                    st.rerun()
                else:
                    st.error("சரியான பெயர் மற்றும் Email உள்ளிடவும்.")

# 6. MAIN APP
if st.session_state.usage_count >= 2 and st.session_state.user_email is None:
    show_login_page()
else:
    # Top Right Profile Circle
    if st.session_state.user_email:
        avatar_letter = st.session_state.user_name[0].upper()
        st.markdown(f"""
            <div class="profile-box">
                <div class="circle-avatar">{avatar_letter}</div>
                <div>
                    <div style="color:white; font-weight:bold; font-size:13px;">{st.session_state.user_name}</div>
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
                    <div style="color:white; font-weight:bold; font-size:13px;">Guest User</div>
                    <div style="color:#ff0055; font-size:10px;">{left} Uses Left</div>
                </div>
            </div>
            <div style="clear:both;"></div>
        """, unsafe_allow_html=True)

    # Title & Owner Info
    st.markdown("<h1 style='text-align: center; color: #ff0055;'>⚡ RST ASSISTANT ⚡</h1>", unsafe_allow_html=True)
    st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 10px;">
            <b style="color:white;">SYSTEM INFORMATION</b> | 
            <b>OWNER:</b> <span style="color:#00f0ff;">MOHAMMED RASITH</span>
        </div>
    """, unsafe_allow_html=True)

    # Navigation Buttons
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

    st.markdown("<hr style='border: 0.5px solid rgba(0,240,255,0.2);'>", unsafe_allow_html=True)

    # Mode 1: AI Chat
    if st.session_state.active_mode == "chat":
        st.subheader("🤖 RST Smart Chatbot")
        
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_input = st.chat_input("Ask something...")

        if user_input:
            if st.session_state.user_email is None:
                st.session_state.usage_count += 1
                
            display_user = f"{st.session_state.user_name} ({st.session_state.user_email})" if st.session_state.user_email else "Guest"
            st.session_state.chat_history_db.append({"user": display_user, "prompt": user_input})

            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.spinner("Thinking..."):
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

    # Mode 2: Voice Gen
    elif st.session_state.active_mode == "voice":
        st.subheader("🎙️ Voice Generator")
        v_text = st.text_area("உரை சமர்ப்பிக்கவும்:", "வணக்கம்!")
        if st.button("Generate Voice"):
            if v_text:
                async def make_voice():
                    comm = edge_tts.Communicate(v_text, "ta-IN-ValluvarNeural")
                    await comm.save("voice.mp3")
                asyncio.run(make_voice())
                st.audio("voice.mp3")

    # Mode 3: Admin
    elif st.session_state.active_mode == "admin":
        st.subheader("👑 Admin Panel")
        pwd = st.text_input("Password:", type="password")
        if pwd == "RSTA02EHYDR6":
            st.write(st.session_state.chat_history_db)
