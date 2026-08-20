import streamlit as st
import edge_tts
import asyncio
import os

# Page Config & Futuristic Dark UI
st.set_page_config(page_title="RST ASSISTANT", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #05050a; color: #00ffcc; }
    h1 { color: #ff0055; text-shadow: 0 0 10px #ff0055; text-align: center; }
    .stButton>button { background-color: #ff0055; color: white; border-radius: 5px; font-weight: bold; width: 100%; }
    .owner-card { background: #161b22; border: 1px solid #00ffcc; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
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
            if password == "RSTA02EHYDR6":  # Updated Security Key
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

    # Owner & System Details
    st.markdown("""
        <div class="owner-card">
            <h3 style="color: #ff0055; margin:0;">SYSTEM INFORMATION</h3>
            <p style="margin:5px 0;"><b>SYSTEM NAME:</b> RST ASSISTANT</p>
            <p style="margin:5px 0;"><b>RST AI OWNER:</b> MOHAMMED RASITH</p>
            <p style="margin:5px 0;"><b>EMAIL:</b> MOHAMMEDRASITH27@GMAIL.COM</p>
            <p style="margin:5px 0;"><b>PHONE:</b> 0753967528</p>
        </div>
    """, unsafe_allow_html=True)

    # Interactive Chatbot Engine
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

        # Voice Output Engine
        async def speak():
            clean_text = reply.replace("*", "")
            communicate = edge_tts.Communicate(clean_text, "ta-IN-PallaviNeural")
            await communicate.save("rst_response.mp3")

        asyncio.run(speak())
        st.audio("rst_response.mp3")