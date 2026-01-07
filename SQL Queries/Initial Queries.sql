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


