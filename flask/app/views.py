from app import app
import os
from flask import render_template

@app.route("/")
def index():

    # Use os.getenv("key") to get environment variables
    app_name = os.getenv("YHB")

    return render_template("index.html")
