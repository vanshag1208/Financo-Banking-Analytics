import pyodbc
import random
from faker import Faker
from datetime import date

fake = Faker()

# ---------- SQL CONNECTION ----------
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=VANSHPC\SQLEXPRESS02;"          # apna server name
    "DATABASE=banking_analytics;"
    "Trusted_Connection=yes;"
)

cursor = conn.cursor()

# ---------- MASTER DATA ----------
categories = [
    "Food", "Groceries", "Shopping",
    "Travel", "Bills", "Entertainment",
    "Healthcare", "Investment", "EMI"
]

merchants = {
    "Food": ["Swiggy", "Zomato"],
    "Groceries": ["Reliance Mart", "Big Bazaar"],
    "Shopping": ["Amazon", "Flipkart"],
    "Travel": ["Uber", "IRCTC"],
    "Bills": ["Electricity Board", "Gas Agency"],
    "Entertainment": ["Netflix", "Spotify"],
    "Healthcare": ["Apollo Pharmacy"],
    "Investment": ["Zerodha"],
    "EMI": ["Bank EMI"]
}

transaction_id = 1

# ---------- LOOP THROUGH ACCOUNTS ----------
for account_id in range(1, 101):

    # 🔵 MONTHLY SALARY (CREDIT)
    for month in range(12):
        cursor.execute("""
            INSERT INTO transactions
            (transaction_id, account_id, transaction_date,
             amount, transaction_type, category, merchant)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        transaction_id,
        account_id,
        fake.date_between(start_date='-1y', end_date='today'),
        random.randint(30000, 80000),
        "Credit",
        "Salary",
        "Employer"
        )
        transaction_id += 1

    # 🔴 DEBIT TRANSACTIONS
    for _ in range(180):
        category = random.choice(categories)

        cursor.execute("""
            INSERT INTO transactions
            (transaction_id, account_id, transaction_date,
             amount, transaction_type, category, merchant)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        transaction_id,
        account_id,
        fake.date_between(start_date='-1y', end_date='today'),
        random.randint(100, 15000),
        "Debit",
        category,
        random.choice(merchants[category])
        )

        transaction_id += 1

conn.commit()
cursor.close()
conn.close()

print("🔥 Transactions inserted successfully")
