import streamlit as st
import requests

st.set_page_config(page_title="PDF Chatbot", layout="centered")
st.markdown("""
    <style>
    .chat-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 10px;
        background-color: #f2f2f2;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .message {
        padding: 10px;
        margin: 5px;
        border-radius: 10px;
        max-width: 80%;
        word-wrap: break-word;
    }
    .user {
        background-color: #0084ff;
        color: white;
        align-self: flex-end;
        margin-left: auto;
    }
    .bot {
        background-color: #e5e5ea;
        color: black;
        align-self: flex-start;
        margin-right: auto;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center;'>🤖 PDF + General Knowledge Chatbot</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Upload a PDF and chat below. The bot will respond based on the PDF if uploaded, or general knowledge otherwise.</p>", unsafe_allow_html=True)

# Initialize session state
if "pdf_uploaded" not in st.session_state:
    st.session_state.pdf_uploaded = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Upload PDF
st.markdown("### 📄 Upload a PDF (optional)")
uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
if uploaded_file is not None:
    with st.spinner("Uploading and processing PDF..."):
        files = {
            "file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")
        }
        response = requests.post("http://localhost:8000/upload", files=files)
        if response.status_code == 200:
            st.success("✅ PDF uploaded and processed successfully!")
            st.session_state.pdf_uploaded = True
        else:
            st.error(response.json().get("error", "❌ Upload failed."))
            st.session_state.pdf_uploaded = False

# Chat Interface
st.markdown("### 💬 Chat")
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

for entry in st.session_state.chat_history:
    sender, msg = entry
    css_class = "user" if sender == "You" else "bot"
    st.markdown(f"<div class='message {css_class}'><b>{sender}:</b><br>{msg}</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("Message:", placeholder="Type your question here...")
    submit_button = st.form_submit_button(label="Send")

if submit_button and user_input:
    st.session_state.chat_history.append(("You", user_input))
    with st.spinner("Thinking..."):
        endpoint = "http://localhost:8000/chat" if st.session_state.pdf_uploaded else "http://localhost:8000/chat_general"
        res = requests.post(endpoint, data={"query": user_input})
        if res.status_code == 200:
            answer = res.json()['answer']
        else:
            answer = res.json().get("error", "Something went wrong.")
        st.session_state.chat_history.append(("Bot", answer))
