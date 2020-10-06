from functools import wraps
from flask import g, request, redirect, url_for, session

def login_required(f):
    """
    https://flask.palletsprojects.com/en/1.0.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id') is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def check_password(input_string):
    if any(char.isdigit() for char in input_string) \
        and any(char.islower() for char in input_string) \
        and any(char.isupper() for char in input_string) \
        and any(not char.isalnum() for char in input_string):
        return True
    else:
        return False
