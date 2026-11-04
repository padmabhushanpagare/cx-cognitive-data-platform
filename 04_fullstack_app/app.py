import streamlit as st
import requests
import uuid
import os

st.set_page_config(page_title="Enterprise CX Platform", page_icon="🤖", layout="centered")
st.title("🤖 Enterprise CX Agent")
st.markdown("Welcome to the autonomous customer experience portal. Ask about our books or request a human agent.")

# Read API URL from environment (Docker) or default to localhost
API_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# Initialize Chat History and Session ID
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    # Generate a unique ID for this chat session
    st.session_state.session_id = str(uuid.uuid4())

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    payload = {"message": prompt, "session_id": st.session_state.session_id}
    
    with st.spinner("Agent is thinking..."):
        try:
            response = requests.post(f"{API_URL}/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            
            ai_response = data.get("response", "Error: No response text found.")
            requires_human = data.get("requires_human", False)
            
            with st.chat_message("assistant"):
                if requires_human:
                    st.error("🚨 **HUMAN HANDOFF TRIGGERED** 🚨")
                    st.markdown(ai_response)
                else:
                    st.markdown(ai_response)
                    
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            
        except requests.exceptions.ConnectionError:
            st.error(f"Failed to connect to the backend at {API_URL}.")