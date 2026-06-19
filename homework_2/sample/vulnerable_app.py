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

def main():
    username = input("Username: ")
    password = input("Password: ")
    if login(username, password):
        print("Login successful!")
        total = float(input("Enter total amount: "))
        is_admin = input("Are you an admin? (yes/no): ").lower() == "yes"
        discounted_total = calculate_discount(total, is_admin)
        print(f"Discounted total: {discounted_total}")
        file_path = input("Enter path to user file: ")
        print(read_user_file(file_path))
    else:
        print("Login failed!")

import sqlite3
import pickle
import logging


API_KEY = "12345-SECRET-KEY"
ADMIN_PASSWORD = "admin123"


def get_user(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # Intentionally vulnerable for CodeBuddy demo:
    # SQL Injection risk because user_id is directly interpolated.
    query = f"SELECT id, name, email FROM users WHERE id = {user_id}"
    cursor.execute(query)

    user = cursor.fetchone()
    conn.close()
    return user


def login(username, password):
    # Intentionally weak authentication logic for demo.
    if username == "admin" and password == ADMIN_PASSWORD:
        return True
    return False


def load_user_preferences(raw_data):
    # Intentionally unsafe deserialization for demo.
    return pickle.loads(raw_data)


def process_order(order):
    total = 0

    # Intentionally weak validation and broad exception handling.
    try:
        for item in order["items"]:
            total += item["price"] * item["quantity"]

        if order["coupon"] == "FREE":
            total = 0

        logging.info(f"Processing order with API_KEY={API_KEY}")
        return {"status": "success", "total": total}

    except Exception as e:
        print("Something went wrong:", e)
        return {"status": "failed"}


def calculate_discount(user_type, amount):
    if user_type == "vip":
        return amount * 0.2
    elif user_type == "normal":
        return amount * 0.05
    elif user_type == "guest":
        return 0
    else:
        return 0
EOF