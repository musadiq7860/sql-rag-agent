"""
Step 4: Create tables + insert dummy company data (sales, orders, customers)
Run this once to set up the database.
"""

import psycopg2
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)
cur = conn.cursor()

# ---- Create tables ----
cur.execute("""
DROP TABLE IF EXISTS sales CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS products CASCADE;

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    city VARCHAR(100),
    email VARCHAR(100)
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    category VARCHAR(50),
    price NUMERIC(10,2)
);

CREATE TABLE sales (
    sale_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    product_id INT REFERENCES products(product_id),
    quantity INT,
    total_amount NUMERIC(10,2),
    sale_date DATE
);
""")
conn.commit()
print("Tables created.")

# ---- Insert customers ----
cities = ["Islamabad", "Lahore", "Karachi", "Abbottabad", "Peshawar"]
names = ["Ali Raza", "Sara Khan", "Bilal Ahmed", "Ayesha Malik", "Usman Tariq",
         "Hina Shah", "Kamran Iqbal", "Zara Sheikh", "Faisal Butt", "Nadia Yousaf"]

for i in range(10):
    cur.execute(
        "INSERT INTO customers (name, city, email) VALUES (%s, %s, %s)",
        (names[i], random.choice(cities), f"{names[i].split()[0].lower()}@example.com")
    )

# ---- Insert products ----
products = [
    ("Wireless Mouse", "Electronics", 1500),
    ("Office Chair", "Furniture", 12000),
    ("Notebook Pack", "Stationery", 500),
    ("LED Desk Lamp", "Electronics", 2200),
    ("Water Bottle", "Accessories", 800),
]

for p in products:
    cur.execute(
        "INSERT INTO products (name, category, price) VALUES (%s, %s, %s)",
        p
    )

conn.commit()
print("Customers and products inserted.")

# ---- Insert random sales over the last 30 days ----
today = datetime.now().date()

for _ in range(150):
    customer_id = random.randint(1, 10)
    product_id = random.randint(1, 5)
    quantity = random.randint(1, 5)

    cur.execute("SELECT price FROM products WHERE product_id = %s", (product_id,))
    price = cur.fetchone()[0]
    total_amount = float(price) * quantity

    days_ago = random.randint(0, 30)
    sale_date = today - timedelta(days=days_ago)

    cur.execute(
        "INSERT INTO sales (customer_id, product_id, quantity, total_amount, sale_date) VALUES (%s, %s, %s, %s, %s)",
        (customer_id, product_id, quantity, total_amount, sale_date)
    )

conn.commit()
print("150 sample sales records inserted.")

cur.close()
conn.close()
print("Done. Database is ready.")