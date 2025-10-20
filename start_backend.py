#!/usr/bin/env python3
"""
Backend startup script that handles Windows Fortran runtime issues
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the backend with proper environment setup."""
    
    # Set environment variables to handle Fortran runtime issues
    os.environ["FOR_DISABLE_CONSOLE_CTRL_HANDLER"] = "1"
    os.environ["OMP_NUM_THREADS"] = "1"  # Limit OpenMP threads
    os.environ["MKL_NUM_THREADS"] = "1"  # Limit MKL threads
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Activate virtual environment and start server
    venv_python = project_dir / "venv_fresh" / "Scripts" / "python.exe"
    
    if not venv_python.exists():
        print(f"Virtual environment not found at {venv_python}")
        return False
    
    # Start the server
    cmd = [
        str(venv_python),
        "-m", "uvicorn",
        "src.api.main:app",
        "--host", "0.0.0.0",
        "--port", "8001",
        "--reload"
    ]
    
    print("Starting backend server...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print(f"Backend started with PID: {process.pid}")
        print("Server should be available at http://127.0.0.1:8001")
        print("Press Ctrl+C to stop the server")
        
        # Wait for the process
        process.wait()
        
    except KeyboardInterrupt:
        print("\nShutting down server...")
        process.terminate()
        process.wait()
        print("Server stopped")
        
    except Exception as e:
        print(f"Error starting server: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
