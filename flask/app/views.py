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

# Create dictionary for navbar and make it global for all templates
href_dict = {
    "Home": "/", 
    "Accounts": "/accounts",
    "Payees": "/payees",
    "Categories": "/categories",
    }


@app.context_processor
def inject_dict_for_all_templates():
    return dict(href_dict=href_dict)


# All Flask modules

@app.route("/")
@login_required
def index():
    """Homepage"""
    st_name = "Home"
    # Use os.getenv("key") to get environment variables
    app_name = os.getenv("YHB")
    return render_template("index.html", st_name=st_name)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    if request.method == "POST":
        # Forget any user_id
        session.clear()
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
        if 'user_id' in session:
            flash("You are already logged in", "info")
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
            if not request.form.get("re_password") or request.form.get("password") != request.form.get("re_password"):
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
    today = datetime.now().strftime('%Y-%m-%d')
    st_name = "Accounts"
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
            total_accounts = round(float(total_accounts), 2)
            account_dict["account_hide"] = acc[4]
            user_accounts_list.append(account_dict)
    con.close()

    return render_template(
        "accounts.html", user_accounts_list=user_accounts_list, 
        total_accounts=total_accounts, st_name=st_name, today=today)


@app.route("/transfer", methods=["POST"])
@login_required
def transfer():
    # TO DO 
    return redirect("/accounts")


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
                """SELECT * FROM account WHERE user_id = ? 
                AND account_name = ?""", (user_id, account_name))
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
    """Edit details of account"""
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
            starting_balance = account_db[3]
            account_hide = int(account_db[4])
        con.close()
        return render_template("account_edit.html", account_name=account_name,
        starting_balance=starting_balance, account_hide=account_hide)


@app.route("/account/<account_name>")
@login_required
def account(account_name):
    """List of all transactions in the account"""
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
        category_list_dict=category_list_dict, 
        trans_list_dict=trans_list_dict)


@app.route("/add_transaction", methods=["POST"])
@login_required
def add_transaction():
    """Add new transaction"""
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
        return redirect(f"/transaction/{ transaction_id }")
    else:
        transaction_id = int(transaction_id)
        with sql.connect("sqlite.db") as con:
            cur = con.cursor()
            cur.execute(
                "SELECT * FROM transactions WHERE transaction_id = ?", 
                (transaction_id,))
            transaction_db = cur.fetchone()
            if (not transaction_db 
                or transaction_id != transaction_db[0] 
                or session["user_id"] != transaction_db[5]):
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
            cur.execute(
                "SELECT account_name FROM account WHERE account_id = ?",
                (account_id,))
            account_name = cur.fetchone()[0]
        con.close()
        return render_template(
            "transaction.html", date=date, tran_type=tran_type, amount=amount,
            transaction_id=transaction_id, 
            payee_list_dict=payee_list_dict, payee_name=payee_name, 
            category_list_dict=category_list_dict, 
            category_name=category_name, account_list_dict=account_list_dict, 
            account_name=account_name)


@app.route("/delete_transaction/<transaction_id>")
@login_required
def delete_transaction(transaction_id):
    """Delete transaction"""
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
    """List of all user's payees"""
    st_name = "Payees"
    with sql.connect("sqlite.db") as con:
        cur = con.cursor()
        payee_list_dict = payee_list_from_db(session["user_id"], cur)
        for payee in payee_list_dict:
            cur.execute(
                "SELECT MAX(date) FROM transactions WHERE payee_id = ?",
                (payee["payee_id"],))
            payee["last_paid"] = cur.fetchone()[0]
    con.close()
    return render_template("payees.html", payee_list_dict=payee_list_dict, 
                           st_name=st_name)


@app.route("/add_payee", methods=["POST"])
@login_required
def payee_add():
    """Add new payee"""
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
    """Preview of selected payee"""
    with sql.connect("sqlite.db") as con:
        cur = con.cursor()
        # payee name
        cur.execute("SELECT * FROM payee WHERE payee_id = ?", (payee_id,))
        payee_db = cur.fetchall()[0]
        payee_name = payee_db[1]
        description = payee_db[3]
        if description == None:
            description = ""
        # category list
        category_list_dict = category_list_from_db(session["user_id"], cur)
        # account list
        account_list_dict = account_list_from_db(session["user_id"], cur)
        # transaction list
        cur.execute(
            """SELECT * FROM transactions WHERE user_id = ? AND payee_id = ? 
            ORDER BY date""", (session["user_id"], payee_id))
        trans_db = cur.fetchall()
    con.close()
    total = 0
    trans_list_dict = []
    for tran in trans_db:
        tran_dict = {}
        tran_dict["transaction_id"] = tran[0]
        tran_dict["date"] = tran[1]
        tran_dict["payee_id"] = tran[2]
        tran_dict["payee_name"] = payee_name
        tran_dict["category_id"] = tran[3]
        for cat in category_list_dict:
            if cat["category_id"] == tran[3]:
                tran_dict["category_name"] = cat["category_name"]
        tran_dict["amount"] = tran[4]
        total = round(float(total + tran[4]), 2)
        tran_dict["user_id"] = tran[5]
        tran_dict["account_id"] = tran[6]
        for acc in account_list_dict:
            if acc["account_id"] == tran[6]:
                tran_dict["account_name"] = acc["account_name"]
        trans_list_dict.append(tran_dict)

    return render_template("payee.html", payee_name=payee_name, total=total, 
                           trans_list_dict=trans_list_dict, payee_id=payee_id,
                           description=description)


@app.route("/payee_edit/<payee_id>", methods=["POST", "GET"])
@login_required
def payee_edit(payee_id):
    """Edit detail of payee"""
    if request.method == "POST":
        new_payee_name = request.form.get("payee_name")
        new_description = request.form.get("description")
        with sql.connect("sqlite.db") as con:
            cur = con.cursor()
            cur.execute("""UPDATE payee SET payee_name = ?, description = ?
                        WHERE payee_id = ?""", 
                        (new_payee_name, new_description, payee_id,))
            con.commit()
        con.close()
        flash("Payee successfully edited", "info")
        return redirect(f"/payee/{payee_id}")
    else:
        with sql.connect("sqlite.db") as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM payee WHERE payee_id = ?", (payee_id,))
            payee_db = cur.fetchall()[0]
            user_id = payee_db[2]
            if user_id != session["user_id"]:
                flash("Error", "error")
                return redirect("/")
            payee_name = payee_db[1]
            description = payee_db[3]
        con.close()
        return render_template("payee_edit.html", payee_id=payee_id, 
                               payee_name=payee_name, description=description)


@app.route("/categories")
@login_required
def categories():
    """List of all user's categories"""
    st_name = "Categories"
    with sql.connect("sqlite.db") as con:
        cur = con.cursor()
        category_list_dict = category_list_from_db(session['user_id'], cur)
        for cat in category_list_dict:
            cur.execute(
                "SELECT MAX(date) FROM transactions WHERE category_id = ?",
                (cat["category_id"],))
            cat["last_paid"] = cur.fetchone()[0]
    con.close()
    return render_template(
        "categories.html", category_list_dict=category_list_dict, 
        st_name=st_name)


@app.route("/category_add", methods=["POST"])
@login_required
def category_add():
    """Add new category"""
    with sql.connect("sqlite.db") as con:
        cur = con.cursor()
        cur.execute(
            """SELECT category_id FROM category 
            WHERE category_name = ? AND user_id = ?""", 
            (request.form.get("category_name"), session["user_id"]))
        category_id = cur.fetchone()
        if not category_id:
            cur.execute(
                """INSERT INTO category (category_name, user_id) 
                VALUES (?, ?)""", 
                (request.form.get("category_name"),session["user_id"]))
            con.commit()
    con.close()
    return redirect("/categories")


@app.route("/category/<category_id>")
@login_required
def category(category_id):
    """Preview of selected category"""
    with sql.connect("sqlite.db") as con:
        cur = con.cursor()
        # payee name
        cur.execute(
            "SELECT category_name FROM category WHERE category_id = ?",
            (category_id,))
        category_name = cur.fetchone()[0]
        # category list
        payee_list_dict = payee_list_from_db(session["user_id"], cur)
        # account list
        account_list_dict = account_list_from_db(session["user_id"], cur)
        # transaction list
        cur.execute(
            """SELECT * FROM transactions 
            WHERE user_id = ? AND category_id = ? ORDER BY date""", 
            (session["user_id"], category_id))
        trans_db = cur.fetchall()
    con.close()
    total = 0
    trans_list_dict = []
    for tran in trans_db:
        tran_dict = {}
        tran_dict["transaction_id"] = tran[0]
        tran_dict["date"] = tran[1]
        tran_dict["payee_id"] = tran[2]
        for pay in payee_list_dict:
            if pay["payee_id"] == tran[2]:
                tran_dict["payee_name"] = pay["payee_name"]
        tran_dict["category_id"] = tran[3]
        tran_dict["category_name"] = category_name
        tran_dict["amount"] = tran[4]
        total = round(float(total + tran[4]), 2)
        tran_dict["user_id"] = tran[5]
        tran_dict["account_id"] = tran[6]
        for acc in account_list_dict:
            if acc["account_id"] == tran[6]:
                tran_dict["account_name"] = acc["account_name"]
        trans_list_dict.append(tran_dict)

    return render_template("category.html", category_name=category_name, 
                           trans_list_dict=trans_list_dict, total=total)


@app.route("/category_edit/<category_id>", methods=["POST", "GET"])
@login_required
def category_edit(category_id):
    # TO DO
    return redirect("/")


@app.route("/login_change", methods=["POST", "GET"])
@login_required
def login_change():
    if request.method == "POST":
        return redirect("/")
    else:
        return render_template("login_change.html")


@app.route("/password_change", methods=["POST", "GET"])
@login_required
def password_change():
    if request.method == "POST":
        return redirect("/")
    else:
        return render_template("password_change.html")


@app.route("/user_delete", methods=["POST", "GET"])
@login_required
def settings():
    if request.method == "POST":
        with sql.connect("sqlite.db") as con:
            cur = con.cursor()
            user_id = session["user_id"]
            cur.execute("SELECT hash FROM users WHERE user_id = ?",(user_id,))
            hash_db = cur.fetchone()[0]
            # Check in database if user exists
            if not hash_db:
                flash("Error in database", "error")
                return redirect("/")
            # Check correctness of password
            if not check_password_hash(hash_db, request.form.get("password")):
                flash("Incorrect password", "error")
                return redirect("/")
            cur.execute("DELETE FROM transactions WHERE user_id = ?", 
                        (user_id,))
            cur.execute("DELETE FROM payee WHERE user_id = ?", (user_id,))
            cur.execute("DELETE FROM category WHERE user_id = ?", (user_id,))
            cur.execute("DELETE FROM account WHERE user_id = ?", (user_id,))
            cur.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            con.commit()
        con.close()
        session.clear()
        flash("Account deleted", "info")
        return redirect("/")
    else:
        return render_template("user_delete.html")