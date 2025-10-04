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
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Set matplotlib backend before importing any GUI components
import matplotlib
import os
# Force matplotlib to use the correct backend for PySide6
os.environ['QT_API'] = 'pyside6'
matplotlib.use('Qt5Agg')

from PySide6.QtWidgets import QApplication, QMessageBox

def check_api_connection(max_attempts=5, delay=2):
    """Check if the API server is running and accessible."""
    print("🔍 Checking API server connection...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://127.0.0.1:8001/health", timeout=5)
            if response.status_code == 200:
                print("✅ API server is running and accessible!")
                return True
        except requests.exceptions.RequestException as e:
            print(f"   Attempt {attempt + 1}/{max_attempts}: API not ready ({e})")
        
        if attempt < max_attempts - 1:
            time.sleep(delay)
    
    print("❌ API server is not accessible")
    return False

if __name__ == "__main__":
    try:
        print("🚀 Starting Therapy Compliance Analyzer GUI...")
        
        # Check if API is running
        if not check_api_connection():
            print("⚠️  API server not detected. Please start the API server first:")
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
        
        from src.gui.main_window import MainApplicationWindow
        main_win = MainApplicationWindow()
        main_win.show()  # Show the window
        
        print("✅ GUI application started successfully!")
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()
        print("\nPlease ensure PySide6 is installed: pip install PySide6")
        sys.exit(1)