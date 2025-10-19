#!/usr/bin/env python3
"""Generate encryption keys for ElectroAnalyzer.

This script generates secure encryption keys for file encryption and JWT tokens.
Run this script to generate keys for your .env file.
"""

import base64
import secrets
import string
from pathlib import Path


def generate_jwt_secret_key(length: int = 64) -> str:
    """Generate a secure JWT secret key."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_fernet_key() -> str:
    """Generate a Fernet encryption key."""
    key = secrets.token_bytes(32)
    return base64.urlsafe_b64encode(key).decode()


def generate_password(length: int = 32) -> str:
    """Generate a secure password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_salt(length: int = 16) -> str:
    """Generate a random salt."""
    return secrets.token_hex(length)


def main():
    """Generate and display encryption keys."""
    print("🔐 ElectroAnalyzer Encryption Key Generator")
    print("=" * 50)
    print()

    # Generate keys
    jwt_secret = generate_jwt_secret_key()
    file_fernet_key = generate_fernet_key()
    db_fernet_key = generate_fernet_key()
    file_encryption_password = generate_password()
    file_encryption_salt = generate_salt()
    db_encryption_password = generate_password()
    db_encryption_salt = generate_salt()

    print("Generated Keys:")
    print("-" * 20)
    print(f"JWT Secret Key: {jwt_secret}")
    print()
    print(f"File Encryption Key: {file_fernet_key}")
    print()
    print(f"Database Encryption Key: {db_fernet_key}")
    print()
    print(f"File Encryption Password: {file_encryption_password}")
    print()
    print(f"File Encryption Salt: {file_encryption_salt}")
    print()
    print(f"Database Encryption Password: {db_encryption_password}")
    print()
    print(f"Database Encryption Salt: {db_encryption_salt}")
    print()

    # Generate .env content
    env_content = f"""# ElectroAnalyzer Environment Configuration
# Generated on {secrets.token_hex(8)}

# Security - REQUIRED: Generate a strong secret key
SECRET_KEY={jwt_secret}

# File Encryption - REQUIRED: Generate strong encryption keys
FILE_ENCRYPTION_KEY={file_fernet_key}
# Alternative: Use password-based key generation
# FILE_ENCRYPTION_PASSWORD={file_encryption_password}
# FILE_ENCRYPTION_SALT={file_encryption_salt}

# Database Encryption - REQUIRED: Generate strong encryption keys for database fields
DATABASE_ENCRYPTION_KEY={db_fernet_key}
# Alternative: Use password-based key generation
# DATABASE_ENCRYPTION_PASSWORD={db_encryption_password}
# DATABASE_ENCRYPTION_SALT={db_encryption_salt}

# Environment (development, testing, production)
ENVIRONMENT=development

# AI Configuration
USE_AI_MOCKS=false

# Database Configuration (if using external DB)
# DATABASE_URL=sqlite:///./compliance.db

# API Configuration
API_HOST=127.0.0.1
API_PORT=8001

# Logging
LOG_LEVEL=INFO

# Development Settings
DEBUG=false
TESTING=false
"""

    # Write to .env file
    env_file = Path(".env")
    if env_file.exists():
        backup_file = Path(".env.backup")
        print(f"⚠️  .env file already exists. Creating backup at {backup_file}")
        env_file.rename(backup_file)

    with open(env_file, 'w') as f:
        f.write(env_content)

    print(f"✅ Generated .env file with secure keys")
    print()
    print("🔒 Security Notes:")
    print("- Keep your .env file secure and never commit it to version control")
    print("- Store these keys securely in production")
    print("- Use different keys for different environments")
    print("- Rotate keys regularly in production")
    print()
    print("🚀 You can now start the application with secure encryption!")


if __name__ == "__main__":
    main()
