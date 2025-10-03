#!/usr/bin/env python3
"""
Quick test script for the modern UI.
"""

import sys
import os
import pytest

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


@pytest.mark.skip(reason="GUI tests cannot be run in a headless environment.")
def test_modern_ui():
    """Test the modern UI directly."""
    try:
        from PyQt6.QtWidgets import QApplication
        from src.gui.main_window_working import ModernMainWindow

        print("🧪 Testing Modern UI...")

        # Create application
        app = QApplication(sys.argv)

        # Create window
        window = ModernMainWindow()
        window.show()

        print("✅ Modern UI created and shown!")
        print(f"Window visible: {window.isVisible()}")
        print(f"Window size: {window.size().width()}x{window.size().height()}")

        # Start the window
        window.start()

        print("🎯 Test complete - window should be visible with content!")
        print("Press Ctrl+C to close or close the window manually.")

        # Run the app
        return app.exec()

    except Exception as e:
        print(f"❌ Error testing UI: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(test_modern_ui())
