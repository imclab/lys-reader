from flask import make_response, jsonify, session, request
from functools import wraps
from os import urandom
from datetime import datetime, timedelta
from base64 import b64encode
from api import DB

def register_user(email, password):

    if not is_registered(email):
        con = DB.get_connection()
        cur = con.cursor()

        cur.execute('INSERT INTO lysr_user (email, password) VALUES (%s, %s)', (email, password))
        con.commit()

        return True
    return False

def check_user_credentials(email, password):

    if is_registered(email):
        con = DB.get_connection()
        cur = con.cursor()

        cur.execute('SELECT id FROM lysr_user WHERE email = %s and password = %s', (email, password))
        con.commit()

        if cur.rowcount is 1:
            return cur.fetchone()[0]

        return None

def is_registered(email):
    con = DB.get_connection()
    cur = con.cursor()

    cur.execute('SELECT id FROM lysr_user WHERE email = %s', (email,))
    con.commit()

    if cur.rowcount is 0:
        return False

    return True

def generate_csrf_token(session):
    expire_time = datetime.now() + timedelta(minutes=15)
    token = b64encode(urandom(30))
    session['csrf'] = token
    session['csrf_expire'] = expire_time

def get_unread(id):
    con = DB.get_connection()
    cur = con.cursor()

    cur.execute('SELECT COUNT(*) FROM lysr_feed_entry_status WHERE read = FALSE and id = %s;', (id,))
    con.commit()

    return cur.fetchone()[0]

# Decorators

def require_authentication(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not 'loggedin' in session or not session['loggedin']:
            return make_response(jsonify({ 'status':'BAD REQUEST', 'message':'User not logged in'}), 400)
        return f(*args, **kwargs)
    return decorated_function

def require_csrf_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not 'csrf' in session or not 'csrf_token' in request.json \
            or session['csrf'] != request.json['csrf_token'] or datetime.now() > session['csrf_expire']:
            generate_csrf_token(session)
            return make_response(jsonify({ 'status':'BAD REQUEST', 'message':'csrf token invalid'}), 400)

        generate_csrf_token(session)
        kwargs['csrf'] = session['csrf']

        return f(*args, **kwargs)
    return decorated_function

