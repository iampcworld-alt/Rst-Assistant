import streamlit as st
import edge_tts
import asyncio
import urllib.parse
from PIL import Image, ImageEnhance, ImageFilter

# Page Config & Futuristic Dark UI
st.set_page_config(page_title="RST ASSISTANT", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #05050a; color: #00ffcc; }
    h1 { color: #ff0055; text-shadow: 0 0 10px #ff0055; text-align: center; }
    .stButton>button { background-color: #ff0055; color: white; border-radius: 5px; font-weight: bold; width: 100%; }
    /* Compact System Info Card */
    .owner-card { 
        background: #161b22; 
        border: 1px solid #00ffcc; 
        padding: 10px 15px; 
        border-radius: 8px; 
        margin: 10px auto 20px auto; 
        max-width: 500px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Master Login Protection System
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
    # Welcome Greeting
    st.title("⚡ WELCOME TO RST ASSISTANT ⚡")
    st.markdown("<p style='text-align: center; color: #00ffcc;'>UNBREAKABLE PRIVATE AI CONTROL CENTER</p>", unsafe_allow_html=True)

    # Compact Owner & System Details (Email & Phone Hidden)
    st.markdown("""
        <div class="owner-card">
            <h4 style="color: #ff0055; margin:0 0 5px 0;">SYSTEM INFORMATION</h4>
            <p style="margin:2px 0; font-size:14px;"><b>SYSTEM:</b> RST ASSISTANT | <b>OWNER:</b> MOHAMMED RASITH</p>
            <p style="margin:2px 0; font-size:13px; color: #8b949e;"><b>EMAIL:</b> [PROTECTED / HIDDEN] | <b>PHONE:</b> [PROTECTED / HIDDEN]</p>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar Navigation Controls
    st.sidebar.title("⚡ RST Control Panel")
    mode = st.sidebar.radio("தேர்வு செய்க (Select Mode):", ["🤖 RST Chatbot", "🎨 Image Generator", "🖼️ Photo Upload & Edit"])

    # 1. Chatbot Mode
    if mode == "🤖 RST Chatbot":
        st.subheader("🤖 RST Interactive Chatbot")
        
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_input = st.chat_input("Ask RST Assistant something...")

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

            # Male Voice Output Engine (ValluvarVoice)
            async def speak():
                clean_text = reply.replace("*", "")
                communicate = edge_tts.Communicate(clean_text, "ta-IN-ValluvarNeural")
                await communicate.save("rst_response.mp3")

            asyncio.run(speak())
            st.audio("rst_response.mp3")

    # 2. AI Image Generator Mode
    elif mode == "🎨 Image Generator":
        st.subheader("🎨 RST AI Image Generator")
        st.write("உங்களுக்குத் தேவையான படத்தின் விவரத்தை ஆங்கிலத்தில் டைப் செய்யவும்:")
        
        prompt = st.text_input("Enter Image Prompt (e.g., A futuristic cyberpunk city):")
        
        if st.button("Generate Image"):
            if prompt:
                with st.spinner("உங்களது புகைப்படம் உருவாக்கப்பட்டு கொண்டிருக்கிறது..."):
                    encoded_prompt = urllib.parse.quote(prompt)
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
                    st.image(image_url, caption=f"Generated: {prompt}", use_column_width=True)
            else:
                st.warning("தயவுசெய்து ஏதேனும் விவரத்தை டைப் செய்யவும்!")

    # 3. Photo Upload & Edit Studio
    elif mode == "🖼️ Photo Upload & Edit":
        st.subheader("🖼️ RST Photo Editing Studio")
        st.write("உங்கள் கணினி அல்லது மொபைலில் இருந்து படத்தை பதிவேற்றி எடிட் செய்யவும்:")

        uploaded_file = st.file_uploader("Upload an Image", type=["jpg", "jpeg", "png"])

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Original Image")
                st.image(image, use_column_width=True)

            # Image Editing Controls
            st.sidebar.subheader("🎛️ Image Adjustments")
            brightness = st.sidebar.slider("Brightness", 0.5, 2.0, 1.0)
            contrast = st.sidebar.slider("Contrast", 0.5, 2.0, 1.0)
            blur = st.sidebar.slider("Blur Effect", 0, 5, 0)
            grayscale = st.sidebar.checkbox("Black & White (Grayscale)")

            # Process Image
            edited_img = image.copy()

            if grayscale:
                edited_img = edited_img.convert("L")

            enhancer = ImageEnhance.Brightness(edited_img)
            edited_img = enhancer.enhance(brightness)

            enhancer = ImageEnhance.Contrast(edited_img)
            edited_img = enhancer.enhance(contrast)

            if blur > 0:
                edited_img = edited_img.filter(ImageFilter.GaussianBlur(blur))

            with col2:
                st.subheader("Edited Image")
                st.image(edited_img, use_column_width=True)
