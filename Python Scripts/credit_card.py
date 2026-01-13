import pyodbc
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# ---------------- CONFIG ----------------
ANNUAL_INTEREST_RATE = 0.16
MONTHLY_RATE = ANNUAL_INTEREST_RATE / 12

# ---------------- DB CONNECTION ----------------
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=VANSHPC\\SQLEXPRESS02;"
    "DATABASE=banking_analytics;"
    "Trusted_Connection=yes;"
)
cursor = conn.cursor()

# ---------------- CLEAN OLD DATA ----------------
cursor.execute("TRUNCATE TABLE credit_card_statement")
conn.commit()

# ---------------- IDS ----------------
cursor.execute("SELECT ISNULL(MAX(statement_id),0) FROM credit_card_statement")
statement_id = cursor.fetchone()[0] + 1

cursor.execute("SELECT ISNULL(MAX(transaction_id),0) FROM transactions")
transaction_id = cursor.fetchone()[0] + 1

# ---------------- FETCH CREDIT CARDS ----------------
cursor.execute("""
    SELECT card_id, account_id
    FROM cards
    WHERE card_type = 'Credit'
""")
cards = cursor.fetchall()

# ---------------- DATE RANGE ----------------
cursor.execute("""
    SELECT MIN(transaction_date), MAX(transaction_date)
    FROM transactions
    WHERE transaction_channel = 'Credit Card'
""")
min_date, max_date = cursor.fetchone()

start_month = datetime(min_date.year, min_date.month, 1)
end_month   = datetime(max_date.year, max_date.month, 1)

# ---------------- CUSTOMER PAYMENT BEHAVIOUR ----------------
def assign_behaviour():
    return random.choices(
        ["GOOD", "OCCASIONAL", "RISKY"],
        weights=[65, 20, 15]
    )[0]

def decide_payment(behaviour, final_due, minimum_due, stmt_date):

    if behaviour == "GOOD":
        choice = random.choices(["FULL", "LATE"], [90, 10])[0]
    elif behaviour == "OCCASIONAL":
        choice = random.choices(["FULL", "LATE", "PARTIAL"], [60, 25, 15])[0]
    else:
        choice = random.choices(["FULL", "LATE", "PARTIAL", "NONE"], [20, 30, 30, 20])[0]

    if choice == "FULL":
        return final_due, stmt_date + timedelta(days=random.randint(5, 12))

    if choice == "LATE":
        return final_due, stmt_date + timedelta(days=random.randint(25, 40))

    if choice == "PARTIAL":
        return round(random.uniform(minimum_due, final_due * 0.6), 2), stmt_date + timedelta(days=15)

    return 0, None

# ---------------- MAIN SINGLE LOOP ----------------
for card_id, account_id in cards:

    prev_outstanding = 0.0
    behaviour = assign_behaviour()
    current_month = start_month

    while current_month <= end_month:

        next_month = current_month + relativedelta(months=1)
        statement_month = datetime(next_month.year, next_month.month, 1)

        # ---- CURRENT MONTH SPEND ----
        cursor.execute("""
            SELECT ISNULL(SUM(amount),0)
            FROM transactions
            WHERE transaction_channel = 'Credit Card'
              AND card_id = ?
              AND transaction_date >= ?
              AND transaction_date < ?
        """, card_id, current_month, next_month)

        total_spend = float(cursor.fetchone()[0])

        if total_spend == 0 and prev_outstanding == 0:
            current_month = next_month
            continue

        # ---- LOGIC AS PER YOU ----
        total_due = total_spend
        interest_amount = round(prev_outstanding * MONTHLY_RATE, 2)
        final_due = round(total_due + prev_outstanding + interest_amount, 2)
        minimum_due = max(round(final_due * 0.05, 2), 500)

        # ---- INSERT STATEMENT ----
        cursor.execute("""
            INSERT INTO credit_card_statement
            (statement_id, card_id, account_id,
             statement_month,
             total_spend,
             total_due,
             prev_outstanding,
             interest_amount,
             minimum_due,
             final_due)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        statement_id,
        card_id,
        account_id,
        statement_month.date(),
        total_spend,
        total_due,
        prev_outstanding,
        interest_amount,
        minimum_due,
        final_due
        )

        # ---- PAYMENT ----
        pay_amount, pay_date = decide_payment(
            behaviour,
            final_due,
            minimum_due,
            statement_month
        )

        if pay_amount > 0:
            cursor.execute("""
                INSERT INTO transactions
                (transaction_id, account_id, transaction_date,
                 amount, transaction_type, transaction_channel,
                 category, merchant, card_id)
                VALUES (?, ?, ?, ?, 'Debit', 'Bank Transfer',
                        'Bills', 'Credit Card Payment', ?)
            """,
            transaction_id,
            account_id,
            pay_date,
            pay_amount,
            card_id
            )
            transaction_id += 1

        # ---- CARRY FORWARD ----
        prev_outstanding = round(final_due - pay_amount, 2)

        statement_id += 1
        current_month = next_month

# ---------------- COMMIT ----------------
conn.commit()
cursor.close()
conn.close()

print("🔥 FINAL SINGLE-LOOP CREDIT CARD LOGIC EXECUTED SUCCESSFULLY")
