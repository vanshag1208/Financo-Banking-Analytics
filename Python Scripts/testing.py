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

# ---------------- CLEAN OLD STATEMENTS ----------------
cursor.execute("TRUNCATE TABLE credit_card_statement")
conn.commit()

# ---------------- IDS ----------------
cursor.execute("SELECT ISNULL(MAX(statement_id),0) FROM credit_card_statement")
statement_id = cursor.fetchone()[0] + 1

cursor.execute("SELECT ISNULL(MAX(transaction_id),0) FROM transactions")
transaction_id = cursor.fetchone()[0] + 1

# ---------------- FETCH CREDIT CARDS ----------------
cursor.execute("""
    SELECT card_id, account_id, credit_limit
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

# ---------------- CUSTOMER TYPE ----------------
def assign_customer_type():
    return random.choices(
        ["DISCIPLINED", "DELAYED", "RISKY"],
        weights=[45, 30, 25]
    )[0]

# ---------------- SPEND LOGIC ----------------
def calculate_spend(customer_type, credit_limit, prev_outstanding):

    # High outstanding → card usage almost blocked
    if prev_outstanding > credit_limit * 0.8:
        return 0.0

    if customer_type in ["DISCIPLINED", "DELAYED"]:
        return round(credit_limit * 0.30, 2)

    # Risky users
    return round(credit_limit * random.uniform(0.4, 0.9), 2)

# ---------------- PAYMENT LOGIC ----------------
def decide_payment(customer_type, final_due, minimum_due, statement_date, prev_outstanding):

    # DISCIPLINED → full & on time
    if customer_type == "DISCIPLINED":
        return final_due, statement_date + timedelta(days=7)

    # DELAYED → full but late
    if customer_type == "DELAYED":
        return final_due, statement_date + timedelta(days=30)

    # RISKY → mostly no payment
    if prev_outstanding > 0 and random.random() < 0.7:
        return 0, None

    # Sometimes minimum payment
    return minimum_due, statement_date + timedelta(days=35)

# ---------------- MAIN LOOP ----------------
for card_id, account_id, credit_limit in cards:

    credit_limit = float(credit_limit)   # 🔥 DECIMAL → FLOAT FIX

    prev_outstanding = 0.0
    customer_type = assign_customer_type()
    current_month = start_month

    while current_month <= end_month:

        next_month = current_month + relativedelta(months=1)
        statement_date = datetime(next_month.year, next_month.month, 1)

        # ---- SPEND ----
        total_spend = calculate_spend(
            customer_type,
            credit_limit,
            prev_outstanding
        )

        # ---- INTEREST ----
        interest_amount = round(prev_outstanding * MONTHLY_RATE, 2)

        # ---- DUES ----
        total_due = total_spend
        final_due = round(total_spend + prev_outstanding + interest_amount, 2)
        minimum_due = max(round(final_due * 0.05, 2), 500)

        # ---- PAYMENT ----
        pay_amount, pay_date = decide_payment(
            customer_type,
            final_due,
            minimum_due,
            statement_date,
            prev_outstanding
        )

        # ---- INSERT STATEMENT (EXACT TABLE MATCH) ----
        cursor.execute("""
            INSERT INTO credit_card_statement
            (statement_id, card_id, account_id,
             statement_month,
             total_spend,
             total_due,
             minimum_due,
             prev_outstanding,
             interest_amount,
             final_due)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        statement_id,
        card_id,
        account_id,
        statement_date.date(),
        total_spend,
        total_due,
        minimum_due,
        prev_outstanding,
        interest_amount,
        final_due
        )

        # ---- INSERT PAYMENT TRANSACTION ----
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

print("CREDIT CARD DATA GENERATED SUCCESSFULLY")
