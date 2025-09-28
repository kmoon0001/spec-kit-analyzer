#!/usr/bin/env python3
"""
Minimal GUI test to isolate window visibility issues.
"""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

class MinimalTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Therapy Compliance Analyzer - Test Window")
        self.setGeometry(200, 200, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Add test content
        title_label = QLabel("🎯 Therapy Compliance Analyzer")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        
        status_label = QLabel("✅ GUI is working! This is a test window.")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet("font-size: 16px; margin: 20px;")
        
        info_label = QLabel("""
        If you can see this window, then PyQt6 is working correctly.
        
        The main application should work too. Try running:
        python run_gui_safe.py
        
        If the main app still doesn't show, there might be an issue with
        the AI model loading or window management.
        """)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("margin: 20px; padding: 20px; background-color: #f0f0f0;")
        
        layout.addWidget(title_label)
        layout.addWidget(status_label)
        layout.addWidget(info_label)
        
        # Force window to be visible and on top
        self.show()
        self.raise_()
        self.activateWindow()
        
        print(f"✅ Test window created and shown")
        print(f"Window visible: {self.isVisible()}")
        print(f"Window geometry: {self.geometry().x()}, {self.geometry().y()}, {self.geometry().width()}, {self.geometry().height()}")

def main():
    print("🔍 Starting minimal GUI test...")
    
    app = QApplication(sys.argv)
    app.setApplicationName("Therapy Compliance Analyzer Test")
    
    window = MinimalTestWindow()
    
    print("👀 Look for the test window on your screen!")
    print("   It should be titled 'Therapy Compliance Analyzer - Test Window'")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())