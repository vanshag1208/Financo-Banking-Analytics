import pyodbc 
import random
from faker import Faker

fake = Faker()

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=VANSHPC\SQLEXPRESS02;"
    "DATABASE=banking_analytics;"
    "Trusted_Connection=yes;"
)

cursor = conn.cursor()

for acc_id in range(1, 101):
    cursor.execute("""
        INSERT INTO accounts
        VALUES (?, ?, ?, ?, ?)
    """,
    acc_id,
    acc_id,
    random.choice(["Savings", "Current"]),
    random.randint(20000, 300000),
    fake.date_between(start_date='-4y', end_date='today')
    )

conn.commit()
cursor.close()
conn.close()

print("✅ Accounts inserted")
