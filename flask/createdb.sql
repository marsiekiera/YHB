CREATE TABLE users (user_id INTEGER PRIMARY KEY, 
user_name TEXT NOT NULL, hash TEXT NOT NULL);

CREATE TABLE account (account_id INTEGER PRIMARY KEY, 
account_name TEXT NOT NULL, user_id INTEGER NOT NULL, 
starting_balance REAL DEFAULT 0, account_hide INTEGER DEFAULT 0);

CREATE TABLE category (category_id INTEGER PRIMARY KEY, 
category_name TEXT NOT NULL, user_id INTEGER NOT NULL);

CREATE TABLE payee (payee_id INTEGER PRIMARY KEY, 
payee_name TEXT NOT NULL, user_id INTEGER NOT NULL);

CREATE TABLE transactions (transaction_id INTEGER PRIMARY KEY, 
date TEXT NOT NULL, payee_id INTEGER NOT NULL, 
category_id INTEGER NOT NULL, amount REAL NOT NULL, 
user_id INTEGER NOT NULL, account_id INTEGER NOT NULL);