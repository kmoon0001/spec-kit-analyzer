import sqlite3
import os
import logging
import secrets
import string
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Configuration ---
DATABASE_PATH = os.path.join("data", "compliance.db")
SALT_SIZE = 16
HASH_ALGORITHM = hashes.SHA256()
ITERATIONS = 100000


def hash_password(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=HASH_ALGORITHM,
        length=32,
        salt=salt,
        iterations=ITERATIONS,
        backend=default_backend(),
    )
    return kdf.derive(password.encode())


def add_user(cursor, username, password):
    # Check if user already exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        logging.info(f"User '{username}' already exists.")
        return

    salt = os.urandom(SALT_SIZE)
    password_hash = hash_password(password, salt)

    cursor.execute(
        "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
        (username, password_hash, salt),
    )
    logging.info(f"User '{username}' added successfully.")


def generate_random_password(length=12):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = "".join(secrets.choice(alphabet) for i in range(length))
    return password


def main():
    # --- Create data directory if it doesn't exist ---
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    # --- Connect to the database ---
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # --- Create the users table ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash BLOB NOT NULL,
        salt BLOB NOT NULL
    )
    """)

    # --- Add the admin user ---
    admin_password = generate_random_password()
    add_user(cursor, "admin", admin_password)
    logging.info(f"Admin password: {admin_password}")

    # --- Commit changes and close the connection ---
    conn.commit()
    conn.close()

    logging.info("Database created and initialized successfully.")


if __name__ == "__main__":
    main()
