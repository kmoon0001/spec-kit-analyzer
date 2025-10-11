#!/usr/bin/env python3
"""
Simple working GUI version to test basic functionality.
"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget


class SimpleMainWindow(QMainWindow):
    """Simple main window for testing."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Therapy Compliance Analyzer - Simple Mode")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Add components
        title = QLabel("Therapy Compliance Analyzer")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        status = QLabel("Status: Ready")
        status.setStyleSheet("color: green; margin: 5px;")
        layout.addWidget(status)

        # Add buttons
        upload_btn = QPushButton("Upload Document")
        upload_btn.clicked.connect(self.upload_document)
        layout.addWidget(upload_btn)

        analyze_btn = QPushButton("Run Analysis")
        analyze_btn.clicked.connect(self.run_analysis)
        layout.addWidget(analyze_btn)

        # Add text area for results
        self.results_area = QTextEdit()
        self.results_area.setPlaceholderText("Analysis results will appear here...")
        layout.addWidget(self.results_area)

        print("Simple GUI initialized successfully")

    def upload_document(self):
        """Handle document upload."""
        self.results_area.append("📄 Document upload clicked - functionality would go here")
        print("Upload document clicked")

    def run_analysis(self):
        """Handle analysis."""
        self.results_area.append("🔍 Analysis clicked - functionality would go here")
        print("Run analysis clicked")

    def closeEvent(self, event):
        """Handle window close event."""
        print("Window closing...")
        event.accept()


def main():
    """Main function."""
    print("Starting simple GUI...")

    app = QApplication(sys.argv)

    # Create and show window
    window = SimpleMainWindow()
    window.show()

    print("GUI started successfully")

    # Run the application
    result = app.exec()
    print("GUI closed")
    return result


if __name__ == "__main__":
    sys.exit(main())
