"""
GUI entry point script.

This script launches the PySide6 GUI application.
"""
import sys
from pathlib import Path
import asyncio
import time
import requests

# Add project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Set matplotlib backend before importing any GUI components
import matplotlib
import os
# Force matplotlib to use the correct backend for PySide6
os.environ['QT_API'] = 'pyside6'
matplotlib.use('Qt5Agg')

from PySide6.QtWidgets import QApplication, QMessageBox

def check_api_connection(max_attempts=5, delay=2):
    """Check if the API server is running and accessible."""
    print("Checking API server connection...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://127.0.0.1:8001/health", timeout=5)
            if response.status_code == 200:
                print("SUCCESS: API server is running and accessible!")
                return True
        except requests.exceptions.RequestException as e:
            print(f"   Attempt {attempt + 1}/{max_attempts}: API not ready ({e})")
        
        if attempt < max_attempts - 1:
            time.sleep(delay)
    
    print("ERROR: API server is not accessible")
    return False

if __name__ == "__main__":
    try:
        print("Starting Therapy Compliance Analyzer GUI...")
        
        # Check if API is running
        if not check_api_connection():
            print("WARNING: API server not detected. Please start the API server first:")
            print("   python run_api.py")
            print("\nOr use the combined startup script:")
            print("   python start_application.py")
            
            # Show a dialog to the user
            app = QApplication(sys.argv)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("API Server Required")
            msg.setText("The API server is not running.")
            msg.setInformativeText("Please start the API server first:\n\npython run_api.py\n\nOr use: python start_application.py")
            msg.exec()
            sys.exit(1)
        
        # Initialize the database first to ensure tables are created
        from src.database import init_db
        asyncio.run(init_db())

        # Create and run the application
        app = QApplication(sys.argv)
        
        # Show login dialog
        from src.gui.dialogs.login_dialog import LoginDialog
        from src.database import models
        
        login_dialog = LoginDialog()
        
        if login_dialog.exec():
            # Get credentials
            username, password = login_dialog.get_credentials()
            
            # Authenticate with API
            try:
                response = requests.post(
                    "http://127.0.0.1:8001/auth/login",
                    data={"username": username, "password": password},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get("access_token")
                    
                    # Get user info
                    user_response = requests.get(
                        "http://127.0.0.1:8001/auth/me",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=10
                    )
                    
                    if user_response.status_code == 200:
                        user_data = user_response.json()
                        
                        # Create user object
                        user = models.User(
                            id=user_data.get("id"),
                            username=user_data.get("username"),
                            is_admin=user_data.get("is_admin", False)
                        )
                        
                        from src.gui.main_window import MainApplicationWindow
                        main_win = MainApplicationWindow(user, token)
                        main_win.show()
                        
                        print("SUCCESS: GUI application started successfully!")
                        sys.exit(app.exec())
                    else:
                        QMessageBox.critical(None, "Error", "Failed to get user information")
                        sys.exit(1)
                else:
                    QMessageBox.critical(None, "Login Failed", "Invalid username or password")
                    sys.exit(1)
                    
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Authentication failed: {e}")
                sys.exit(1)
        else:
            # User cancelled login
            print("Login cancelled by user")
            sys.exit(0)
        
    except Exception as e:
        print(f"ERROR: Error starting application: {e}")
        import traceback
        traceback.print_exc()
        print("\nPlease ensure PySide6 is installed: pip install PySide6")
        sys.exit(1)