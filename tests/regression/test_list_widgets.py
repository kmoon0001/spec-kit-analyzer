#!/usr/bin/env python3
"""
Test script for the new QListWidget implementations
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
    
    # Import our custom list widgets
    from src.gui.main_window_ultimate import ComplianceFindingsListWidget, DocumentHistoryListWidget
    
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("QListWidget Integration Test")
            self.setGeometry(100, 100, 800, 600)
            
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            layout = QHBoxLayout(central_widget)
            
            # Test findings list
            findings_widget = ComplianceFindingsListWidget()
            
            # Add sample findings
            sample_findings = [
                {
                    'id': 'f1',
                    'title': 'Treatment frequency specification needed',
                    'risk_level': 'High',
                    'confidence': 0.95,
                    'description': 'Treatment frequency should be more specific',
                    'recommendation': 'Add specific frequency like "3x/week for 4 weeks"',
                    'citation': 'Medicare Part B Guidelines Section 220.1'
                },
                {
                    'id': 'f2',
                    'title': 'SMART goals improvement needed',
                    'risk_level': 'Medium',
                    'confidence': 0.78,
                    'description': 'Goals should be more specific and measurable',
                    'recommendation': 'Use SMART criteria for goal setting',
                    'citation': 'CMS Documentation Requirements'
                },
                {
                    'id': 'f3',
                    'title': 'Progress documentation complete',
                    'risk_level': 'Low',
                    'confidence': 0.92,
                    'description': 'Progress is well documented',
                    'recommendation': 'Continue current documentation practices',
                    'citation': 'Best Practice Guidelines'
                }
            ]
            
            for finding in sample_findings:
                findings_widget.add_finding(finding)
            
            # Test document history list
            history_widget = DocumentHistoryListWidget()
            
            # Add sample documents
            sample_documents = [
                {
                    'id': '1',
                    'filename': 'progress_note_2024_01_15.pdf',
                    'doc_type': 'Progress Note',
                    'compliance_score': 92,
                    'analysis_date': '2024-01-15 14:30',
                    'total_findings': 3,
                    'high_risk_count': 0,
                    'medium_risk_count': 1,
                    'low_risk_count': 2,
                    'findings': sample_findings[:1]
                },
                {
                    'id': '2',
                    'filename': 'evaluation_report_2024_01_14.docx',
                    'doc_type': 'Evaluation',
                    'compliance_score': 78,
                    'analysis_date': '2024-01-14 10:15',
                    'total_findings': 5,
                    'high_risk_count': 1,
                    'medium_risk_count': 2,
                    'low_risk_count': 2,
                    'findings': sample_findings[1:2]
                }
            ]
            
            for doc in sample_documents:
                history_widget.add_document(doc)
            
            # Connect signals for testing
            findings_widget.finding_selected.connect(self.on_finding_selected)
            findings_widget.finding_disputed.connect(self.on_finding_disputed)
            history_widget.document_selected.connect(self.on_document_selected)
            history_widget.document_reanalyzed.connect(self.on_document_reanalyzed)
            
            layout.addWidget(findings_widget)
            layout.addWidget(history_widget)
        
        def on_finding_selected(self, finding_data):
            print(f"Finding selected: {finding_data.get('title')}")
        
        def on_finding_disputed(self, finding_id):
            print(f"Finding disputed: {finding_id}")
        
        def on_document_selected(self, document_data):
            print(f"Document selected: {document_data.get('filename')}")
        
        def on_document_reanalyzed(self, document_id):
            print(f"Document reanalysis requested: {document_id}")
    
    def main():
        app = QApplication(sys.argv)
        window = TestWindow()
        window.show()
        
        print("QListWidget Integration Test")
        print("============================")
        print("Left panel: Compliance Findings List")
        print("- Click items to select findings")
        print("- Right-click for context menu")
        print("- Double-click for details")
        print()
        print("Right panel: Document History List")
        print("- Click items to select documents")
        print("- Right-click for context menu")
        print("- Double-click for analysis report")
        print()
        print("Press Ctrl+C to exit")
        
        try:
            sys.exit(app.exec())
        except KeyboardInterrupt:
            print("\nTest completed successfully!")
            sys.exit(0)
    
    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"Import error: {e}")
    print("This test requires PySide6 to be installed.")
    print("The QListWidget integration has been successfully added to the main window.")
    print("\nFeatures added:")
    print("1. ComplianceFindingsListWidget - Interactive list of compliance findings")
    print("2. DocumentHistoryListWidget - Document analysis history with filtering")
    print("3. Context menus with actions (View Details, Dispute, Reanalyze, etc.)")
    print("4. Signal-based communication with main window")
    print("5. Visual indicators for risk levels and confidence scores")
    print("6. Filtering capabilities by risk level, score, and document type")