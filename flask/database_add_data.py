import sqlite3 as sql
from random import choice, uniform
from datetime import datetime

# Add data to database
with sql.connect("sqlite.db") as con:
    db = con.cursor()

    payee_id_list = [1, 2, 3, 4]
    category_id_list = [1, 2, 3, 4]
    user_id = 1
    account_id = 1

    year = 2020
    month = 1
    for m in range(0, 12):
        if month in [1, 3, 5, 7, 8, 10, 12]:
            day = 1
            for d in range(0, 30):

                date = datetime(year, month, day).strftime('%Y-%m-%d')
                payee_id = choice(payee_id_list)
                category_id = choice(category_id_list)
                amount = round(uniform(0.01, 1100.00), 2) * -1

                db.execute("""INSERT INTO transactions 
                    (date, payee_id, category_id, amount, user_id, account_id)
                    VALUES (?, ?, ?, ?, ?, ?)""", 
                    (date, payee_id, category_id, amount, user_id, account_id))
                day += 1

        elif month in [4, 6, 9, 11]:
            day = 1
            for d in range(0, 29):

                date = datetime(year, month, day).strftime('%Y-%m-%d')
                payee_id = choice(payee_id_list)
                category_id = choice(category_id_list)
                amount = round(uniform(0.01, 1100.00), 2) * -1

                db.execute("""INSERT INTO transactions 
                    (date, payee_id, category_id, amount, user_id, account_id)
                    VALUES (?, ?, ?, ?, ?, ?)""", 
                    (date, payee_id, category_id, amount, user_id, account_id))
                day += 1
        else:
            day = 1
            for d in range(0, 27):

                date = datetime(year, month, day).strftime('%Y-%m-%d')
                payee_id = choice(payee_id_list)
                category_id = choice(category_id_list)
                amount = round(uniform(0.01, 1100.00), 2) * -1

                db.execute("""INSERT INTO transactions 
                    (date, payee_id, category_id, amount, user_id, account_id)
                    VALUES (?, ?, ?, ?, ?, ?)""", 
                    (date, payee_id, category_id, amount, user_id, account_id))
                day += 1
        month += 1
con.close()