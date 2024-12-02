import streamlit as st
import requests
import time
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict
import threading
import uvicorn
from profanityfilter import ProfanityFilter

pf = ProfanityFilter()

# FastAPI backend setup
app = FastAPI()

# Allow CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for messages
chat_messages: List[Dict[str, str]] = []

# Message model
class Message(BaseModel):
    role: str
    content: str

@app.post("/messages/send")
def send_message(message: Message):
    # Censor profane words in the message content
    censored_content = pf.censor(message.content)
    
    # Check if censorship occurred
    was_censored = censored_content != message.content
    
    # Update the message content
    message.content = censored_content
    chat_messages.append(message.dict())
    
    # Return the censorship status
    return {"status": "Message sent", "was_censored": was_censored}

@app.get("/messages/fetch")
def fetch_messages():
    return JSONResponse(content=chat_messages)

# Run FastAPI in a separate thread
def run_backend():
    uvicorn.run(app, host="127.0.0.1", port=8000)

backend_thread = threading.Thread(target=run_backend, daemon=True)
backend_thread.start()

# Streamlit frontend
# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "username" not in st.session_state:
    st.session_state.username = None

# Function to detect and convert URLs in text to hyperlinks
def convert_urls_to_links(text):
    url_regex = r'(https?://\S+)'
    return re.sub(url_regex, r'<a href="\1" target="_blank">\1</a>', text)

# Prompt user to log in with a username
if not st.session_state.username:
    st.session_state.username = st.text_input("Enter your username to join the chat:")

if st.session_state.username:
    # Display chat title
    st.markdown(
        f"<h1 style='text-align: center;'>Live Chat Room</h1>",
        unsafe_allow_html=True,
    )

    # Fetch messages from backend
    def fetch_messages():
        try:
            response = requests.get("http://127.0.0.1:8000/messages/fetch")
            if response.status_code == 200:
                return response.json()
            response.raise_for_status()
        except Exception as e:
            st.error(f"Error fetching messages: {e}")
        return []

    # Send message to backend
    def send_message(username, content):
        try:
            payload = {"role": username, "content": content}
            response = requests.post("http://127.0.0.1:8000/messages/send", json=payload)
            if response.status_code == 200:
                data = response.json()
                if data.get("was_censored"):
                    st.warning("Your message contained profanity and was censored.")
            else:
                st.error(f"Error sending message: {response.text}")
        except Exception as e:
            st.error(f"Error sending message: {e}")

    # Display new chat messages with styled bubbles
    def display_new_messages(new_messages):
        for message in new_messages:
            formatted_content = convert_urls_to_links(message['content'])
            
            # User's own message (right-aligned, light blue bubble)
            if message["role"] == st.session_state.username:
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: flex-end; align-items: center; margin: 10px 0;">
                        <div style="max-width: 70%; background-color: #ADD8E6; border-radius: 15px; padding: 10px; text-align: left; color: black;">
                            {formatted_content}
                        </div>
                        <span style="margin-left: 10px; font-size: 14px; color: gray;">You</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            
            # Other user's message (left-aligned, light gray bubble)
            else:
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: flex-start; align-items: center; margin: 10px 0;">
                        <span style="margin-right: 10px; font-size: 14px; color: gray;">{message['role']}</span>
                        <div style="max-width: 70%; background-color: #E5E5EA; border-radius: 15px; padding: 10px; text-align: left; color: black;">
                            {formatted_content}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # Poll for new messages and update the chat history
    def update_chat():
        new_messages = fetch_messages()
        if len(new_messages) > len(st.session_state.messages):
            # Determine only the truly new messages
            start_index = len(st.session_state.messages)
            st.session_state.messages = new_messages
            display_new_messages(new_messages[start_index:])

    # Initial display of chat history
    display_new_messages(st.session_state.messages)

    # Input for sending new messages
    if prompt := st.chat_input("Type your message and press Enter:"):
        # Convert URLs in the input message to clickable links
        formatted_prompt = convert_urls_to_links(prompt)
        
        # Display the user's message immediately
        st.markdown(
            f"""
            <div style="display: flex; justify-content: flex-end; align-items: center; margin: 10px 0;">
                <div style="max-width: 70%; background-color: #ADD8E6; border-radius: 15px; padding: 10px; text-align: left; color: black;">
                    {formatted_prompt}
                </div>
                <span style="margin-left: 10px; font-size: 14px; color: gray;">You</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Append the message to session state and send it to the backend
        st.session_state.messages.append({"role": st.session_state.username, "content": prompt})
        send_message(st.session_state.username, prompt)


    # Polling for updates every second
    while True:
        time.sleep(1)  # Adjust as needed for faster/slower updates
        update_chat()
