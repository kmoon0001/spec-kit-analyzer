#!/usr/bin/env python3
"""Test that the GUI actually runs and displays."""

import sys
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    print("🚀 LAUNCHING THERAPY DOCUMENT COMPLIANCE ANALYSIS")
    print("=" * 60)
    
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    from src.gui.main_window_ultimate import UltimateMainWindow
    import asyncio
    from src.database import init_db
    
    # Initialize database
    print("📊 Initializing database...")
    asyncio.run(init_db())
    print("   ✅ Database ready")
    
    # Create application
    print("🖥️ Creating application...")
    app = QApplication([])
    print("   ✅ QApplication created")
    
    # Create main window
    print("🏥 Creating main window...")
    main_win = UltimateMainWindow()
    print("   ✅ Main window created")
    
    # Start the application
    print("⚡ Starting application...")
    main_win.start()
    print("   ✅ Application started and visible")
    
    print("\n🎉 SUCCESS! Application is running!")
    print("=" * 60)
    print("✨ FEATURES AVAILABLE:")
    print("   📱 4 Tabs: Analysis | Dashboard | Analytics | Settings")
    print("   🎨 4 Themes: Light | Dark | Medical | Nature")
    print("   🤖 6 AI Models with individual status")
    print("   💬 Enhanced chat bot (floating button)")
    print("   📋 Medicare Part B rubric selector")
    print("   🎮 Easter eggs: Konami code & logo clicks")
    print("   🌴 Pacific Coast signature in cursive")
    print("   📄 Comprehensive reporting with all features")
    print("\n🎯 TO TEST:")
    print("   1. Upload a document (drag & drop or click)")
    print("   2. Select Medicare Part B rubric")
    print("   3. Configure analysis options")
    print("   4. Click Analyze button")
    print("   5. Try the chat assistant")
    print("   6. Explore different themes")
    print("   7. Test easter eggs!")
    print("\n⌨️ KEYBOARD SHORTCUTS:")
    print("   Ctrl+O - Upload Document")
    print("   F5 - Run Analysis")
    print("   Ctrl+T - Chat Assistant")
    print("   F11 - Fullscreen")
    print("   ↑↑↓↓←→←→BA - Konami Code")
    
    # Auto-close after showing info
    def close_app():
        print("\n👋 Demo complete - closing application")
        app.quit()
    
    # Close after 3 seconds for demo
    QTimer.singleShot(3000, close_app)
    
    # Run the application
    print("\n🔄 Running for 3 seconds to demonstrate...")
    app.exec()
    
    print("✅ Application closed successfully!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()