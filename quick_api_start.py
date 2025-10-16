#!/usr/bin/env python3
"""
Quick API Starter - Just start the FastAPI server
"""

import subprocess
import sys
import time
import requests
from pathlib import Path

def start_api():
    print("🚀 Starting FastAPI server...")
    
    # Start the API server
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "src.api.main:app",
        "--host", "127.0.0.1",
        "--port", "8100",
        "--reload"
    ])
    
    print(f"API server started with PID: {process.pid}")
    
    # Wait for it to be ready
    print("Waiting for API to be ready...")
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get("http://127.0.0.1:8100/health", timeout=2)
            if response.status_code == 200:
                print("✅ API server is ready!")
                print("🔗 API URL: http://127.0.0.1:8100")
                print("📊 Health: http://127.0.0.1:8100/health")
                print("📈 Docs: http://127.0.0.1:8100/docs")
                print("\n💡 Press Ctrl+C to stop")
                break
        except:
            pass
        time.sleep(1)
        print(f"  Waiting... ({i+1}/30)")
    
    try:
        # Keep running
        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping API server...")
        process.terminate()
        process.wait()
        print("✅ API server stopped")

if __name__ == "__main__":
    start_api()