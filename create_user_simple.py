#!/usr/bin/env python3
"""Simple user creation script that bypasses bcrypt issues."""

import sqlite3
import hashlib
import os

# Create the database file if it doesn't exist
db_path = "compliance.db"

# Connect to SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create users table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    license_key VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Simple password hash (for testing only - not secure for production)
username = "admin"
password = "admin"
simple_hash = hashlib.sha256(password.encode()).hexdigest()

# Insert the user
try:
    cursor.execute('''
    INSERT INTO users (username, hashed_password, is_admin, is_active)
    VALUES (?, ?, ?, ?)
    ''', (username, simple_hash, True, True))
    
    conn.commit()
    print(f"✅ Created user: {username}/{password}")
    print("⚠️  Note: This uses a simple hash for testing only!")
    
except sqlite3.IntegrityError:
    print(f"User '{username}' already exists")

conn.close()