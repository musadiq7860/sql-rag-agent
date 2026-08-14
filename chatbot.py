"""
Step 10: Unified chatbot — routes each question to either the SQL agent
(structured data: sales, customers, products) or the Doc agent (company
policies from company_docs.txt), based on what the question is about.
"""

import os
from dotenv import load_dotenv
from groq import Groq

from query_agent import ask as ask_sql
from doc_agent import load_and_chunk, build_index, ask_docs

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def classify(question: str) -> str:
    prompt = f"""Classify the user's question into exactly one category:

- "sql" -> if it's about sales figures, revenue, orders, customers, products, quantities, dates, totals, rankings (best-selling, top customer, etc.)
- "docs" -> if it's about company policies, return policy, shipping, warranty, support hours, or general company information

Question: {question}

Answer with only one word: sql or docs"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    label = response.choices[0].message.content.strip().lower()
    return "sql" if "sql" in label else "docs"


def main():
    print("Loading document index...")
    chunks = load_and_chunk("company_docs.txt")
    index = build_index(chunks)
    print("Ready. Ask anything about sales data or company policies (type 'exit' to quit)\n")

    while True:
        q = input("You: ")
        if q.lower() in ("exit", "quit"):
            break

        category = classify(q)

        if category == "sql":
            answer = ask_sql(q)
        else:
            answer = ask_docs(q, index, chunks)

        print(f"Bot: {answer}\n")


if __name__ == "__main__":
    main()
    