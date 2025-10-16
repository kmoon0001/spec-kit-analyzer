#!/usr/bin/env python3
"""
Quick startup script for development and testing.
Bypasses heavy AI model loading for faster startup.
"""

import subprocess
import sys
import time
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def start_lightweight_api():
    """Start API server without heavy AI models."""
    print("🚀 Starting lightweight API server...")
    try:
        # Use uvicorn directly for faster startup
        cmd = [sys.executable, "-m", "uvicorn", "src.api.main:app", "--host", "127.0.0.1", "--port", "8001", "--reload"]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        # Wait a moment for server to start
        time.sleep(3)
        print("✅ API server started on http://127.0.0.1:8001")
        return process

    except Exception as e:
        print(f"❌ Failed to start API: {e}")
        return None


def start_simple_gui():
    """Start the simple GUI version."""
    print("🖥️  Starting simple GUI...")
    try:
        from simple_gui import main as simple_main

        return simple_main()
    except Exception as e:
        print(f"❌ Failed to start GUI: {e}")
        return 1


def main():
    """Quick startup for development."""
    print("=" * 50)
    print("🏥 THERAPY COMPLIANCE ANALYZER - QUICK START")
    print("   Fast startup for development/testing")
    print("=" * 50)

    # Option 1: Just start simple GUI (no API needed)
    print("\n1. Simple GUI only (no backend)")
    print("2. Full stack (API + GUI)")

    choice = input("\nChoose option (1 or 2): ").strip()

    if choice == "1":
        print("\n🎯 Starting simple GUI only...")
        return start_simple_gui()

    elif choice == "2":
        print("\n🎯 Starting full stack...")

        # Start API
        api_process = start_lightweight_api()
        if not api_process:
            return 1

        try:
            # Start GUI
            gui_result = start_simple_gui()
            return gui_result
        finally:
            if api_process:
                print("🧹 Stopping API server...")
                api_process.terminate()

    else:
        print("❌ Invalid choice. Use 1 or 2.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
