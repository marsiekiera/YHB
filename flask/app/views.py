from app import app
import os
from flask import render_template, request, redirect, flash
import sqlite3 as sql
from werkzeug.security import check_password_hash, generate_password_hash

from app.helpers import check_password

# Templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

#conn = sqlite3.connect('sqlite.db', check_same_thread=False)
#db = conn.cursor()

@app.route("/")
def index():

    # Use os.getenv("key") to get environment variables
    app_name = os.getenv("YHB")

    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # connect with database
        with sql.connect("sqlite.db") as con:
            con.row_factory = sql.Row
            cur = con.cursor()
            user_name = request.form.get("user_name")

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
        flash('You have sucessfully register', 'info')
        return redirect("/")
    else:
        return render_template("register.html")
