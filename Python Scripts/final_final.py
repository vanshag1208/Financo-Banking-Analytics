import pyodbc
import random
from faker import Faker
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

fake = Faker()

# =========================================================
# CONFIG
# =========================================================
ANNUAL_INTEREST_RATE = 0.16
MONTHLY_RATE = ANNUAL_INTEREST_RATE / 12

credit_limits = {
    "Silver": 50000,
    "Gold": 150000,
    "Platinum": 300000
}

customer_types = ["DISCIPLINED", "DELAYED", "RISKY", "DEFAULTER"]

categories = ["Food", "Shopping", "Travel", "Bills", "Entertainment", "Groceries"]
merchants = {
    "Food": ["Swiggy", "Zomato"],
    "Shopping": ["Amazon", "Flipkart"],
    "Travel": ["Uber", "IRCTC"],
    "Bills": ["Electricity Board"],
    "Entertainment": ["Netflix"],
    "Groceries": ["Reliance Mart"]
}

# =========================================================
# DB CONNECTION
# =========================================================
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=VANSHPC\\SQLEXPRESS02;"
    "DATABASE=banking_analytics;"
    "Trusted_Connection=yes;"
)
cursor = conn.cursor()

# =========================================================
# CLEAN OLD STATEMENTS
# =========================================================
cursor.execute("TRUNCATE TABLE credit_card_statement")
conn.commit()

# =========================================================
# IDS
# =========================================================
cursor.execute("SELECT ISNULL(MAX(transaction_id),0) FROM transactions")
transaction_id = cursor.fetchone()[0] + 1

cursor.execute("SELECT ISNULL(MAX(statement_id),0) FROM credit_card_statement")
statement_id = cursor.fetchone()[0] + 1

# =========================================================
# FETCH ACCOUNTS
# =========================================================
cursor.execute("SELECT account_id FROM accounts")
accounts = cursor.fetchall()

MONTHS = 24

# =========================================================
# PAYMENT LOGIC (RUNTIME ONLY)
# =========================================================
def decide_payment(customer_type, final_due, minimum_due, statement_date):

    due_date = statement_date + timedelta(days=20)

    # month end cap (safe for all months)
    month_end = statement_date + timedelta(days=29)  # max 30

    # 🟢 DISCIPLINED → full payment before due date
    if customer_type == "DISCIPLINED":
        pay_date = due_date - timedelta(days=random.randint(2, 5))
        return final_due, pay_date

    # 🟡 DELAYED → full payment between 22–30
    if customer_type == "DELAYED":
        pay_date = due_date + timedelta(days=random.randint(1, 9))
        pay_date = min(pay_date, month_end)
        return final_due, pay_date

    # 🟠 RISKY → minimum payment late (22–30) or skip
    if customer_type == "RISKY":
        if random.random() < 0.6:
            return 0, None
        pay_date = due_date + timedelta(days=random.randint(2, 9))
        pay_date = min(pay_date, month_end)
        return minimum_due, pay_date

    # 🔴 DEFAULTER → mostly no payment
    if random.random() < 0.85:
        return 0, None

    # rare minimum payment (still within month)
    pay_date = due_date + timedelta(days=random.randint(5, 9))
    pay_date = min(pay_date, month_end)
    return minimum_due, pay_date


# =========================================================
# MAIN LOOP
# =========================================================
for (account_id,) in accounts:

    # ---- cards ----
    cursor.execute("""
        SELECT card_id FROM cards
        WHERE account_id=? AND card_type='Debit'
    """, account_id)
    dc = cursor.fetchone()
    debit_card_id = dc[0] if dc else None

    cursor.execute("""
        SELECT card_id FROM cards
        WHERE account_id=? AND card_type='Credit'
    """, account_id)
    cc = cursor.fetchone()
    credit_card_id = cc[0] if cc else None

    # ---- runtime behaviour tag (NOT STORED) ----
    customer_type = random.choice(customer_types)

    prev_outstanding = 0.0

    start_month = datetime.now().replace(day=1) - relativedelta(months=MONTHS-1)

    for m in range(MONTHS):

        month_start = start_month + relativedelta(months=m)
        next_month = month_start + relativedelta(months=1)
        statement_date = next_month

        # ================= INCOME =================
        salary = random.randint(25000, 80000)
        interest_income = round(salary * 0.02 / 12, 2)
        monthly_credit = salary + interest_income

        cursor.execute("""
            INSERT INTO transactions VALUES
            (?, ?, ?, ?, 'Credit', 'Bank Transfer',
             'Salary', 'Company', NULL)
        """, transaction_id, account_id, month_start, salary)
        transaction_id += 1

        cursor.execute("""
            INSERT INTO transactions VALUES
            (?, ?, ?, ?, 'Credit', 'Bank Transfer',
             'Interest', 'Bank', NULL)
        """, transaction_id, account_id,
             month_start + timedelta(days=2), interest_income)
        transaction_id += 1

        # ================= TIER =================
        annual_income = salary * 12
        tier = (
            "Platinum" if annual_income >= 1200000 else
            "Gold" if annual_income >= 600000 else
            "Silver"
        )

        credit_limit = credit_limits[tier] if credit_card_id else 0

        if credit_card_id:
            cursor.execute("""
                UPDATE cards SET card_tier=?, credit_limit=?
                WHERE card_id=?
            """, tier, credit_limit, credit_card_id)

        # ================= SPENDS =================
        total_spent = 0
        bank_spent = 0
        total_cap = monthly_credit * random.uniform(0.8, 0.95)
        bank_cap = total_cap * random.uniform(0.5, 0.7)

        # ---- debit spends ----
        for _ in range(random.randint(6, 12)):
            remaining = min(
                bank_cap - bank_spent,
                total_cap - total_spent,
                monthly_credit - bank_spent
            )
            if remaining <= 0:
                break

            amt = min(random.randint(500, 15000), remaining)

            category = random.choice(categories)
            merchant = random.choice(merchants[category])

            cursor.execute("""
                INSERT INTO transactions VALUES
                (?, ?, ?, ?, 'Debit', 'Debit Card',
                 ?, ?, ?)
            """,
            transaction_id, account_id,
            fake.date_between(month_start, month_start + timedelta(days=25)),
            amt, category, merchant, debit_card_id)

            transaction_id += 1
            bank_spent += amt
            total_spent += amt

        # ---- credit card spends ----
        credit_spent = 0
        if credit_card_id:
            usage_cap = min(
                credit_limit * random.uniform(0.25, 0.6),
                total_cap - total_spent
            )

            for _ in range(random.randint(3, 6)):
                amt = random.randint(2000, 12000)
                if credit_spent + amt > usage_cap:
                    break

                cursor.execute("""
                    INSERT INTO transactions VALUES
                    (?, ?, ?, ?, 'Debit', 'Credit Card',
                     'Shopping', 'Amazon', ?)
                """,
                transaction_id, account_id,
                fake.date_between(month_start, month_start + timedelta(days=25)),
                amt, credit_card_id)

                transaction_id += 1
                credit_spent += amt
                total_spent += amt

        # ================= STATEMENT =================
        interest_amount = round(prev_outstanding * MONTHLY_RATE, 2)
        final_due = round(prev_outstanding + credit_spent + interest_amount, 2)
        minimum_due = max(round(final_due * 0.05, 2), 500)

        pay_amount, pay_date = decide_payment(
            customer_type, final_due, minimum_due, statement_date
        )

        cursor.execute("""
            INSERT INTO credit_card_statement VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        statement_id, credit_card_id, account_id,
        statement_date.date(),
        credit_spent,
        credit_spent,
        minimum_due,
        prev_outstanding,
        interest_amount,
        final_due)

        # ---- payment transaction ----
        if pay_amount and pay_date:
            cursor.execute("""
                INSERT INTO transactions VALUES
                (?, ?, ?, ?, 'Debit', 'Bank Transfer',
                 'Bills', 'Credit Card Payment', ?)
            """,
            transaction_id, account_id, pay_date, pay_amount, credit_card_id)
            transaction_id += 1

        prev_outstanding = round(final_due - (pay_amount or 0), 2)
        statement_id += 1

# =========================================================
# COMMIT & CLOSE
# =========================================================
conn.commit()
cursor.close()
conn.close()

print("🔥 FULL BANKING SIMULATION COMPLETED SUCCESSFULLY")
