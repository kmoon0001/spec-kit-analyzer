#!/usr/bin/env python3
"""
Professional GUI for Therapy Compliance Analyzer.
Modern, sleek design with premium medical application aesthetics.
"""

import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def start_professional_gui():
    """Start the professional GUI application."""
    logger = logging.getLogger(__name__)

    try:
        from PyQt6.QtWidgets import (
            QApplication,
            QMainWindow,
            QVBoxLayout,
            QHBoxLayout,
            QWidget,
            QTextEdit,
            QPushButton,
            QLabel,
            QFrame,
            QSplitter,
            QTabWidget,
            QProgressBar,
        )
        from PyQt6.QtCore import Qt, QThread, pyqtSignal

        class NERWorker(QThread):
            """Background worker for NER processing."""

            finished = pyqtSignal(dict)
            progress = pyqtSignal(str)

            def __init__(self, text, analyzer):
                super().__init__()
                self.text = text
                self.analyzer = analyzer

            def run(self):
                try:
                    self.progress.emit("Initializing analysis...")
                    lines = [
                        line.strip() for line in self.text.split("\n") if line.strip()
                    ]

                    results = {"lines": [], "total_clinicians": [], "summary": {}}

                    for i, line in enumerate(lines, 1):
                        self.progress.emit(f"Analyzing line {i} of {len(lines)}...")
                        clinicians = self.analyzer.extract_clinician_name(line)

                        results["lines"].append(
                            {"number": i, "text": line, "clinicians": clinicians}
                        )
                        results["total_clinicians"].extend(clinicians)

                    unique_clinicians = list(set(results["total_clinicians"]))
                    results["summary"] = {
                        "total_lines": len(lines),
                        "lines_with_clinicians": len(
                            [line for line in results["lines"] if line["clinicians"]]
                        ),
                        "unique_clinicians": unique_clinicians,
                        "total_clinicians": len(unique_clinicians),
                    }

                    self.progress.emit("Analysis complete!")
                    self.finished.emit(results)

                except Exception as e:
                    self.finished.emit({"error": str(e)})

        class ProfessionalNERWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setup_window()
                self.setup_ui()
                self.setup_styling()
                self.init_ner()

            def setup_window(self):
                """Configure main window properties."""
                self.setWindowTitle(
                    "Therapy Compliance Analyzer - Professional Edition"
                )
                self.setGeometry(100, 100, 1400, 900)
                self.setMinimumSize(1200, 800)

            def setup_styling(self):
                """Apply professional styling."""
                self.setStyleSheet("""
                    QMainWindow {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #f8f9fa, stop:1 #e9ecef);
                    }
                    
                    QFrame#headerFrame {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #2c3e50, stop:1 #34495e);
                        border: none;
                        border-radius: 0px;
                        min-height: 80px;
                        max-height: 80px;
                    }
                    
                    QLabel#titleLabel {
                        color: white;
                        font-size: 28px;
                        font-weight: bold;
                        font-family: 'Segoe UI', Arial, sans-serif;
                    }
                    
                    QLabel#subtitleLabel {
                        color: #bdc3c7;
                        font-size: 14px;
                        font-family: 'Segoe UI', Arial, sans-serif;
                    }
                    
                    QFrame#contentFrame {
                        background: white;
                        border: 1px solid #dee2e6;
                        border-radius: 12px;
                        margin: 10px;
                    }
                    
                    QLabel#sectionLabel {
                        color: #2c3e50;
                        font-size: 16px;
                        font-weight: bold;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        padding: 10px;
                        background: #f8f9fa;
                        border-radius: 6px;
                        border: 1px solid #e9ecef;
                    }
                    
                    QTextEdit {
                        border: 2px solid #e9ecef;
                        border-radius: 8px;
                        padding: 12px;
                        font-family: 'Consolas', 'Courier New', monospace;
                        font-size: 13px;
                        background: white;
                        selection-background-color: #3498db;
                    }
                    
                    QTextEdit:focus {
                        border: 2px solid #3498db;
                    }
                    
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #3498db, stop:1 #2980b9);
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 12px 24px;
                        font-size: 14px;
                        font-weight: bold;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        min-height: 20px;
                    }
                    
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #5dade2, stop:1 #3498db);
                    }
                    
                    QPushButton:pressed {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #2980b9, stop:1 #1f618d);
                    }
                    
                    QPushButton#secondaryButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #95a5a6, stop:1 #7f8c8d);
                    }
                    
                    QPushButton#secondaryButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #bdc3c7, stop:1 #95a5a6);
                    }
                    
                    QPushButton#successButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #27ae60, stop:1 #229954);
                    }
                    
                    QPushButton#successButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #58d68d, stop:1 #27ae60);
                    }
                    
                    QProgressBar {
                        border: 2px solid #bdc3c7;
                        border-radius: 8px;
                        text-align: center;
                        font-weight: bold;
                        background: #ecf0f1;
                    }
                    
                    QProgressBar::chunk {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #3498db, stop:1 #2980b9);
                        border-radius: 6px;
                    }
                    
                    QTabWidget::pane {
                        border: 1px solid #bdc3c7;
                        border-radius: 8px;
                        background: white;
                    }
                    
                    QTabBar::tab {
                        background: #ecf0f1;
                        border: 1px solid #bdc3c7;
                        padding: 8px 16px;
                        margin-right: 2px;
                        border-top-left-radius: 8px;
                        border-top-right-radius: 8px;
                    }
                    
                    QTabBar::tab:selected {
                        background: white;
                        border-bottom: 1px solid white;
                    }
                    
                    QTabBar::tab:hover {
                        background: #d5dbdb;
                    }
                    
                    QScrollArea {
                        border: none;
                        background: transparent;
                    }
                    
                    QStatusBar {
                        background: #34495e;
                        color: white;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        font-size: 12px;
                        border-top: 1px solid #2c3e50;
                    }
                """)

            def setup_ui(self):
                """Create the user interface."""
                central_widget = QWidget()
                self.setCentralWidget(central_widget)
                main_layout = QVBoxLayout(central_widget)
                main_layout.setContentsMargins(0, 0, 0, 0)
                main_layout.setSpacing(0)

                # Header
                header_frame = QFrame()
                header_frame.setObjectName("headerFrame")
                header_layout = QHBoxLayout(header_frame)
                header_layout.setContentsMargins(30, 20, 30, 20)

                # Title section
                title_section = QVBoxLayout()
                title_label = QLabel("🏥 Therapy Compliance Analyzer")
                title_label.setObjectName("titleLabel")
                subtitle_label = QLabel(
                    "Professional NER Analysis Suite - spaCy-Free Implementation"
                )
                subtitle_label.setObjectName("subtitleLabel")

                title_section.addWidget(title_label)
                title_section.addWidget(subtitle_label)
                title_section.addStretch()

                # Status section
                status_section = QVBoxLayout()
                status_section.addStretch()
                self.status_label = QLabel("🟢 System Ready")
                self.status_label.setStyleSheet(
                    "color: #2ecc71; font-size: 14px; font-weight: bold;"
                )
                status_section.addWidget(self.status_label)

                header_layout.addLayout(title_section)
                header_layout.addStretch()
                header_layout.addLayout(status_section)

                main_layout.addWidget(header_frame)

                # Content area
                content_frame = QFrame()
                content_frame.setObjectName("contentFrame")
                content_layout = QVBoxLayout(content_frame)
                content_layout.setContentsMargins(20, 20, 20, 20)
                content_layout.setSpacing(20)

                # Create splitter for input/output
                splitter = QSplitter(Qt.Orientation.Horizontal)

                # Left panel - Input
                left_panel = QWidget()
                left_layout = QVBoxLayout(left_panel)
                left_layout.setSpacing(15)

                input_label = QLabel("📝 Clinical Documentation Input")
                input_label.setObjectName("sectionLabel")
                left_layout.addWidget(input_label)

                self.input_text = QTextEdit()
                self.input_text.setPlaceholderText(
                    "Enter clinical documentation text here...\n\n"
                    "Examples:\n"
                    "• Signature: Dr. Jane Smith, PT\n"
                    "• Therapist: Michael Brown, COTA\n"
                    "• Co-signed by: Dr. Emily White, OTR\n"
                    "• Patient John Doe reported improvement\n\n"
                    "The system will automatically identify clinician names "
                    "while ignoring patient references."
                )
                self.input_text.setMinimumHeight(200)
                left_layout.addWidget(self.input_text)

                # Button panel
                button_layout = QHBoxLayout()

                self.analyze_button = QPushButton("🔍 Analyze Text")
                self.analyze_button.clicked.connect(self.start_analysis)

                self.clear_button = QPushButton("🗑️ Clear All")
                self.clear_button.setObjectName("secondaryButton")
                self.clear_button.clicked.connect(self.clear_all)

                self.example_button = QPushButton("📋 Load Example")
                self.example_button.setObjectName("successButton")
                self.example_button.clicked.connect(self.load_example)

                button_layout.addWidget(self.analyze_button)
                button_layout.addWidget(self.clear_button)
                button_layout.addWidget(self.example_button)

                left_layout.addLayout(button_layout)

                # Progress bar
                self.progress_bar = QProgressBar()
                self.progress_bar.setVisible(False)
                left_layout.addWidget(self.progress_bar)

                # Right panel - Results
                right_panel = QWidget()
                right_layout = QVBoxLayout(right_panel)
                right_layout.setSpacing(15)

                results_label = QLabel("📊 Analysis Results")
                results_label.setObjectName("sectionLabel")
                right_layout.addWidget(results_label)

                # Tabbed results
                self.results_tabs = QTabWidget()

                # Summary tab
                self.summary_text = QTextEdit()
                self.summary_text.setReadOnly(True)
                self.results_tabs.addTab(self.summary_text, "📈 Summary")

                # Detailed tab
                self.detailed_text = QTextEdit()
                self.detailed_text.setReadOnly(True)
                self.results_tabs.addTab(self.detailed_text, "🔍 Detailed Analysis")

                # System tab
                self.system_text = QTextEdit()
                self.system_text.setReadOnly(True)
                self.results_tabs.addTab(self.system_text, "⚙️ System Info")

                right_layout.addWidget(self.results_tabs)

                # Add panels to splitter
                splitter.addWidget(left_panel)
                splitter.addWidget(right_panel)
                splitter.setSizes([600, 800])  # Give more space to results

                content_layout.addWidget(splitter)
                main_layout.addWidget(content_frame)

                # Status bar
                self.statusBar().showMessage(
                    "Ready - Professional NER system initialized"
                )

            def init_ner(self):
                """Initialize NER analyzer."""
                try:
                    from src.core.ner import NERAnalyzer

                    self.ner_analyzer = NERAnalyzer(model_names=[])

                    # Update system info
                    system_info = """🚀 NER System Initialization Complete
═══════════════════════════════════════════

✅ Core Components Loaded:
   • Regex-based clinician name extraction
   • Presidio PHI detection and anonymization
   • Medical entity categorization
   • Context-aware pattern matching

✅ Key Improvements:
   • spaCy dependency removed (no version conflicts)
   • Faster startup and processing
   • Reduced memory footprint
   • Enhanced reliability

✅ Supported Analysis Types:
   • Clinical signature detection
   • Therapist identification
   • Co-signer recognition
   • Patient name filtering

✅ Privacy Features:
   • Local processing only
   • PHI detection and scrubbing
   • No external API calls
   • HIPAA-compliant design

System Status: READY FOR ANALYSIS"""

                    self.system_text.setText(system_info)
                    self.status_label.setText("🟢 NER System Ready")
                    self.statusBar().showMessage("Ready - All systems operational")

                except Exception as e:
                    error_msg = f"❌ System initialization failed: {e}"
                    self.system_text.setText(error_msg)
                    self.status_label.setText("🔴 System Error")
                    self.statusBar().showMessage("Error - System initialization failed")

            def load_example(self):
                """Load example clinical text."""
                example_text = """Progress Note - Physical Therapy

Date: [REDACTED]
Patient: [REDACTED] 

ASSESSMENT:
Patient demonstrates improved mobility and strength following 
therapeutic interventions. Range of motion has increased by 15 degrees 
in affected joint. Patient reports decreased pain levels.

TREATMENT PROVIDED:
- Therapeutic exercises
- Manual therapy techniques  
- Gait training with assistive device
- Patient education on home exercise program

PLAN:
Continue current treatment plan. Patient to be seen 3x per week.
Goals remain appropriate and achievable.

SIGNATURES:
Primary Therapist: Dr. Sarah Johnson, PT
Co-treating: Michael Chen, PTA
Supervising: Dr. Emily Rodriguez, DPT

Quality Review: Dr. James Wilson, PT
Department Head: Lisa Thompson, OTR"""

                self.input_text.setText(example_text)
                self.statusBar().showMessage("Example loaded - Ready for analysis")

            def clear_all(self):
                """Clear all content."""
                self.input_text.clear()
                self.summary_text.clear()
                self.detailed_text.clear()
                self.statusBar().showMessage("Content cleared - Ready for new input")

            def start_analysis(self):
                """Start NER analysis."""
                text = self.input_text.toPlainText()
                if not text.strip():
                    self.statusBar().showMessage("Error - Please enter text to analyze")
                    return

                if not hasattr(self, "ner_analyzer") or not self.ner_analyzer:
                    self.statusBar().showMessage("Error - NER system not available")
                    return

                # Show progress
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)  # Indeterminate
                self.analyze_button.setEnabled(False)
                self.status_label.setText("🟡 Analyzing...")

                # Start worker thread
                self.worker = NERWorker(text, self.ner_analyzer)
                self.worker.progress.connect(self.update_progress)
                self.worker.finished.connect(self.analysis_complete)
                self.worker.start()

            def update_progress(self, message):
                """Update progress message."""
                self.statusBar().showMessage(message)

            def analysis_complete(self, results):
                """Handle analysis completion."""
                self.progress_bar.setVisible(False)
                self.analyze_button.setEnabled(True)
                self.status_label.setText("🟢 Analysis Complete")

                if "error" in results:
                    self.summary_text.setText(f"❌ Analysis failed: {results['error']}")
                    self.statusBar().showMessage("Error - Analysis failed")
                    return

                # Generate summary
                summary = results["summary"]
                summary_text = f"""📊 ANALYSIS SUMMARY
═══════════════════════════════════════════

📄 Document Statistics:
   • Total lines analyzed: {summary["total_lines"]}
   • Lines with clinicians: {summary["lines_with_clinicians"]}
   • Success rate: {(summary["lines_with_clinicians"] / summary["total_lines"] * 100):.1f}%

👨‍⚕️ Clinician Detection Results:
   • Unique clinicians found: {summary["total_clinicians"]}
   • Names identified: {", ".join(summary["unique_clinicians"]) if summary["unique_clinicians"] else "None"}

✅ Analysis Status: COMPLETE
🔒 Privacy: All processing performed locally
⚡ Performance: spaCy-free implementation"""

                self.summary_text.setText(summary_text)

                # Generate detailed results
                detailed_text = "🔍 DETAILED LINE-BY-LINE ANALYSIS\n"
                detailed_text += "═" * 50 + "\n\n"

                for line_result in results["lines"]:
                    detailed_text += (
                        f"Line {line_result['number']}: {line_result['text']}\n"
                    )
                    if line_result["clinicians"]:
                        detailed_text += f"   👨‍⚕️ Clinicians: {', '.join(line_result['clinicians'])}\n"
                    else:
                        detailed_text += "   ℹ️ No clinicians detected\n"
                    detailed_text += "\n"

                detailed_text += "\n" + "═" * 50 + "\n"
                detailed_text += (
                    "✅ Analysis completed successfully using regex-based extraction\n"
                )
                detailed_text += "🔒 No PHI was transmitted - all processing local\n"

                self.detailed_text.setText(detailed_text)

                # Update status
                self.statusBar().showMessage(
                    f"Complete - Found {summary['total_clinicians']} clinician(s)"
                )

        app = QApplication(sys.argv)

        # Set application properties
        app.setApplicationName("Therapy Compliance Analyzer")
        app.setApplicationVersion("2.0 Professional")
        app.setOrganizationName("Healthcare Analytics")

        window = ProfessionalNERWindow()
        window.show()

        logger.info("✅ Professional GUI started successfully")
        return app.exec()

    except Exception as e:
        logger.error(f"❌ Professional GUI failed to start: {e}")
        import traceback

        traceback.print_exc()
        return 1


def main():
    """Main function."""
    logging.basicConfig(level=logging.INFO)

    print("🚀 Therapy Compliance Analyzer - Professional Edition")
    print("=" * 60)
    print("Premium medical application with advanced NER capabilities")
    print()

    return start_professional_gui()


if __name__ == "__main__":
    sys.exit(main())
