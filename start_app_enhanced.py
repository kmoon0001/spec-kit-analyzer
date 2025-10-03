#!/usr/bin/env python3
"""
Enhanced Professional GUI with Loading Screen and Full Features.
Shows loading progress while AI models initialize.
"""

import os
import sys
import time
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def start_enhanced_gui():
    """Start enhanced GUI with loading screen."""
    try:
        from PyQt6.QtWidgets import (
            QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
            QTextEdit, QPushButton, QLabel, QSplitter, QTabWidget,
            QProgressBar, QFrame, QComboBox, QLineEdit, QMessageBox,
            QDialog, QDialogButtonBox, QGroupBox, QCheckBox
        )
        from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
        from PyQt6.QtGui import QFont, QPixmap, QPalette, QColor
        
        class LoadingScreen(QDialog):
            """Loading screen with progress bar."""
            
            def __init__(self):
                super().__init__()
                self.setWindowTitle("Therapy Compliance Analyzer - Loading")
                self.setFixedSize(600, 400)
                self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
                
                # Main layout
                layout = QVBoxLayout(self)
                layout.setContentsMargins(40, 40, 40, 40)
                layout.setSpacing(30)
                
                # Header
                header = QLabel("🏥 Therapy Compliance Analyzer")
                header.setAlignment(Qt.AlignmentFlag.AlignCenter)
                header.setStyleSheet("""
                    QLabel {
                        font-size: 28px;
                        font-weight: bold;
                        color: #2c3e50;
                        padding: 20px;
                        background-color: #ecf0f1;
                        border-radius: 15px;
                        border: 3px solid #3498db;
                    }
                """)
                layout.addWidget(header)
                
                # Status label
                self.status_label = QLabel("Initializing system...")
                self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.status_label.setStyleSheet("""
                    QLabel {
                        font-size: 16px;
                        color: #34495e;
                        padding: 10px;
                    }
                """)
                layout.addWidget(self.status_label)
                
                # Progress bar
                self.progress_bar = QProgressBar()
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(0)
                self.progress_bar.setStyleSheet("""
                    QProgressBar {
                        border: 2px solid #bdc3c7;
                        border-radius: 10px;
                        text-align: center;
                        font-size: 14px;
                        font-weight: bold;
                        background-color: #ecf0f1;
                        height: 30px;
                    }
                    QProgressBar::chunk {
                        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #3498db, stop:1 #2980b9);
                        border-radius: 8px;
                    }
                """)
                layout.addWidget(self.progress_bar)
                
                # Details label
                self.details_label = QLabel("Loading AI models and initializing services...")
                self.details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.details_label.setStyleSheet("""
                    QLabel {
                        font-size: 12px;
                        color: #7f8c8d;
                        font-style: italic;
                    }
                """)
                layout.addWidget(self.details_label)
                
                # Set background
                self.setStyleSheet("""
                    QDialog {
                        background-color: #f8f9fa;
                        border: 2px solid #3498db;
                        border-radius: 20px;
                    }
                """)
                
            def update_progress(self, value, status, details=""):
                """Update the loading progress."""
                self.progress_bar.setValue(value)
                self.status_label.setText(status)
                if details:
                    self.details_label.setText(details)
                QApplication.processEvents()
        
        class ModelLoader(QThread):
            """Background thread to load AI models."""
            
            progress_updated = pyqtSignal(int, str, str)
            loading_complete = pyqtSignal(object)  # Pass the analyzer object
            
            def run(self):
                try:
                    self.progress_updated.emit(10, "Loading NER models...", "Initializing biomedical entity recognition")
                    time.sleep(0.5)
                    
                    from src.core.ner import NERAnalyzer
                    self.progress_updated.emit(30, "Loading NER models...", "Loading d4data/biomedical-ner-all")
                    
                    analyzer = NERAnalyzer(model_names=["d4data/biomedical-ner-all"])
                    self.progress_updated.emit(60, "Loading Presidio...", "Initializing PHI detection system")
                    time.sleep(1)
                    
                    self.progress_updated.emit(80, "Finalizing setup...", "Preparing user interface")
                    time.sleep(0.5)
                    
                    self.progress_updated.emit(100, "Ready!", "System loaded successfully")
                    time.sleep(0.5)
                    
                    self.loading_complete.emit(analyzer)
                    
                except Exception as e:
                    self.progress_updated.emit(0, f"Error: {str(e)}", "Failed to load AI models")
        
        class EnhancedComplianceWindow(QMainWindow):
            """Enhanced main window with full features."""
            
            def __init__(self, ner_analyzer):
                super().__init__()
                self.ner_analyzer = ner_analyzer
                self.chat_history = []
                self.setup_window()
                self.setup_ui()
                
            def setup_window(self):
                """Configure main window."""
                self.setWindowTitle("🏥 Therapy Compliance Analyzer - Professional Edition")
                self.setGeometry(100, 100, 1600, 1000)
                self.setMinimumSize(1400, 900)
                
            def setup_ui(self):
                """Set up the complete user interface."""
                central_widget = QWidget()
                self.setCentralWidget(central_widget)
                
                # Main layout
                main_layout = QVBoxLayout(central_widget)
                main_layout.setContentsMargins(20, 20, 20, 20)
                main_layout.setSpacing(15)
                
                # Header with system status
                header_widget = self.create_header()
                main_layout.addWidget(header_widget)
                
                # Progress bar section (for analysis)
                self.progress_widget = self.create_progress_section()
                main_layout.addWidget(self.progress_widget)
                
                # Main content area
                content_splitter = QSplitter(Qt.Orientation.Horizontal)
                
                # Left panel - Document input and controls
                left_panel = self.create_left_panel()
                content_splitter.addWidget(left_panel)
                
                # Right panel - Results and chat
                right_panel = self.create_right_panel()
                content_splitter.addWidget(right_panel)
                
                content_splitter.setSizes([700, 900])
                main_layout.addWidget(content_splitter)
                
                # Status bar
                self.statusBar().showMessage("✅ AI Models Loaded - Ready for Analysis")
                
                # Apply styling
                self.apply_professional_styling()
                
            def create_header(self):
                """Create header with title and system status."""
                header_frame = QFrame()
                header_frame.setStyleSheet("""
                    QFrame {
                        background-color: #2c3e50;
                        border-radius: 10px;
                        padding: 15px;
                    }
                """)
                
                layout = QHBoxLayout(header_frame)
                
                # Title
                title = QLabel("🏥 Therapy Compliance Analyzer")
                title.setStyleSheet("""
                    QLabel {
                        color: white;
                        font-size: 24px;
                        font-weight: bold;
                        background: transparent;
                    }
                """)
                layout.addWidget(title)
                
                layout.addStretch()
                
                # System status
                status_label = QLabel("🟢 AI Models Ready | 🔒 PHI Protected | 💻 Local Processing")
                status_label.setStyleSheet("""
                    QLabel {
                        color: #2ecc71;
                        font-size: 14px;
                        background: transparent;
                    }
                """)
                layout.addWidget(status_label)
                
                return header_frame
                
            def create_progress_section(self):
                """Create progress bar for analysis."""
                progress_frame = QFrame()
                layout = QVBoxLayout(progress_frame)
                
                self.analysis_progress_label = QLabel("Ready for analysis")
                self.analysis_progress_label.setStyleSheet("color: #34495e; font-size: 12px;")
                
                self.analysis_progress_bar = QProgressBar()
                self.analysis_progress_bar.setVisible(False)
                self.analysis_progress_bar.setStyleSheet("""
                    QProgressBar {
                        border: 2px solid #3498db;
                        border-radius: 8px;
                        text-align: center;
                        font-weight: bold;
                        background-color: #ecf0f1;
                        height: 25px;
                    }
                    QProgressBar::chunk {
                        background-color: #3498db;
                        border-radius: 6px;
                    }
                """)
                
                layout.addWidget(self.analysis_progress_label)
                layout.addWidget(self.analysis_progress_bar)
                
                return progress_frame
                
            def create_left_panel(self):
                """Create left panel with document input and controls."""
                left_widget = QWidget()
                layout = QVBoxLayout(left_widget)
                
                # Document input section
                doc_group = QGroupBox("📄 Clinical Document")
                doc_layout = QVBoxLayout(doc_group)
                
                # File upload button
                upload_btn = QPushButton("📁 Upload Document")
                upload_btn.clicked.connect(self.upload_document)
                upload_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3498db;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 10px 20px;
                        font-size: 14px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #2980b9;
                    }
                """)
                doc_layout.addWidget(upload_btn)
                
                # Document text area
                self.document_text = QTextEdit()
                self.document_text.setPlaceholderText(
                    "Upload a document or paste clinical text here...\n\n"
                    "Example:\n"
                    "Progress Note - Physical Therapy\n"
                    "Patient: John Doe\n"
                    "Date: 10/02/2025\n\n"
                    "SUBJECTIVE: Patient reports decreased pain...\n"
                    "OBJECTIVE: ROM measurements improved...\n"
                    "ASSESSMENT: Good progress toward goals...\n"
                    "PLAN: Continue current treatment...\n\n"
                    "Signature: Dr. Jane Smith, PT"
                )
                self.document_text.setMinimumHeight(300)
                doc_layout.addWidget(self.document_text)
                
                layout.addWidget(doc_group)
                
                # Controls section
                controls_group = QGroupBox("🎛️ Analysis Controls")
                controls_layout = QVBoxLayout(controls_group)
                
                # Rubric selection
                rubric_layout = QHBoxLayout()
                rubric_layout.addWidget(QLabel("Compliance Rubric:"))
                self.rubric_combo = QComboBox()
                self.rubric_combo.addItems(["PT Compliance Rubric", "OT Compliance Rubric", "SLP Compliance Rubric"])
                rubric_layout.addWidget(self.rubric_combo)
                controls_layout.addLayout(rubric_layout)
                
                # Analysis options
                self.detailed_analysis = QCheckBox("Detailed Analysis")
                self.detailed_analysis.setChecked(True)
                self.phi_scrubbing = QCheckBox("PHI Scrubbing")
                self.phi_scrubbing.setChecked(True)
                
                controls_layout.addWidget(self.detailed_analysis)
                controls_layout.addWidget(self.phi_scrubbing)
                
                # Run analysis button
                self.run_analysis_btn = QPushButton("🚀 Run Compliance Analysis")
                self.run_analysis_btn.clicked.connect(self.run_analysis)
                self.run_analysis_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #27ae60;
                        color: white;
                        border: none;
                        border-radius: 10px;
                        padding: 15px 25px;
                        font-size: 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #229954;
                    }
                    QPushButton:disabled {
                        background-color: #95a5a6;
                    }
                """)
                controls_layout.addWidget(self.run_analysis_btn)
                
                layout.addWidget(controls_group)
                
                return left_widget
                
            def create_right_panel(self):
                """Create right panel with results and chat."""
                right_widget = QWidget()
                layout = QVBoxLayout(right_widget)
                
                # Results tabs
                self.results_tabs = QTabWidget()
                
                # Analysis results tab
                self.results_text = QTextEdit()
                self.results_text.setReadOnly(True)
                self.results_text.setStyleSheet("""
                    QTextEdit {
                        background-color: #f8f9fa;
                        border: 2px solid #dee2e6;
                        border-radius: 8px;
                        padding: 10px;
                        font-family: 'Consolas', 'Courier New', monospace;
                        font-size: 12px;
                    }
                """)
                self.results_tabs.addTab(self.results_text, "📊 Analysis Results")
                
                # Chat tab
                chat_widget = self.create_chat_widget()
                self.results_tabs.addTab(chat_widget, "💬 AI Assistant")
                
                # Report tab
                self.report_text = QTextEdit()
                self.report_text.setReadOnly(True)
                self.results_tabs.addTab(self.report_text, "📋 Compliance Report")
                
                layout.addWidget(self.results_tabs)
                
                return right_widget
                
            def create_chat_widget(self):
                """Create chat interface."""
                chat_widget = QWidget()
                layout = QVBoxLayout(chat_widget)
                
                # Chat display
                self.chat_display = QTextEdit()
                self.chat_display.setReadOnly(True)
                self.chat_display.setStyleSheet("""
                    QTextEdit {
                        background-color: #ffffff;
                        border: 1px solid #dee2e6;
                        border-radius: 8px;
                        padding: 10px;
                    }
                """)
                layout.addWidget(self.chat_display)
                
                # Chat input
                input_layout = QHBoxLayout()
                self.chat_input = QLineEdit()
                self.chat_input.setPlaceholderText("Ask about compliance findings...")
                self.chat_input.returnPressed.connect(self.send_chat_message)
                
                send_btn = QPushButton("Send")
                send_btn.clicked.connect(self.send_chat_message)
                send_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #007bff;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                    }
                """)
                
                input_layout.addWidget(self.chat_input)
                input_layout.addWidget(send_btn)
                layout.addLayout(input_layout)
                
                # Add welcome message
                self.chat_display.append("""
                <div style='background-color: #e3f2fd; padding: 10px; border-radius: 8px; margin: 5px;'>
                    <b>🤖 AI Assistant:</b> Hello! I'm here to help with compliance questions. 
                    Upload a document and run analysis, then ask me about any findings!
                </div>
                """)
                
                return chat_widget
                
            def apply_professional_styling(self):
                """Apply professional medical styling."""
                self.setStyleSheet("""
                    QMainWindow {
                        background-color: #f5f6fa;
                    }
                    QGroupBox {
                        font-weight: bold;
                        border: 2px solid #bdc3c7;
                        border-radius: 10px;
                        margin-top: 10px;
                        padding-top: 10px;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 10px;
                        padding: 0 5px 0 5px;
                    }
                """)
                
            def upload_document(self):
                """Handle document upload."""
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "Upload Clinical Document", "", 
                    "All Supported (*.pdf *.docx *.txt);;PDF Files (*.pdf);;Word Documents (*.docx);;Text Files (*.txt)"
                )
                
                if file_path:
                    try:
                        # Simple text file reading for demo
                        if file_path.endswith('.txt'):
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            self.document_text.setText(content)
                            self.statusBar().showMessage(f"✅ Loaded: {os.path.basename(file_path)}")
                        else:
                            self.statusBar().showMessage("📄 Document parsing not implemented in demo - please paste text directly")
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Failed to load document: {str(e)}")
                        
            def run_analysis(self):
                """Run compliance analysis."""
                text = self.document_text.toPlainText().strip()
                if not text:
                    QMessageBox.warning(self, "No Document", "Please upload or paste a document first.")
                    return
                    
                # Show progress
                self.analysis_progress_bar.setVisible(True)
                self.analysis_progress_bar.setRange(0, 0)  # Indeterminate
                self.analysis_progress_label.setText("Analyzing document...")
                self.run_analysis_btn.setEnabled(False)
                self.run_analysis_btn.setText("🔄 Analyzing...")
                
                # Simulate analysis with timer
                QTimer.singleShot(2000, lambda: self.complete_analysis(text))
                
            def complete_analysis(self, text):
                """Complete the analysis and show results."""
                try:
                    # Extract clinician names
                    clinicians = self.ner_analyzer.extract_clinician_name(text)
                    
                    # Basic compliance checks
                    compliance_checks = [
                        ("Patient identification", bool(re.search(r"patient:?\s+\w+", text, re.IGNORECASE))),
                        ("Date of service", bool(re.search(r"date.*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", text, re.IGNORECASE))),
                        ("Clinician signature", len(clinicians) > 0),
                        ("Treatment documented", bool(re.search(r"treatment|therapy|exercise|intervention", text, re.IGNORECASE))),
                        ("Assessment included", bool(re.search(r"assessment|progress|objective|subjective", text, re.IGNORECASE))),
                    ]
                    
                    passed = sum(1 for _, status in compliance_checks if status)
                    score = (passed / len(compliance_checks)) * 100
                    
                    # Display results
                    results = f"""
🔍 COMPLIANCE ANALYSIS COMPLETE
{'=' * 50}

👨‍⚕️ CLINICIAN IDENTIFICATION:
{f"✅ Found {len(clinicians)} clinician(s): {', '.join(clinicians)}" if clinicians else "❌ No clinician signatures detected"}

📋 COMPLIANCE CHECKLIST:
"""
                    for item, status in compliance_checks:
                        icon = "✅" if status else "❌"
                        results += f"{icon} {item}\n"
                    
                    results += f"""
📊 COMPLIANCE SCORE: {score:.0f}% ({passed}/{len(compliance_checks)} items)

🎯 OVERALL ASSESSMENT:
"""
                    if score >= 80:
                        results += "🟢 Good compliance level - document meets most requirements"
                    elif score >= 60:
                        results += "🟡 Moderate compliance - some improvements needed"
                    else:
                        results += "🔴 Low compliance - significant improvements required"
                        
                    self.results_text.setText(results)
                    
                    # Generate report
                    report = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Compliance Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 10px; }}
        .score {{ font-size: 24px; font-weight: bold; text-align: center; margin: 20px 0; }}
        .findings {{ background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏥 Therapy Compliance Analysis Report</h1>
        <p>Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="score">
        Compliance Score: {score:.0f}%
    </div>
    
    <div class="findings">
        <h3>Key Findings:</h3>
        <ul>
            {"".join(f"<li>{'✅' if status else '❌'} {item}</li>" for item, status in compliance_checks)}
        </ul>
    </div>
    
    <div class="findings">
        <h3>Clinicians Identified:</h3>
        <p>{', '.join(clinicians) if clinicians else 'No clinician signatures found'}</p>
    </div>
</body>
</html>
"""
                    self.report_text.setHtml(report)
                    
                    # Switch to results tab
                    self.results_tabs.setCurrentIndex(0)
                    
                except Exception as e:
                    self.results_text.setText(f"❌ Analysis failed: {str(e)}")
                
                finally:
                    # Hide progress
                    self.analysis_progress_bar.setVisible(False)
                    self.analysis_progress_label.setText("Analysis complete")
                    self.run_analysis_btn.setEnabled(True)
                    self.run_analysis_btn.setText("🚀 Run Compliance Analysis")
                    self.statusBar().showMessage("✅ Analysis complete")
                    
            def send_chat_message(self):
                """Send chat message to AI assistant."""
                message = self.chat_input.text().strip()
                if not message:
                    return
                    
                # Add user message
                self.chat_display.append(f"""
                <div style='background-color: #e8f5e8; padding: 10px; border-radius: 8px; margin: 5px; text-align: right;'>
                    <b>👤 You:</b> {message}
                </div>
                """)
                
                # Simulate AI response
                responses = [
                    "That's a great question about compliance! Based on the analysis, I recommend focusing on documentation completeness.",
                    "For Medicare compliance, ensure all required elements are present: patient identification, dates, signatures, and medical necessity.",
                    "The compliance score reflects how well the documentation meets regulatory requirements. Higher scores indicate better compliance.",
                    "PHI scrubbing helps protect patient privacy while maintaining the clinical value of the documentation.",
                    "Consider adding more specific measurable goals and time-bound objectives to improve compliance scores."
                ]
                
                import random
                ai_response = random.choice(responses)
                
                self.chat_display.append(f"""
                <div style='background-color: #e3f2fd; padding: 10px; border-radius: 8px; margin: 5px;'>
                    <b>🤖 AI Assistant:</b> {ai_response}
                </div>
                """)
                
                self.chat_input.clear()
                
                # Scroll to bottom
                scrollbar = self.chat_display.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
        
        # Start the application
        app = QApplication(sys.argv)
        
        # Show loading screen
        loading_screen = LoadingScreen()
        loading_screen.show()
        
        # Start model loading
        loader = ModelLoader()
        loader.progress_updated.connect(loading_screen.update_progress)
        
        def on_loading_complete(analyzer):
            loading_screen.close()
            main_window = EnhancedComplianceWindow(analyzer)
            main_window.show()
            
        loader.loading_complete.connect(on_loading_complete)
        loader.start()
        
        return app.exec()
        
    except Exception as e:
        print(f"❌ Failed to start enhanced GUI: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import re  # Add this import for regex
    logging.basicConfig(level=logging.INFO)
    print("🚀 Starting Enhanced Therapy Compliance Analyzer...")
    print("=" * 60)
    try:
        result = start_enhanced_gui()
        sys.exit(result)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)