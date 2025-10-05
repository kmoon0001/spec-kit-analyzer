#!/usr/bin/env python3
"""Interactive test to verify the floating chat button is working properly."""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

def main():
    """Run interactive chat button test"""
    
    print("🚀 INTERACTIVE CHAT BUTTON TEST")
    print("=" * 50)
    
    try:
        # Import and setup
        from PySide6.QtWidgets import QApplication, QMessageBox
        from src.gui.main_window import MainApplicationWindow
        from src.database import init_db
        
        print("✅ Imports successful")
        
        # Initialize database
        asyncio.run(init_db())
        print("✅ Database initialized")
        
        # Create application
        app = QApplication([])
        main_win = MainApplicationWindow()
        
        # Start the application (this makes chat button visible)
        main_win.start()
        
        print("✅ Application started")
        print("\n" + "=" * 50)
        print("🎯 CHAT BUTTON VERIFICATION")
        print("=" * 50)
        
        if hasattr(main_win, 'chat_button'):
            button = main_win.chat_button
            print("✅ Chat button found")
            print(f"   📐 Size: {button.width()}x{button.height()}")
            print(f"   👁️ Visible: {button.isVisible()}")
            print(f"   ⚡ Enabled: {button.isEnabled()}")
            pos = button.pos()
            print(f"   📍 Position: ({pos.x()}, {pos.y()})")
            
            # Show informational message
            msg = QMessageBox(main_win)
            msg.setWindowTitle("Chat Button Test")
            msg.setText("Look for the floating chat button (💬) in the top-right corner!")
            msg.setInformativeText(
                "The chat button should be:\n"
                "• Blue circular button with 💬 emoji\n"
                "• Located in top-right corner\n"
                "• Draggable around the window\n"
                "• Clickable to open chat dialog\n\n"
                "Try clicking and dragging it!"
            )
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.show()
            
        else:
            print("❌ Chat button not found!")
            
        print("\n🎮 INSTRUCTIONS:")
        print("1. Look for the blue 💬 button in the top-right corner")
        print("2. Try clicking it to open the chat dialog")
        print("3. Try dragging it around the window")
        print("4. Close the application when done testing")
        
        # Run the application
        return app.exec()
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())