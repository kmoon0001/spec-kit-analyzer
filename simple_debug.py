#!/usr/bin/env python3
"""
Therapy Compliance Analyzer - Simple Debug Tool
Quick debugging utilities without Unicode characters.
"""

import sys
import traceback
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

def debug_api():
    """Debug API startup."""
    print("DEBUGGING API STARTUP")
    print("=" * 50)
    
    try:
        print("1. Testing imports...")
        from fastapi import FastAPI
        print("   [OK] FastAPI imported")
        
        from src.api.main import app
        print("   [OK] API app imported")
        
        print("2. Testing configuration...")
        from src.config import settings
        print(f"   [OK] Config loaded: {getattr(settings, 'app_name', 'Therapy Compliance Analyzer')}")
        
        print("3. Testing database...")
        from src.database.database import init_db
        print("   [OK] Database module imported")
        
        print("4. Testing AI services...")
        from src.core.analysis_service import AnalysisService
        print("   [OK] AnalysisService imported")
        
        print("\n[SUCCESS] API startup components are ready!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] API startup failed: {e}")
        traceback.print_exc()
        return False

def debug_gui():
    """Debug GUI startup."""
    print("\nDEBUGGING GUI STARTUP")
    print("=" * 50)
    
    try:
        print("1. Testing PySide6...")
        from PySide6.QtWidgets import QApplication
        print("   [OK] PySide6 imported")
        
        print("2. Testing GUI components...")
        from src.gui.main_window import MainApplicationWindow
        print("   [OK] MainWindow imported")
        
        print("3. Testing theme system...")
        from src.gui.widgets.pycharm_dark_theme import pycharm_theme
        print("   [OK] Theme system imported")
        
        print("\n[SUCCESS] GUI startup components are ready!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] GUI startup failed: {e}")
        traceback.print_exc()
        return False

def debug_endpoints():
    """Debug API endpoints."""
    print("\nDEBUGGING API ENDPOINTS")
    print("=" * 50)
    
    try:
        from fastapi.testclient import TestClient
        from src.api.main import app
        
        client = TestClient(app)
        
        print("1. Testing health endpoint...")
        response = client.get("/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
            print("   [OK] Health endpoint working")
        else:
            print(f"   [ERROR] Health endpoint failed: {response.text}")
            return False
        
        print("2. Testing auth endpoint...")
        response = client.post("/auth/token", data={"username": "admin", "password": "admin123"})
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            token_data = response.json()
            print(f"   [OK] Auth working, token: {token_data.get('access_token', '')[:20]}...")
            return True
        else:
            print(f"   [ERROR] Auth failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"[ERROR] API endpoint testing failed: {e}")
        traceback.print_exc()
        return False

def debug_system():
    """Debug system resources."""
    print("\nDEBUGGING SYSTEM RESOURCES")
    print("=" * 50)
    
    try:
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"1. CPU Usage: {cpu_percent}%")
        
        # Memory usage
        memory = psutil.virtual_memory()
        print(f"2. RAM Usage: {memory.percent}% ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)")
        
        # Python processes
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            if 'python' in proc.info['name'].lower():
                python_processes.append(proc.info)
        
        print(f"3. Python Processes: {len(python_processes)}")
        for proc in python_processes:
            memory_mb = proc['memory_info'].rss / 1024**2
            print(f"   PID {proc['pid']}: {memory_mb:.1f}MB")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] System resource debugging failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Main debug function."""
    print("THERAPY COMPLIANCE ANALYZER - DEBUG TOOL")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "api":
            debug_api()
        elif command == "gui":
            debug_gui()
        elif command == "endpoints":
            debug_endpoints()
        elif command == "system":
            debug_system()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: api, gui, endpoints, system")
    else:
        # Run all tests
        results = {
            'api': debug_api(),
            'gui': debug_gui(),
            'endpoints': debug_endpoints(),
            'system': debug_system()
        }
        
        print("\nDEBUG SUMMARY")
        print("=" * 50)
        for test, result in results.items():
            status = "[PASS]" if result else "[FAIL]"
            print(f"{test.upper()}: {status}")

if __name__ == "__main__":
    main()
