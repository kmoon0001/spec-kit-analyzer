#!/usr/bin/env python3
"""Environment Setup Script for ElectroAnalyzer"""

import os
import secrets
from pathlib import Path

def generate_secret_key():
    """Generate a cryptographically secure secret key."""
    return secrets.token_urlsafe(32)

def create_env_file():
    """Create a .env file with secure defaults."""
    env_path = Path(".env")

    if env_path.exists():
        print("[WARNING] .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing .env file.")
            return

    secret_key = generate_secret_key()

    env_content = f"""# ElectroAnalyzer Environment Configuration
# Generated automatically

# Security - REQUIRED: Strong secret key for JWT tokens
SECRET_KEY={secret_key}

# AI Configuration
USE_AI_MOCKS=false

# Database Configuration
DATABASE_URL=sqlite:///./compliance.db

# API Configuration
API_HOST=127.0.0.1
API_PORT=8001

# Logging
LOG_LEVEL=INFO

# Development Settings
DEBUG=false
TESTING=false

# Optional: Custom model paths
# MODEL_CACHE_DIR=./models
# HF_CACHE_DIR=./hf_cache
"""

    with open(env_path, 'w') as f:
        f.write(env_content)

    print("[SUCCESS] Created .env file with secure configuration!")
    print(f"[KEY] Generated SECRET_KEY: {secret_key[:10]}...")
    print("\nNext steps:")
    print("1. Review the .env file")
    print("2. Start your application")
    print("3. Keep your SECRET_KEY secure!")

def check_environment():
    """Check if environment is properly configured."""
    env_path = Path(".env")

    if not env_path.exists():
        print("[ERROR] No .env file found!")
        print("Run this script to create one.")
        return False

    # Load environment variables
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

    secret_key = os.environ.get('SECRET_KEY')

    if not secret_key:
        print("[ERROR] SECRET_KEY not found in environment!")
        return False

    if secret_key == "your-super-secret-jwt-key-change-this-in-production":
        print("[ERROR] Using default SECRET_KEY - this is insecure!")
        return False

    print("[SUCCESS] Environment configuration looks good!")
    print(f"[KEY] SECRET_KEY: {secret_key[:10]}...")
    return True

if __name__ == "__main__":
    print("ElectroAnalyzer Environment Setup")
    print("=" * 40)

    if len(os.sys.argv) > 1 and os.sys.argv[1] == "check":
        check_environment()
    else:
        create_env_file()
