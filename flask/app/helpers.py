from functools import wraps
from flask import g, request, redirect, url_for, session, flash

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


def only_digit(input_string):
    dots = 0
    for letter in input_string:
        if letter in (".", ","):
            dots += 1
        elif not letter.isdigit():
            return False
    if dots > 1:
        return False        
    else:
        return True


def payee_list_from_db(user_id, cur):
    """Create user's payee list of dict"""
    payee_list_dict = []
    cur.execute("""SELECT * FROM payee WHERE user_id = ? 
        ORDER BY payee_name""",(user_id,))
    payee_db = cur.fetchall()
    if not payee_db:
        flash("You need to add payee before", 'error')
        return redirect("/payees")
    for pay in payee_db:
        payee_dict = {}
        payee_dict["payee_id"] = pay[0]
        payee_dict["payee_name"] = pay[1]
        payee_dict["user_id"] = pay[2]
        payee_list_dict.append(payee_dict)
    return payee_list_dict


def category_list_from_db(user_id, cur):
    """Create user's category list of dict"""
    category_list_dict = []
    cur.execute("""SELECT * FROM category WHERE user_id = ? 
        ORDER BY category_name""", (user_id,))
    category_db = cur.fetchall()
    if not category_db:
        flash("You need to add category before", "error")
        return redirect("/categories")
    for category in category_db:
        category_dict = {}
        category_dict["category_id"] = category[0]
        category_dict["category_name"] = category[1]
        category_dict["user_id"] = category[2]
        category_list_dict.append(category_dict)
    return category_list_dict


def transaction_list_from_db(
    user_id, cur, payee_list_dict, category_list_dict):
    """Create user's transactions list of dict"""
    trans_list_dict = []
    cur.execute(
        """SELECT * FROM transactions WHERE user_id = ? AND account_id = ? 
        ORDER BY date""", (user_id, session["account_id"]))
    trans_db = cur.fetchall()
    total = 0
    for tran in trans_db:
        tran_dict = {}
        tran_dict["transaction_id"] = tran[0]
        tran_dict["date"] = tran[1]
        tran_dict["payee_id"] = tran[2]
        for pay in payee_list_dict:
            if pay["payee_id"] == tran[2]:
                tran_dict["payee_name"] = pay["payee_name"]
        tran_dict["category_id"] = tran[3]
        for cat in category_list_dict:
            if cat["category_id"] == tran[3]:
                tran_dict["category_name"] = cat["category_name"]
        tran_dict["amount"] = tran[4]
        total = round(float(total + tran[4]), 2)
        tran_dict["user_id"] = tran[5]
        tran_dict["account_id"] = tran[6]
        trans_list_dict.append(tran_dict)
    return [trans_list_dict, total]


def account_list_from_db(user_id, cur):
    """Create user's category list of dict"""
    account_list_dict = []
    cur.execute("""SELECT * FROM account WHERE user_id = ? 
        ORDER BY account_name""", (user_id,))
    account_db = cur.fetchall()
    if not account_db:
        flash("You need to add category before", "error")
        return redirect("/add_account")
    for acc in account_db:
        account_dict = {}
        account_dict["account_id"] = acc[0]
        account_dict["account_name"] = acc[1]
        account_dict["user_id"] = acc[2]
        account_dict["starting_balance"] = acc[3]
        account_dict["account_hide"] = acc[4]
        account_list_dict.append(account_dict)
    return account_list_dict