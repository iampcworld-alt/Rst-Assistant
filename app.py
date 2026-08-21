import streamlit as st
import edge_tts
import asyncio
import urllib.parse
from PIL import Image, ImageEnhance, ImageFilter

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
    st.markdown("<h5 style='text-align: center; color: #ff0055;'>⚡ SELECT AI TOOL (கிளிக் செய்யவும்)</h5>", unsafe_allow_html=True)
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
        if st.button("🖼️ Photo Edit"):
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

            # Male Voice Output Engine
            async def speak():
                clean_text = reply.replace("*", "")
                communicate = edge_tts.Communicate(clean_text, "ta-IN-ValluvarNeural")
                await communicate.save("rst_response.mp3")

            asyncio.run(speak())
            st.audio("rst_response.mp3")

    # ---------------- 2. MODE: IMAGE GENERATOR ----------------
    elif st.session_state.active_mode == "image":
        st.subheader("🎨 RST AI Image Generator")
        img_prompt = st.text_input("Enter Image Prompt (எ.கா: A futuristic lion):")
        if st.button("Generate Image Now"):
            if img_prompt:
                with st.spinner("🖼️ Image உருவாக்கப்படுகிறது..."):
                    encoded_prompt = urllib.parse.quote(img_prompt)
                    img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
                    st.image(img_url, caption=f"Generated: {img_prompt}", use_container_width=True)
            else:
                st.warning("தயவுசெய்து விவரத்தை டைப் செய்யவும்!")

    # ---------------- 3. MODE: VIDEO GENERATOR ----------------
    elif st.session_state.active_mode == "video":
        st.subheader("🎬 RST AI Video Generator")
        vid_prompt = st.text_input("Enter Video Prompt (எ.கா: Flying car in neon city):")
        if st.button("Generate Video Now"):
            if vid_prompt:
                with st.spinner("🎬 Video உருவாக்கப்படுகிறது..."):
                    encoded_vprompt = urllib.parse.quote(vid_prompt)
                    vid_url = f"https://image.pollinations.ai/prompt/{encoded_vprompt}?model=flux&nologo=true"
                    st.video(vid_url)
            else:
                st.warning("தயவுசெய்து வீடியோ விவரத்தை டைப் செய்யவும்!")

    # ---------------- 4. MODE: VOICE GENERATOR ----------------
    elif st.session_state.active_mode == "voice":
        st.subheader("🎙️ RST Voice Generator")
        v_text = st.text_area("பேச்சாக மாற்ற வேண்டிய உரையை டைப் செய்யவும்:", "வணக்கம் நண்பா, RST ASSISTANT தளத்திற்கு வரவேற்கிறேன்.")
        if st.button("Generate Voice Now"):
            if v_text:
                with st.spinner("🎙️ Voice உருவாக்கப்படுகிறது..."):
                    async def make_custom_voice():
                        comm = edge_tts.Communicate(v_text, "ta-IN-ValluvarNeural")
                        await comm.save("custom_voice.mp3")
                    asyncio.run(make_custom_voice())
                    st.audio("custom_voice.mp3")
            else:
                st.warning("தயவுசெய்து உரையை டைப் செய்யவும்!")

    # ---------------- 5. MODE: PHOTO EDIT STUDIO ----------------
    elif st.session_state.active_mode == "edit":
        st.subheader("🖼️ RST Photo Editing Studio")
        uploaded_file = st.file_uploader("Upload an Image to Edit", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Original Image")
                st.image(image, use_container_width=True)

            b_val = st.slider("Brightness", 0.5, 2.0, 1.0)
            c_val = st.slider("Contrast", 0.5, 2.0, 1.0)
            blur_val = st.slider("Blur Effect", 0, 5, 0)
            bw = st.checkbox("Black & White")

            edited_img = image.copy()
            if bw:
                edited_img = edited_img.convert("L")
            edited_img = ImageEnhance.Brightness(edited_img).enhance(b_val)
            edited_img = ImageEnhance.Contrast(edited_img).enhance(c_val)
            if blur_val > 0:
                edited_img = edited_img.filter(ImageFilter.GaussianBlur(blur_val))

            with col2:
                st.subheader("Edited Image")
                st.image(edited_img, use_container_width=True)
