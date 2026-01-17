import pyodbc
import random
from faker import Faker

fake = Faker()

# ---------- SQL CONNECTION ----------
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=VANSHPC\SQLEXPRESS02;"          
    "DATABASE=banking_analytics;"
    "Trusted_Connection=yes;"
)

cursor = conn.cursor()

BASE_URL = "https://raw.githubusercontent.com/vanshag1208/Financo-Banking-Analytics/main/images/cards/"

tiers = ["Silver", "Gold", "Platinum"]
credit_limits = {
    "Silver": 50000,
    "Gold": 150000,
    "Platinum": 300000
}

card_id = 1

# ---------- LOOP THROUGH ACCOUNTS ----------
cursor.execute("SELECT account_id FROM accounts")
accounts = cursor.fetchall()

for acc in accounts:
    account_id = acc[0]

    # 🔹 DEBIT CARD (EVERY ACCOUNT)
    debit_tier = random.choice(tiers)
    debit_last4 = random.randint(1000, 9999)

    cursor.execute("""
        INSERT INTO cards
        (card_id, account_id, card_type, card_tier,
         masked_card_number, credit_limit, expiry_date, card_image_url)
        VALUES (?, ?, ?, ?, ?, ?, DATEADD(YEAR, 5, GETDATE()), ?)
    """,
    card_id,
    account_id,
    "Debit",
    debit_tier,
    f"XXXX-XXXX-XXXX-{debit_last4}",
    None,
    f"{BASE_URL}debit_{debit_tier.lower()}.png"
    )

    card_id += 1

    # 🔹 CREDIT CARD (RANDOM ASSIGNMENT)
    if random.choice([True, False]):
        credit_tier = random.choice(tiers)
        credit_last4 = random.randint(1000, 9999)

        cursor.execute("""
            INSERT INTO cards
            (card_id, account_id, card_type, card_tier,
             masked_card_number, credit_limit, expiry_date, card_image_url)
            VALUES (?, ?, ?, ?, ?, ?, DATEADD(YEAR, 5, GETDATE()), ?)
        """,
        card_id,
        account_id,
        "Credit",
        credit_tier,
        f"XXXX-XXXX-XXXX-{credit_last4}",
        credit_limits[credit_tier],
        f"{BASE_URL}credit_{credit_tier.lower()}.png"
        )

        card_id += 1

conn.commit()
cursor.close()
conn.close()

print("🔥 Cards inserted successfully")
