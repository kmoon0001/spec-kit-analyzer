import sqlite3
import os
import argparse
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.hashes import SHA256

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, '..', 'data', 'compliance.db')
HASH_ALGORITHM = SHA256()
ITERATIONS = 100000

def create_tables(conn):
    """Creates all necessary tables if they don't exist."""
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
    conn.commit()

def add_default_rubric(conn):
    """Adds the default rubric if no rubrics exist."""
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
        print("Added default rubric.")

def create_user(conn, username, password):
    """Creates a new user with a salted and hashed password."""
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE username = ?", (username,))
    if cur.fetchone() is not None:
        print(f"Error: User '{username}' already exists.")
        return

    salt = os.urandom(16)
    kdf = PBKDF2HMAC(algorithm=HASH_ALGORITHM, length=32, salt=salt, iterations=ITERATIONS)
    password_hash = kdf.derive(password.encode())

    cur.execute("INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)", (username, password_hash, salt))
    conn.commit()
    print(f"Successfully created user '{username}'.")


def main():
    parser = argparse.ArgumentParser(description="Database setup script for the Therapy Compliance Analyzer.")
    parser.add_argument('--create-user', nargs=2, metavar=('USERNAME', 'PASSWORD'), help='Create a new user.')

    args = parser.parse_args()

    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as conn:
        create_tables(conn)
        add_default_rubric(conn)
        print("Database tables created and default rubric checked.")

        if args.create_user:
            username, password = args.create_user
            create_user(conn, username, password)

if __name__ == '__main__':
    main()
