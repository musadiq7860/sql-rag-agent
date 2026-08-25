"""
Step 7: Natural language -> SQL -> Answer
Ask questions in plain English (or Roman Urdu mixed), it converts to SQL,
runs it on Postgres, and answers back in natural language.
"""

import os
import psycopg2
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Schema description given to the LLM so it knows table/column names
SCHEMA = """
Tables:

customers (customer_id, name, city, email)
products (product_id, name, category, price)
sales (sale_id, customer_id, product_id, quantity, total_amount, sale_date)

sale_date is a DATE column. Use CURRENT_DATE for today.
"today" = CURRENT_DATE
"yesterday" / "kal" = CURRENT_DATE - INTERVAL '1 day'
"this week" = sale_date >= date_trunc('week', CURRENT_DATE)
"this month" = sale_date >= date_trunc('month', CURRENT_DATE)
"""


def generate_sql(question: str) -> str:
    prompt = f"""You are a PostgreSQL expert. Convert the user's question into a single valid PostgreSQL SELECT query.

{SCHEMA}

Rules:
- Only output the raw SQL query, nothing else. No explanation, no markdown, no ```sql fences.
- Only SELECT statements. Never write/modify data.
- Use proper JOINs when the question needs data from multiple tables.

Question: {question}

SQL:"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    sql = response.choices[0].message.content.strip()
    # strip accidental markdown fences if the model adds them
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql


def run_sql(sql: str):
    cur = conn.cursor()
    cur.execute(sql)
    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    cur.close()
    return columns, rows


def answer_in_words(question: str, columns, rows) -> str:
    data_str = f"Columns: {columns}\nRows: {rows}"

    prompt = f"""The user asked: "{question}"

Here is the database result:
{data_str}

Answer the user's question in one short, natural sentence based on this data.
If rows is empty, say no data was found for that.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content.strip()


def ask(question: str, show_sql: bool = False):
    sql = generate_sql(question)
    if show_sql:
        print(f"\n[Generated SQL]: {sql}")

    try:
        columns, rows = run_sql(sql)
    except Exception as e:
        conn.rollback()
        return f"Query failed: {e}"

    final_answer = answer_in_words(question, columns, rows)
    return final_answer


if __name__ == "__main__":
    print("Ask questions about sales/customers/products (type 'exit' to quit)\n")
    while True:
        q = input("You: ")
        if q.lower() in ("exit", "quit"):
            break
        answer = ask(q)
        print(f"Bot: {answer}\n")