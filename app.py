import streamlit as st
import edge_tts
import asyncio
import urllib.parse
from PIL import Image

# 1. Page Config & High-Level Futuristic UI Setup
st.set_page_config(page_title="RST ASSISTANT", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    /* Dark Futuristic Theme */
    .stApp { background-color: #030308; color: #00f0ff; font-family: 'Segoe UI', sans-serif; }
    h1 { color: #ff0055; text-shadow: 0 0 15px #ff0055, 0 0 25px #ff0055; text-align: center; font-weight: 800; }
    
    /* Neon Glow Quick Action Buttons */
    .stButton>button { 
        background: linear-gradient(45deg, #161b22, #0d1117); 
        color: #00f0ff; 
        border: 1px solid #00f0ff;
        border-radius: 8px; 
        font-weight: bold; 
        height: 50px;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.2);
        transition: 0.3s;
    }
    .stButton>button:hover {
        background: linear-gradient(45deg, #ff0055, #7928ca);
        color: #ffffff;
        border: 1px solid #ff0055;
        box-shadow: 0 0 20px #ff0055;
        transform: scale(1.02);
    }

    /* Compact Owner Card */
    .owner-card { 
        background: rgba(22, 27, 34, 0.8); 
        border: 1px solid #00f0ff; 
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.3);
        padding: 10px 15px; 
        border-radius: 12px; 
        margin: 10px auto 20px auto; 
        max-width: 550px;
        text-align: center;
    }

    /* RST Custom Processing Pulse Ring */
    .rst-loader-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 20px 0;
    }
    .rst-circle {
        width: 70px;
        height: 70px;
        border: 4px solid #161b22;
        border-top: 4px solid #ff0055;
        border-right: 4px solid #00f0ff;
        border-radius: 50%;
        animation: spin 1s linear infinite, glow 1.5s ease-in-out infinite alternate;
    }
    .rst-text-pulse {
        margin-top: 12px;
        font-weight: bold;
        font-size: 16px;
        color: #00f0ff;
        letter-spacing: 2px;
        animation: pulseText 1.2s infinite alternate;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    @keyframes glow {
        from { box-shadow: 0 0 5px #ff0055; }
        to { box-shadow: 0 0 20px #00f0ff; }
    }
    @keyframes pulseText {
        from { opacity: 0.4; color: #ff0055; }
        to { opacity: 1; color: #00f0ff; }
    }
    </style>
""", unsafe_allow_html=True)

# 2. Master Login Protection System
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔒 RST ASSISTANT - RESTRICTED ACCESS")
        password = st.text_input("Enter Master Password:", type="password")
        if st.button("Unlock RST System"):
            if password == "RSTA02EHYDR6":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("ACCESS DENIED: Unauthorized Identity Detected!")
        return False
    return True

if check_password():
    # Header Section
    st.title("⚡ RST ASSISTANT ⚡")
    st.markdown("<p style='text-align: center; color: #00f0ff; letter-spacing: 2px;'>HIGH-LEVEL PRIVATE AI CONTROL CENTER</p>", unsafe_allow_html=True)

    # Compact System Information
    st.markdown("""
        <div class="owner-card">
            <h4 style="color: #ff0055; margin:0 0 4px 0; letter-spacing: 1px;">SYSTEM INFORMATION</h4>
            <p style="margin:2px 0; font-size:14px; color:#ffffff;"><b>SYSTEM:</b> RST ASSISTANT | <b>OWNER:</b> MOHAMMED RASITH</p>
            <p style="margin:2px 0; font-size:12px; color: #8b949e;"><b>EMAIL:</b> [PROTECTED] | <b>PHONE:</b> [PROTECTED]</p>
        </div>
    """, unsafe_allow_html=True)

    # Active Mode State Manager
    if "active_mode" not in st.session_state:
        st.session_state.active_mode = "chat"

    # Clickable Quick Action Menu
    st.markdown("<h5 style='text-align: center; color: #ff0055;'>⚡ SELECT AI TOOL</h5>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        if st.button("🤖 AI Chat"):
            st.session_state.active_mode = "chat"
    with c2:
        if st.button("🎨 Image Gen"):
            st.session_state.active_mode = "image"
    with c3:
        if st.button("🎬 Video Gen"):
            st.session_state.active_mode = "video"
    with c4:
        if st.button("🎙️ Voice Gen"):
            st.session_state.active_mode = "voice"
    with c5:
        if st.button("🚀 AI Photo Re-Imagine"):
            st.session_state.active_mode = "edit"

    st.markdown("<hr style='border: 0.5px solid #161b22;'>", unsafe_allow_html=True)

    # ---------------- 1. MODE: CHATBOT ----------------
    if st.session_state.active_mode == "chat":
        st.subheader("🤖 RST Interactive Chatbot")
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_input = st.chat_input("Ask RST Assistant anything...")

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            query = user_input.lower()
            if any(keyword in query for keyword in ["owner", "who made", "details", "contact", "created", "rasith", "developer", "யார் உருவாக்கினா", "விவரம்"]):
                reply = """இதை உருவாக்கியவர் **MOHAMMED RASITH** (RST AI OWNER).
📧 **Email:** MOHAMMEDRASITH27@GMAIL.COM  
📞 **Phone:** 0753967528  
⚡ **System:** RST ASSISTANT Engine"""
            else:
                reply = f"வணக்கம்! நான் உங்கள் RST ASSISTANT. நீங்கள் கேட்ட செய்தி: '{user_input}'. உங்களுக்கு உதவ நான் தயாராக உள்ளேன்!"

            with st.chat_message("assistant"):
                st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

            async def speak():
                clean_text = reply.replace("*", "")
                communicate = edge_tts.Communicate(clean_text, "ta-IN-ValluvarNeural")
                await communicate.save("rst_response.mp3")

            asyncio.run(speak())
            st.audio("rst_response.mp3")

    # ---------------- 2. MODE: IMAGE GENERATOR ----------------
    elif st.session_state.active_mode == "image":
        st.subheader("🎨 RST AI Image Generator")
        img_prompt = st.text_input("Enter Image Prompt:")
        if st.button("Generate Image Now"):
            if img_prompt:
                st.markdown("""
                    <div class="rst-loader-container">
                        <div class="rst-circle"></div>
                        <div class="rst-text-pulse">⚡ RST PROCESSING IMAGE...</div>
                    </div>
                """, unsafe_allow_html=True)
                encoded_prompt = urllib.parse.quote(img_prompt)
                img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux&width=1080&height=1080&nologo=true"
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.image(img_url, caption=f"Generated: {img_prompt}", use_container_width=True)
            else:
                st.warning("தயவுசெய்து விவரத்தை டைப் செய்யவும்!")

    # ---------------- 3. MODE: VIDEO GENERATOR ----------------
    elif st.session_state.active_mode == "video":
        st.subheader("🎬 RST AI Video Generator")
        vid_prompt = st.text_input("Enter Video Prompt:")
        if st.button("Generate Video Now"):
            if vid_prompt:
                st.markdown("""
                    <div class="rst-loader-container">
                        <div class="rst-circle"></div>
                        <div class="rst-text-pulse">⚡ RST PROCESSING VIDEO...</div>
                    </div>
                """, unsafe_allow_html=True)
                encoded_vprompt = urllib.parse.quote(vid_prompt)
                vid_url = f"https://image.pollinations.ai/prompt/{encoded_vprompt}?model=flux&nologo=true"
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.video(vid_url)
            else:
                st.warning("தயவுசெய்து வீடியோ விவரத்தை டைப் செய்யவும்!")

    # ---------------- 4. MODE: VOICE GENERATOR ----------------
    elif st.session_state.active_mode == "voice":
        st.subheader("🎙️ RST Voice Generator")
        v_text = st.text_area("பேச்சாக மாற்ற வேண்டிய உரை:", "வணக்கம் நண்பா, RST ASSISTANT தளத்திற்கு வரவேற்கிறேன்.")
        if st.button("Generate Voice Now"):
            if v_text:
                st.markdown("""
                    <div class="rst-loader-container">
                        <div class="rst-circle"></div>
                        <div class="rst-text-pulse">⚡ RST GENERATING VOICE...</div>
                    </div>
                """, unsafe_allow_html=True)
                async def make_custom_voice():
                    comm = edge_tts.Communicate(v_text, "ta-IN-ValluvarNeural")
                    await comm.save("custom_voice.mp3")
                asyncio.run(make_custom_voice())
                st.audio("custom_voice.mp3")
            else:
                st.warning("தயவுசெய்து உரையை டைப் செய்யவும்!")

    # ---------------- 5. MODE: COMPACT HIGH-LEVEL AI PHOTO RE-IMAGINE ----------------
    elif st.session_state.active_mode == "edit":
        st.subheader("🚀 RST High-Level AI Photo Re-Imagine")
        
        uploaded_file = st.file_uploader("Upload Your Image", type=["jpg", "jpeg", "png"])
        edit_prompt = st.text_input("AI Prompt (எ.கா: Convert into cyberpunk style, add futuristic neon suit):")
        
        if uploaded_file is not None and st.button("✨ Transform with AI"):
            if edit_prompt:
                # Custom RST Loader Display
                st.markdown("""
                    <div class="rst-loader-container">
                        <div class="rst-circle"></div>
                        <div class="rst-text-pulse">⚡ RST AI PROCESSING YOUR IMAGE...</div>
                    </div>
                """, unsafe_allow_html=True)

                # Process Image Output Compactly
                combined_prompt = f"portrait of the person in uploaded image, {edit_prompt}, hyperrealistic, ultra detailed, 8k resolution, realistic lighting"
                encoded_prompt = urllib.parse.quote(combined_prompt)
                ai_image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux&width=1080&height=1080&nologo=true"

                # Center Column Compact View
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.image(ai_image_url, caption="RST AI Transformed Output", use_container_width=True)
            else:
                st.warning("தயவுசெய்து Prompt டைப் செய்யவும்!")
