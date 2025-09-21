import sqlite3
import os
import hashlib
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def _ensure_directories():
    """Ensures that the necessary directories exist."""
    db_dir = os.path.dirname(DATABASE_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

def _prepare_database_file():
    """Ensures the database file exists."""
    if not os.path.exists(DATABASE_PATH):
        with open(DATABASE_PATH, "w") as f:
            pass

def _backup_corrupt_db(db_path):
    """Backs up a corrupt database file."""
    if os.path.exists(db_path):
        backup_path = f"{db_path}.bak"
        if os.path.exists(backup_path):
            os.remove(backup_path)
        os.rename(db_path, backup_path)
        logger.warning(f"Backed up corrupt database to {backup_path}")

def _ensure_core_schema(conn: sqlite3.Connection):
    """Ensures the core schema exists in the database."""
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.commit()
    except Exception as e:
        logger.warning(f"Ensure core schema failed: {e}")

def _get_db_connection() -> sqlite3.Connection:
    _ensure_directories()
    _prepare_database_file()
    try:
        conn = sqlite3.connect(DATABASE_PATH)
    except sqlite3.DatabaseError as e:
        logger.warning(f"sqlite connect failed: {e}; attempting recreate")
        _backup_corrupt_db(DATABASE_PATH)
        conn = sqlite3.connect(DATABASE_PATH)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON")
        cur.execute("PRAGMA journal_mode = WAL")
        cur.execute("PRAGMA synchronous = NORMAL")
        conn.commit()
        _ensure_core_schema(conn)
    except Exception as e:
        logger.warning(f"SQLite PRAGMA/schema setup partial: {e}")
    return conn

def get_setting(key: str) -> Optional[str]:
    try:
        with _get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cur.fetchone()
            return row[0] if row else None
    except Exception:
        return None

def set_setting(key: str, value: str) -> None:
    try:
        with _get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
            conn.commit()
    except Exception:
        ...

def get_bool_setting(key: str, default: bool) -> bool:
    raw = get_setting(key)
    if raw is None:
        return default
    return str(raw).lower() in ("1", "true", "yes", "on")

def set_bool_setting(key: str, value: bool) -> None:
    set_setting(key, "1" if value else "0")

def get_int_setting(key: str, default: int) -> int:
    raw = get_setting(key)
    if raw is None:
        return default
    try:
        return int(str(raw).strip())
    except Exception:
        return default

def get_str_setting(key: str, default: str) -> str:
    raw = get_setting(key)
    return default if raw is None else str(raw)

def set_str_setting(key: str, value: str) -> None:
    set_setting(key, value)

# This is a simplified version of the database code from the original file.
# I will add more functions as needed.
DATABASE_PATH = os.getenv(
    "SPEC_KIT_DB", os.path.join(os.path.expanduser("~"), "Documents", "SpecKitData", "spec_kit.db")
)
