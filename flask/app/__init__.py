from flask import Flask
import sqlite3

app = Flask(__name__)
app.secret_key = b'"\xe2.\xf9C>Z\'q\xad2U\xa4o,\xb2'

# Templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

from app import views

#conn = sqlite3.connect('sqlite.db')
#db = conn.cursor()
