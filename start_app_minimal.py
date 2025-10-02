#!/usr/bin/env python3
"""
Minimal startup script that focuses on core NER functionality.
Bypasses LLM loading to avoid freezing issues.
"""

import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

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
        from src.core.analysis_service import AnalysisService
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
        from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QLabel
        from PyQt6.QtCore import Qt
        
        class MinimalNERWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("Therapy Compliance Analyzer - NER Test")
                self.setGeometry(100, 100, 800, 600)
                
                # Create central widget
                central_widget = QWidget()
                self.setCentralWidget(central_widget)
                layout = QVBoxLayout(central_widget)
                
                # Add title
                title = QLabel("🧪 NER Functionality Test")
                title.setAlignment(Qt.AlignmentFlag.AlignCenter)
                title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
                layout.addWidget(title)
                
                # Add input area
                self.input_text = QTextEdit()
                self.input_text.setPlaceholderText("Enter clinical text here (e.g., 'Signature: Dr. Jane Smith, PT')")
                self.input_text.setMaximumHeight(100)
                layout.addWidget(QLabel("Input Text:"))
                layout.addWidget(self.input_text)
                
                # Add test button
                test_button = QPushButton("🔍 Extract Clinician Names")
                test_button.clicked.connect(self.test_ner)
                layout.addWidget(test_button)
                
                # Add results area
                layout.addWidget(QLabel("Results:"))
                self.results_text = QTextEdit()
                self.results_text.setReadOnly(True)
                layout.addWidget(self.results_text)
                
                # Initialize NER
                self.ner_analyzer = None
                self.init_ner()
                
                # Add some example text
                self.input_text.setText("Signature: Dr. Jane Smith, PT\nTherapist: Michael Brown, COTA")
            
            def init_ner(self):
                """Initialize NER analyzer."""
                try:
                    from src.core.ner import NERAnalyzer
                    self.ner_analyzer = NERAnalyzer(model_names=[])
                    self.results_text.append("✅ NER analyzer initialized successfully")
                except Exception as e:
                    self.results_text.append(f"❌ Failed to initialize NER: {e}")
            
            def test_ner(self):
                """Test NER functionality."""
                if not self.ner_analyzer:
                    self.results_text.append("❌ NER analyzer not available")
                    return
                
                text = self.input_text.toPlainText()
                if not text.strip():
                    self.results_text.append("❌ Please enter some text")
                    return
                
                try:
                    # Extract clinician names
                    clinicians = self.ner_analyzer.extract_clinician_name(text)
                    
                    self.results_text.append(f"\n🔍 Analyzing: {text[:100]}...")
                    self.results_text.append(f"👨‍⚕️ Clinicians found: {clinicians}")
                    
                    if clinicians:
                        self.results_text.append("✅ NER extraction successful!")
                    else:
                        self.results_text.append("ℹ️ No clinician names found (this may be correct)")
                        
                except Exception as e:
                    self.results_text.append(f"❌ NER extraction failed: {e}")
        
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
    logger = logging.getLogger(__name__)
    
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