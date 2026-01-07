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

for i in range(1, 101):
    cursor.execute("""
        INSERT INTO customers
        VALUES (?, ?, ?, ?, ?)
    """,
    i,
    fake.name(),
    random.randint(18, 60),
    fake.city(),
    fake.date_between(start_date='-5y', end_date='today')
    )

conn.commit()
cursor.close()
conn.close()

print("✅ Customers inserted")
