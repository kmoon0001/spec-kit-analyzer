#!/usr/bin/env python3
"""Quick GUI test to identify issues."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    print("1. Testing PySide6 import...")
    from PySide6.QtWidgets import QApplication

    print("   ✓ PySide6 imported successfully")

    print("2. Testing database import...")
    from src.database import init_db

    print("   ✓ Database import successful")

    print("3. Testing GUI import...")
    from src.gui.main_window import MainApplicationWindow

    print("   ✓ GUI import successful")

    print("4. Creating QApplication...")
    app = QApplication([])
    print("   ✓ QApplication created")

    print("5. Testing database init...")
    import asyncio

    asyncio.run(init_db())
    print("   ✓ Database initialized")

    print("6. Creating main window...")
    main_win = MainApplicationWindow()
    print("   ✓ Main window created")

    print("\n✅ All tests passed! PySide6 GUI should work.")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback

    traceback.print_exc()
