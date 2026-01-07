import pyodbc

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=VANSHPC\SQLEXPRESS02;"
    "DATABASE=banking_analytics;"
    "Trusted_Connection=yes;"
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM customers")
print("Connection successful")

cursor.close()
conn.close()
