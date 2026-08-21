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

# 3. HIGH-KICK ULTRA-TRANSPARENT NEON UI & ANIMATION CSS
st.markdown("""
    <style>
    /* Glowing Animated Cyber Background */
    .stApp {
        background: radial-gradient(circle at 20% 20%, rgba(255, 0, 85, 0.15), transparent 40%),
                    radial-gradient(circle at 80% 80%, rgba(0, 240, 255, 0.15), transparent 40%),
                    linear-gradient(135deg, #030008, #0a0518, #020d1a);
        background-size: 200% 200%;
        animation: cyberGlow 12s ease infinite !important;
        color: #00f0ff;
    }

    @keyframes cyberGlow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Ultra Transparent Glass Box */
    .glass-card {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(20px) saturate(200%) !important;
        -webkit-backdrop-filter: blur(20px) saturate(200%) !important;
        border: 1px solid rgba(0, 240, 255, 0.25) !important;
        border-radius: 20px !important;
        padding: 20px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6), 
                    inset 0 0 15px rgba(0, 240, 255, 0.1) !important;
    }

    /* Top-Right Glowing Circle Profile Badge */
    .profile-box {
        float: right;
        display: flex;
        align-items: center;
        gap: 12px;
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(0, 240, 255, 0.5);
        padding: 6px 18px 6px 8px;
        border-radius: 40px;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.3);
    }

    .circle-avatar {
        width: 38px;
        height: 38px;
        background: linear-gradient(135deg, #ff0055, #7928ca);
        color: #ffffff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 17px;
        box-shadow: 0 0 12px #ff0055;
    }

    /* Neon Glass Buttons */
    .stButton>button {
        background: rgba(0, 240, 255, 0.05) !important;
        backdrop-filter: blur(10px) !important;
        color: #00f0ff !important;
        border: 1px solid rgba(0, 240, 255, 0.4) !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        padding: 10px 20px !important;
        transition: all 0.3s ease-in-out !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4) !important;
    }

    .stButton>button:hover {
        background: linear-gradient(135deg, #ff0055, #7928ca) !important;
        color: #ffffff !important;
        border-color: #ff0055 !important;
        box-shadow: 0 0 25px rgba(255, 0, 85, 0.9) !important;
        transform: translateY(-3px) scale(1.02) !important;
    }

    /* Transparent Input Fields */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background: rgba(0, 0, 0, 0.5) !important;
        color: #00f0ff !important;
        border: 1px solid rgba(0, 240, 255, 0.3) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px) !important;
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
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

# 5. LOGIN SCREEN
def show_login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('''
            <div class="glass-card" style="text-align:center;">
                <h1 style="color:#ff0055; text-shadow:0 0 15px #ff0055; margin-bottom:5px;">⚡ RST LOGIN</h1>
                <p style="color:#8b949e; font-size:13px;">இலவச பயன்பாடு முடிந்தது! தொடர லாக் இன் செய்யவும்.</p>
            </div>
        ''', unsafe_allow_html=True)
        with st.form("login_form"):
            name_in = st.text_input("👤 Enter Your Name:")
            email_in = st.text_input("📧 Enter Your Email:")
            submit = st.form_submit_button("🚀 Unlock Unlimited Access")
            if submit:
                if name_in.strip() and "@" in email_in:
                    st.session_state.user_name = name_in.strip()
                    st.session_state.user_email = email_in.strip()
                    st.success("✅ லாக் இன் வெற்றி!")
                    st.rerun()
                else:
                    st.error("❌ சரியான பெயர் மற்றும் Email உள்ளிடவும்.")

# 6. SEPARATE DEDICATED ADMIN DASHBOARD
def show_admin_dashboard():
    st.markdown("<h1 style='text-align: center; color: #ff0055; text-shadow: 0 0 25px #ff0055;'>👑 OWNER ADMIN DASHBOARD</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #00f0ff;'>RST Assistant System Control & User Activity Center</p>", unsafe_allow_html=True)
    
    col_exit, col_clear = st.columns([1, 5])
    with col_exit:
        if st.button("🚪 Exit Admin Panel"):
            st.session_state.admin_authenticated = False
            st.session_state.active_mode = "chat"
            st.rerun()
            
    st.markdown("<hr style='border: 0.5px solid rgba(0,240,255,0.2); margin: 15px 0;'>", unsafe_allow_html=True)

    # Analytics Cards
    total_chats = len(st.session_state.chat_history_db)
    unique_users = len(set([log['user'] for log in st.session_state.chat_history_db])) if total_chats > 0 else 0

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f'''
            <div class="glass-card" style="text-align:center; padding:15px !important;">
                <h3 style="color:#00f0ff; margin:0;">{total_chats}</h3>
                <p style="color:#ffffff; margin:0; font-size:12px;">Total Chat Prompts</p>
            </div>
        ''', unsafe_allow_html=True)
    with m2:
        st.markdown(f'''
            <div class="glass-card" style="text-align:center; padding:15px !important;">
                <h3 style="color:#ff0055; margin:0;">{unique_users}</h3>
                <p style="color:#ffffff; margin:0; font-size:12px;">Active Users Registered</p>
            </div>
        ''', unsafe_allow_html=True)
    with m3:
        st.markdown('''
            <div class="glass-card" style="text-align:center; padding:15px !important;">
                <h3 style="color:#00ff88; margin:0;">ONLINE</h3>
                <p style="color:#ffffff; margin:0; font-size:12px;">System Status</p>
            </div>
        ''', unsafe_allow_html=True)

    st.subheader("📊 Live User Prompts Log")
    if st.session_state.chat_history_db:
        for idx, log in enumerate(reversed(st.session_state.chat_history_db)):
            st.markdown(f"""
                <div class="glass-card" style="padding: 12px 20px !important;">
                    <p style="color: #ff0055; margin: 0; font-size: 13px;"><b>User Details:</b> {log['user']}</p>
                    <p style="color: #00f0ff; margin: 6px 0 0 0; font-size: 14px;"><b>Prompt Requested:</b> {log['prompt']}</p>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("இன்னும் எந்த பயனர் உரையாடல்களும் பதிவாகவில்லை.")

# 7. MAIN APPLICATION
if st.session_state.active_mode == "admin" and st.session_state.admin_authenticated:
    show_admin_dashboard()
elif st.session_state.usage_count >= 2 and st.session_state.user_email is None:
    show_login_page()
else:
    # Top-Right Transparent Circle Avatar
    if st.session_state.user_email:
        avatar_letter = st.session_state.user_name[0].upper()
        st.markdown(f"""
            <div class="profile-box">
                <div class="circle-avatar">{avatar_letter}</div>
                <div>
                    <div style="color:#ffffff; font-weight:bold; font-size:13px; line-height:1.2;">{st.session_state.user_name}</div>
                    <div style="color:#00f0ff; font-size:10px; opacity:0.8;">{st.session_state.user_email}</div>
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
                    <div style="color:#ffffff; font-weight:bold; font-size:13px; line-height:1.2;">Guest User</div>
                    <div style="color:#ff0055; font-size:10px; font-weight:bold;">{left} Free Uses Left</div>
                </div>
            </div>
            <div style="clear:both;"></div>
        """, unsafe_allow_html=True)

    # Main Header
    st.markdown("<h1 style='text-align: center; color: #ff0055; text-shadow: 0 0 25px #ff0055; font-size: 42px;'>⚡ RST ASSISTANT ⚡</h1>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 12px !important; max-width: 650px; margin: 0 auto 25px auto;">
            <span style="color:#8b949e; font-size:12px; letter-spacing:1px;">SYSTEM INFORMATION</span><br>
            <b style="color:#ffffff;">OWNER:</b> <span style="color:#00f0ff; text-shadow:0 0 8px #00f0ff;">MOHAMMED RASITH</span>
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

    st.markdown("<hr style='border: 0.5px solid rgba(0,240,255,0.2); margin: 20px 0;'>", unsafe_allow_html=True)

    # 1. AI CHAT MODE
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
                
            display_user = f"{st.session_state.user_name} ({st.session_state.user_email})" if st.session_state.user_email else "Guest User"
            st.session_state.chat_history_db.append({"user": display_user, "prompt": user_input})

            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.spinner("⚡ RST Thinking..."):
                if HAS_GEMINI and client is not None:
                    try:
                        response = client.models.generate_content(
                            model="gemini-3.6-flash",
                            contents=f"You are RST ASSISTANT built by Mohammed Rasith. Be smart, quick and concise. Reply to: {user_input}"
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

    # 2. VOICE GEN MODE
    elif st.session_state.active_mode == "voice":
        st.subheader("🎙️ RST Voice Generator")
        v_text = st.text_area("பேச்சாக மாற்ற வேண்டிய உரை:", "வணக்கம், RST ASSISTANT தளத்திற்கு வரவேற்கிறேன்.")
        if st.button("Generate Voice Now"):
            if v_text:
                if st.session_state.user_email is None:
                    st.session_state.usage_count += 1
                with st.spinner("⚡ RST Generating Voice..."):
                    async def make_voice():
                        comm = edge_tts.Communicate(v_text, "ta-IN-ValluvarNeural")
                        await comm.save("voice.mp3")
                    asyncio.run(make_voice())
                    st.audio("voice.mp3")
                if st.session_state.usage_count >= 2 and st.session_state.user_email is None:
                    st.rerun()

    # 3. ADMIN LOGIN CHECK MODE
    elif st.session_state.active_mode == "admin":
        st.subheader("👑 Master Admin Authentication")
        col_a1, col_a2, col_a3 = st.columns([1, 2, 1])
        with col_a2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            pwd = st.text_input("Enter Master Password:", type="password")
            if st.button("Access Admin Console"):
                if pwd == "RSTA02EHYDR6":
                    st.session_state.admin_authenticated = True
                    st.success("Access Granted! Loading Admin Dashboard...")
                    st.rerun()
                else:
                    st.error("Incorrect Password!")
            st.markdown('</div>', unsafe_allow_html=True)
