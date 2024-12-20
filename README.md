﻿# [Streamlit Chat App](https://live-chat.streamlit.app/)
DEMO: [live-chat.streamlit.app/](https://live-chat.streamlit.app/)

## Description

This project is a real-time and multi-user chat application built using Streamlit (crazy right?) for the frontend and FastAPI for the backend. It includes a profanity filter to censor inappropriate language in messages.

## Features

- Real-time chat functionality
- Profanity filtering
- User-friendly interface
- Backend API with FastAPI
- CORS support for frontend-backend communication

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/chat-app.git
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run ```app.py``` with Streamlit:

```
streamlit run app.py
```
Open your web browser and go to http://localhost:8501 to access the chat application.

## Note
The application uses the profanityfilter library to censor inappropriate language in messages. If a message contains profane words, they will be replaced with asterisks (*), and the user will be notified (It will only take effect for other users, your own text won't be censored)

