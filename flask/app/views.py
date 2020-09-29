from app import app
import os
from flask import render_template, request, redirect
import sqlite3 as sql
from werkzeug.security import check_password_hash, generate_password_hash

from app.helpers import has_lower, has_number, has_symbol, has_upper, check_password

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
                return render_template("error.html", message="Please provide User Name")

            # Check in database if user already exists
            cur.execute("SELECT * FROM users WHERE user_name = ?", (user_name,))
            if cur.fetchone():
                return render_template("error.html", message="User already exists")

            # Check correctness of password
            if not request.form.get("password"):
                return render_template("error.html", message="Please provide password")
            elif not request.form.get("re_password") or request.form.get("password") != request.form.get("re_password"):
                return render_template("error.html", message="Please re-type the same password")
            # elif not has_number(request.form.get("password")) or not has_symbol(request.form.get("password")) or not has_lower(request.form.get("password")) or not has_upper(request.form.get("password")):
            #     return render_template("error.html", message="Need number")
            elif not check_password(request.form.get("password")):
                return render_template("error.html", message="Please provide password with at least one uppercase and lowercase letter, a number and a symbol.")

            hash_password = generate_password_hash(request.form.get("password"))
            #cur.execute("INSERT INTO users (user_name, hash) VALUES (?, ?)", (user_name, hash_password))
            con.commit()
        con.close()
        return redirect("/")
    else:
        return render_template("register.html")
