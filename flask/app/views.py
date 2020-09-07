from app import app
import os
from flask import render_template, request, redirect

@app.route("/")
def index():

    # Use os.getenv("key") to get environment variables
    app_name = os.getenv("YHB")

    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        #to do
        return redirect("/")
    else:
        return render_template("register.html")
