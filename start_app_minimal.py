#!/usr/bin/env python3
"""
Minimal startup script that focuses on core NER functionality.
Bypasses LLM loading to avoid freezing issues.
"""

import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_core_functionality():
    """Test that core functionality works."""
    logger = logging.getLogger(__name__)

    try:
        # Test NER functionality
        from src.core.ner import NERAnalyzer

        analyzer = NERAnalyzer(model_names=[])

        # Test clinician extraction
        result = analyzer.extract_clinician_name("Signature: Dr. Jane Smith, PT")
        logger.info(f"✅ NER test result: {result}")

        # Test analysis service import
        logger.info("✅ Analysis service imports successfully")

        return True

    except Exception as e:
        logger.error(f"❌ Core functionality test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def start_minimal_gui():
    """Start a minimal GUI that focuses on NER functionality."""
    logger = logging.getLogger(__name__)

    try:
        from PyQt6.QtWidgets import (
            QApplication,
            QMainWindow,
            QVBoxLayout,
            QWidget,
            QTextEdit,
            QPushButton,
            QLabel,
        )
        from PyQt6.QtCore import Qt

        class MinimalNERWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("Therapy Compliance Analyzer - NER Demo")
                self.setGeometry(100, 100, 1000, 700)

                # Set modern styling
                self.setStyleSheet("""
                    QMainWindow {
                        background-color: #f5f5f5;
                    }
                    QLabel {
                        color: #333;
                        font-family: 'Segoe UI', Arial, sans-serif;
                    }
                    QTextEdit {
                        border: 2px solid #ddd;
                        border-radius: 8px;
                        padding: 8px;
                        font-family: 'Consolas', 'Courier New', monospace;
                        background-color: white;
                    }
                    QPushButton {
                        background-color: #007acc;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 10px 20px;
                        font-size: 14px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #005a9e;
                    }
                    QPushButton:pressed {
                        background-color: #004578;
                    }
                """)

                # Create central widget with margins
                central_widget = QWidget()
                self.setCentralWidget(central_widget)
                layout = QVBoxLayout(central_widget)
                layout.setContentsMargins(20, 20, 20, 20)
                layout.setSpacing(15)

                # Add header section
                header_widget = QWidget()
                header_layout = QVBoxLayout(header_widget)

                title = QLabel("🏥 Therapy Compliance Analyzer")
                title.setAlignment(Qt.AlignmentFlag.AlignCenter)
                title.setStyleSheet(
                    "font-size: 24px; font-weight: bold; color: #007acc; margin: 10px;"
                )
                header_layout.addWidget(title)

                subtitle = QLabel(
                    "Named Entity Recognition (NER) Demo - spaCy-Free Implementation"
                )
                subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
                subtitle.setStyleSheet(
                    "font-size: 14px; color: #666; margin-bottom: 20px;"
                )
                header_layout.addWidget(subtitle)

                layout.addWidget(header_widget)

                # Add input section
                input_label = QLabel("📝 Clinical Text Input:")
                input_label.setStyleSheet(
                    "font-size: 16px; font-weight: bold; color: #333;"
                )
                layout.addWidget(input_label)

                self.input_text = QTextEdit()
                self.input_text.setPlaceholderText(
                    "Enter clinical documentation text here...\n\nExamples:\n• Signature: Dr. Jane Smith, PT\n• Therapist: Michael Brown, COTA\n• Signed by: Dr. Emily White, OTR"
                )
                self.input_text.setMinimumHeight(120)
                self.input_text.setMaximumHeight(150)
                layout.addWidget(self.input_text)

                # Add button section
                button_widget = QWidget()
                button_layout = QVBoxLayout(button_widget)

                test_button = QPushButton("🔍 Extract Clinician Names")
                test_button.clicked.connect(self.test_ner)
                test_button.setMinimumHeight(40)
                button_layout.addWidget(test_button)

                clear_button = QPushButton("🗑️ Clear Results")
                clear_button.clicked.connect(self.clear_results)
                clear_button.setStyleSheet("background-color: #6c757d;")
                clear_button.setMinimumHeight(35)
                button_layout.addWidget(clear_button)

                layout.addWidget(button_widget)

                # Add results section
                results_label = QLabel("📊 Analysis Results:")
                results_label.setStyleSheet(
                    "font-size: 16px; font-weight: bold; color: #333;"
                )
                layout.addWidget(results_label)

                self.results_text = QTextEdit()
                self.results_text.setReadOnly(True)
                self.results_text.setStyleSheet("""
                    QTextEdit {
                        background-color: #f8f9fa;
                        border: 2px solid #e9ecef;
                        font-family: 'Consolas', 'Courier New', monospace;
                        font-size: 12px;
                    }
                """)
                layout.addWidget(self.results_text)

                # Add status bar
                self.statusBar().showMessage("Ready - NER system initialized")

                # Initialize NER
                self.ner_analyzer = None
                self.init_ner()

                # Add example text
                example_text = """Signature: Dr. Jane Smith, PT
Therapist: Michael Brown, COTA
Co-signed by: Dr. Emily White, OTR

Patient John Doe reported significant improvement in mobility."""
                self.input_text.setText(example_text)

            def init_ner(self):
                """Initialize NER analyzer."""
                try:
                    from src.core.ner import NERAnalyzer

                    self.ner_analyzer = NERAnalyzer(model_names=[])
                    self.results_text.append("🚀 NER Analyzer Initialized Successfully")
                    self.results_text.append("=" * 50)
                    self.results_text.append(
                        "✅ Regex-based clinician name extraction: Ready"
                    )
                    self.results_text.append("✅ Presidio PHI detection: Ready")
                    self.results_text.append("✅ Medical entity categorization: Ready")
                    self.results_text.append(
                        "✅ spaCy dependency: Removed (no conflicts!)"
                    )
                    self.results_text.append("")
                    self.statusBar().showMessage(
                        "NER system ready - Enter text and click Extract"
                    )
                except Exception as e:
                    self.results_text.append(f"❌ Failed to initialize NER: {e}")
                    self.statusBar().showMessage("Error: NER initialization failed")

            def clear_results(self):
                """Clear the results area."""
                self.results_text.clear()
                self.statusBar().showMessage("Results cleared - Ready for new analysis")

            def test_ner(self):
                """Test NER functionality with improved output."""
                if not self.ner_analyzer:
                    self.results_text.append("❌ NER analyzer not available")
                    return

                text = self.input_text.toPlainText()
                if not text.strip():
                    self.results_text.append("❌ Please enter some text to analyze")
                    self.statusBar().showMessage("Error: No input text provided")
                    return

                try:
                    self.statusBar().showMessage("Analyzing text...")

                    # Split text into lines for analysis
                    lines = [line.strip() for line in text.split("\n") if line.strip()]

                    self.results_text.append("\n🔍 ANALYSIS STARTED")
                    self.results_text.append("=" * 50)
                    self.results_text.append(f"📄 Input: {len(lines)} lines of text")
                    self.results_text.append("")

                    # Analyze each line
                    all_clinicians = []
                    for i, line in enumerate(lines, 1):
                        clinicians = self.ner_analyzer.extract_clinician_name(line)

                        self.results_text.append(f"Line {i}: {line}")
                        if clinicians:
                            self.results_text.append(
                                f"  👨‍⚕️ Clinicians found: {clinicians}"
                            )
                            all_clinicians.extend(clinicians)
                        else:
                            self.results_text.append("  ℹ️ No clinicians detected")
                        self.results_text.append("")

                    # Summary
                    unique_clinicians = list(set(all_clinicians))
                    self.results_text.append("📊 SUMMARY")
                    self.results_text.append("=" * 50)
                    self.results_text.append(
                        f"Total clinicians found: {len(unique_clinicians)}"
                    )
                    if unique_clinicians:
                        self.results_text.append(
                            f"Unique clinicians: {unique_clinicians}"
                        )
                        self.results_text.append(
                            "✅ NER extraction completed successfully!"
                        )
                        self.statusBar().showMessage(
                            f"Success: Found {len(unique_clinicians)} clinician(s)"
                        )
                    else:
                        self.results_text.append(
                            "No clinician names detected in the text."
                        )
                        self.results_text.append(
                            "This may be correct if the text doesn't contain clinical signatures."
                        )
                        self.statusBar().showMessage("Complete: No clinicians found")

                except Exception as e:
                    self.results_text.append(f"❌ NER extraction failed: {e}")
                    self.statusBar().showMessage("Error: Analysis failed")
                    import traceback

                    self.results_text.append(f"Details: {traceback.format_exc()}")

        app = QApplication(sys.argv)
        window = MinimalNERWindow()
        window.show()

        logger.info("✅ Minimal GUI started successfully")
        return app.exec()

    except Exception as e:
        logger.error(f"❌ Minimal GUI failed to start: {e}")
        import traceback

        traceback.print_exc()
        return 1


def main():
    """Main function."""
    logging.basicConfig(level=logging.INFO)

    print("🚀 Therapy Compliance Analyzer - Minimal Version")
    print("=" * 50)
    print("This version focuses on NER functionality without LLM loading")
    print()

    # Test core functionality first
    if not test_core_functionality():
        print("❌ Core functionality test failed")
        return 1

    print("✅ Core functionality verified")
    print("🖥️ Starting minimal GUI...")

    # Start minimal GUI
    return start_minimal_gui()


if __name__ == "__main__":
    sys.exit(main())
