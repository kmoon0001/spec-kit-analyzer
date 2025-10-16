#!/usr/bin/env python3
"""
Minimal API Startup Script
Simple, reliable startup without complex diagnostics
"""

import subprocess
import sys
import time
import requests
from pathlib import Path

def kill_existing_processes():
    """Kill any existing processes on port 8100"""
    try:
        # Kill processes using port 8100
        subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                      capture_output=True, text=True)
        time.sleep(2)
    except Exception as e:
        print(f"Note: {e}")

def start_api():
    """Start the FastAPI server"""
    print("🚀 Starting Therapy Compliance Analyzer API...")
    
    # Kill existing processes
    kill_existing_processes()
    
    # Start the API server
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "src.api.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8100",
        "--reload"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    # Start the process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Wait a moment for startup
    time.sleep(3)
    
    # Check if API is responding
    for attempt in range(10):
        try:
            response = requests.get("http://127.0.0.1:8100/health", timeout=5)
            if response.status_code == 200:
                print("✅ API is running and healthy!")
                print(f"🌐 API available at: http://127.0.0.1:8100")
                print(f"📊 Health check: http://127.0.0.1:8100/health")
                return process
        except requests.exceptions.RequestException:
            print(f"⏳ Waiting for API... (attempt {attempt + 1}/10)")
            time.sleep(2)
    
    print("❌ API failed to start properly")
    return process

if __name__ == "__main__":
    process = start_api()
    
    if process:
        try:
            print("\n📝 API Logs:")
            print("=" * 50)
            
            # Stream output
            for line in process.stdout:
                print(line.strip())
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down API...")
            process.terminate()
            process.wait()