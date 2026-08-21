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
    
    /* Neon Glow Buttons */
    .stButton>button { 
        background: linear-gradient(45deg, #ff0055, #7928ca); 
        color: white; 
        border: none;
        border-radius: 8px; 
        font-weight: bold; 
        box-shadow: 0 0 10px #ff0055;
        transition: 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0 0 20px #ff0055, 0 0 30px #00f0ff;
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
    
    /* High-Contrast Clear Command Box */
    .cmd-box {
        background: #161b22;
        border: 1px solid #ff0055;
        box-shadow: 0 0 10px rgba(255, 0, 85, 0.2);
        padding: 12px 18px;
        border-radius: 10px;
        margin: 15px auto 25px auto;
        max-width: 700px;
        color: #ffffff;
        font-size: 14px;
        line-height: 1.6;
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
    st.markdown("<p style='text-align: center; color: #00f0ff; letter-spacing: 2px;'>HIGH-LEVEL PRIVATE AI COMMAND CENTER</p>", unsafe_allow_html=True)

    # Compact System Information
    st.markdown("""
        <div class="owner-card">
            <h4 style="color: #ff0055; margin:0 0 4px 0; letter-spacing: 1px;">SYSTEM INFORMATION</h4>
            <p style="margin:2px 0; font-size:14px; color:#ffffff;"><b>SYSTEM:</b> RST ASSISTANT | <b>OWNER:</b> MOHAMMED RASITH</p>
            <p style="margin:2px 0; font-size:12px; color: #8b949e;"><b>EMAIL:</b> [PROTECTED] | <b>PHONE:</b> [PROTECTED]</p>
        </div>
    """, unsafe_allow_html=True)

    # Clear Command Guide Box
    st.markdown("""
        <div class="cmd-box">
            <b style="color: #ff0055; font-size: 15px;">⚡ SMART COMMAND GUIDE:</b><br>
            • <b style="color: #00f0ff;">Image Generate:</b> <code style="color:#ff0055;">/image [Prompt]</code> (எ.கா: /image a futuristic lion)<br>
            • <b style="color: #00f0ff;">Video Generate:</b> <code style="color:#ff0055;">/video [Prompt]</code> (எ.கா: /video flying car in night city)<br>
            • <b style="color: #00f0ff;">Voice Generate:</b> <code style="color:#ff0055;">/voice [Text]</code> (எ.கா: /voice வணக்கம் நண்பா)<br>
            • <b style="color: #00f0ff;">Normal Chat:</b> எந்தக் கேள்வியையும் நேரடியாக டைப் செய்யவும்.
        </div>
    """, unsafe_allow_html=True)

    # Main Chat & History Manager
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["type"] == "text":
                st.markdown(message["content"])
            elif message["type"] == "image":
                st.image(message["content"], caption=message.get("caption", ""))
            elif message["type"] == "video":
                st.video(message["content"])
            elif message["type"] == "audio":
                st.audio(message["content"])

    # Unified Search Input Bar
    user_input = st.chat_input("Enter command (/image, /video, /voice) or ask anything...")

    if user_input:
        # Display User Input
        st.session_state.messages.append({"role": "user", "type": "text", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # ---------------- 1. COMMAND: IMAGE GENERATION ----------------
        if user_input.startswith("/image"):
            prompt = user_input.replace("/image", "").strip()
            if prompt:
                with st.chat_message("assistant"):
                    with st.spinner("🖼️ AI Image உருவாக்குகிறது..."):
                        encoded_prompt = urllib.parse.quote(prompt)
                        img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
                        st.image(img_url, caption=f"Generated Image: {prompt}")
                        st.session_state.messages.append({"role": "assistant", "type": "image", "content": img_url, "caption": f"Generated: {prompt}"})
            else:
                reply = "⚠️ படத்தின் விவரத்தைக் குறிப்பிடுங்கள்! எ.கா: `/image a glowing cyber lion`"
                with st.chat_message("assistant"):
                    st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "type": "text", "content": reply})

        # ---------------- 2. COMMAND: VIDEO GENERATION ----------------
        elif user_input.startswith("/video"):
            v_prompt = user_input.replace("/video", "").strip()
            if v_prompt:
                with st.chat_message("assistant"):
                    with st.spinner("🎬 AI Video உருவாக்குகிறது (சில நொடிகள் காத்திருக்கவும்)..."):
                        encoded_vprompt = urllib.parse.quote(v_prompt)
                        vid_url = f"https://image.pollinations.ai/prompt/{encoded_vprompt}?model=flux&nologo=true"
                        st.video(vid_url)
                        st.session_state.messages.append({"role": "assistant", "type": "video", "content": vid_url})
            else:
                reply = "⚠️ வீடியோவின் விவரத்தைக் குறிப்பிடுங்கள்! எ.கா: `/video cyberpunk car driving`"
                with st.chat_message("assistant"):
                    st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "type": "text", "content": reply})

        # ---------------- 3. COMMAND: CUSTOM VOICE GENERATION ----------------
        elif user_input.startswith("/voice"):
            v_text = user_input.replace("/voice", "").strip()
            if v_text:
                with st.chat_message("assistant"):
                    with st.spinner("🎙️ Voice Audio உருவாக்குகிறது..."):
                        async def make_custom_voice():
                            comm = edge_tts.Communicate(v_text, "ta-IN-ValluvarNeural")
                            await comm.save("custom_voice.mp3")
                        asyncio.run(make_custom_voice())
                        st.audio("custom_voice.mp3")
                        st.session_state.messages.append({"role": "assistant", "type": "audio", "content": "custom_voice.mp3"})
            else:
                reply = "⚠️ பேச்சாக மாற்ற வேண்டிய உரையைத் தட்டச்சு செய்யுங்கள்! எ.கா: `/voice வணக்கம்`"
                with st.chat_message("assistant"):
                    st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "type": "text", "content": reply})

        # ---------------- 4. NORMAL CHATBOT RESPONSE ----------------
        else:
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
            st.session_state.messages.append({"role": "assistant", "type": "text", "content": reply})

            # Auto Voice Response for Chat
            async def speak():
                clean_text = reply.replace("*", "")
                communicate = edge_tts.Communicate(clean_text, "ta-IN-ValluvarNeural")
                await communicate.save("rst_response.mp3")

            asyncio.run(speak())
            st.audio("rst_response.mp3")

    # ---------------- 5. PHOTO UPLOAD & EDIT STUDIO EXPANDABLE ----------------
    with st.expander("🖼️ Photo Upload & Edit Studio (படங்களை எடிட் செய்ய கிளிக் செய்யவும்)"):
        uploaded_file = st.file_uploader("Upload an Image", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Original Image")
                st.image(image, use_column_width=True)

            b_val = st.slider("Brightness", 0.5, 2.0, 1.0)
            c_val = st.slider("Contrast", 0.5, 2.0, 1.0)
            blur_val = st.slider("Blur", 0, 5, 0)
            bw = st.checkbox("Grayscale (Black & White)")

            edited_img = image.copy()
            if bw:
                edited_img = edited_img.convert("L")
            edited_img = ImageEnhance.Brightness(edited_img).enhance(b_val)
            edited_img = ImageEnhance.Contrast(edited_img).enhance(c_val)
            if blur_val > 0:
                edited_img = edited_img.filter(ImageFilter.GaussianBlur(blur_val))

            with col2:
                st.subheader("Edited Image")
                st.image(edited_img, use_column_width=True)
