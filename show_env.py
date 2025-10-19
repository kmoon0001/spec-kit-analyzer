#!/usr/bin/env python3
"""Show current environment variables and configuration"""

import os
import sys
from pathlib import Path

def show_environment():
    """Display current environment variables"""
    print("=" * 60)
    print("ELECTROANALYZER ENVIRONMENT STATUS")
    print("=" * 60)

    # Check for .env file
    env_file = Path(".env")
    if env_file.exists():
        print("\n[FOUND] .env file exists")
        with open(env_file) as f:
            lines = f.readlines()
            print(f"[INFO] .env file has {len(lines)} lines")
    else:
        print("\n[NOT FOUND] No .env file")

    # Show environment variables
    print("\nEnvironment Variables:")
    print("-" * 30)

    env_vars = {
        'SECRET_KEY': 'Security key for JWT tokens',
        'USE_AI_MOCKS': 'Enable/disable AI mocking',
        'API_HOST': 'API server host',
        'API_PORT': 'API server port',
        'LOG_LEVEL': 'Logging level',
        'DEBUG': 'Debug mode',
        'TESTING': 'Testing mode'
    }

    for var, description in env_vars.items():
        value = os.environ.get(var, '[NOT SET]')
        if var == 'SECRET_KEY' and value != '[NOT SET]':
            value = value[:20] + '...' if len(value) > 20 else value
        print(f"{var:12}: {value}")
        print(f"{'':12}  ({description})")
        print()

    # Test configuration loading
    print("Configuration Test:")
    print("-" * 20)
    try:
        sys.path.append(str(Path.cwd()))
        from src.config import get_settings
        settings = get_settings()

        print(f"[SUCCESS] Configuration loaded!")
        print(f"SECRET_KEY: {settings.auth.secret_key.get_secret_value()[:20]}...")
        print(f"AI Mocks: {settings.use_ai_mocks}")
        print(f"Host: {settings.host}:{settings.port}")
        print(f"Log Level: {settings.log_level}")

    except Exception as e:
        print(f"[ERROR] Failed to load configuration: {e}")

def set_environment():
    """Set environment variables"""
    print("\n" + "=" * 60)
    print("SETTING ENVIRONMENT VARIABLES")
    print("=" * 60)

    import secrets

    # Generate secure secret key
    secret_key = secrets.token_urlsafe(32)

    # Set environment variables
    os.environ['SECRET_KEY'] = secret_key
    os.environ['USE_AI_MOCKS'] = 'false'
    os.environ['API_HOST'] = '127.0.0.1'
    os.environ['API_PORT'] = '8001'
    os.environ['LOG_LEVEL'] = 'INFO'
    os.environ['DEBUG'] = 'false'
    os.environ['TESTING'] = 'false'

    print("[SUCCESS] Environment variables set!")
    print(f"SECRET_KEY: {secret_key[:20]}...")
    print("USE_AI_MOCKS: false")
    print("API_HOST: 127.0.0.1")
    print("API_PORT: 8001")
    print("LOG_LEVEL: INFO")
    print("DEBUG: false")
    print("TESTING: false")

    # Test configuration
    try:
        sys.path.append(str(Path.cwd()))
        from src.config import get_settings
        settings = get_settings()
        print(f"\n[SUCCESS] Configuration test passed!")
    except Exception as e:
        print(f"\n[ERROR] Configuration test failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "set":
        set_environment()
    else:
        show_environment()
