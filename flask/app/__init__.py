from flask import Flask

app = Flask(__name__)
app.secret_key = b'"\xe2.\xf9C>Z\'q\xad2U\xa4o,\xb2'

from app import views