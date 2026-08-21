import streamlit as st
import edge_tts
import asyncio
import urllib.parse
from PIL import Image

# 1. Gemini API Setup using Streamlit Secrets
HAS_GEMINI = False
client = None

if "GEMINI_API_KEY" in st.secrets:
    try:
        from google import genai
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        HAS_GEMINI = True
    except Exception as e:
        HAS_GEMINI = False

# 2. Page Config & Theme Setup
st.set_page_config(page_title="RST ASSISTANT", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #030308; color: #00f0ff; font-family: 'Segoe UI', sans-serif; }
    h1 { color: #ff0055; text-shadow: 0 0 15px #ff0055; text-align: center; font-weight: 800; }
    
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

# 3. Master Login Protection System
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
    st.title("⚡ RST ASSISTANT ⚡")
    st.markdown("<p style='text-align: center; color: #00f0ff;'>HIGH-LEVEL PRIVATE AI CONTROL CENTER</p>", unsafe_allow_html=True)

    st.markdown("""
        <div class="owner-card">
            <h4 style="color: #ff0055; margin:0 0 4px 0;">SYSTEM INFORMATION</h4>
            <p style="margin:2px 0; font-size:14px; color:#ffffff;"><b>SYSTEM:</b> RST ASSISTANT | <b>OWNER:</b> MOHAMMED RASITH</p>
            <p style="margin:2px 0; font-size:12px; color: #8b949e;"><b>EMAIL:</b> [PROTECTED] | <b>PHONE:</b> [PROTECTED]</p>
        </div>
    """, unsafe_allow_html=True)

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

    # ---------------- 1. MODE: REAL AI CHATBOT ----------------
    if st.session_state.active_mode == "chat":
        st.subheader("🤖 RST Interactive Smart AI Chatbot")
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

            if any(k in query for k in ["owner", "who made", "details", "contact", "created", "rasith", "developer", "உருவாக்கியவர்"]):
                reply = """இதை உருவாக்கியவர் **MOHAMMED RASITH** (RST AI OWNER).
📧 **Email:** MOHAMMEDRASITH27@GMAIL.COM  
📞 **Phone:** 0753967528"""
            else:
                with st.spinner("⚡ RST Thinking..."):
                    if HAS_GEMINI and client is not None:
                        try:
                            prompt_config = "You are RST ASSISTANT created by Mohammed Rasith. Be smart, intelligent, empathetic, and answer strictly in the language/style used by user (English, Tamil, or Tanglish)."
                            full_prompt = f"{prompt_config}\nUser: {user_input}"
                            
                            response = client.models.generate_content(
                                model="gemini-2.5-flash",
                                contents=full_prompt,
                            )
                            reply = response.text
                        except Exception as e:
                            reply = f"AI Error: {str(e)}"
                    else:
                        reply = "⚠️ Streamlit Secrets-இல் 'GEMINI_API_KEY' தவறாக உள்ளது அல்லது சேர்க்கப்படவில்லை. தயவுசெய்து Streamlit Settings ➔ Secrets பக்கத்தில் API Key-ஐ சேர்க்கவும்."

            with st.chat_message("assistant"):
                st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

            async def speak():
                clean_text = reply.replace("*", "").replace("#", "")
                comm = edge_tts.Communicate(clean_text, "ta-IN-ValluvarNeural")
                await comm.save("rst_response.mp3")

            asyncio.run(speak())
            st.audio("rst_response.mp3")

# ---------------- 4. MODE: VOICE GENERATOR ----------------
    elif st.session_state.active_mode == "voice":
        st.subheader("🎙️ RST Voice Generator")
        
        col1, col2 = st.columns(2)
        
        with col1:
            voice_options = {
                "🕵️‍♂️ Hacker / Cyber Voice (Male)": ("en-US-GuyNeural", "-15Hz", "-10%"),
                "Tamil (LK) - Sarar (Male - Sri Lanka)": ("ta-LK-KumarNeural", "+0Hz", "+0%"),
                "Tamil (LK) - Saranya (Female - Sri Lanka)": ("ta-LK-SaranyaNeural", "+0Hz", "+0%"),
                "Tamil (IN) - Valluvar (Male - India)": ("ta-IN-ValluvarNeural", "+0Hz", "+0%"),
                "Tamil (IN) - Pallavi (Female - India)": ("ta-IN-PallaviNeural", "+0Hz", "+0%"),
                "English (US) - Jenny (Female)": ("en-US-JennyNeural", "+0Hz", "+0%"),
                "English (US) - Guy (Male)": ("en-US-GuyNeural", "+0Hz", "+0%"),
                "English (UK) - Sonia (Female)": ("en-GB-SoniaNeural", "+0Hz", "+0%"),
                "English (UK) - Ryan (Male)": ("en-GB-RyanNeural", "+0Hz", "+0%")
            }
            selected_voice_name = st.selectbox("Select Voice Style:", list(voice_options.keys()))
            selected_voice_id, default_pitch, default_rate = voice_options[selected_voice_name]

        with col2:
            speed_options = {
                "Normal Speed (1.0x)": "+0%",
                "Fast (1.25x)": "+25%",
                "Very Fast (1.5x)": "+50%",
                "Slow (0.8x)": "-20%",
                "Very Slow (0.6x)": "-40%"
            }
            selected_speed_label = st.selectbox("Select Voice Speed:", list(speed_options.keys()))
            # If hacker voice is chosen, use custom rate or default speed
            selected_rate = default_rate if "Hacker" in selected_voice_name else speed_options[selected_speed_label]

        v_text = st.text_area("பேச்சாக மாற்ற வேண்டிய உரை:", "System hacked. Access granted to RST Control Center.")
        
        if st.button("Generate Voice Now"):
            if v_text:
                with st.spinner("⚡ RST Generating Voice..."):
                    async def make_custom_voice():
                        comm = edge_tts.Communicate(v_text, selected_voice_id, pitch=default_pitch, rate=selected_rate)
                        await comm.save("custom_voice.mp3")
                    asyncio.run(make_custom_voice())
                    st.audio("custom_voice.mp3")
            else:
                st.warning("தயவுசெய்து உரையை டைப் செய்யவும்!")

# ---------------- 4. MODE: VOICE GENERATOR ----------------
    elif st.session_state.active_mode == "voice":
        st.subheader("🎙️ RST Voice Generator")
        
        col1, col2 = st.columns(2)
        
        with col1:
            voice_options = {
                "🇱🇰 Sarar (Sri Lanka Male)": ("ta-LK-KumarNeural", "+0Hz", "+0%"),
                "🇱🇰 Saranya (Sri Lanka Female)": ("ta-LK-SaranyaNeural", "+0Hz", "+0%"),
                "🇮🇳 Valluvar (India Male)": ("ta-IN-ValluvarNeural", "+0Hz", "+0%"),
                "🇮🇳 Pallavi (India Female)": ("ta-IN-PallaviNeural", "+0Hz", "+0%"),
                "🕵️‍♂️ Tamil Hacker / Cyber Voice": ("ta-IN-ValluvarNeural", "-20Hz", "-15%")
            }
            selected_voice_name = st.selectbox("Select Voice:", list(voice_options.keys()))
            selected_voice_id, default_pitch, default_rate = voice_options[selected_voice_name]

        with col2:
            speed_options = {
                "Normal (1.0x)": "+0%",
                "Fast (1.25x)": "+25%",
                "Very Fast (1.5x)": "+50%",
                "Slow (0.8x)": "-20%",
                "Very Slow (0.6x)": "-40%"
            }
            selected_speed_label = st.selectbox("Select Speed:", list(speed_options.keys()))
            selected_rate = default_rate if "Hacker" in selected_voice_name else speed_options[selected_speed_label]

        v_text = st.text_area("பேச்சாக மாற்ற வேண்டிய உரை:", "சிஸ்டம் ஹேக் செய்யப்பட்டது. அக்சஸ் வழங்கப்பட்டுள்ளது.")
        
        if st.button("Generate Voice Now"):
            if v_text:
                with st.spinner("⚡ RST Generating Voice..."):
                    async def make_custom_voice():
                        comm = edge_tts.Communicate(v_text, selected_voice_id, pitch=default_pitch, rate=selected_rate)
                        await comm.save("custom_voice.mp3")
                    asyncio.run(make_custom_voice())
                    st.audio("custom_voice.mp3")
            else:
                st.warning("தயவுசெய்து உரையை டைப் செய்யவும்!")

# ---------------- 4. MODE: VOICE GENERATOR ----------------
    elif st.session_state.active_mode == "voice":
        st.subheader("🎙️ RST Voice Generator")
        
        col1, col2 = st.columns(2)
        
        with col1:
            voice_options = {
                "Tamil - Valluvar (Male)": "ta-IN-ValluvarNeural",
                "Tamil - Pallavi (Female)": "ta-IN-PallaviNeural",
                "English (US) - Jenny (Female)": "en-US-JennyNeural",
                "English (US) - Guy (Male)": "en-US-GuyNeural",
                "English (UK) - Sonia (Female)": "en-GB-SoniaNeural",
                "English (UK) - Ryan (Male)": "en-GB-RyanNeural"
            }
            selected_voice_name = st.selectbox("Select Voice Style:", list(voice_options.keys()))
            selected_voice_id = voice_options[selected_voice_name]

        with col2:
            # Voice Speed Option (+0%, +25%, -25% etc.)
            speed_options = {
                "Normal Speed (1.0x)": "+0%",
                "Fast (1.25x)": "+25%",
                "Very Fast (1.5x)": "+50%",
                "Slow (0.8x)": "-20%",
                "Very Slow (0.6x)": "-40%"
            }
            selected_speed_label = st.selectbox("Select Voice Speed:", list(speed_options.keys()))
            selected_rate = speed_options[selected_speed_label]

        v_text = st.text_area("பேச்சாக மாற்ற வேண்டிய உரை:", "வணக்கம், RST ASSISTANT தளத்திற்கு வரவேற்கிறேன்.")
        
        if st.button("Generate Voice Now"):
            if v_text:
                with st.spinner("⚡ RST Generating Voice..."):
                    async def make_custom_voice():
                        comm = edge_tts.Communicate(v_text, selected_voice_id, rate=selected_rate)
                        await comm.save("custom_voice.mp3")
                    asyncio.run(make_custom_voice())
                    st.audio("custom_voice.mp3")
            else:
                st.warning("தயவுசெய்து உரையை டைப் செய்யவும்!")
    # ---------------- 5. MODE: PHOTO RE-IMAGINE ----------------
    elif st.session_state.active_mode == "edit":
        st.subheader("🚀 RST High-Level AI Photo Re-Imagine")
        uploaded_file = st.file_uploader("Upload Your Image", type=["jpg", "jpeg", "png"])
        edit_prompt = st.text_input("AI Prompt:")
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
