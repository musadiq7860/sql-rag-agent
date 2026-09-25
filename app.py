"""
Step 11: FastAPI backend for the chatbot.
Exposes POST /chat which takes a question and returns the routed answer.
Run with: uvicorn app:app --reload
"""

from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from query_agent import ask as ask_sql
from doc_agent import load_and_chunk, build_index, ask_docs
from chatbot import classify

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load document index once at startup, not per-request
print("Loading document index...")
doc_chunks = load_and_chunk("company_docs.txt")
doc_index = build_index(doc_chunks)
print("Backend ready.")


class Question(BaseModel):
    question: str


@app.post("/chat")
def chat(q: Question):
    category = classify(q.question)

    if category == "sql":
        answer = ask_sql(q.question)
    else:
        answer = ask_docs(q.question, doc_index, doc_chunks)

    return {"answer": answer, "source": category}


# Serve the frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")
