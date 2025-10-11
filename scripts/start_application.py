#!/usr/bin/env python3
"""
Complete application startup script.
Starts both the FastAPI backend and PySide6 GUI in the correct order.
"""

import sys
import time
import subprocess
import requests
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def start_api_server():
    """Start the FastAPI server in a separate process."""
    print("🚀 Starting FastAPI backend server...")
    try:
        # Use subprocess to start the API server
        api_script_path = Path(__file__).parent / "run_api.py"
        process = subprocess.Popen([
            sys.executable, str(api_script_path)
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
        
        # Monitor the process output for Uvicorn's startup message
        for line in iter(process.stdout.readline, ''):
            print(f"[API] {line.strip()}")
            if "Application startup complete." in line:
                print("✅ API server is ready!")
                break
        
        return process
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return None

def wait_for_api_ready(max_attempts=30, delay=1):
    """Wait for the API to be ready by checking the health endpoint."""
    print("⏳ Waiting for API to be ready...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://127.0.0.1:8001/health", timeout=5)
            if response.status_code == 200:
                print("✅ API is responding and ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"   Attempt {attempt + 1}/{max_attempts}...")
        time.sleep(delay)
    
    print("❌ API failed to become ready within timeout period")
    return False

def start_gui():
    """Start the PySide6 GUI application."""
    print("🖥️  Starting PySide6 GUI application...")
    try:
        # Use the proper authentication flow from src.gui.main
        from src.gui.main import main as gui_main
        
        print("✅ GUI application started successfully!")
        return gui_main()
        
    except Exception as e:
        print(f"❌ Failed to start GUI: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    """Main application startup orchestrator."""
    print("=" * 60)
    print("🏥 THERAPY COMPLIANCE ANALYZER")
    print("   Starting complete application stack...")
    print("=" * 60)
    
    # Step 1: Start the API server
    api_process = start_api_server()
    if not api_process:
        print("❌ Failed to start API server. Exiting.")
        return 1
    
    try:
        # Step 2: Wait for API to be ready
        if not wait_for_api_ready():
            print("❌ API server not ready. Terminating...")
            api_process.terminate()
            return 1
        
        # Step 3: Start the GUI
        print("\n" + "=" * 60)
        print("🎯 Both backend and frontend are ready!")
        print("   You can now use the Therapy Compliance Analyzer")
        print("=" * 60 + "\n")
        
        gui_exit_code = start_gui()
        
        print("\n🔄 GUI application closed.")
        return gui_exit_code
        
    except KeyboardInterrupt:
        print("\n⏹️  Received interrupt signal. Shutting down...")
        return 0
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Always clean up the API process
        if api_process and api_process.poll() is None:
            print("🧹 Cleaning up API server process...")
            api_process.terminate()
            try:
                api_process.wait(timeout=5)
                print("✅ API server terminated gracefully")
            except subprocess.TimeoutExpired:
                print("⚠️  Force killing API server...")
                api_process.kill()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)