#!/usr/bin/env python3
"""
Debug GUI startup issues step by step.
"""

import sys
import traceback
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget

def test_basic_qt():
    """Test basic Qt functionality."""
    print("Testing basic Qt...")
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("Basic Qt Test")
    
    central_widget = QWidget()
    layout = QVBoxLayout()
    label = QLabel("Qt is working!")
    layout.addWidget(label)
    central_widget.setLayout(layout)
    window.setCentralWidget(central_widget)
    
    window.show()
    print("Basic Qt window created successfully")
    
    # Don't exec, just test creation
    app.quit()
    return True

def test_auth_import():
    """Test auth service import."""
    print("Testing auth import...")
    try:
        from src.auth import AuthService
        auth = AuthService()
        print("Auth service imported successfully")
        return True
    except Exception as e:
        print(f"Auth import failed: {e}")
        traceback.print_exc()
        return False

def test_main_window_import():
    """Test main window import."""
    print("Testing main window import...")
    try:
        from src.gui.main_window import MainApplicationWindow
        print("Main window imported successfully")
        return True
    except Exception as e:
        print(f"Main window import failed: {e}")
        traceback.print_exc()
        return False

def test_main_window_creation():
    """Test main window creation."""
    print("Testing main window creation...")
    try:
        from src.gui.main_window import MainApplicationWindow
        
        # Create a mock user
        class MockUser:
            def __init__(self):
                self.username = "test_user"
                self.is_admin = True
        
        mock_user = MockUser()
        
        # Use existing QApplication instance if available
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        window = MainApplicationWindow(user=mock_user, token="test_token")
        print("Main window created successfully")
        
        return True
    except Exception as e:
        print(f"Main window creation failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run debug tests."""
    print("🔧 Debugging GUI startup issues...\n")
    
    tests = [
        ("Basic Qt", test_basic_qt),
        ("Auth Import", test_auth_import),
        ("Main Window Import", test_main_window_import),
        ("Main Window Creation", test_main_window_creation),
    ]
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            success = test_func()
            if success:
                print(f"✅ {test_name} passed")
            else:
                print(f"❌ {test_name} failed")
                break
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            traceback.print_exc()
            break
    
    print("\n🔧 Debug complete")

if __name__ == "__main__":
    main()