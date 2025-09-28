#!/usr/bin/env python3
"""
Simple startup script for the Therapy Compliance Analyzer.
Handles environment setup and launches the application.
"""
import sys
import os
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
        print("✅ Core dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def main():
    """Main startup function."""
    print("🚀 Starting Therapy Compliance Analyzer...")
    print("=" * 50)
    
    # Check virtual environment
    if not check_virtual_environment():
        print("⚠️  Warning: Not running in a virtual environment")
        print("   Consider activating .venv first:")
        print("   .venv\\Scripts\\activate")
        print()
    
    # Check dependencies
    if not check_dependencies():
        print("\n📦 Installing dependencies...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            print("   Please run: pip install -r requirements.txt")
            return 1
    
    # Check if run_gui.py exists
    if not Path("run_gui.py").exists():
        print("❌ run_gui.py not found in current directory")
        print("   Make sure you're in the project root directory")
        return 1
    
    # Launch the application
    print("\n🎯 Launching GUI application...")
    try:
        subprocess.run([sys.executable, "run_gui.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start application: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())