import sqlite3
import os

# This script is intended for one-time setup of the database schema.
# It should not be used for seeding data, especially not users.

def main():
    """
    Creates the database and the necessary tables.
    """
    # --- Configuration ---
    # Construct a robust path to the database file
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, '..', '..', 'data')
    DATABASE_PATH = os.path.join(DATA_DIR, 'compliance.db')

    # --- Create data directory if it doesn't exist ---
    os.makedirs(DATA_DIR, exist_ok=True)

    try:
        # --- Connect to the database ---
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # --- Create the users table ---
        # Note: User creation and management should be handled by a separate process or API endpoint.
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash BLOB NOT NULL,
            salt BLOB NOT NULL
        )
        ''')

        # You could add other table creation statements here, for example:
        # cursor.execute('''
        # CREATE TABLE IF NOT EXISTS rubrics (
        #     id INTEGER PRIMARY KEY AUTOINCREMENT,
        #     name TEXT NOT NULL UNIQUE,
        #     content TEXT NOT NULL,
        #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        # )
        # ''')

        conn.commit()
        print("Database schema created successfully.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == '__main__':
    main()
    print("Database creation script finished.")