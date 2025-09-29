#!/usr/bin/env python3
"""
Simple startup script for the Therapy Compliance Analyzer.
Handles environment setup and launches the application.
"""
import sys
import subprocess
from pathlib import Path

def check_virtual_environment():
    """Check if we're in a virtual environment."""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import PyQt6
        import fastapi
        import sqlalchemy
        print("[OK] Core dependencies found")
        return True
    except ImportError as e:
        print(f"[ERROR] Missing dependency: {e}")
        return False

def main():
    """Main startup function."""
    print("[START] Starting Therapy Compliance Analyzer...")
    print("=" * 50)

    # Check virtual environment
    if not check_virtual_environment():
        print("[WARN]  Warning: Not running in a virtual environment")
        print("   Consider activating .venv first:")
        print("   .venv\\Scripts\\activate")
        print()

    # Check dependencies
    if not check_dependencies():
        print("\n[SETUP] Installing dependencies...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            print("[OK] Dependencies installed successfully")
        except subprocess.CalledProcessError:
            print("[ERROR] Failed to install dependencies")
            print("   Please run: pip install -r requirements.txt")
            return 1

    # Check if startup files exist
    startup_file = "run_gui_safe.py" if Path("run_gui_safe.py").exists() else "run_gui.py"
    if not Path(startup_file).exists():
        print(f"[ERROR] {startup_file} not found in current directory")
        print("   Make sure you're in the project root directory")
        return 1

    # Launch the application
    print(f"\n[INFO] Launching GUI application using {startup_file}...")
    print("   (First startup may take 30-60 seconds to load AI models)")
    try:
        result = subprocess.run([sys.executable, startup_file], check=False)
        if result.returncode != 0:
            print(f"[WARN]  Application exited with code {result.returncode}")
            if result.returncode == 3221226505:
                print("   This appears to be a Windows access violation - try running as administrator")
            else:
                print("   This might be normal if you closed the application")
        else:
            print("[OK] Application closed normally")
    except KeyboardInterrupt:
        print("\n[STOP] Application stopped by user")
        return 0

    return 0

if __name__ == "__main__":
    sys.exit(main())