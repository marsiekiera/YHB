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
                flash("Please provide User Name", "danger")
                return redirect("/login")
            cur.execute(
                "SELECT * FROM users WHERE user_name = ?", (user_name,))
            records = cur.fetchall()
            # Check in database if user exists
            if not records:
                flash("Incorrect user name", "danger")
                return redirect("/login")
            for row in records:
                user_id = row["user_id"]
                user_name = row["user_name"]
                hash_password = row["hash"]
            # Check correctness of password
            if not check_password_hash(hash_password, 
                                       request.form.get("password")):
                flash("Incorrect password", "danger")
                return redirect("/login")
            # Remember which user has logged in
            session["user_id"] = user_id
            session["user_name"] = user_name
        con.close()

        flash("You were successfully logged in", "success")
        return redirect("/")
    else:
        if 'user_id' in session:
            flash("You are already logged in", "success")
            return redirect("/")
        else:
            return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # connect with database
        with sql.connect("sqlite.db") as con:
            cur = con.cursor()
            user_name = str.lower(request.form.get("user_name"))
            if not user_name:
                flash("Please provide User Name", "danger")
                return redirect("/register")
            # Check in database if user already exists
            cur.execute("SELECT * FROM users WHERE user_name = ?", 
                        (user_name,))
            if cur.fetchone():
                flash("User already exists", "danger")
                return redirect("/register")
            # Check correctness of password
            if not request.form.get("password"):
                flash("Please provide password", "danger")
                return redirect("/register")
            if not request.form.get("re_password") or request.form.get("password") != request.form.get("re_password"):
                flash("Please re-type the same password", "danger")
                return redirect("/register")
            elif not check_password(request.form.get("password")):
                flash(
                    """Please provide password with at least one uppercase and 
                    lowercase letter, a number and a symbol.""", "danger")
                return redirect("/register")
            # Create hash password
            hash_password = generate_password_hash(
                request.form.get("password"))
            # Add user to database
            cur.execute("INSERT INTO users (user_name, hash) VALUES (?, ?)", 
                        (user_name, hash_password))
            con.commit()
        con.close()
        flash("You have successfully register. You can login now.", "success")
        return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()
    flash("You have been successfully logged out.", "success")
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
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            """SELECT * FROM account WHERE user_id = ? 
            ORDER BY account_name COLLATE NOCASE ASC""", 
            (user_id,))
        user_accounts = cur.fetchall()
        if not user_accounts:
            flash("You don't have any account yet. Please create new account", 
                  "warning")
            return redirect("/add_account")
        total_accounts = 0 # total balance all accounts
        for acc in user_accounts:
            account_dict = {}
            account_dict["account_id"] = acc["account_id"]
            account_dict["account_name"] = acc["account_name"]
            balance = acc[3] # starting balance
            cur.execute("""SELECT * FROM transactions 
                        WHERE user_id = ? AND account_id = ?""", 
                        (user_id, account_dict["account_id"]))
            trans_db = cur.fetchall()
            for tran in trans_db:
                balance = round(float(balance + tran["amount"]), 2)
            account_dict["balance"] = balance # current balance
            total_accounts += balance
            total_accounts = round(float(total_accounts), 2)
            account_dict["account_hide"] = acc["starting_balance"]
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
        if not request.form.get("account_name"):
            flash("You must enter the name of the account", "danger")
            return redirect("/add_account")
        else:
            # connect with database
            with sql.connect("sqlite.db") as con:
                cur = con.cursor()
                user_id = session["user_id"]
                account_name = request.form.get("account_name")
                # Check in database if user already use that account name
                cur.execute(
                    """SELECT * FROM account WHERE user_id = ? 
                    AND account_name = ?""", (user_id, account_name))
                if cur.fetchone():
                    flash("You already have an account with that name", 
                          "danger")
                    return redirect("/add_account")
                if not request.form.get("starting_balance"):
                    starting_balance = 0.00
                else:
                    starting_balance = round(float(request.form.get
                                             ("starting_balance").replace
                                             (',','.')), 2)
                # Add new user's account to database
                cur.execute(
                    """INSERT INTO account 
                    (account_name, user_id, starting_balance) 
                    VALUES (?, ?, ?)""", 
                    (account_name, user_id, starting_balance))
                con.commit()  
            con.close()
            flash("You have successfully add new account", "success")
        return redirect("/accounts")
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
        flash("Changes saved", "success")
        return redirect(f"/account/{ session['account_name'] }")
    else:
        with sql.connect("sqlite.db") as con:
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute("""SELECT * FROM account WHERE account_id = ?""", 
                        (session["account_id"],))
            account_db = cur.fetchall()[0]
            starting_balance = account_db["starting_balance"]
            account_hide = int(account_db["account_hide"])
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
        con.row_factory = sql.Row
        cur = con.cursor()
        # create session account id
        cur.execute("""SELECT * FROM account WHERE user_id = ? 
            AND account_name = ?""", (user_id, account_name))
        account_db = cur.fetchall()[0]
        session["account_id"] = account_db["account_id"]
        starting_balance = account_db["starting_balance"]
        # user's payee list of dict using payee_list function
        payee_list_dict = payee_list_from_db(user_id, cur)
        if not payee_list_dict:
            payee_list_dict = []
        # user's category list of dict using category_list function
        category_list_dict = category_list_from_db(user_id, cur)
        if not category_list_dict:
            category_list_dict = []
        # user's transactions list of dict using transaction_list function
        trans_list_dict_db = transaction_list_from_db(user_id, cur, 
                                                      payee_list_dict, 
                                                      category_list_dict)
        if not trans_list_dict_db:
            trans_list_dict = []
            total = starting_balance
        else:
            trans_list_dict = trans_list_dict_db[0]
            total = trans_list_dict_db[1] + starting_balance
        total = round(float(total), 2)
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
    if not only_digit(amount_form) or not amount_form:
        flash("Amount incorrect", "danger")
        return redirect(f"/account/{ session['account_name'] }")
    amount = amount_uni(amount_form) * trans_type
    if (request.form.get("payee") == None 
        or request.form.get("category") == None):
        flash("Please choose payee and category", "danger")
        return redirect(f"/account/{ session['account_name'] }")
    if not request.form.get("date"):
        flash("Please enter correct date", "danger")
        return redirect(f"/account/{ session['account_name'] }")
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
    flash("Transaction successfully added", "success")
    return redirect(f"/account/{ session['account_name'] }")


@app.route("/transaction/<transaction_id>", methods=["POST", "GET"])
@login_required
def transaction(transaction_id):
    """Edit transaction"""
    with sql.connect("sqlite.db") as con:
        con.row_factory = sql.Row
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
        flash("Transaction successfully edited", "success")
        return redirect(f"/transaction/{ transaction_id }")
    else:
        transaction_id = int(transaction_id)
        with sql.connect("sqlite.db") as con:
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute(
                "SELECT * FROM transactions WHERE transaction_id = ?", 
                (transaction_id,))
            transaction_db = cur.fetchone()
            if (not transaction_db 
                or transaction_id != transaction_db["transaction_id"] 
                or session["user_id"] != transaction_db["user_id"]):
                flash("Database error. Contact with admin", "danger")
                return redirect("/")
            date = transaction_db["date"]
            payee_id = transaction_db["payee_id"]
            category_id = transaction_db["category_id"]
            amount = transaction_db["amount"]
            account_id = transaction_db["account_id"]
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
    flash("Transaction deleted", "success")
    return redirect("/accounts")


@app.route("/payees")
@login_required
def payees():
    """List of all user's payees"""
    st_name = "Payees"
    with sql.connect("sqlite.db") as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        payee_list_dict = payee_list_from_db(session["user_id"], cur)
        if not payee_list_dict:
            payee_list_dict = []
            flash("You don't have any payee yet. Please create new payee",
                   "warning")
        else:
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
    if not request.form.get("payee_name"):
        flash("You must enter the name of the payee", "danger")
    else:
        with sql.connect("sqlite.db") as con:
            cur = con.cursor()
            cur.execute(
                """INSERT INTO payee (payee_name, user_id, description) 
                VALUES (?, ?, ?)""", (request.form.get("payee_name"),
                session["user_id"], request.form.get("description")))
            con.commit()
        con.close()
        flash("Payee added", "success")
    return redirect("/payees")


@app.route("/payee/<payee_id>")
@login_required
def payee(payee_id):
    """Preview of selected payee"""
    with sql.connect("sqlite.db") as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        # payee name
        cur.execute("SELECT * FROM payee WHERE payee_id = ?", (payee_id,))
        payee_db = cur.fetchall()[0]
        payee_name = payee_db["payee_name"]
        description = payee_db["description"]
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
        tran_dict["transaction_id"] = tran["transaction_id"]
        tran_dict["date"] = tran["date"]
        tran_dict["payee_id"] = tran["payee_id"]
        tran_dict["payee_name"] = payee_name
        tran_dict["category_id"] = tran["category_id"]
        for cat in category_list_dict:
            if cat["category_id"] == tran["category_id"]:
                tran_dict["category_name"] = cat["category_name"]
        tran_dict["amount"] = tran["amount"]
        total = round(float(total + tran["amount"]), 2)
        tran_dict["user_id"] = tran["user_id"]
        tran_dict["account_id"] = tran["account_id"]
        for acc in account_list_dict:
            if acc["account_id"] == tran["account_id"]:
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
        flash("Payee successfully edited", "success")
        return redirect(f"/payee/{payee_id}")
    else:
        with sql.connect("sqlite.db") as con:
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute("SELECT * FROM payee WHERE payee_id = ?", (payee_id,))
            payee_db = cur.fetchall()[0]
            user_id = payee_db["user_id"]
            if user_id != session["user_id"]:
                flash("Error", "danger")
                return redirect("/")
            payee_name = payee_db["payee_name"]
            description = payee_db["description"]
        con.close()
        return render_template("payee_edit.html", payee_id=payee_id, 
                               payee_name=payee_name, description=description)


@app.route("/payee_delete/<payee_id>", methods=["POST", "GET"])
@login_required
def payee_delete(payee_id):
    """Delete payee"""
    with sql.connect("sqlite.db") as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM transactions WHERE payee_id = ?", 
                    (payee_id,))
        transaction_exist = cur.fetchone()
    con.close()
    if request.method == "POST":
        if not request.form.get("payee") and transaction_exist:
            flash("""Select the payee to reassign transactions 
            from the payee you want to delete.""", "warning")
            return redirect(f"/payee_delete/{payee_id}")
        with sql.connect("sqlite.db") as con:
            con.row_factory = sql.Row
            cur = con.cursor()
            if transaction_exist:
                new_payee = request.form.get("payee")
                cur.execute("""SELECT payee_id FROM payee 
                            WHERE payee_name = ? AND user_id = ?""", 
                            (new_payee, session["user_id"]))
                new_payee_id = cur.fetchone()[0]
                cur.execute("""UPDATE transactions SET payee_id = ? 
                            WHERE user_id = ? AND payee_id = ?""",
                            (new_payee_id, session["user_id"], 
                            payee_id))
            cur.execute("""DELETE FROM payee 
                        WHERE payee_id = ? AND user_id = ?""", 
                        (payee_id, session["user_id"]))
            con.commit()
        con.close
        flash("Category deleted", "success")
        return redirect("/payees")
    else:
        with sql.connect("sqlite.db") as con:
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute("SELECT * FROM payee WHERE payee_id = ?", 
                        (payee_id,))
            payee_db = cur.fetchall()[0]
            user_id = payee_db["user_id"]
            if user_id != session["user_id"]:
                flash("Error", "danger")
                return redirect("/")
            payee_name = payee_db["payee_name"]
            payee_list_dict = payee_list_from_db(session["user_id"], 
                                                       cur)
            if transaction_exist and len(payee_list_dict) < 2:
                flash("""You must first create a new payee where 
                      all transactions from the payee you want 
                      to delete will be reassigned""", "warning")
                return redirect(f"/payee_edit/{payee_id}")
        con.close()
        return render_template("payee_delete.html", 
                               payee_id=payee_id, 
                               payee_name=payee_name, 
                               payee_list_dict=payee_list_dict)  


@app.route("/categories")
@login_required
def categories():
    """List of all user's categories"""
    st_name = "Categories"
    with sql.connect("sqlite.db") as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        category_list_dict = category_list_from_db(session['user_id'], cur)
        if not category_list_dict:
            category_list_dict = []
            flash(
                "You don't have any category yet. Please create new category",
                "warning")
        else:
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
    if not request.form.get("category_name"):
        flash("You must enter the name of the category", "danger")
    else:
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
        flash("Category added", "success")
    return redirect("/categories")


@app.route("/category/<category_id>")
@login_required
def category(category_id):
    """Preview of selected category"""
    with sql.connect("sqlite.db") as con:
        con.row_factory = sql.Row
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
        tran_dict["transaction_id"] = tran["transaction_id"]
        tran_dict["date"] = tran["date"]
        tran_dict["payee_id"] = tran["payee_id"]
        for pay in payee_list_dict:
            if pay["payee_id"] == tran["payee_id"]:
                tran_dict["payee_name"] = pay["payee_name"]
        tran_dict["category_id"] = tran["category_id"]
        tran_dict["category_name"] = category_name
        tran_dict["amount"] = tran["amount"]
        total = round(float(total + tran["amount"]), 2)
        tran_dict["user_id"] = tran["user_id"]
        tran_dict["account_id"] = tran["account_id"]
        for acc in account_list_dict:
            if acc["account_id"] == tran["account_id"]:
                tran_dict["account_name"] = acc["account_name"]
        trans_list_dict.append(tran_dict)
    return render_template("category.html", category_name=category_name, 
                           trans_list_dict=trans_list_dict, total=total,
                           category_id=category_id)


@app.route("/category_edit/<category_id>", methods=["POST", "GET"])
@login_required
def category_edit(category_id):
    """Edit detail of category"""
    if request.method == "POST":
        new_category_name = request.form.get("category_name")
        if not new_category_name:
            flash("Please enter new category name", "danger")
            return redirect(f"/category_edit/{category_id}")
        else:
            with sql.connect("sqlite.db") as con:
                cur = con.cursor()
                cur.execute("""UPDATE category SET category_name = ?
                            WHERE category_id = ?""", 
                            (new_category_name, category_id,))
                con.commit()
            con.close()
            flash("Payee successfully edited", "success")
        return redirect(f"/category/{category_id}")
    else:
        with sql.connect("sqlite.db") as con:
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute("SELECT * FROM category WHERE category_id = ?", (category_id,))
            category_db = cur.fetchall()[0]
            user_id = category_db["user_id"]
            if user_id != session["user_id"]:
                flash("Error", "danger")
                return redirect("/")
            category_name = category_db["category_name"]
        con.close()
        return render_template("category_edit.html", category_id=category_id, 
                               category_name=category_name)


@app.route("/category_delete/<category_id>", methods=["POST", "GET"])
@login_required
def category_delete(category_id):
    """Delete category"""
    with sql.connect("sqlite.db") as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM transactions WHERE category_id = ?", 
                    (category_id,))
        transaction_exist = cur.fetchone()
    con.close()
    if request.method == "POST":
        if not request.form.get("category") and transaction_exist:
            flash("""Select the category to reassign transactions 
            from the category you want to delete.""", "warning")
            return redirect(f"/category_delete/{category_id}")
        with sql.connect("sqlite.db") as con:
            con.row_factory = sql.Row
            cur = con.cursor()
            if transaction_exist:
                new_category = request.form.get("category")
                cur.execute("""SELECT category_id FROM category 
                            WHERE category_name = ? AND user_id = ?""", 
                            (new_category, session["user_id"]))
                new_category_id = cur.fetchone()[0]
                cur.execute("""UPDATE transactions SET category_id = ? 
                            WHERE user_id = ? AND category_id = ?""",
                            (new_category_id, session["user_id"], 
                            category_id))
            cur.execute("""DELETE FROM category 
                        WHERE category_id = ? AND user_id = ?""", 
                        (category_id, session["user_id"]))
            con.commit()
        con.close
        flash("Category deleted", "success")
        return redirect("/categories")
    else:
        with sql.connect("sqlite.db") as con:
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute("SELECT * FROM category WHERE category_id = ?", 
                        (category_id,))
            category_db = cur.fetchall()[0]
            user_id = category_db["user_id"]
            if user_id != session["user_id"]:
                flash("Error", "danger")
                return redirect("/")
            category_name = category_db["category_name"]
            category_list_dict = category_list_from_db(session["user_id"], 
                                                       cur)
            if transaction_exist and len(category_list_dict) < 2:
                flash("""You must first create a new category where 
                      all transactions from the category you want 
                      to delete will be reassigned""", "warning")
                return redirect(f"/category_edit/{category_id}")
        con.close()
        return render_template("category_delete.html", 
                               category_id=category_id, 
                               category_name=category_name, 
                               category_list_dict=category_list_dict)

   
@app.route("/login_change", methods=["POST", "GET"])
@login_required
def login_change():
    """User login change"""
    if request.method == "POST":
        new_user_name = str.lower(request.form.get("new_user_name"))
        if not new_user_name:
            flash("You must provide new Login", "danger")
            return redirect("/login_change")
        if not request.form.get("password"):
            flash("You must provide password", "danger")
            return redirect("/login_change")
        # connect with database
        with sql.connect("sqlite.db") as con:
            cur = con.cursor()
            # Password check
            cur.execute("SELECT hash FROM users WHERE user_id = ?", 
                        (session["user_id"],))
            hash_password = cur.fetchone()[0]
            if not check_password_hash(hash_password, 
                                       request.form.get("password")):
                flash("Incorrect password", "danger")
                return redirect("/login_change")
            # Check in database if user with that name already exists
            cur.execute("SELECT * FROM users WHERE user_name = ?", 
                        (new_user_name,))
            if cur.fetchone():
                flash("User already exists", "danger")
                return redirect("/login_change")
            # Change user login in database
            cur.execute("UPDATE users SET user_name = ? WHERE user_id = ?",
                        (new_user_name, session["user_id"]))
            con.commit()
        con.close()
        session["user_name"] = new_user_name
        flash(f"You have successfully change your login to: {new_user_name}",
              "success")
        return redirect("/")
    else:
        return render_template("user_login.html", 
                               user_name=session["user_name"])


@app.route("/password_change", methods=["POST", "GET"])
@login_required
def password_change():
    """User password change"""
    if request.method == "POST":
        if not request.form.get("password"):
            flash("You must provide correct current password", "danger")
            return redirect("/password_change")
        if not request.form.get("new_password"):
            flash("You must provide new password", "danger")
            return redirect("/password_change")
        if (request.form.get("re_password") != 
            request.form.get("new_password")):
            flash("You must correct re-type new password", "danger")
            return redirect("/password_change")
        # connect with database
        with sql.connect("sqlite.db") as con:
            cur = con.cursor()
            # Password check
            cur.execute("SELECT hash FROM users WHERE user_id = ?", 
                        (session["user_id"],))
            hash_password = cur.fetchone()[0]
            if not check_password_hash(hash_password, 
                                       request.form.get("password")):
                flash("Incorrect current password", "danger")
                return redirect("/password_change")
            # Create hash password
            hash_password = generate_password_hash(
                request.form.get("new_password"))
            # Change user password in database
            cur.execute("UPDATE users SET hash = ? WHERE user_id = ?",
                        (hash_password, session["user_id"]))
            con.commit()
        con.close()
        flash("You have successfully change your password", "success")
        return redirect("/")
    else:
        return render_template("user_password.html", 
                               user_name=session["user_name"])


@app.route("/user_delete", methods=["POST", "GET"])
@login_required
def settings():
    if request.method == "POST":
        if not request.form.get("password"):
            flash("You must enter a password", "danger")
            return redirect("/user_delete")
        with sql.connect("sqlite.db") as con:
            cur = con.cursor()
            user_id = session["user_id"]
            cur.execute("SELECT hash FROM users WHERE user_id = ?",(user_id,))
            hash_db = cur.fetchone()[0]
            if not hash_db:
                flash("Error in database", "danger")
                return redirect("/")
            # Check correctness of password
            if not check_password_hash(hash_db, request.form.get("password")):
                flash("Incorrect password", "danger")
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
        flash("Account deleted", "success")
        return redirect("/")
    else:
        return render_template("user_delete.html", 
                               user_name=session["user_name"])