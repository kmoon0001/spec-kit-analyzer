#!/usr/bin/env python3
"""Minimal GUI launcher that bypasses heavy imports."""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QTextEdit

class MinimalMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Therapy Compliance Analyzer - Quick Start")
        self.setGeometry(100, 100, 800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Therapy Compliance Analyzer")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # Status
        status = QLabel("✅ Quick start mode - bypassing heavy imports")
        status.setStyleSheet("color: green; margin: 10px;")
        layout.addWidget(status)
        
        # Document area
        self.document_area = QTextEdit()
        self.document_area.setPlaceholderText("Document content will appear here...")
        layout.addWidget(self.document_area)
        
        # Buttons
        btn_layout = QVBoxLayout()
        
        upload_btn = QPushButton("Upload Document")
        upload_btn.clicked.connect(self.upload_document)
        btn_layout.addWidget(upload_btn)
        
        analyze_btn = QPushButton("Run Analysis")
        analyze_btn.clicked.connect(self.run_analysis)
        btn_layout.addWidget(analyze_btn)
        
        layout.addLayout(btn_layout)
        
    def upload_document(self):
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Document", 
            "", 
            "All Files (*.pdf *.docx *.txt);;PDF Files (*.pdf);;Word Files (*.docx);;Text Files (*.txt)"
        )
        if file_path:
            self.document_area.setText(f"Document loaded: {file_path}")
            
    def run_analysis(self):
        self.document_area.append("\n--- Analysis Results ---")
        self.document_area.append("✅ Quick analysis complete!")
        self.document_area.append("Note: This is minimal mode. Full analysis requires full startup.")

def main():
    app = QApplication(sys.argv)
    
    window = MinimalMainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()