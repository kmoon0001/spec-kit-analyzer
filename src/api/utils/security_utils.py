"""Security Utilities for Clinical Compliance Analysis API.

This module provides security utility functions.
"""

import hashlib
import secrets
import re
from typing import Optional
from passlib.context import CryptContext
from passlib.hash import bcrypt

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS."""
    if not text:
        return ""

    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', text)
    return sanitized.strip()


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """Validate password strength."""
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")

    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")

    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")

    return len(errors) == 0, errors


def is_safe_filename(filename: str) -> bool:
    """Check if filename is safe."""
    if not filename:
        return False

    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False

    # Check for dangerous characters
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
    if any(char in filename for char in dangerous_chars):
        return False

    return True


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()
