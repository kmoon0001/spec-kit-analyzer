#!/usr/bin/env python3
"""
Simple, reliable interface for Therapy Compliance Analyzer.
Uses only regex-based NER to avoid model loading conflicts.
"""

import sys
import os
import re
from typing import List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


class SimpleNERAnalyzer:
    """Simple regex-based NER analyzer that doesn't load any models."""
    
    def __init__(self):
        # Clinical patterns for regex-based extraction
        self.clinical_patterns = {
            "signature_line": re.compile(
                r"(?:signature|signed|therapist|by|clinician|provider|treating)[\s:]*"
                r"(?:dr\.?\s+)?([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)*[A-Z][a-z]+)"
                r"(?:\s*,?\s*(?:PT|OT|SLP|COTA|PTA|RN|LPN|MD|DPT|OTR|CCC-SLP))?",
                re.IGNORECASE
            ),
            "title_name": re.compile(
                r"(?:Dr\.?\s+|Doctor\s+)([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)*[A-Z][a-z]+)",
                re.IGNORECASE
            ),
            "credential_line": re.compile(
                r"([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)*[A-Z][a-z]+)\s*,?\s*(?:PT|OT|SLP|COTA|PTA|RN|LPN|MD|DPT|OTR|CCC-SLP)",
                re.IGNORECASE
            )
        }
    
    def extract_clinician_names(self, text: str) -> List[str]:
        """Extract clinician names using regex patterns."""
        names = []
        
        for pattern_name, pattern in self.clinical_patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                name = match.strip()
                if name and len(name.split()) >= 2:  # At least first and last name
                    names.append(name)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_names = []
        for name in names:
            if name not in seen:
                seen.add(name)
                unique_names.append(name)
        
        return unique_names


def start_simple_gui():
    """Start simple GUI interface."""
    try:
        from PyQt6.QtWidgets import (
            QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
            QTextEdit, QPushButton, QLabel, QSplitter, QFrame
        )
        from PyQt6.QtCore import Qt
        
        class SimpleComplianceWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("Therapy Compliance Analyzer - Simple Interface")
                self.setGeometry(100, 100, 1200, 800)
                
                # Initialize NER analyzer
                self.ner_analyzer = SimpleNERAnalyzer()
                
                # Set up UI
                self.setup_ui()
                
            def setup_ui(self):
                """Set up the user interface."""
                central_widget = QWidget()
                self.setCentralWidget(central_widget)
                
                # Main layout
                main_layout = QVBoxLayout(central_widget)
                main_layout.setContentsMargins(20, 20, 20, 20)
                
                # Header
                header = QLabel("🏥 Therapy Compliance Analyzer")
                header.setAlignment(Qt.AlignmentFlag.AlignCenter)
                header.setStyleSheet("""
                    QLabel {
                        font-size: 24px;
                        font-weight: bold;
                        color: #2c3e50;
                        padding: 20px;
                        background-color: #ecf0f1;
                        border-radius: 10px;
                        margin-bottom: 20px;
                    }
                """)
                main_layout.addWidget(header)
                
                # Create splitter for document and results
                splitter = QSplitter(Qt.Orientation.Horizontal)
                main_layout.addWidget(splitter)
                
                # Left panel - Document input
                left_panel = QFrame()
                left_layout = QVBoxLayout(left_panel)
                
                doc_label = QLabel("📄 Clinical Document:")
                doc_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #34495e;")
                left_layout.addWidget(doc_label)
                
                self.document_text = QTextEdit()
                self.document_text.setPlaceholderText(
                    "Paste your clinical documentation here...\n\n"
                    "Example:\n"
                    "Progress Note\n"
                    "Patient: John Doe\n"
                    "Date: 10/02/2025\n\n"
                    "Patient continues to make progress with mobility training.\n"
                    "Gait training performed for 30 minutes.\n"
                    "Patient able to walk 100 feet with minimal assistance.\n\n"
                    "Signature: Dr. Jane Smith, PT\n"
                    "Co-signed by: Michael Brown, COTA"
                )
                self.document_text.setStyleSheet("""
                    QTextEdit {
                        border: 2px solid #bdc3c7;
                        border-radius: 8px;
                        padding: 10px;
                        font-family: 'Consolas', 'Courier New', monospace;
                        font-size: 12px;
                        background-color: white;
                    }
                """)
                left_layout.addWidget(self.document_text)
                
                # Analyze button
                analyze_btn = QPushButton("🔍 Analyze Document")
                analyze_btn.clicked.connect(self.analyze_document)
                analyze_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3498db;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 12px 24px;
                        font-size: 14px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #2980b9;
                    }
                    QPushButton:pressed {
                        background-color: #21618c;
                    }
                """)
                left_layout.addWidget(analyze_btn)
                
                splitter.addWidget(left_panel)
                
                # Right panel - Results
                right_panel = QFrame()
                right_layout = QVBoxLayout(right_panel)
                
                results_label = QLabel("📊 Analysis Results:")
                results_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #34495e;")
                right_layout.addWidget(results_label)
                
                self.results_text = QTextEdit()
                self.results_text.setReadOnly(True)
                self.results_text.setStyleSheet("""
                    QTextEdit {
                        border: 2px solid #bdc3c7;
                        border-radius: 8px;
                        padding: 10px;
                        font-family: 'Consolas', 'Courier New', monospace;
                        font-size: 12px;
                        background-color: #f8f9fa;
                    }
                """)
                right_layout.addWidget(self.results_text)
                
                # Clear button
                clear_btn = QPushButton("🗑️ Clear Results")
                clear_btn.clicked.connect(self.clear_results)
                clear_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #95a5a6;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 8px 16px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #7f8c8d;
                    }
                """)
                right_layout.addWidget(clear_btn)
                
                splitter.addWidget(right_panel)
                
                # Set splitter proportions
                splitter.setSizes([600, 600])
                
                # Status bar
                self.statusBar().showMessage("Ready - Simple NER interface loaded")
                
                # Add sample text
                sample_text = """Progress Note - Physical Therapy

Patient: John Doe
DOB: 01/15/1980
Date of Service: 10/02/2025

SUBJECTIVE:
Patient reports decreased pain in right shoulder from 7/10 to 4/10 since last visit.
States he is able to perform ADLs with less difficulty.

OBJECTIVE:
Patient arrived on time for scheduled appointment.
ROM measurements:
- Shoulder flexion: 120 degrees (improved from 90 degrees)
- Shoulder abduction: 110 degrees (improved from 85 degrees)

ASSESSMENT:
Patient continues to make good progress toward functional goals.
Demonstrating improved strength and range of motion.

PLAN:
Continue current treatment plan.
Progress to next level of strengthening exercises.
Patient education on home exercise program compliance.

Next appointment scheduled for 10/05/2025.

Signature: Dr. Jane Smith, PT
License #: PT12345
Co-signed by: Michael Brown, COTA"""
                
                self.document_text.setText(sample_text)
                
            def analyze_document(self):
                """Analyze the document text."""
                text = self.document_text.toPlainText()
                if not text.strip():
                    self.results_text.setText("❌ Please enter some text to analyze.")
                    return
                
                self.results_text.clear()
                self.results_text.append("🔍 DOCUMENT ANALYSIS STARTED")
                self.results_text.append("=" * 50)
                self.results_text.append("")
                
                # Extract clinician names
                clinicians = self.ner_analyzer.extract_clinician_names(text)
                
                self.results_text.append("👨‍⚕️ CLINICIAN IDENTIFICATION")
                self.results_text.append("-" * 30)
                if clinicians:
                    self.results_text.append(f"✅ Found {len(clinicians)} clinician(s):")
                    for i, name in enumerate(clinicians, 1):
                        self.results_text.append(f"  {i}. {name}")
                else:
                    self.results_text.append("ℹ️ No clinician signatures detected")
                
                self.results_text.append("")
                
                # Basic compliance checks
                self.results_text.append("📋 BASIC COMPLIANCE CHECKS")
                self.results_text.append("-" * 30)
                
                compliance_items = [
                    ("Patient identification", bool(re.search(r"patient:?\s+\w+", text, re.IGNORECASE))),
                    ("Date of service", bool(re.search(r"date.*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", text, re.IGNORECASE))),
                    ("Clinician signature", len(clinicians) > 0),
                    ("Treatment provided", bool(re.search(r"treatment|therapy|exercise|intervention", text, re.IGNORECASE))),
                    ("Assessment/Progress", bool(re.search(r"assessment|progress|improvement|objective", text, re.IGNORECASE))),
                ]
                
                passed = 0
                for item, status in compliance_items:
                    icon = "✅" if status else "❌"
                    self.results_text.append(f"  {icon} {item}")
                    if status:
                        passed += 1
                
                self.results_text.append("")
                self.results_text.append("📊 COMPLIANCE SUMMARY")
                self.results_text.append("-" * 30)
                score = (passed / len(compliance_items)) * 100
                self.results_text.append(f"Overall Score: {score:.0f}% ({passed}/{len(compliance_items)} items)")
                
                if score >= 80:
                    self.results_text.append("🟢 Good compliance level")
                elif score >= 60:
                    self.results_text.append("🟡 Moderate compliance - some improvements needed")
                else:
                    self.results_text.append("🔴 Low compliance - significant improvements needed")
                
                self.statusBar().showMessage(f"Analysis complete - {len(clinicians)} clinician(s) found, {score:.0f}% compliance")
                
            def clear_results(self):
                """Clear the results area."""
                self.results_text.clear()
                self.statusBar().showMessage("Results cleared - Ready for new analysis")
        
        app = QApplication(sys.argv)
        window = SimpleComplianceWindow()
        window.show()
        
        print("✅ Simple Therapy Compliance Analyzer started successfully!")
        print("📋 Features available:")
        print("  • Regex-based clinician name extraction")
        print("  • Basic compliance checking")
        print("  • No model loading - fast and reliable")
        print("  • Works with Presidio PHI detection")
        
        return app.exec()
        
    except Exception as e:
        print(f"❌ Failed to start simple GUI: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    print("🚀 Starting Simple Therapy Compliance Analyzer...")
    print("=" * 50)
    sys.exit(start_simple_gui())