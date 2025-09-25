import os
import sqlite3
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.hashes import SHA256

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, '..', 'data', 'compliance.db')
HASH_ALGORITHM = SHA256()
ITERATIONS = 100000

def get_db_connection():
    """Establishes a connection to the database."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Failed to connect to database: {e}")
        return None

def create_tables():
    """Creates the database tables if they don't already exist."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(DATABASE_PATH)), exist_ok=True)
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash BLOB NOT NULL, salt BLOB NOT NULL)")
            cur.execute("CREATE TABLE IF NOT EXISTS rubrics (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, content TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            conn.commit()
    except sqlite3.Error as e:
        print(f"Failed to create tables: {e}")

def seed_database():
    """Seeds the database with initial data."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
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
        print(f"Failed to seed database: {e}")

def create_user(username, password):
    """Creates a new user in the database."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(algorithm=HASH_ALGORITHM, length=32, salt=salt, iterations=ITERATIONS)
            password_hash = kdf.derive(password.encode())
            cur.execute("INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)", (username, password_hash, salt))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Failed to create user: {e}")

def initialize_database():
    """Initializes the database by creating tables and seeding data."""
    create_tables()
    seed_database()