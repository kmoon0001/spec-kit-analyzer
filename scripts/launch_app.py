#!/usr/bin/env python3
"""Launch the Therapy Document Compliance Analysis application."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

print("🏥 THERAPY DOCUMENT COMPLIANCE ANALYSIS")
print("=" * 50)
print("🚀 Launching application...")

try:
    import asyncio

    from PySide6.QtWidgets import QApplication
    from src.gui.main_window_ultimate import UltimateMainWindow

    from src.database import init_db

    # Initialize database
    asyncio.run(init_db())

    # Create and run application
    app = QApplication(sys.argv)
    main_win = UltimateMainWindow()
    main_win.start()

    print("✅ Application launched successfully!")
    print("\n🎯 READY TO USE:")
    print("   • Upload documents via drag & drop")
    print("   • Select Medicare Part B rubrics")
    print("   • Run comprehensive analysis")
    print("   • Use AI chat assistant")
    print("   • Try easter eggs!")
    print("\n💡 TIP: Click the hospital logo 7 times for credits!")
    print("🎮 TIP: Enter ↑↑↓↓←→←→BA for developer mode!")

    # Run the application
    sys.exit(app.exec())

except Exception as e:
    print(f"❌ Error launching application: {e}")
    import traceback

    traceback.print_exc()
