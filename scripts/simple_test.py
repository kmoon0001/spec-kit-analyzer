#!/usr/bin/env python3
"""Simple test to check what's causing the slow startup."""

import sys
import time

print("Starting simple test...")

try:
    print("1. Testing basic imports...")
    start = time.time()
    from PySide6.QtWidgets import QApplication
    print(f"   PySide6 imported in {time.time() - start:.2f}s")
    
    start = time.time()
    from src.config import get_settings
    print(f"   Config imported in {time.time() - start:.2f}s")
    
    start = time.time()
    settings = get_settings()
    print(f"   Settings loaded in {time.time() - start:.2f}s")
    
    print("2. Testing database imports...")
    start = time.time()
    from src.database import init_db
    print(f"   Database imports in {time.time() - start:.2f}s")
    
    print("3. Testing GUI imports...")
    start = time.time()
    from src.gui.main_window import MainApplicationWindow
    print(f"   Main window imported in {time.time() - start:.2f}s")
    
    print("4. Creating QApplication...")
    start = time.time()
    app = QApplication(sys.argv)
    print(f"   QApplication created in {time.time() - start:.2f}s")
    
    print("✅ All imports successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()