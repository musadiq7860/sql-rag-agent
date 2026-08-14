"""
Step 9: Document-based Q&A using FAISS + sentence-transformers
Reads company_docs.txt, splits into chunks, embeds them, builds a FAISS index.
Answers questions using the most relevant chunk(s) as context for the LLM.
"""

import os
import re
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("Loading embedding model (first run downloads it, ~90MB)...")
embed_model = SentenceTransformer("all-MiniLM-L6-v2")  # small, fast, free, local


def load_and_chunk(filepath: str, chunk_size: int = 300):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # split on blank lines (paragraphs) first — keeps each policy section together
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    chunks = []
    for para in paragraphs:
        if len(para) <= chunk_size:
            chunks.append(para)
        else:
            # further split long paragraphs into smaller pieces
            words = para.split()
            current = []
            length = 0
            for w in words:
                current.append(w)
                length += len(w) + 1
                if length >= chunk_size:
                    chunks.append(" ".join(current))
                    current = []
                    length = 0
            if current:
                chunks.append(" ".join(current))

    return chunks


def build_index(chunks):
    embeddings = embed_model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # cosine similarity via normalized vectors
    index.add(embeddings)
    return index


def search(query: str, index, chunks, top_k: int = 2):
    query_vec = embed_model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    scores, indices = index.search(query_vec, top_k)
    results = [chunks[i] for i in indices[0] if i < len(chunks)]
    return results


def answer_from_docs(question: str, context_chunks: list) -> str:
    context = "\n\n".join(context_chunks)
    prompt = f"""Answer the user's question using ONLY the context below. If the answer isn't in the context, say you don't have that information.

Context:
{context}

Question: {question}

Answer:"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content.strip()


def ask_docs(question: str, index, chunks):
    relevant = search(question, index, chunks)
    return answer_from_docs(question, relevant)


if __name__ == "__main__":
    chunks = load_and_chunk("company_docs.txt")
    print(f"Loaded {len(chunks)} chunks from company_docs.txt")

    index = build_index(chunks)
    print("FAISS index built. Ready.\n")

    print("Ask questions about company policies (type 'exit' to quit)\n")
    while True:
        q = input("You: ")
        if q.lower() in ("exit", "quit"):
            break
        answer = ask_docs(q, index, chunks)
        print(f"Bot: {answer}\n")