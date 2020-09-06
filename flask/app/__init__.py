from flask import Flask
import sqlite3

app = Flask(__name__)

from app import views

conn = sqlite3.connect('sqlite.db')
db = conn.cursor()
