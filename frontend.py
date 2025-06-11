import streamlit as st
import requests

st.set_page_config(page_title="PDF Chatbot", layout="centered")
st.title("🤖 PDF + General Knowledge Chatbot")

st.markdown("""
This chatbot can answer general knowledge questions and, if you upload a PDF, it will answer based on that document.
""")

# Session state to track if a PDF has been uploaded
if "pdf_uploaded" not in st.session_state:
    st.session_state.pdf_uploaded = False

# Upload PDF
st.subheader("📄 Upload a PDF (optional)")
uploaded_file = st.file_uploader("Upload a PDF to enable document-based Q&A", type="pdf")
if uploaded_file is not None:
    with st.spinner("Uploading and processing PDF..."):
        response = requests.post("http://localhost:8000/upload", files={"file": uploaded_file.getvalue()})
        if response.status_code == 200:
            st.success("✅ PDF uploaded and processed successfully!")
            st.session_state.pdf_uploaded = True
        else:
            st.error(response.json().get("error", "❌ Upload failed."))
            st.session_state.pdf_uploaded = False

# Chat Section
st.subheader("💬 Ask the Chatbot Anything")
question = st.text_input("Ask a question:")

if st.button("🔍 Get Answer") and question:
    with st.spinner("Thinking..."):
        if st.session_state.pdf_uploaded:
            endpoint = "http://localhost:8000/chat"
        else:
            endpoint = "http://localhost:8000/chat_general"

        res = requests.post(endpoint, data={"query": question})
        if res.status_code == 200:
            st.markdown(f"**🧠 Answer:**\n\n{res.json()['answer']}")
        else:
            st.error(res.json().get("error", "Something went wrong."))