from flask import Flask
import sqlite3

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

from app import views

#conn = sqlite3.connect('sqlite.db')
#db = conn.cursor()
