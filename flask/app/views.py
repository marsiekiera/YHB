from app import app
import os
from flask import render_template

@app.route("/")
def index():

    # Use os.getenv("key") to get environment variables
    app_name = os.getenv("YHB")

    return render_template("index.html")

    # if app_name:
    #     return f"Hello from {app_name} running in a Docker container behind Nginx!"

    # return "Hello from Flask"
