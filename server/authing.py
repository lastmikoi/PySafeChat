import sqlite3


def init_db():
    try:
        conn = sqlite3.connect('./db.sqlite')
        c = conn.cursor()
        c.execute('''create table users (joined date, username text, pubkey text)''')
        conn.commit()
        c.close()
    except sqlite3.OperationalError:
        pass


def get_auth(username):
    conn = sqlite3.connect('./db.sqlite')
    c = conn.cursor()
    t = (username,)
    c.execute('select * from users where username=?', t)
    result = c.fetchone()
    if result is None:
        c.close()
        return "Unknown"
    else:
        c.close()
        return "Ok"


def get_pubkey(username):
    conn = sqlite3.connect('./db.sqlite')
    c = conn.cursor()
    t = (username,)
    c.execute('select * from users where username=?', t)
    result = c.fetchone()
    if result is None:
        c.close()
        return None
    else:
        c.close()
        return result[2]


def add_user(username, pubkey):
    conn = sqlite3.connect('./db.sqlite')
    c = conn.cursor()
    from datetime import date
    t = (date.today(), username, pubkey)
    if get_auth(username) == 'Unknown':
        c.execute('insert into users values (?, ?, ?)', t)
        conn.commit()
    c.close()
