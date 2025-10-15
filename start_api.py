#!/usr/bin/env python3
"""
Quick API server starter for development.
"""

import os
import subprocess
import sys
from pathlib import Path

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = "8100"


def main():
    """Start the API server using the existing script."""
    script_path = Path(__file__).parent / "scripts" / "run_api.py"

    if not script_path.exists():
        print(f"Error: API script not found at {script_path}")
        return 1

    port = os.environ.get("API_PORT", DEFAULT_PORT)
    os.environ["API_PORT"] = str(port)

    print("Starting Therapy Compliance Analyzer API Server...")
    print(f"This will run on http://{DEFAULT_HOST}:{port}")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)

    try:
        subprocess.run([sys.executable, str(script_path)], check=True)
    except KeyboardInterrupt:
        print("\nAPI server stopped by user")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error starting API server: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
