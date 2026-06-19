import sqlite3


def login(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    return cursor.fetchone() is not None


def calculate_discount(total, is_admin):
    if is_admin:
        return total * 0.5
    if total > 100:
        return total * 0.9
    return total


def read_user_file(path):
    with open(path) as file:
        return file.read()
