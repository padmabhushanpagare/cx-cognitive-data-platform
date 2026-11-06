import streamlit as st
import requests
import uuid
import os

st.set_page_config(page_title="Enterprise CX Platform", page_icon="🤖", layout="centered")
st.title("🤖 Enterprise CX Agent")
st.markdown("Welcome to the autonomous customer experience portal.")

# Fail fast if API URL is missing
API_URL = os.getenv("API_BASE_URL")
if not API_URL:
    st.error("CRITICAL: API_BASE_URL environment variable is not set.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False

with st.sidebar:
    st.header("Customer Authentication")
    # No default value. User must type it.
    input_customer_id = st.text_input("Enter your Customer ID")
    
    if st.button("Authenticate"):
        if input_customer_id.strip():
            st.session_state.customer_id = input_customer_id.strip().upper()
            st.session_state.is_authenticated = True
            st.success(f"Authenticated as {st.session_state.customer_id}")
        else:
            st.error("Please enter a valid Customer ID.")

# Block chat until authenticated
if not st.session_state.is_authenticated:
    st.info("👈 Please authenticate using the sidebar to start chatting.")
    st.stop()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    payload = {
        "message": prompt, 
        "session_id": st.session_state.session_id,
        "customer_id": st.session_state.customer_id
    }
    
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