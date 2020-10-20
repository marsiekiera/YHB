from app import app
import os
from tempfile import mkdtemp
from flask import render_template, request, redirect, flash, session
import sqlite3 as sql
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from app.helpers import (check_password, login_required, only_digit, 
    payee_list_from_db, category_list_from_db, transaction_list_from_db,
    account_list_from_db, amount_uni)

# Templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"


@app.route("/")
@login_required
def index():
    """Homepage"""
    # Use os.getenv("key") to get environment variables
    app_name = os.getenv("YHB")
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()
    if request.method == "POST":
        # connect with database
        with sql.connect("sqlite.db") as con:
            con.row_factory = sql.Row
            cur = con.cursor()
            user_name = str.lower(request.form.get("user_name"))
            if not user_name:
                flash("Please provide User Name", "error")
                return redirect("/login")
            cur.execute(
                "SELECT * FROM users WHERE user_name = ?", (user_name,))
            records = cur.fetchall()
            # Check in database if user exists
            if not records:
                flash("Incorrect user name", "error")
                return redirect("/login")
            for row in records:
                user_id = row[0]
                user_name = row[1]
                hash_password = row[2]
            # Check correctness of password
            if not check_password_hash(hash_password, 
                                       request.form.get("password")):
                flash("Incorrect password", "error")
                return redirect("/login")
            # Remember which user has logged in
            session["user_id"] = user_id
            session["user_name"] = user_name
        con.close()

        flash("You were successfully logged in", "info")
        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # connect with database
        with sql.connect("sqlite.db") as con:
            con.row_factory = sql.Row
            cur = con.cursor()
            user_name = str.lower(request.form.get("user_name"))
            if not user_name:
                flash("Please provide User Name", "error")
                return redirect("/register")
            # Check in database if user already exists
            cur.execute("SELECT * FROM users WHERE user_name = ?", 
                        (user_name,))
            if cur.fetchone():
                flash("User already exists", "error")
                return redirect("/register")
            # Check correctness of password
            if not request.form.get("password"):
                flash("Please provide password", "error")
                return redirect("/register")
            elif not (request.form.get("re_password") or 
                     request.form.get("password") != 
                     request.form.get("re_password")):
                flash("Please re-type the same password", "error")
                return redirect("/register")
            elif not check_password(request.form.get("password")):
                flash(
                    """Please provide password with at least one uppercase and 
                    lowercase letter, a number and a symbol.""", "error")
                return redirect("/register")
            # Create hash password
            hash_password = generate_password_hash(
                request.form.get("password"))
            # Add user to database
            cur.execute("INSERT INTO users (user_name, hash) VALUES (?, ?)", 
                        (user_name, hash_password))
            con.commit()
        con.close()
        flash("You have successfully register. You can login now.", "info")
        return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect("/")


@app.route("/accounts")
@login_required
def accounts():
    """List of all accounts and balance"""
    user_id = session["user_id"]
    user_accounts_list = []
    with sql.connect("sqlite.db") as con:
        cur = con.cursor()
        cur.execute(
            """SELECT * FROM account WHERE user_id = ? 
            ORDER BY account_name COLLATE NOCASE ASC""", 
            (user_id,))
        user_accounts = cur.fetchall()
        if not user_accounts:
            flash("You don't have any account", "error")
            return redirect("/")
        total_accounts = 0 # total balance all accounts
        for acc in user_accounts:
            account_dict = {}
            account_dict["account_id"] = acc[0]
            account_dict["account_name"] = acc[1]
            balance = acc[3] # starting balance
            cur.execute("""SELECT * FROM transactions 
                        WHERE user_id = ? AND account_id = ?""", 
                        (user_id, account_dict["account_id"]))
            trans_db = cur.fetchall()
            for tran in trans_db:
                balance = round(float(balance + tran[4]), 2)
            account_dict["balance"] = balance # current balance
            total_accounts += balance
            account_dict["account_hide"] = acc[4]
            user_accounts_list.append(account_dict)
    con.close()

    return render_template(
        "accounts.html", user_accounts_list=user_accounts_list, 
        total_accounts=total_accounts)


@app.route("/add_account", methods=["POST", "GET"])
@login_required
def add_account():
    """Create new user's account"""
    if request.method == "POST":
        # connect with database
        with sql.connect("sqlite.db") as con:
            cur = con.cursor()
            user_id = session["user_id"]
            account_name = request.form.get("account_name")
            # Check in database if user already have account with that name
            cur.execute(
                "SELECT * FROM account WHERE user_id = ? AND account_name = ?",
                (user_id, account_name))
            if cur.fetchone():
                flash("You already have an account with that name", "error")
                return redirect("/add_account")
            if not request.form.get("starting_balance"):
                starting_balance = 0.00
            else:
                starting_balance = round(float(
                    request.form.get("starting_balance").replace(',','.')), 2)
            # Add new user's account to database
            cur.execute(
                """INSERT INTO account 
                (account_name, user_id, starting_balance) VALUES (?, ?, ?)""", 
                (account_name, user_id, starting_balance))
            con.commit()  
        con.close()

        flash("You have successfully add new account", "info")
        return redirect("/")
    else:
        return render_template("account_add.html")


@app.route("/edit_account/<account_name>", methods=["POST", "GET"])
@login_required
def edit_account(account_name):
    if request.method == "POST":
        new_account_name = request.form.get("account_name")
        new_starting_balance = request.form.get("starting_balance")
        account_hide = 1 if request.form.get("account_hide") == "on" else 0
        with sql.connect("sqlite.db") as con:
            cur = con.cursor()
            cur.execute("""UPDATE account SET account_name = ?, 
                        starting_balance = ?, account_hide = ?
                        WHERE account_id = ?""", 
                        (new_account_name, new_starting_balance, account_hide,
                        session['account_id']))
            con.commit()
        con.close
        session['account_name'] = new_account_name
        flash("Changes saved", "info")
        return redirect(f"/account/{ session['account_name'] }")
    else:
        with sql.connect("sqlite.db") as con:
            cur = con.cursor()
            cur.execute("""SELECT * FROM account WHERE account_id = ?""", 
                        (session["account_id"],))
            account_db = cur.fetchall()[0]
            print(account_db)
            starting_balance = account_db[3]
            account_hide = int(account_db[4])
        con.close()
        return render_template("account_edit.html", account_name=account_name,
        starting_balance=starting_balance, account_hide=account_hide)


@app.route("/account/<account_name>")
@login_required
def account(account_name):
    """ List of all transactions in the account"""
    user_id = session["user_id"]
    session["account_name"] = account_name
    today = datetime.now().strftime('%Y-%m-%d')

    with sql.connect("sqlite.db") as con:
        cur = con.cursor()
        # create session account id
        cur.execute("""SELECT * FROM account WHERE user_id = ? 
            AND account_name = ?""", (user_id, account_name))
        account_db = cur.fetchall()[0]
        session["account_id"] = account_db[0]
        starting_balance = account_db[3]
        # user's payee list of dict using payee_list function
        payee_list_dict = payee_list_from_db(user_id, cur)
        # user's category list of dict using category_list function
        category_list_dict = category_list_from_db(user_id, cur)
        # user's transactions list of dict using transaction_list function
        trans_list_dict_db = transaction_list_from_db(user_id, cur, 
                                                      payee_list_dict, 
                                                      category_list_dict)
        trans_list_dict = trans_list_dict_db[0]
        total = trans_list_dict_db[1] + starting_balance
    con.close()

    return render_template("account.html", account_name=account_name, 
        today=today, payee_list_dict=payee_list_dict, total=total,
        category_list_dict=category_list_dict, trans_list_dict=trans_list_dict)


@app.route("/add_transaction", methods=["POST"])
@login_required
def add_transaction():
    user_id = session["user_id"]
    account_id = session["account_id"]
    # Amount
    amount_form = request.form.get("amount")
    trans_type = int(request.form.get("transaction_type"))
    print(amount_form)
    if not only_digit(amount_form):
        flash("Amount incorrect", "error")
        return redirect(f"/account/{ session['account_name'] }")
    amount = amount_uni(amount_form) * trans_type
    # Connect with database
    with sql.connect("sqlite.db") as con:
        cur = con.cursor()
        # select payee_id from db
        cur.execute("""SELECT payee_id FROM payee WHERE user_id = ? 
            AND payee_name = ?""", (user_id, request.form.get("payee")))
        payee_id = cur.fetchone()[0]
        # selecy category_id from db
        cur.execute("""SELECT category_id FROM category WHERE user_id = ? 
            AND category_name = ?""", (user_id, request.form.get("category")))
        category_id = cur.fetchone()[0]
        # insert transaction to db
        cur.execute("""INSERT INTO transactions 
            (date, payee_id, category_id, amount, user_id, account_id)
            VALUES (?, ?, ?, ?, ?, ?)""", (request.form.get("date"), payee_id,
            category_id, amount, user_id, account_id))
        con.commit()      
    con.close()
    flash("Transaction successfully added", "info")
    return redirect(f"/account/{ session['account_name'] }")


@app.route("/transaction/<transaction_id>", methods=["POST", "GET"])
@login_required
def transaction(transaction_id):
    """Edit transaction"""
    with sql.connect("sqlite.db") as con:
        cur =  con.cursor()
        # user's payee list of dict using payee_list function
        payee_list_dict = payee_list_from_db(session["user_id"], cur)
        # user's category list of dict using category_list function
        category_list_dict = category_list_from_db(session["user_id"], cur)
        # user's accounts list of dict using account_list function
        account_list_dict = account_list_from_db(session["user_id"], cur)
    con.close()

    if request.method == "POST":
        for pay in payee_list_dict:
            if pay["payee_name"] == request.form.get("payee"):
                payee_id = pay["payee_id"]
        for cat in category_list_dict:
            if cat["category_name"] == request.form.get("category"):
                category_id = cat["category_id"]
        for acc in account_list_dict:
            if acc["account_name"] == request.form.get("account"):
                account_id = acc["account_id"]
        amount = (amount_uni(request.form.get("amount")) 
                    * int(request.form.get("transaction_type")))
        with sql.connect("sqlite.db") as con:
            cur =  con.cursor()
            cur.execute("""
                UPDATE transactions 
                SET date = ?, payee_id = ?, category_id = ?, amount = ?, 
                account_id = ?
                WHERE transaction_id = ?
                """, (request.form.get("date"), payee_id, category_id, amount, 
                account_id, transaction_id))
            con.commit()
        con.close()
        flash("Transaction successfully edited", "info")
        return redirect(f"/account/{ session['account_name'] }")
    else:
        account_name = session["account_name"]
        account_id = session["account_id"]
        transaction_id = int(transaction_id)
        with sql.connect("sqlite.db") as con:
            cur = con.cursor()
            cur.execute(
                "SELECT * FROM transactions WHERE transaction_id = ?", 
                (transaction_id,))
            transaction_db = cur.fetchone()
            if (not transaction_db 
                or transaction_id != transaction_db[0] 
                or session["user_id"] != transaction_db[5] 
                or account_id != transaction_db[6]):
                flash("Database error. Contact with admin", "error")
                return redirect("/")

            date = transaction_db[1]
            payee_id = transaction_db[2]
            category_id = transaction_db[3]
            amount = transaction_db[4]
            account_id = transaction_db[6]
            if amount > 0:
                tran_type = "Deposit"
            else:
                tran_type = "Withdrawal"
                amount *= -1
            cur.execute("SELECT payee_name FROM payee WHERE payee_id = ?",
                        (payee_id,))
            payee_name = cur.fetchone()[0]

            cur.execute(
                "SELECT category_name FROM category WHERE category_id = ?",
                (category_id,))
            category_name = cur.fetchone()[0]
        con.close()
        return render_template(
            "transaction.html", date=date, tran_type=tran_type, amount=amount,
            transaction_id=transaction_id, 
            payee_list_dict=payee_list_dict, payee_name=payee_name, 
            category_list_dict=category_list_dict, category_name=category_name,
            account_list_dict=account_list_dict, account_name=account_name)


@app.route("/delete_transaction/<transaction_id>")
@login_required
def delete_transaction(transaction_id):
    with sql.connect("sqlite.db") as con:
        cur = con.cursor()
        cur.execute("DELETE FROM transactions WHERE transaction_id = ?", 
                    (transaction_id,))
        con.commit()
    con.close()
    flash("Transaction deleted", "info")
    return redirect(f"/account/{ session['account_name'] }")


@app.route("/payees")
@login_required
def payees():
    with sql.connect("sqlite.db") as con:
        cur = con.cursor()
        payee_list_dict = payee_list_from_db(session["user_id"], cur)
        for payee in payee_list_dict:
            cur.execute(
                "SELECT MAX(date) FROM transactions WHERE payee_id = ?",
                (payee["payee_id"],))
            payee["last_paid"] = cur.fetchone()[0]
    con.close()
    return render_template("payees.html", payee_list_dict=payee_list_dict)


@app.route("/add_payee", methods=["POST"])
@login_required
def payee_add():
    with sql.connect("sqlite.db") as con:
        cur = con.cursor()
        cur.execute("""INSERT INTO payee (payee_name, user_id, description) 
                    VALUES (?, ?, ?)""", (request.form.get("payee_name"),
                    session["user_id"], request.form.get("description")))
        con.commit()
    con.close()
    flash("Payee added", "info")
    return redirect("/payees")


@app.route("/payee/<payee_id>")
@login_required
def payee(payee_id):
    redirect("/")


# to do
@app.route("/categories", methods=["POST", "GET"])
@login_required
def categories():
    if request.method == "POST":
        return redirect("/")
    
        with sql.connect("sqlite.db") as con:
            con.row_factory = sql.Row
            cur = con.cursor()

            cur.execute("""SELECT category_id FROM category WHERE 
            category_name = ? AND user_id = ?""", (category, user_id))
            category_id = cur.fetchone()
            
            if not category_id:
                # Add new category to database
                cur.execute("""INSERT INTO category (category_name, user_id) 
                    VALUES (?, ?)""", (category, user_id))
                con.commit()
                cur.execute("""SELECT category_id FROM category 
                    WHERE category_name = ? AND user_id = ?""", 
                    (category, user_id))
                category_id = cur.fetchone()
                print(f"category_id = { category_id }")
        con.close()
    else:
        return redirect("/")