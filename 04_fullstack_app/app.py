import streamlit as st
import requests

# 1. Page Configuration
st.set_page_config(page_title="Enterprise CX Platform", page_icon="🤖", layout="centered")
st.title("🤖 Enterprise CX Agent")
st.markdown("Welcome to the autonomous customer experience portal. Ask about our books or request a human agent.")

# 2. Initialize Chat History in Streamlit's Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Render previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Handle User Input
if prompt := st.chat_input("Type your message here..."):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 5. Send request to the FastAPI Backend
    api_url = "http://127.0.0.1:8000/chat"
    payload = {"message": prompt}
    
    with st.spinner("Agent is thinking..."):
        try:
            response = requests.post(api_url, json=payload)
            response.raise_for_status() # Check for HTTP errors
            data = response.json()
            
            ai_response = data.get("response", "Error: No response text found.")
            requires_human = data.get("requires_human", False)
            
            # Display AI message
            with st.chat_message("assistant"):
                # If human handoff is required, show a massive warning banner
                if requires_human:
                    st.error("🚨 **HUMAN HANDOFF TRIGGERED** 🚨")
                    st.markdown(ai_response)
                else:
                    st.markdown(ai_response)
                    
            # Save AI response to history
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            
        except requests.exceptions.ConnectionError:
            st.error("Failed to connect to the backend. Is FastAPI running on port 8000?")