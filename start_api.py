#!/usr/bin/env python3
"""
Quick API server starter for development.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Start the API server using the existing script."""
    script_path = Path(__file__).parent / "scripts" / "run_api.py"

    if not script_path.exists():
        print(f"Error: API script not found at {script_path}")
        return 1

    print("Starting Therapy Compliance Analyzer API Server...")
    print("This will run on http://127.0.0.1:8001")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)

    try:
        # Run the API script
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
