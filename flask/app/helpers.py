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
        ORDER BY payee_name COLLATE NOCASE ASC""",(user_id,))
    payee_db = cur.fetchall()
    if not payee_db:
        return False
    for pay in payee_db:
        payee_dict = {}
        payee_dict["payee_id"] = pay["payee_id"]
        payee_dict["payee_name"] = pay["payee_name"]
        payee_dict["user_id"] = pay["user_id"]
        payee_dict["description"] = pay["description"]
        payee_list_dict.append(payee_dict)
    return payee_list_dict


def category_list_from_db(user_id, cur):
    """Create user's category list of dict"""
    category_list_dict = []
    cur.execute("""SELECT * FROM category WHERE user_id = ? 
        ORDER BY category_name COLLATE NOCASE ASC""", (user_id,))
    category_db = cur.fetchall()
    if not category_db:
        return False
    for category in category_db:
        category_dict = {}
        category_dict["category_id"] = category["category_id"]
        category_dict["category_name"] = category["category_name"]
        category_dict["user_id"] = category["user_id"]
        category_list_dict.append(category_dict)
    return category_list_dict


def transaction_list_from_db(user_id, account_id, cur, payee_list_dict, 
                             category_list_dict, account_list_dict):
    """Create user's transactions list of dict"""
    trans_list_dict = []
    cur.execute(
        """SELECT * FROM transactions WHERE user_id = ? AND (account_id = ? OR transf_to_account_id = ?) 
        ORDER BY date""", (user_id, account_id, account_id))
    trans_db = cur.fetchall()
    if not trans_db:
        return False
    total = 0
    for tran in trans_db:
        tran_dict = {}
        tran_dict["transaction_id"] = tran["transaction_id"]
        tran_dict["date"] = tran["date"]
        account_id_db = tran["account_id"]
        transf_to_account_id = tran["transf_to_account_id"]
        if transf_to_account_id == int(account_id):
            for account in account_list_dict:
                if account["account_id"] == account_id_db:
                    account_name = account["account_name"]
            tran_dict["payee_name"] = f"Transfer from: {account_name}"
            tran_dict["amount"] = tran["amount"]
        elif transf_to_account_id:
            for account in account_list_dict:
                if account["account_id"] == transf_to_account_id:
                    account_name = account["account_name"]
            tran_dict["payee_name"] = f"Transfer to: {account_name}"
            tran_dict["amount"] = tran["amount"] * -1
        else:
            tran_dict["payee_id"] = tran["payee_id"]
            for pay in payee_list_dict:
                if pay["payee_id"] == tran["payee_id"]:
                    tran_dict["payee_name"] = pay["payee_name"]
            tran_dict["category_id"] = tran["category_id"]
            for cat in category_list_dict:
                if cat["category_id"] == tran["category_id"]:
                    tran_dict["category_name"] = cat["category_name"]
            tran_dict["amount"] = tran["amount"]
        tran_dict["account_id"] = tran["account_id"]
        total = round(float(total + tran["amount"]), 2)
        tran_dict["user_id"] = tran["user_id"]
        trans_list_dict.append(tran_dict)
    return [trans_list_dict, total]


def account_list_from_db(user_id, cur):
    """Create user's category list of dict"""
    account_list_dict = []
    cur.execute("""SELECT * FROM account WHERE user_id = ? 
        ORDER BY account_name COLLATE NOCASE ASC""", (user_id,))
    account_db = cur.fetchall()
    for acc in account_db:
        account_dict = {}
        account_dict["account_id"] = acc["account_id"]
        account_dict["account_name"] = acc["account_name"]
        account_dict["user_id"] = acc["user_id"]
        account_dict["starting_balance"] = acc["starting_balance"]
        account_dict["account_hide"] = acc["account_hide"]
        account_list_dict.append(account_dict)
    return account_list_dict


def amount_uni(amount):
    return round(float(amount.replace(',','.')), 2)