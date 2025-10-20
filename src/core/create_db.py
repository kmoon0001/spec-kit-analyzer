import logging
import os
import secrets
import sqlite3
import string

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Configuration ---
DATABASE_PATH = os.path.join("data", "compliance.db")
SALT_SIZE = 16
HASH_ALGORITHM = hashes.SHA256()
ITERATIONS = 100000


def hash_password(password, salt):
    """Hashes a password using PBKDF2HMAC.

    Args:
        password (str): The password to hash.
        salt (bytes): The salt to use for hashing.

    Returns:
        bytes: The hashed password.

    """
    kdf = PBKDF2HMAC(
        algorithm=HASH_ALGORITHM,
        length=32,
        salt=salt,
        iterations=ITERATIONS,
        backend=default_backend(),
    )
    return kdf.derive(password.encode())


def add_user(cursor, username, password):
    """Adds a new user to the database.

    Args:
        cursor: The database cursor object.
        username (str): The username of the new user.
        password (str): The password of the new user.

    """
    # Check if user already exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        logging.info("User '%s' already exists.", username)
        return

    salt = os.urandom(SALT_SIZE)
    password_hash = hash_password(password, salt)

    cursor.execute(
        "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
        (username, password_hash, salt),
    )
    logging.info("User '%s' added successfully.", username)


def generate_random_password(length=12):
    """Generates a random password.

    Args:
        length (int): The length of the password to generate.

    Returns:
        str: The generated random password.

    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = "".join(secrets.choice(alphabet) for i in range(length))
    return password


def main():
    """Main function to create and initialize the database with an admin user."""
    # --- Create data directory if it doesn't exist ---
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    # --- Connect to the database ---
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # --- Create the users table ---
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash BLOB NOT NULL,
        salt BLOB NOT NULL
    )
    """
    )

    # --- Add the admin user ---
    admin_password = generate_random_password()
    add_user(cursor, "admin", admin_password)
    logging.info("Admin password: %s", admin_password)

    # --- Commit changes and close the connection ---
    conn.commit()
    conn.close()

    logging.info("Database created and initialized successfully.")


if __name__ == "__main__":
    pass
if __name__ == "__main__":
    pass
if __name__ == "__main__":
    main()
