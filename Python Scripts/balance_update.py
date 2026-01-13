import pyodbc
import random

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=VANSHPC\\SQLEXPRESS02;"
    "DATABASE=banking_analytics;"
    "Trusted_Connection=yes;"
)
cursor = conn.cursor()

# Fetch accounts
cursor.execute("SELECT account_id, account_type FROM accounts")
accounts = cursor.fetchall()

for account_id, acc_type in accounts:

    if acc_type == "Savings":
        opening_balance = random.randint(20000, 150000)
    else:  # Current
        opening_balance = random.randint(100000, 500000)

    cursor.execute("""
        UPDATE accounts
        SET balance = ?
        WHERE account_id = ?
    """, opening_balance, account_id)

conn.commit()
cursor.close()
conn.close()

print(" Opening balances reset successfully")
