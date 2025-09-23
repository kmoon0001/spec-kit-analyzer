import sqlite3
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

# --- Configuration ---
DATABASE_PATH = os.path.join('..', 'data', 'compliance.db')
SALT_SIZE = 16
HASH_ALGORITHM = hashes.SHA256()
ITERATIONS = 100000

# --- Create data directory if it doesn't exist ---
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# --- Connect to the database ---
conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

# --- Create the users table ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash BLOB NOT NULL,
    salt BLOB NOT NULL
)
''')

# --- Hash a sample password ---
def hash_password(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=HASH_ALGORITHM,
        length=32,
        salt=salt,
        iterations=ITERATIONS,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

# --- Add a sample user ---
def add_user(username, password):
    # Check if user already exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        print(f"User '{username}' already exists.")
        return

    salt = os.urandom(SALT_SIZE)
    password_hash = hash_password(password, salt)

    cursor.execute(
        "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
        (username, password_hash, salt)
    )
    conn.commit()
    print(f"User '{username}' added successfully.")

# --- Add the admin user ---
add_user("admin", "password")

# --- Close the connection ---
conn.close()

print("Database created and initialized successfully.")