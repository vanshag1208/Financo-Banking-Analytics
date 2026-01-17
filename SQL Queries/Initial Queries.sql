CREATE DATABASE banking_analytics;


USE banking_analytics

CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    full_name VARCHAR(100),
    age INT,
    city VARCHAR(50),
    join_date DATE
);

CREATE TABLE accounts (
    account_id INT PRIMARY KEY,
    customer_id INT,
    account_type VARCHAR(30),
    balance DECIMAL(12,2),
    open_date DATE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE transactions (
    transaction_id INT PRIMARY KEY,
    account_id INT,
    transaction_date DATE,
    amount DECIMAL(10,2),
    transaction_type VARCHAR(10),
    category VARCHAR(50),
    merchant VARCHAR(100),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

CREATE INDEX idx_txn_date ON transactions(transaction_date);
CREATE INDEX idx_txn_account ON transactions(account_id);
CREATE INDEX idx_txn_type ON transactions(transaction_type);

SELECT * FROM accounts

SELECT * FROM customers

SELECT * FROM transactions

CREATE TABLE cards (
    card_id INT PRIMARY KEY,                  
    account_id INT NOT NULL,                  

    card_type VARCHAR(10) NOT NULL,            
    card_tier VARCHAR(20) NOT NULL,            

    masked_card_number VARCHAR(25) NOT NULL,   

    credit_limit DECIMAL(12,2) NULL,           
    expiry_date DATE NOT NULL,

    card_image_url VARCHAR(255),               

    created_at DATETIME DEFAULT GETDATE(),

    CONSTRAINT fk_cards_account
        FOREIGN KEY (account_id)
        REFERENCES accounts(account_id)
);

SELECT * from cards

DROP TABLE transactions;

CREATE TABLE transactions (
    transaction_id INT PRIMARY KEY,
    account_id INT NOT NULL,

    transaction_date DATETIME NOT NULL,
    amount DECIMAL(12,2) NOT NULL,

    transaction_type VARCHAR(10) NOT NULL,     
    transaction_channel VARCHAR(20) NOT NULL,  

    category VARCHAR(50),
    merchant VARCHAR(100),

    card_id INT NULL,

    CONSTRAINT fk_txn_account
        FOREIGN KEY (account_id)
        REFERENCES accounts(account_id),

    CONSTRAINT fk_txn_card
        FOREIGN KEY (card_id)
        REFERENCES cards(card_id)
);

SELECT * from transactions
where category = 'Bills'


TRUNCATE TABLE transactions;

SELECT transaction_type, COUNT(*)
FROM transactions
GROUP BY transaction_type;

UPDATE transactions
SET merchant = 'Company'
WHERE merchant IN ('TCS', 'Infosys', 'Accenture', 'Google', 'Amazon');

TRUNCATE TABLE credit_card_statement

SELECT * from credit_card_statement

CREATE TABLE credit_card_statement (
    statement_id INT PRIMARY KEY,
    card_id INT,
    account_id INT,
    statement_month DATE,
    total_spend DECIMAL(12,2),
    total_due DECIMAL(12,2),
    minimum_due DECIMAL(12,2)
);

CREATE TABLE credit_card_statement (
    statement_id INT PRIMARY KEY,
    card_id INT,
    account_id INT,
    statement_month DATE,
    total_spend DECIMAL(12,2),
    total_due DECIMAL(12,2),
    minimum_due DECIMAL(12,2),
    due_date DATE,
    payment_status VARCHAR(20),
    payment_date DATE
);

DELETE FROM transactions
WHERE category = 'Bills'
  AND merchant = 'Credit Card Payment';

ALTER TABLE credit_card_statement
ADD
    prev_outstanding   DECIMAL(14,2),
    interest_amount    DECIMAL(14,2),
    final_due          DECIMAL(14,2);

SELECT * FROM transactions
WHERE category = 'Bills'
  AND merchant = 'Credit Card Payment'

 SELECT * FROM credit_card_statement
 WHERE account_id ='98'
 ORDER BY statement_month

UPDATE accounts
SET balance = NULL;



-- Late Customers Count 
SELECT
    COUNT(DISTINCT account_id) AS late_customers
FROM (
    SELECT
        s.account_id
    FROM credit_card_statement s
    LEFT JOIN transactions t
        ON s.account_id = t.account_id
        AND t.merchant = 'Credit Card Payment'
        AND t.transaction_date
            BETWEEN s.statement_month
                AND DATEADD(DAY, 20, s.statement_month)
    GROUP BY
        s.statement_id,
        s.account_id,
        s.statement_month,
        s.final_due
    HAVING
        DATEADD(DAY, 20, s.statement_month) < GETDATE()
        AND ISNULL(SUM(t.amount), 0) < s.final_due
) late_accounts;




--Update Cards URL
UPDATE cards
SET card_image_url =
    CASE
        WHEN card_type = 'Credit' AND card_tier = 'Silver'
            THEN 'https://raw.githubusercontent.com/vanshag1208/Financo-Banking-Analytics/main/images/cards/credit_silver.png'

        WHEN card_type = 'Credit' AND card_tier = 'Gold'
            THEN 'https://raw.githubusercontent.com/vanshag1208/Financo-Banking-Analytics/main/images/cards/credit_gold.png'

        WHEN card_type = 'Credit' AND card_tier = 'Platinum'
            THEN 'https://raw.githubusercontent.com/vanshag1208/Financo-Banking-Analytics/main/images/cards/credit_platinum.png'
    END
WHERE card_type = 'Credit';


