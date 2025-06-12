from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import fitz  # PyMuPDF
import os
import uuid
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploaded_pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Load models
embed_model = SentenceTransformer('all-MiniLM-L6-v2')
model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)
chat = pipeline("text-generation", model=model, tokenizer=tokenizer)

# In-memory storage for document vectors
doc_texts = []
doc_embeddings = None
index = None

# Utils
def extract_text(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text()
    return text

def embed_and_index(text):
    global doc_texts, doc_embeddings, index
    doc_texts = [text[i:i+500] for i in range(0, len(text), 500)]
    if not doc_texts:
        raise ValueError("No text extracted from PDF.")
    doc_embeddings = embed_model.encode(doc_texts)
    index = faiss.IndexFlatL2(doc_embeddings.shape[1])
    index.add(np.array(doc_embeddings))

def retrieve_context(query):
    query_embedding = embed_model.encode([query])
    D, I = index.search(np.array(query_embedding), k=3)
    return "\n".join([doc_texts[i] for i in I[0]])

def ask_llm(prompt):
    result = chat(prompt, max_new_tokens=256, do_sample=True, temperature=0.7)
    return result[0]["generated_text"].replace(prompt, "").strip()

# Endpoints
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1]
    if ext.lower() != "pdf":
        return JSONResponse(status_code=400, content={"error": "Only PDF files are supported."})

    file_id = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(UPLOAD_DIR, file_id)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    text = extract_text(file_path)
    try:
        embed_and_index(text)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    return {"message": "PDF uploaded and processed successfully."}

@app.post("/chat")
async def chat_with_pdf(query: str = Form(...)):
    if index is None or not doc_texts:
        return JSONResponse(status_code=400, content={"error": "No PDF uploaded or content not processed."})

    context = retrieve_context(query)
    prompt = f"You are an intelligent assistant. Based solely on the context provided below, answer the question explicitly without including any additional information or context.\n\n{context}\n\nQuestion: {query}\nAnswer:"
    answer = ask_llm(prompt)
    return {"answer": answer}

@app.post("/chat_general")
async def chat_general(query: str = Form(...)):
    prompt = f"You are a helpful assistant.Provide a concise and direct answer to the following question without any additional information or follow-up questions:\n\nQuestion: {query}\nAnswer:"
    answer = ask_llm(prompt)
    return {"answer": answer}
