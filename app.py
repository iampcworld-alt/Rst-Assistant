import streamlit as st
import edge_tts
import asyncio
import urllib.parse
from PIL import Image

# 1. Page Config & Theme Setup
st.set_page_config(page_title="RST ASSISTANT", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #030308; color: #00f0ff; font-family: 'Segoe UI', sans-serif; }
    h1 { color: #ff0055; text-shadow: 0 0 15px #ff0055; text-align: center; font-weight: 800; }
    
    /* Neon Glow Quick Action Buttons */
    .stButton>button { 
        background: linear-gradient(45deg, #161b22, #0d1117); 
        color: #00f0ff; 
        border: 1px solid #00f0ff;
        border-radius: 8px; 
        font-weight: bold; 
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.2);
    }
    .stButton>button:hover {
        background: linear-gradient(45deg, #ff0055, #7928ca);
        color: #ffffff;
        border: 1px solid #ff0055;
    }

    /* Owner Card */
    .owner-card { 
        background: rgba(22, 27, 34, 0.8); 
        border: 1px solid #00f0ff; 
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
    st.markdown("<p style='text-align: center; color: #00f0ff;'>HIGH-LEVEL PRIVATE AI CONTROL CENTER</p>", unsafe_allow_html=True)

    # System Information Panel
    st.markdown("""
        <div class="owner-card">
            <h4 style="color: #ff0055; margin:0 0 4px 0;">SYSTEM INFORMATION</h4>
            <p style="margin:2px 0; font-size:14px; color:#ffffff;"><b>SYSTEM:</b> RST ASSISTANT | <b>OWNER:</b> MOHAMMED RASITH</p>
            <p style="margin:2px 0; font-size:12px; color: #8b949e;"><b>EMAIL:</b> [PROTECTED] | <b>PHONE:</b> [PROTECTED]</p>
        </div>
    """, unsafe_allow_html=True)

    # Active Tool Mode Selector
    if "active_mode" not in st.session_state:
        st.session_state.active_mode = "chat"

    st.markdown("<h5 style='text-align: center; color: #ff0055;'>⚡ SELECT AI TOOL</h5>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        if st.button("🤖 AI Chat"): st.session_state.active_mode = "chat"
    with c2:
        if st.button("🎨 Image Gen"): st.session_state.active_mode = "image"
    with c3:
        if st.button("🎬 Video Gen"): st.session_state.active_mode = "video"
    with c4:
        if st.button("🎙️ Voice Gen"): st.session_state.active_mode = "voice"
    with c5:
        if st.button("🚀 AI Photo Re-Imagine"): st.session_state.active_mode = "edit"

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
            if any(k in query for k in ["owner", "who made", "details", "contact", "created", "rasith", "developer"]):
                reply = """இதை உருவாக்கியவர் **MOHAMMED RASITH** (RST AI OWNER).
📧 **Email:** MOHAMMEDRASITH27@GMAIL.COM  
📞 **Phone:** 0753967528"""
            else:
                reply = f"வணக்கம்! நான் உங்கள் RST ASSISTANT. நீங்கள் கேட்டது: '{user_input}'."

            with st.chat_message("assistant"):
                st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

            async def speak():
                comm = edge_tts.Communicate(reply.replace("*", ""), "ta-IN-ValluvarNeural")
                await comm.save("rst_response.mp3")

            asyncio.run(speak())
            st.audio("rst_response.mp3")

    # ---------------- 2. MODE: IMAGE GENERATOR ----------------
    elif st.session_state.active_mode == "image":
        st.subheader("🎨 RST AI Image Generator")
        img_prompt = st.text_input("Enter Image Prompt:")
        if st.button("Generate Image Now"):
            if img_prompt:
                with st.spinner("⚡ RST Processing Image..."):
                    encoded_prompt = urllib.parse.quote(img_prompt)
                    img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux&width=1080&height=1080&nologo=true"
                    
                    st.image(img_url, width=280)
                    st.markdown(f'<a href="{img_url}" target="_blank"><button style="background:#00f0ff; color:#000; border:none; padding:8px 15px; border-radius:5px; font-weight:bold; cursor:pointer;">📥 Download HD Image</button></a>', unsafe_allow_html=True)
            else:
                st.warning("தயவுசெய்து விவரத்தை டைப் செய்யவும்!")

    # ---------------- 3. MODE: VIDEO / MOTION GENERATOR ----------------
    elif st.session_state.active_mode == "video":
        st.subheader("🎬 RST AI Video & Motion Generator")
        vid_prompt = st.text_input("Enter Video Prompt:")
        
        if st.button("Generate Video Now"):
            if vid_prompt:
                with st.spinner("⚡ RST Generating Cinematic AI Motion..."):
                    encoded_vprompt = urllib.parse.quote(f"cinematic animation, high quality video motion, {vid_prompt}")
                    motion_url = f"https://image.pollinations.ai/prompt/{encoded_vprompt}?model=flux&width=1280&height=720&nologo=true"
                    
                    st.success("✅ RST Motion Frame Created!")
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.image(motion_url, caption="RST Cinematic AI Motion", width=500)
                    with col2:
                        st.write("**Controls:**")
                        st.markdown(f'<a href="{motion_url}" target="_blank"><button style="width:100%; background:#00f0ff; color:#000; border:none; padding:10px; border-radius:6px; font-weight:bold; cursor:pointer;">📥 Download HD Motion</button></a>', unsafe_allow_html=True)
            else:
                st.warning("தயவுசெய்து வீடியோ விவரத்தை டைப் செய்யவும்!")

    # ---------------- 4. MODE: VOICE GENERATOR ----------------
    elif st.session_state.active_mode == "voice":
        st.subheader("🎙️ RST Voice Generator")
        v_text = st.text_area("பேச்சாக மாற்ற வேண்டிய உரை:", "வணக்கம், RST ASSISTANT தளத்திற்கு வரவேற்கிறேன்.")
        if st.button("Generate Voice Now"):
            if v_text:
                with st.spinner("⚡ RST Generating Voice..."):
                    async def make_custom_voice():
                        comm = edge_tts.Communicate(v_text, "ta-IN-ValluvarNeural")
                        await comm.save("custom_voice.mp3")
                    asyncio.run(make_custom_voice())
                    st.audio("custom_voice.mp3")
            else:
                st.warning("தயவுசெய்து உரையை டைப் செய்யவும்!")

    # ---------------- 5. MODE: PHOTO RE-IMAGINE ----------------
    elif st.session_state.active_mode == "edit":
        st.subheader("🚀 RST High-Level AI Photo Re-Imagine")
        
        uploaded_file = st.file_uploader("Upload Your Image", type=["jpg", "jpeg", "png"])
        edit_prompt = st.text_input("AI Prompt (எ.கா: Convert into cyberpunk style, add futuristic neon suit):")
        
        if uploaded_file is not None and st.button("✨ Transform with AI"):
            if edit_prompt:
                with st.spinner("⚡ RST AI Processing Your Image..."):
                    combined_prompt = f"portrait of the person in uploaded image, {edit_prompt}, hyperrealistic, ultra detailed, 8k resolution"
                    encoded_prompt = urllib.parse.quote(combined_prompt)
                    ai_image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux&width=1080&height=1080&nologo=true"

                st.success("✅ Image Generated!")
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(ai_image_url, width=280)
                with col2:
                    st.markdown(f'<a href="{ai_image_url}" target="_blank"><button style="background:#00f0ff; color:#000; border:none; padding:10px 20px; border-radius:6px; font-weight:bold; cursor:pointer;">📥 Download / Open Full HD Image</button></a>', unsafe_allow_html=True)
            else:
                st.warning("தயவுசெய்து Prompt டைப் செய்யவும்!")
