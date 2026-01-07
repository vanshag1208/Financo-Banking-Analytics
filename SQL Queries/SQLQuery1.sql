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