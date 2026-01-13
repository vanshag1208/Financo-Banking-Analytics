import pyodbc
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()

# ---------- DB CONNECTION ----------
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=VANSHPC\\SQLEXPRESS02;"
    "DATABASE=banking_analytics;"
    "Trusted_Connection=yes;"
)
cursor = conn.cursor()

# ---------- MASTER DATA ----------
categories = ["Food", "Shopping", "Travel", "Bills", "Entertainment", "Groceries"]

merchants = {
    "Food": ["Swiggy", "Zomato"],
    "Shopping": ["Amazon", "Flipkart"],
    "Travel": ["Uber", "IRCTC"],
    "Bills": ["Electricity Board"],
    "Entertainment": ["Netflix"],
    "Groceries": ["Reliance Mart"]
}

# ---------- FETCH ACCOUNTS ----------
cursor.execute("SELECT account_id FROM accounts")
accounts = cursor.fetchall()

cursor.execute("SELECT ISNULL(MAX(transaction_id),0) FROM transactions")
transaction_id = cursor.fetchone()[0] + 1

MONTHS = 24

# =================================================

for (account_id,) in accounts:

    # ---- FETCH CARDS ----
    cursor.execute("""
        SELECT card_id FROM cards
        WHERE account_id=? AND card_type='Debit'
    """, account_id)
    dc = cursor.fetchone()
    debit_card_id = dc[0] if dc else None

    cursor.execute("""
        SELECT card_id, credit_limit FROM cards
        WHERE account_id=? AND card_type='Credit'
    """, account_id)
    cc = cursor.fetchone()

    credit_card_id = cc[0] if cc else None
    credit_limit = float(cc[1]) if cc else 0

    # ---- MONTH LOOP ----
    for m in range(MONTHS):

        month_start = datetime.now().replace(day=1) - timedelta(days=30*m)

        # ---- MONTHLY TRACKERS ----
        monthly_credit = 0
        total_spent = 0
        bank_spent = 0

        # ---- SALARY ----
        salary = random.randint(25000, 80000)
        monthly_credit += salary

        cursor.execute("""
            INSERT INTO transactions VALUES
            (?, ?, ?, ?, 'Credit', 'Bank Transfer',
             'Salary', 'Company', NULL)
        """, transaction_id, account_id, month_start, salary)
        transaction_id += 1

        # ---- INTEREST ----
        interest = round(salary * 0.02 / 12, 2)
        monthly_credit += interest

        cursor.execute("""
            INSERT INTO transactions VALUES
            (?, ?, ?, ?, 'Credit', 'Bank Transfer',
             'Interest', 'Bank', NULL)
        """, transaction_id, account_id,
             month_start + timedelta(days=2), interest)
        transaction_id += 1

        # ---- GLOBAL MONTHLY SPEND CAP (CORE RULE) ----
        total_spend_cap = monthly_credit * random.uniform(0.75, 0.95)

        # ---- BANK / DEBIT SPENDS ----
        max_bank_spend = total_spend_cap * random.uniform(0.5, 0.7)

        for _ in range(random.randint(6, 12)):

            if bank_spent >= max_bank_spend or total_spent >= total_spend_cap:
                break

            category = random.choice(categories)
            merchant = random.choice(merchants[category])

            channel = (
                "Debit Card"
                if debit_card_id and random.random() < 0.7
                else "Bank Transfer"
            )
            card_id = debit_card_id if channel == "Debit Card" else None
            amount = random.randint(500, 15000)

            remaining_cap = min(
                max_bank_spend - bank_spent,
                total_spend_cap - total_spent
            )

            if amount > remaining_cap:
                amount = remaining_cap

            if amount <= 0:
                break

            tx_date = fake.date_between(
                start_date=month_start,
                end_date=month_start + timedelta(days=25)
            )

            cursor.execute("""
                INSERT INTO transactions VALUES
                (?, ?, ?, ?, 'Debit', ?, ?, ?, ?)
            """, transaction_id, account_id, tx_date,
                 amount, channel, category, merchant, card_id)

            transaction_id += 1
            bank_spent += amount
            total_spent += amount

        # ---- CREDIT CARD SPENDS ----
        if credit_card_id and total_spent < total_spend_cap:

            remaining_cap = total_spend_cap - total_spent
            usage_cap = min(
                credit_limit * random.uniform(0.2, 0.6),
                remaining_cap
            )

            cc_spent = 0

            for _ in range(random.randint(3, 6)):
                amt = random.randint(2000, 12000)

                if cc_spent + amt > usage_cap:
                    break

                tx_date = fake.date_between(
                    start_date=month_start,
                    end_date=month_start + timedelta(days=25)
                )

                cursor.execute("""
                    INSERT INTO transactions VALUES
                    (?, ?, ?, ?, 'Debit', 'Credit Card',
                     'Shopping', 'Amazon', ?)
                """, transaction_id, account_id,
                     tx_date, amt, credit_card_id)

                transaction_id += 1
                cc_spent += amt
                total_spent += amt

# ---------- COMMIT ----------
conn.commit()
cursor.close()
conn.close()

print(" Transactions inserted successfully")
