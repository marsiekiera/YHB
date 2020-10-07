from app import app
import os
from tempfile import mkdtemp
from flask import render_template, request, redirect, flash, session
import sqlite3 as sql
from werkzeug.security import check_password_hash, generate_password_hash

from app.helpers import check_password, login_required

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
    """Show Account list"""
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
                flash('Please provide User Name', 'error')
                return redirect("/login")
            
            cur.execute("SELECT * FROM users WHERE user_name = ?", (user_name,))
            records = cur.fetchall()

            # Check in database if user exists
            if not records:
                flash('Incorrect user name', 'error')
                return redirect("/login")

            for row in records:
                user_id = row[0]
                user_name = row[1]
                hash_password = row[2]
            
            # Check correctness of password
            if not check_password_hash(hash_password, request.form.get("password")):
                flash('Incorrect password', 'error')
                return redirect("/login")
            
            # Remember which user has logged in
            session["user_id"] = user_id
            session["user_name"] = user_name

        con.close()

        flash("You were successfully logged in", 'info')
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
                flash('Please provide User Name', 'error')
                return redirect("/register")

            # Check in database if user already exists
            cur.execute("SELECT * FROM users WHERE user_name = ?", (user_name,))
            if cur.fetchone():
                flash('User already exists', 'error')
                return redirect("/register")

            # Check correctness of password
            if not request.form.get("password"):
                flash('Please provide password', 'error')
                return redirect("/register")
            elif not request.form.get("re_password") or request.form.get("password") != request.form.get("re_password"):
                flash('Please re-type the same password', 'error')
                return redirect("/register")
            elif not check_password(request.form.get("password")):
                flash('Please provide password with at least one uppercase and lowercase letter, a number and a symbol.', 'error')
                return redirect("/register")
            
            # Create hash password
            hash_password = generate_password_hash(request.form.get("password"))

            # Add user to database
            cur.execute("INSERT INTO users (user_name, hash) VALUES (?, ?)", (user_name, hash_password))
            con.commit()

        con.close()
        flash('You have sucessfully register. You can login now.', 'info')
        return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    flash("You have been successfully logged out.", 'info')
    return redirect("/")


@app.route("/add_account", methods=["POST", "GET"])
@login_required
def add_account():
    """Create new users account"""
    if request.method == "POST":
        # connect with database
        with sql.connect("sqlite.db") as con:
            con.row_factory = sql.Row
            cur = con.cursor()

            user_id = session["user_id"]
            account_name = request.form.get("account_name")

            # Check in database if user already have account with that name
            cur.execute("SELECT * FROM account WHERE user_id = ? AND account_name = ?", (user_id, account_name))
            if cur.fetchone():
                flash('You already have an account with that name', 'error')
                return redirect("/add_account")

            if not request.form.get("starting_balance"):
                starting_balance = 0.00
            else:
                starting_balance = round(float(request.form.get("starting_balance").replace(',','.')), 2)

            # Add new user's account to database
            cur.execute("INSERT INTO account (account_name, user_id, starting_balance) VALUES (?, ?, ?)", (account_name, user_id, starting_balance))
            con.commit()  
        con.close()

        flash('You have sucessfully add new account', "info")
        return redirect("/")
    else:
        return render_template("add_account.html")



@app.route("/edit_account", methods=["POST", "GET"])
@login_required
def edit_account():
    if request.method == "POST":
        flash('Changes saved', "info")
        return redirect("/")
    else:
        return render_template("edit_account.html")