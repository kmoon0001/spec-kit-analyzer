import sqlite3
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.hashes import SHA256

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, '..', 'data', 'compliance.db')
HASH_ALGORITHM = SHA256()
ITERATIONS = 100000

def initialize_app_database():
    """Creates the database and tables if they don't exist."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(DATABASE_PATH)), exist_ok=True)
        with sqlite3.connect(DATABASE_PATH) as conn:
            cur = conn.cursor()
            # User table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash BLOB NOT NULL,
                salt BLOB NOT NULL
            )
            """)
            # Rubrics table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS rubrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            # Default rubric
            cur.execute("SELECT COUNT(*) FROM rubrics")
            if cur.fetchone()[0] == 0:
                default_rubric_name = "Default Best Practices"
                default_rubric_content = """# General Documentation Best Practices
- All entries must be dated and signed.
- Patient identification must be clear on every page.
- Use of approved abbreviations only.
- Document skilled intervention, not just patient performance.
- Goals must be measurable and time-bound."""
                cur.execute("INSERT INTO rubrics (name, content) VALUES(?, ?)", (default_rubric_name, default_rubric_content))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database initialization failed: {e}")
        # In a real app, you might want to raise this exception
        # or handle it more gracefully.

def verify_user(username, password):
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT password_hash, salt FROM users WHERE username = ?", (username,))
            result = cur.fetchone()
            if result is None:
                return False, "Invalid username or password."

            password_hash, salt = result
            kdf = PBKDF2HMAC(algorithm=HASH_ALGORITHM, length=32, salt=salt, iterations=ITERATIONS)

            try:
                kdf.verify(password.encode(), password_hash)
                return True, "Login successful."
            except Exception:
                return False, "Invalid username or password."

    except sqlite3.Error as e:
        return False, f"Database error during login: {e}"

def create_user(username, password):
    if not username or not password:
        return False, "Username and password cannot be empty."

    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT username FROM users WHERE username = ?", (username,))
            if cur.fetchone() is not None:
                return False, "User already exists."

            salt = os.urandom(16)
            kdf = PBKDF2HMAC(algorithm=HASH_ALGORITHM, length=32, salt=salt, iterations=ITERATIONS)
            password_hash = kdf.derive(password.encode())

            cur.execute("INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)", (username, password_hash, salt))
            conn.commit()
            return True, "User created successfully."
    except sqlite3.Error as e:
        return False, f"Database error during user creation: {e}"
