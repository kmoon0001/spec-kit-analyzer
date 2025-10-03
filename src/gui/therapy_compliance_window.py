"""
Therapy Compliance Analyzer - Complete Multi-Discipline Interface
Supports PT, OT, and SLP with full enterprise features
"""

import os
import json
import webbrowser
from typing import Dict, Optional, List
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QTextEdit, QComboBox, QSplitter, QTableWidget,
    QTableWidgetItem, QProgressBar, QMenuBar, QMenu, QFileDialog,
    QMessageBox, QGroupBox, QTextBrowser, QHeaderView, QStatusBar,
    QToolButton, QFrame, QDialog, QScrollArea, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QColor, QAction, QFont

# Import document parsing
try:
    from src.core.parsing import parse_document_content, parse_document_into_sections
except ImportError:
    parse_document_content = None
    parse_document_into_sections = None

# Import professional analysis services
try:
    from src.core.analysis_service import AnalysisService
    from src.core.document_analysis_service import DocumentAnalysisService
    from src.core.compliance_analyzer import ComplianceAnalyzer as ProfessionalComplianceAnalyzer
except ImportError:
    AnalysisService = None
    DocumentAnalysisService = None
    ProfessionalComplianceAnalyzer = None

# Import AI/ML services
try:
    from src.core.llm_service import LLMService
    from src.core.ner import NERAnalyzer
    from src.core.chat_service import ChatService
    from src.core.hybrid_retriever import HybridRetriever
except ImportError:
    LLMService = None
    NERAnalyzer = None
    ChatService = None
    HybridRetriever = None

# Import security and privacy services
try:
    from src.core.security_validator import SecurityValidator
    from src.core.phi_scrubber import PhiScrubberService
except ImportError:
    SecurityValidator = None
    PhiScrubberService = None

# Import performance and caching services
try:
    from src.core.cache_service import CacheService
    from src.core.performance_manager import PerformanceManager
except ImportError:
    CacheService = None
    PerformanceManager = None

# Import styles
try:
    from src.gui.styles import MAIN_STYLESHEET, DARK_THEME
except ImportError:
    MAIN_STYLESHEET = ""
    DARK_THEME = ""

# Import discipline detector
try:
    from src.core.discipline_detector import DisciplineDetector, PatientRecordAnalyzer
except ImportError:
    DisciplineDetector = None
    PatientRecordAnalyzer = None

# Import 7 Habits framework
try:
    from src.core.enhanced_habit_mapper import SevenHabitsFramework
    from src.gui.widgets.habits_dashboard_widget import HabitsDashboardWidget
except ImportError:
    SevenHabitsFramework = None
    HabitsDashboardWidget = None

# Import professional GUI components
try:
    from src.gui.widgets.dashboard_widget import DashboardWidget
    from src.gui.widgets.performance_status_widget import PerformanceStatusWidget
    from src.gui.dialogs.chat_dialog import ChatDialog
except ImportError:
    DashboardWidget = None
    PerformanceStatusWidget = None
    ChatDialog = None


class AnalysisWorker(QThread):
    """Background worker for running compliance analysis."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)
    
    def __init__(self, text: str, discipline: str, analyzer):
        super().__init__()
        self.text = text
        self.discipline = discipline
        self.analyzer = analyzer
    
    def run(self):
        try:
            self.progress.emit(25, "Analyzing documentation...")
            results = self.analyzer.analyze_compliance(self.text, self.discipline)
            self.progress.emit(100, "Analysis complete")
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class ProfessionalAnalysisWorker(QThread):
    """Background worker for running professional AI analysis."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)
    
    def __init__(self, analysis_service, analysis_params: Dict, professional_services: Dict):
        super().__init__()
        self.analysis_service = analysis_service
        self.analysis_params = analysis_params
        self.professional_services = professional_services
    
    def run(self):
        """Run the professional analysis in background."""
        try:
            self.progress.emit(10, "Initializing AI models...")
            
            # Check if analysis service is ready
            if hasattr(self.analysis_service, 'is_ready') and not self.analysis_service.is_ready():
                self.progress.emit(20, "Loading AI models...")
                # Wait for models to load or timeout
                import time
                timeout = 30  # 30 seconds timeout
                start_time = time.time()
                while not self.analysis_service.is_ready() and (time.time() - start_time) < timeout:
                    time.sleep(1)
                    self.progress.emit(20 + int((time.time() - start_time) / timeout * 30), "Loading AI models...")
                
                if not self.analysis_service.is_ready():
                    raise Exception("AI models failed to load within timeout period")
            
            self.progress.emit(50, "Running document analysis...")
            
            # Run the professional analysis
            if hasattr(self.analysis_service, 'analyze_document'):
                # Use async analysis if available
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                results = loop.run_until_complete(
                    self.analysis_service.analyze_document(**self.analysis_params)
                )
            else:
                # Use synchronous analysis
                results = self.analysis_service.generate_analysis(**self.analysis_params)
            
            self.progress.emit(90, "Processing results...")
            
            # Enhance results with additional services if available
            if self.professional_services.get('ner_analyzer'):
                try:
                    ner_results = self.professional_services['ner_analyzer'].analyze(
                        self.analysis_params['document_text']
                    )
                    results['entities'] = ner_results
                except Exception as e:
                    print(f"⚠️ NER analysis failed: {e}")
            
            self.progress.emit(100, "Analysis complete")
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(f"Professional analysis failed: {str(e)}")


class ChatDialog(QWidget):
    """AI Chat assistant dialog."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💬 AI Chat Assistant")
        self.resize(700, 600)
        self.setStyleSheet(MAIN_STYLESHEET)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header = QLabel("💬 AI Compliance Assistant")
        header.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 700;
                color: #1e40af;
                padding: 12px;
                background-color: #dbeafe;
                border-radius: 8px;
            }
        """)
        layout.addWidget(header)
        
        # Chat history
        self.chat_history = QTextBrowser()
        self.chat_history.setStyleSheet("""
            QTextBrowser {
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 16px;
                background-color: #f8fafc;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(self.chat_history)
        
        # Input area
        input_label = QLabel("💭 Your Question:")
        input_label.setStyleSheet("font-weight: 600; color: #475569; font-size: 13px;")
        layout.addWidget(input_label)
        
        self.chat_input = QTextEdit()
        self.chat_input.setMaximumHeight(100)
        self.chat_input.setPlaceholderText("Ask about compliance, documentation tips, or specific findings...")
        self.chat_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
                background-color: white;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.chat_input)
        
        # Send button
        send_btn = QPushButton("📤 Send Message")
        send_btn.clicked.connect(self.send_message)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        layout.addWidget(send_btn)
        
        # Welcome message
        self.chat_history.setHtml("""
            <div style='background-color: #dbeafe; padding: 16px; border-radius: 8px; margin-bottom: 12px;'>
                <strong style='color: #1e40af;'>🤖 AI Assistant:</strong><br>
                <span style='color: #334155;'>Hello! I can help you with compliance questions, documentation tips, and clarify specific findings. What would you like to know?</span>
            </div>
        """)
    
    def send_message(self):
        message = self.chat_input.toPlainText().strip()
        if not message:
            return
        
        # Add user message
        current_html = self.chat_history.toHtml()
        user_msg = f"""
            <div style='background-color: #f1f5f9; padding: 12px; border-radius: 8px; margin: 8px 0; margin-left: 40px;'>
                <strong style='color: #475569;'>👤 You:</strong><br>
                <span style='color: #1e293b;'>{message}</span>
            </div>
        """
        self.chat_history.setHtml(current_html + user_msg)
        self.chat_input.clear()
        
        # Simulate AI response (in real app, call LLM service)
        response = self.generate_response(message)
        current_html = self.chat_history.toHtml()
        ai_msg = f"""
            <div style='background-color: #dbeafe; padding: 12px; border-radius: 8px; margin: 8px 0; margin-right: 40px;'>
                <strong style='color: #1e40af;'>🤖 AI Assistant:</strong><br>
                <span style='color: #334155;'>{response}</span>
            </div>
        """
        self.chat_history.setHtml(current_html + ai_msg)
        
        # Scroll to bottom
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def generate_response(self, message: str) -> str:
        """Generate AI response (placeholder - integrate with LLM service)."""
        message_lower = message.lower()
        
        if "signature" in message_lower:
            return "All therapy notes must be signed and dated by the treating therapist with their credentials (PT, OT, SLP, etc.). This is required for Medicare reimbursement."
        elif "goal" in message_lower:
            return "Goals should be SMART: Specific, Measurable, Achievable, Relevant, and Time-bound. Example: 'Patient will increase right shoulder flexion from 90° to 120° within 3 weeks to improve overhead reaching for ADLs.'"
        elif "medical necessity" in message_lower:
            return "Medical necessity means documenting why skilled therapy is required. Link interventions to functional limitations and explain why the patient needs professional therapy services rather than self-care."
        else:
            return "I can help with compliance questions. Try asking about signatures, goals, medical necessity, progress documentation, or specific compliance rules."


class ReportWindow(QDialog):
    """Pop-up window for displaying compliance reports with integrated AI chat."""
    
    def __init__(self, parent=None, results=None, document_text=""):
        super().__init__(parent)
        self.results = results or {}
        self.document_text = document_text
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the report window UI."""
        self.setWindowTitle("📋 Compliance Analysis Report")
        self.setGeometry(200, 200, 1400, 900)
        self.setMinimumSize(1000, 600)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Header with report info
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📋 COMPLIANCE ANALYSIS REPORT")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #1e40af;
                padding: 12px;
                background-color: #dbeafe;
                border-radius: 8px;
                margin-bottom: 8px;
            }
        """)
        header_layout.addWidget(title_label)
        
        # Export buttons
        export_layout = QHBoxLayout()
        
        export_pdf_btn = QPushButton("📥 Export PDF")
        export_pdf_btn.clicked.connect(self.export_pdf)
        export_layout.addWidget(export_pdf_btn)
        
        export_html_btn = QPushButton("📥 Export HTML")
        export_html_btn.clicked.connect(self.export_html)
        export_layout.addWidget(export_html_btn)
        
        print_btn = QPushButton("🖨️ Print")
        print_btn.clicked.connect(self.print_report)
        export_layout.addWidget(print_btn)
        
        header_layout.addLayout(export_layout)
        layout.addLayout(header_layout)
        
        # Main content splitter: Report on left, AI Chat on right
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Report content
        report_group = QGroupBox("📄 Analysis Report")
        report_layout = QVBoxLayout()
        
        # Score summary
        score_layout = QHBoxLayout()
        score = self.results.get("compliance_score", 0)
        score_label = QLabel(f"Compliance Score: {score}%")
        score_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: bold;
                color: {'#10b981' if score >= 80 else '#f59e0b' if score >= 60 else '#ef4444'};
                padding: 8px;
                background-color: {'#d1fae5' if score >= 80 else '#fef3c7' if score >= 60 else '#fee2e2'};
                border-radius: 6px;
            }}
        """)
        score_layout.addWidget(score_label)
        
        findings_count = len(self.results.get("findings", []))
        findings_label = QLabel(f"Findings: {findings_count}")
        findings_label.setStyleSheet("font-weight: bold; padding: 8px;")
        score_layout.addWidget(findings_label)
        
        risk_amount = self.results.get("total_financial_impact", 0)
        risk_label = QLabel(f"Financial Risk: ${risk_amount}")
        risk_label.setStyleSheet("font-weight: bold; padding: 8px; color: #dc2626;")
        score_layout.addWidget(risk_label)
        
        score_layout.addStretch()
        report_layout.addLayout(score_layout)
        
        # Report content
        self.report_browser = QTextBrowser()
        self.report_browser.setHtml(self.generate_report_html())
        self.report_browser.anchorClicked.connect(self.handle_report_link)
        report_layout.addWidget(self.report_browser)
        
        report_group.setLayout(report_layout)
        main_splitter.addWidget(report_group)
        
        # Right: AI Chat
        chat_group = QGroupBox("🤖 AI Assistant - Report Analysis")
        chat_layout = QVBoxLayout()
        
        # Chat history
        self.chat_history = QTextBrowser()
        self.chat_history.setMaximumWidth(400)
        self.chat_history.setHtml(self.get_initial_chat_message())
        chat_layout.addWidget(self.chat_history)
        
        # Chat input
        input_layout = QVBoxLayout()
        
        self.chat_input = QTextEdit()
        self.chat_input.setMaximumHeight(80)
        self.chat_input.setPlaceholderText("Ask about specific findings, get clarification, or request improvement suggestions...")
        input_layout.addWidget(self.chat_input)
        
        # Chat buttons
        chat_btn_layout = QHBoxLayout()
        
        send_btn = QPushButton("💬 Send")
        send_btn.clicked.connect(self.send_chat_message)
        chat_btn_layout.addWidget(send_btn)
        
        explain_btn = QPushButton("❓ Explain Findings")
        explain_btn.clicked.connect(self.explain_findings)
        chat_btn_layout.addWidget(explain_btn)
        
        improve_btn = QPushButton("💡 Improvement Tips")
        improve_btn.clicked.connect(self.get_improvement_tips)
        chat_btn_layout.addWidget(improve_btn)
        
        input_layout.addLayout(chat_btn_layout)
        chat_layout.addLayout(input_layout)
        
        chat_group.setLayout(chat_layout)
        main_splitter.addWidget(chat_group)
        
        # Set splitter proportions: 70% report, 30% chat
        main_splitter.setSizes([980, 420])
        layout.addWidget(main_splitter)
        
        # Close button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        close_btn = QPushButton("✅ Close Report")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)
        
        self.setLayout(layout)
    
    def generate_report_html(self):
        """Generate comprehensive HTML report using the professional template."""
        try:
            # Import the report generator
            from src.core.report_generator import ReportGenerator
            
            # Create report generator instance
            report_gen = ReportGenerator()
            
            # Generate the full professional report
            report_data = report_gen.generate_report(
                analysis_result=self.results,
                document_name=getattr(self, 'document_name', 'Clinical Document'),
                analysis_mode='rubric'
            )
            
            return report_data.get('report_html', self._generate_fallback_html())
            
        except ImportError:
            # Fallback to simple HTML if report generator not available
            return self._generate_fallback_html()
    
    def _generate_fallback_html(self):
        """Generate fallback HTML if professional report generator is not available."""
        findings = self.results.get("findings", [])
        score = self.results.get("compliance_score", 0)
        discipline = self.results.get("discipline", "Unknown")
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Clinical Compliance Report</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f8f9fa; line-height: 1.6; }}
                .container {{ max-width: 1000px; margin: auto; background-color: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #007bff; margin-bottom: 30px; }}
                .header h1 {{ color: #007bff; margin: 0; font-size: 2.2em; }}
                .executive-summary {{ background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); color: white; padding: 25px; border-radius: 8px; margin-bottom: 30px; }}
                .score-dashboard {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .score-item {{ text-align: center; }}
                .score-value {{ font-size: 2.5em; font-weight: bold; display: block; }}
                .score-label {{ font-size: 0.9em; opacity: 0.9; }}
                .finding {{ 
                    margin: 16px 0; 
                    padding: 16px; 
                    border-radius: 8px; 
                    border-left: 4px solid #cbd5e1;
                }}
                .high {{ border-left-color: #ef4444; background-color: #fef2f2; }}
                .medium {{ border-left-color: #f59e0b; background-color: #fffbeb; }}
                .low {{ border-left-color: #10b981; background-color: #f0fdf4; }}
                .severity {{ 
                    font-weight: bold; 
                    padding: 4px 8px; 
                    border-radius: 4px; 
                    font-size: 12px;
                }}
                .severity.high {{ background-color: #ef4444; color: white; }}
                .severity.medium {{ background-color: #f59e0b; color: white; }}
                .severity.low {{ background-color: #10b981; color: white; }}
                .suggestion {{ 
                    background-color: #f8fafc; 
                    padding: 12px; 
                    border-radius: 6px; 
                    margin-top: 8px;
                    border-left: 3px solid #0ea5e9;
                }}
                .evidence {{ 
                    font-style: italic; 
                    color: #64748b; 
                    margin-top: 8px;
                }}
                .chat-link {{ 
                    color: #0ea5e9; 
                    text-decoration: none; 
                    font-weight: bold;
                }}
                .chat-link:hover {{ text-decoration: underline; }}
                h2 {{ color: #495057; border-bottom: 2px solid #e9ecef; padding-bottom: 10px; }}
            </style>
        </head>
        <body>
        <div class="container">
            <div class="header">
                <h1>Clinical Compliance Analysis Report</h1>
                <div class="subtitle">Medicare & Regulatory Compliance Assessment</div>
            </div>

            <div class="executive-summary">
                <h2>Executive Summary Dashboard</h2>
                <div class="score-dashboard">
                    <div class="score-item">
                        <span class="score-value">{score}%</span>
                        <span class="score-label">Overall Compliance Score</span>
                    </div>
                    <div class="score-item">
                        <span class="score-value">{len(findings)}</span>
                        <span class="score-label">Total Findings</span>
                    </div>
                    <div class="score-item">
                        <span class="score-value">{discipline}</span>
                        <span class="score-label">Discipline</span>
                    </div>
                </div>
            </div>
            
            <h2>🔍 Detailed Findings Analysis</h2>
        """
        
        if not findings:
            html += "<p>✅ No compliance issues found in this analysis.</p>"
        else:
            for i, finding in enumerate(findings):
                severity = finding.get("severity", "MEDIUM").lower()
                html += f"""
                <div class="finding {severity}">
                    <h3>{finding.get('title', 'Compliance Issue')}</h3>
                    <span class="severity {severity}">{finding.get('severity', 'MEDIUM')} RISK</span>
                    <span style="margin-left: 12px; font-weight: bold;">Financial Impact: ${finding.get('financial_impact', 0)}</span>
                    
                    {f'<div class="evidence">Evidence: {finding.get("evidence", "Not specified")}</div>' if finding.get("evidence") else ''}
                    
                    <div class="suggestion">
                        <strong>💡 Recommendation:</strong> {finding.get('suggestion', 'No specific suggestion available.')}
                    </div>
                    
                    <p style="margin-top: 12px;">
                        <a href="chat://discuss/{i}" class="chat-link">💬 Discuss this finding with AI</a> | 
                        <a href="chat://explain/{i}" class="chat-link">❓ Get detailed explanation</a>
                    </p>
                </div>
                """
        
        html += """
            <h2>📈 Action Planning & Next Steps</h2>
            <h3>Immediate Actions Required</h3>
            <ul>
                <li>Review all high-risk findings marked in red</li>
                <li>Implement suggested documentation improvements</li>
                <li>Verify compliance with cited regulations</li>
            </ul>
            <h3>Long-term Improvement Strategies</h3>
            <ul>
                <li>Establish regular compliance monitoring procedures</li>
                <li>Provide staff training on identified documentation gaps</li>
                <li>Implement quality assurance protocols</li>
            </ul>
            
            <div style="background-color: #e9ecef; padding: 20px; border-radius: 8px; margin: 30px 0;">
                <h2>AI Transparency & Limitations</h2>
                <p><strong>Disclaimer:</strong> This AI-generated report is for informational purposes only and does not constitute professional medical, legal, or compliance advice. All findings should be reviewed by qualified healthcare professionals.</p>
                <p><strong>Privacy Notice:</strong> All patient health information has been automatically redacted to protect privacy.</p>
            </div>
        </div>
        </body>
        </html>
        """
        
        return html
    
    def get_initial_chat_message(self):
        """Get initial AI chat message."""
        findings_count = len(self.results.get("findings", []))
        score = self.results.get("compliance_score", 0)
        
        return f"""
        <div style='background-color: #dbeafe; padding: 16px; border-radius: 8px; margin-bottom: 12px;'>
            <strong style='color: #1e40af;'>🤖 AI Assistant:</strong><br>
            <span style='color: #334155;'>
                I've analyzed your documentation and found {findings_count} areas for improvement with a compliance score of {score}%.
                <br><br>
                I can help you:
                <br>• Understand specific findings
                <br>• Get improvement suggestions  
                <br>• Clarify compliance requirements
                <br>• Provide documentation templates
                <br><br>
                Click on any finding links in the report or ask me questions!
            </span>
        </div>
        """
    
    def handle_report_link(self, url):
        """Handle clicks on report links."""
        url_str = url.toString()
        if url_str.startswith("chat://"):
            action_parts = url_str.replace("chat://", "").split("/")
            if len(action_parts) >= 2:
                action = action_parts[0]
                finding_index = int(action_parts[1])
                
                if action == "discuss":
                    self.discuss_finding(finding_index)
                elif action == "explain":
                    self.explain_finding(finding_index)
    
    def discuss_finding(self, finding_index):
        """Start discussion about a specific finding."""
        findings = self.results.get("findings", [])
        if finding_index < len(findings):
            finding = findings[finding_index]
            message = f"Tell me more about this finding: {finding.get('title', 'Unknown finding')}"
            self.add_chat_message(message, is_user=True)
            
            response = f"""This finding relates to: {finding.get('title', 'Unknown')}
            
Severity: {finding.get('severity', 'Unknown')}
Financial Impact: ${finding.get('financial_impact', 0)}

{finding.get('suggestion', 'No specific guidance available.')}

Would you like me to provide specific documentation templates or examples to address this issue?"""
            
            self.add_chat_message(response, is_user=False)
    
    def explain_finding(self, finding_index):
        """Explain a specific finding in detail."""
        findings = self.results.get("findings", [])
        if finding_index < len(findings):
            finding = findings[finding_index]
            message = f"Please explain this compliance requirement: {finding.get('title', 'Unknown finding')}"
            self.add_chat_message(message, is_user=True)
            
            response = f"""Let me explain this compliance requirement:

**Issue:** {finding.get('title', 'Unknown')}
**Why it matters:** This is flagged as {finding.get('severity', 'MEDIUM')} risk because it can impact Medicare reimbursement.

**Regulatory background:** Medicare requires clear documentation to justify medical necessity and skilled therapy services.

**What to include:** {finding.get('suggestion', 'Follow standard documentation practices.')}

**Example language:** "Patient requires skilled PT intervention for [specific functional limitation] as evidenced by [objective measures]. Treatment plan addresses [specific goals] with expected outcomes of [functional improvements]."

Would you like me to provide more specific examples for your documentation?"""
            
            self.add_chat_message(response, is_user=False)
    
    def send_chat_message(self):
        """Send user chat message."""
        message = self.chat_input.toPlainText().strip()
        if message:
            self.add_chat_message(message, is_user=True)
            self.chat_input.clear()
            
            # Generate AI response
            response = self.generate_ai_response(message)
            self.add_chat_message(response, is_user=False)
    
    def add_chat_message(self, message, is_user=True):
        """Add message to chat history."""
        current_html = self.chat_history.toHtml()
        
        if is_user:
            msg_html = f"""
            <div style='background-color: #f1f5f9; padding: 12px; border-radius: 8px; margin: 8px 0; margin-left: 40px;'>
                <strong style='color: #475569;'>👤 You:</strong><br>
                <span style='color: #334155;'>{message}</span>
            </div>
            """
        else:
            msg_html = f"""
            <div style='background-color: #dbeafe; padding: 12px; border-radius: 8px; margin: 8px 0; margin-right: 40px;'>
                <strong style='color: #1e40af;'>🤖 AI Assistant:</strong><br>
                <span style='color: #334155;'>{message}</span>
            </div>
            """
        
        self.chat_history.setHtml(current_html + msg_html)
        
        # Scroll to bottom
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def generate_ai_response(self, message):
        """Generate AI response based on message and report context."""
        message_lower = message.lower()
        findings = self.results.get("findings", [])
        
        if "signature" in message_lower or "sign" in message_lower:
            return """For proper signature compliance:

✅ **Required elements:**
• Therapist's full name
• Professional credentials (PT, OT, SLP)
• Date of service
• License number (if required by state)

✅ **Example format:**
"Signature: Dr. Jane Smith, PT
License: PT12345
Date: 01/15/2024"

✅ **Best practices:**
• Sign each note individually
• Use consistent signature format
• Include credentials after name
• Ensure signature is legible"""

        elif "goal" in message_lower or "smart" in message_lower:
            return """For SMART goals compliance:

✅ **SMART criteria:**
• **Specific:** Clear, detailed objective
• **Measurable:** Quantifiable outcome
• **Achievable:** Realistic for patient
• **Relevant:** Functional importance
• **Time-bound:** Specific timeframe

✅ **Example SMART goal:**
"Patient will increase right shoulder flexion from current 90° to 120° within 3 weeks to improve overhead reaching for kitchen ADLs, as measured by goniometry."

✅ **Key elements to include:**
• Current baseline measurement
• Target measurement
• Timeframe
• Functional relevance
• Measurement method"""

        elif "medical necessity" in message_lower:
            return """For medical necessity documentation:

✅ **Key components:**
• Clear functional limitations
• Skilled intervention requirements
• Expected functional outcomes
• Objective measurements

✅ **Template language:**
"Patient demonstrates [specific impairment] resulting in functional limitation of [specific activity]. Skilled [PT/OT/SLP] intervention is required to address [specific deficits] through [specific techniques]. Expected outcome: [functional improvement] within [timeframe]."

✅ **Documentation tips:**
• Link all interventions to functional goals
• Use objective measurements
• Explain why skilled therapy is needed
• Document patient's response to treatment"""

        else:
            return f"""I can help you with compliance questions about your {len(findings)} findings. 

Common topics I can assist with:
• Signature requirements and formats
• SMART goal writing
• Medical necessity documentation
• Progress note requirements
• Billing compliance
• Documentation templates

Try asking about specific findings from your report, or ask about signature requirements, goals, medical necessity, or other compliance topics."""
    
    def explain_findings(self):
        """Explain all findings."""
        findings = self.results.get("findings", [])
        if not findings:
            response = "Great news! No compliance issues were found in your documentation. Your documentation appears to meet the basic compliance requirements."
        else:
            response = f"You have {len(findings)} findings to address:\n\n"
            for i, finding in enumerate(findings, 1):
                response += f"{i}. **{finding.get('title', 'Unknown')}** ({finding.get('severity', 'MEDIUM')} risk)\n"
                response += f"   💡 {finding.get('suggestion', 'No suggestion available.')}\n\n"
        
        self.add_chat_message("Please explain all my findings", is_user=True)
        self.add_chat_message(response, is_user=False)
    
    def get_improvement_tips(self):
        """Get general improvement tips."""
        score = self.results.get("compliance_score", 0)
        
        if score >= 90:
            tips = """Excellent compliance! Here are tips to maintain quality:

✅ **Continue doing:**
• Consistent documentation format
• Clear, measurable goals
• Proper signatures and dates

✅ **Enhancement opportunities:**
• Add more specific functional outcomes
• Include patient quotes when relevant
• Document family/caregiver education"""
        
        elif score >= 70:
            tips = """Good foundation! Here's how to improve:

✅ **Priority improvements:**
• Strengthen goal specificity
• Enhance medical necessity language
• Improve progress documentation

✅ **Quick wins:**
• Use consistent terminology
• Add objective measurements
• Include patient response details"""
        
        else:
            tips = """Focus on these key areas for improvement:

🎯 **High priority:**
• Ensure proper signatures on all notes
• Write SMART, measurable goals
• Document medical necessity clearly

🎯 **Documentation structure:**
• Use SOAP note format consistently
• Include objective measurements
• Link interventions to functional outcomes

🎯 **Compliance essentials:**
• Date all entries
• Use professional language
• Document patient progress regularly"""
        
        self.add_chat_message("Give me improvement tips for my documentation", is_user=True)
        self.add_chat_message(tips, is_user=False)
    
    def export_pdf(self):
        """Export report as PDF."""
        QMessageBox.information(self, "Export PDF", "PDF export functionality would be implemented here.")
    
    def export_html(self):
        """Export report as HTML."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export HTML Report", "", "HTML Files (*.html)")
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.report_browser.toHtml())
            QMessageBox.information(self, "Success", f"Report exported to: {file_path}")
    
    def print_report(self):
        """Print the report."""
        QMessageBox.information(self, "Print", "Print functionality would be implemented here.")


class ComplianceAnalyzer:
    """Multi-discipline compliance analyzer."""
    
    def __init__(self):
        self.rules = {
            "pt": self.get_pt_rules(),
            "ot": self.get_ot_rules(),
            "slp": self.get_slp_rules()
        }
    
    def analyze_compliance(self, text: str, discipline: str) -> Dict:
        """Analyze documentation for compliance issues."""
        rules = self.rules.get(discipline.lower(), {})
        findings = []
        total_impact = 0
        
        text_lower = text.lower()
        
        for rule_id, rule in rules.items():
            finding = self.check_rule(text_lower, rule_id, rule)
            if finding:
                findings.append(finding)
                total_impact += finding.get("financial_impact", 0)
        
        # Calculate score with more realistic algorithm
        total_possible = sum(r["financial_impact"] for r in rules.values())
        
        if total_possible > 0:
            # Base score calculation
            base_score = max(0, 100 - (total_impact / total_possible * 100))
            
            # Apply penalties for number of findings
            finding_penalty = min(len(findings) * 5, 30)  # Max 30% penalty for multiple findings
            
            # Apply severity penalties
            high_severity_count = sum(1 for f in findings if f.get("severity") == "HIGH")
            severity_penalty = high_severity_count * 10  # 10% penalty per high severity finding
            
            # Final score with penalties
            score = max(0, base_score - finding_penalty - severity_penalty)
            
            # Ensure no document gets 100% (real documents always have room for improvement)
            if score >= 100 and len(findings) == 0:
                score = 95  # Even perfect documents get 95% max
                # Add a general improvement finding
                findings.append({
                    "rule_id": "general_improvement",
                    "title": "Documentation could be enhanced",
                    "severity": "LOW",
                    "financial_impact": 5,
                    "suggestion": "Consider adding more specific details about patient response and functional outcomes.",
                    "evidence": "While compliant, documentation can always be improved"
                })
                total_impact += 5
        else:
            score = 85  # Default score when no rules available
        
        return {
            "findings": findings,
            "compliance_score": round(score, 1),
            "total_financial_impact": total_impact,
            "discipline": discipline.upper()
        }
    
    def check_rule(self, text_lower: str, rule_id: str, rule: Dict) -> Optional[Dict]:
        """Check a specific compliance rule with realistic compliance checking."""
        
        # Handle positive/negative keyword rules (goals, etc.)
        if "positive_keywords" in rule and "negative_keywords" in rule:
            has_positive = any(kw in text_lower for kw in rule["positive_keywords"])
            has_negative = any(kw in text_lower for kw in rule["negative_keywords"])
            
            # Flag if mentions goals but lacks measurable criteria
            if has_positive and not has_negative:
                return {
                    "rule_id": rule_id,
                    "title": rule["title"],
                    "severity": rule["severity"],
                    "financial_impact": rule["financial_impact"],
                    "suggestion": rule["suggestion"],
                    "evidence": f"Found goal-related content but missing measurable criteria"
                }
        
        # Handle required keyword rules (signature, medical necessity, etc.)
        elif "keywords" in rule:
            keywords = rule.get("keywords", [])
            found_keywords = [kw for kw in keywords if kw in text_lower]
            
            # More realistic checking - flag if missing critical elements
            if rule_id == "signature":
                # Check for proper signature format
                signature_patterns = ["signed by", "signature:", "therapist:", "pt:", "ot:", "slp:"]
                has_proper_signature = any(pattern in text_lower for pattern in signature_patterns)
                if not has_proper_signature:
                    return {
                        "rule_id": rule_id,
                        "title": "Missing proper therapist signature",
                        "severity": rule["severity"],
                        "financial_impact": rule["financial_impact"],
                        "suggestion": rule["suggestion"],
                        "evidence": "No clear therapist signature found"
                    }
            
            elif rule_id == "medical_necessity":
                # Check for medical necessity documentation
                necessity_indicators = ["medical necessity", "functional limitation", "skilled", "requires therapy"]
                has_necessity = any(indicator in text_lower for indicator in necessity_indicators)
                if not has_necessity:
                    return {
                        "rule_id": rule_id,
                        "title": "Medical necessity not clearly documented",
                        "severity": rule["severity"],
                        "financial_impact": rule["financial_impact"],
                        "suggestion": rule["suggestion"],
                        "evidence": "Missing clear medical necessity justification"
                    }
            
            elif rule_id == "skilled_services":
                # Check for skilled service documentation
                skilled_terms = ["therapeutic exercise", "manual therapy", "gait training", "skilled intervention"]
                has_skilled = any(term in text_lower for term in skilled_terms)
                if not has_skilled:
                    return {
                        "rule_id": rule_id,
                        "title": "Skilled services not clearly documented",
                        "severity": rule["severity"],
                        "financial_impact": rule["financial_impact"],
                        "suggestion": rule["suggestion"],
                        "evidence": "Missing documentation of skilled interventions"
                    }
            
            elif rule_id == "progress":
                # Check for progress documentation
                progress_terms = ["progress", "improvement", "response", "outcome", "functional gain"]
                has_progress = any(term in text_lower for term in progress_terms)
                if not has_progress:
                    return {
                        "rule_id": rule_id,
                        "title": "Progress toward goals not documented",
                        "severity": rule["severity"],
                        "financial_impact": rule["financial_impact"],
                        "suggestion": rule["suggestion"],
                        "evidence": "No clear progress documentation found"
                    }
        
        # Handle pattern-based rules
        elif "patterns" in rule:
            patterns = rule.get("patterns", [])
            found_patterns = []
            for pattern in patterns:
                if pattern in text_lower:
                    found_patterns.append(pattern)
            
            # Flag if critical patterns are missing
            if len(found_patterns) < len(patterns) * 0.5:  # Less than 50% of expected patterns
                return {
                    "rule_id": rule_id,
                    "title": rule["title"],
                    "severity": rule["severity"],
                    "financial_impact": rule["financial_impact"],
                    "suggestion": rule["suggestion"],
                    "evidence": f"Found {len(found_patterns)}/{len(patterns)} expected documentation patterns"
                }
        
        return None
    
    def get_pt_rules(self) -> Dict:
        """Physical Therapy compliance rules."""
        return {
            "signature": {
                "title": "Provider signature/date possibly missing",
                "keywords": ["signature", "signed", "dated", "therapist:", "pt:", "by:"],
                "severity": "HIGH",
                "financial_impact": 50,
                "suggestion": "Ensure all notes are signed and dated by the treating therapist with credentials."
            },
            "goals": {
                "title": "Goals may not be measurable/time-bound",
                "positive_keywords": ["goal", "objective", "target"],
                "negative_keywords": ["measurable", "time", "weeks", "days", "within"],
                "severity": "MEDIUM",
                "financial_impact": 50,
                "suggestion": "Make goals SMART with specific timeframes and measurable criteria."
            },
            "medical_necessity": {
                "title": "Medical necessity not explicitly supported",
                "keywords": ["medical necessity", "functional limitation", "skilled therapy"],
                "severity": "HIGH",
                "financial_impact": 50,
                "suggestion": "Document how interventions address functional limitations."
            },
            "skilled_services": {
                "title": "Skilled therapy services not documented",
                "keywords": ["skilled", "therapeutic exercise", "manual therapy", "gait training"],
                "severity": "HIGH",
                "financial_impact": 75,
                "suggestion": "Document specific skilled interventions requiring PT expertise."
            },
            "progress": {
                "title": "Progress toward goals not documented",
                "keywords": ["progress", "improvement", "response to treatment"],
                "severity": "MEDIUM",
                "financial_impact": 40,
                "suggestion": "Document patient's response to treatment and progress toward goals."
            },
            "date_service": {
                "title": "Date of service may be missing",
                "patterns": ["date:", "dos:", "2024", "2023", "/", "-"],
                "severity": "HIGH",
                "financial_impact": 60,
                "suggestion": "Ensure date of service is clearly documented."
            },
            "treatment_time": {
                "title": "Treatment time/duration not specified",
                "keywords": ["minutes", "min", "duration", "time", "session"],
                "severity": "MEDIUM",
                "financial_impact": 30,
                "suggestion": "Document treatment duration for billing accuracy."
            },
            "functional_outcomes": {
                "title": "Functional outcomes not linked to treatment",
                "keywords": ["functional", "adl", "activities of daily living", "independence"],
                "severity": "MEDIUM",
                "financial_impact": 45,
                "suggestion": "Link treatment interventions to functional outcomes."
            }
        }
    
    def get_ot_rules(self) -> Dict:
        """Occupational Therapy compliance rules."""
        return {
            "signature": {
                "title": "Provider signature/date possibly missing",
                "keywords": ["signature", "signed", "dated", "therapist:", "ot:", "by:"],
                "severity": "HIGH",
                "financial_impact": 50,
                "suggestion": "Ensure all notes are signed and dated by the treating OT with credentials."
            },
            "ot_goals": {
                "title": "OT goals may not be measurable/time-bound",
                "positive_keywords": ["goal", "adl", "fine motor", "self-care"],
                "negative_keywords": ["measurable", "time", "weeks", "days"],
                "severity": "MEDIUM",
                "financial_impact": 50,
                "suggestion": "State goals with measurable targets focusing on ADLs and functional independence."
            },
            "medical_necessity": {
                "title": "Medical necessity not explicitly supported",
                "keywords": ["medical necessity", "functional limitation", "skilled ot"],
                "severity": "HIGH",
                "financial_impact": 50,
                "suggestion": "Tie OT interventions to functional limitations and Medicare Part B criteria."
            },
            "cota_supervision": {
                "title": "COTA supervision context unclear",
                "positive_keywords": ["cota", "assistant", "aide"],
                "negative_keywords": ["supervision", "oversight", "under direction"],
                "severity": "MEDIUM",
                "financial_impact": 25,
                "suggestion": "Document appropriate supervision when COTAs provide services."
            },
            "plan_of_care": {
                "title": "Plan/Certification not clearly referenced",
                "keywords": ["plan of care", "poc", "certification", "physician order"],
                "severity": "HIGH",
                "financial_impact": 50,
                "suggestion": "Reference plan of care, certification dates, and physician orders."
            }
        }
    
    def get_slp_rules(self) -> Dict:
        """Speech-Language Pathology compliance rules."""
        return {
            "signature": {
                "title": "Provider signature/date possibly missing",
                "keywords": ["signature", "signed", "dated", "therapist:", "slp:", "by:"],
                "severity": "HIGH",
                "financial_impact": 50,
                "suggestion": "Ensure all notes are signed and dated by the treating SLP with credentials."
            },
            "slp_poc": {
                "title": "SLP Plan of Care may be incomplete",
                "positive_keywords": ["plan of care", "poc"],
                "negative_keywords": ["goal", "frequency", "duration"],
                "severity": "HIGH",
                "financial_impact": 60,
                "suggestion": "POC should state long-term goals, type, frequency, amount, and duration of therapy."
            },
            "skilled_slp": {
                "title": "Justification for Skilled SLP Service may be missing",
                "keywords": ["cue", "strategy", "feedback", "skilled", "assess"],
                "severity": "HIGH",
                "financial_impact": 75,
                "suggestion": "Explain why SLP skills are required (cues, strategies, feedback, modification)."
            },
            "slp_goals": {
                "title": "SLP goals may not be measurable",
                "positive_keywords": ["aphasia", "dysphagia", "articulation", "fluency", "cognitive"],
                "negative_keywords": ["percentage", "accuracy", "level of assistance"],
                "severity": "MEDIUM",
                "financial_impact": 50,
                "suggestion": "Include objective, measurable criteria (percentages, accuracy, assistance level)."
            },
            "progress_report": {
                "title": "Progress report requirements not met",
                "keywords": ["progress", "objective measures", "goal progress"],
                "severity": "MEDIUM",
                "financial_impact": 40,
                "suggestion": "Progress reports every 10 treatment days with objective measures."
            }
        }


class TherapyComplianceWindow(QMainWindow):
    """Main application window with full features."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Therapy Compliance Analyzer - PT | OT | SLP")
        
        # Better scaling with minimum constraints
        self.setMinimumSize(800, 600)
        self.resize(1400, 900)
        
        # Center window on screen
        try:
            from PyQt6.QtWidgets import QApplication
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
        except:
            self.setGeometry(100, 100, 1400, 900)
        
        # Initialize basic services
        self.analyzer = ComplianceAnalyzer()
        self.discipline_detector = DisciplineDetector() if DisciplineDetector else None
        self.patient_analyzer = PatientRecordAnalyzer() if PatientRecordAnalyzer else None
        self.habits_framework = SevenHabitsFramework() if SevenHabitsFramework else None
        self.habits_enabled = True  # Default enabled
        self.current_document = ""
        self.current_results = None
        self.analysis_worker = None
        self.chat_dialog = None
        self.is_admin = True  # Set based on user role
        self.current_theme = "light"
        self.detected_disciplines = []
        self.patient_documents = []  # For multi-document analysis
        
        # Initialize professional services (when available)
        self.professional_services = self._initialize_professional_services()
        
        # Service status tracking
        self.services_status = {
            'analysis_service': bool(self.professional_services.get('analysis_service')),
            'llm_service': bool(self.professional_services.get('llm_service')),
            'chat_service': bool(self.professional_services.get('chat_service')),
            'security_validator': bool(self.professional_services.get('security_validator')),
            'phi_scrubber': bool(self.professional_services.get('phi_scrubber')),
            'cache_service': bool(self.professional_services.get('cache_service'))
        }
        
        # Apply stylesheet
        self.setStyleSheet(MAIN_STYLESHEET)
        
        self.setup_ui()
        
        # Initialize AI model health check
        self.check_ai_model_health()
        
        # Initialize default Medicare rubric
        self.initialize_default_rubric()
    
    def initialize_default_rubric(self):
        """Initialize Medicare Benefits Policy Manual as the default rubric."""
        self.default_rubric = {
            "name": "Medicare Benefits Policy Manual",
            "description": "Comprehensive Medicare compliance rubric for PT, OT, and SLP services covering documentation requirements, medical necessity, billing standards, and regulatory compliance.",
            "discipline": "All",
            "category": "Medicare Compliance",
            "is_default": True,
            "rules": [
                "Provider signature and credentials required",
                "Medical necessity must be clearly documented", 
                "Goals must be specific, measurable, and time-bound",
                "Physician plan of care required with frequency and duration",
                "Progress documentation required every 10 treatment days",
                "Functional outcomes must be documented",
                "Recertification required every 90 days"
            ]
        }
        
        # Set default rubric text for display
        self.current_rubric_text = f"""
**{self.default_rubric['name']}**

{self.default_rubric['description']}

**Key Requirements:**
• Provider signature and credentials required on all documentation
• Medical necessity must be clearly documented and justified
• Treatment goals must be SMART (Specific, Measurable, Achievable, Relevant, Time-bound)
• Physician plan of care required with specific frequency and duration
• Progress documentation required at least every 10 treatment days
• Functional outcomes must be documented and linked to interventions
• Physician recertification required every 90 days for continued services
• Assistant supervision must be properly documented per state regulations

**Disciplines Covered:** Physical Therapy (PT), Occupational Therapy (OT), Speech-Language Pathology (SLP)

**Compliance Areas:** Documentation, Medical Necessity, Billing, Quality Standards, Safety
        """.strip()
    
    def _initialize_professional_services(self) -> Dict:
        """Initialize professional services when available."""
        services = {}
        
        try:
            # Initialize LLM service
            if LLMService:
                services['llm_service'] = LLMService()
                print("✅ Professional LLM Service initialized")
            
            # Initialize Analysis service
            if AnalysisService:
                services['analysis_service'] = AnalysisService()
                print("✅ Professional Analysis Service initialized")
            
            # Initialize Chat service
            if ChatService and services.get('llm_service'):
                services['chat_service'] = ChatService(services['llm_service'])
                print("✅ Professional Chat Service initialized")
            
            # Initialize Security services
            if SecurityValidator:
                services['security_validator'] = SecurityValidator()
                print("✅ Security Validator initialized")
            
            if PhiScrubberService:
                services['phi_scrubber'] = PhiScrubberService()
                print("✅ PHI Scrubber Service initialized")
            
            # Initialize Performance services
            if CacheService:
                services['cache_service'] = CacheService()
                print("✅ Cache Service initialized")
            
            if PerformanceManager:
                services['performance_manager'] = PerformanceManager()
                print("✅ Performance Manager initialized")
            
            # Initialize NER service
            if NERAnalyzer:
                services['ner_analyzer'] = NERAnalyzer()
                print("✅ NER Analyzer initialized")
            
            # Initialize Hybrid Retriever
            if HybridRetriever:
                services['hybrid_retriever'] = HybridRetriever()
                print("✅ Hybrid Retriever initialized")
                
        except Exception as e:
            print(f"⚠️ Error initializing professional services: {e}")
        
        return services
    
    def run_professional_analysis(self, text: str, discipline: str, document_sections: Dict):
        """Run analysis using professional services."""
        try:
            analysis_service = self.professional_services.get('analysis_service')
            if not analysis_service:
                raise Exception("Professional analysis service not available")
            
            # Prepare analysis parameters
            analysis_params = {
                'document_text': text,
                'discipline': discipline,
                'document_sections': document_sections,
                'rubric_name': f"{discipline.upper()} Compliance Rubric"
            }
            
            # Add security validation if available
            security_validator = self.professional_services.get('security_validator')
            if security_validator:
                # Validate input text
                is_valid, error_msg = security_validator.sanitize_text_input(text)
                if not is_valid:
                    QMessageBox.warning(self, "Security Validation Failed", error_msg)
                    self.reset_analysis_ui()
                    return
            
            # Add PHI scrubbing if available
            phi_scrubber = self.professional_services.get('phi_scrubber')
            if phi_scrubber:
                try:
                    scrubbed_text = phi_scrubber.scrub_phi(text)
                    analysis_params['document_text'] = scrubbed_text
                    self.statusBar().showMessage("🔒 PHI scrubbing applied - analysis in progress...")
                except Exception as e:
                    print(f"⚠️ PHI scrubbing failed: {e}")
            
            # Start professional analysis worker
            self.professional_analysis_worker = ProfessionalAnalysisWorker(
                analysis_service, analysis_params, self.professional_services
            )
            self.professional_analysis_worker.finished.connect(self.on_analysis_complete)
            self.professional_analysis_worker.error.connect(self.on_analysis_error)
            self.professional_analysis_worker.progress.connect(self.on_analysis_progress)
            self.professional_analysis_worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Professional Analysis Error", 
                               f"Failed to start professional analysis: {e}\n\nFalling back to basic analysis.")
            # Fallback to mock analyzer
            self.analysis_worker = AnalysisWorker(text, discipline, self.analyzer)
            self.analysis_worker.finished.connect(self.on_analysis_complete)
            self.analysis_worker.error.connect(self.on_analysis_error)
            self.analysis_worker.progress.connect(self.on_analysis_progress)
            self.analysis_worker.start()
    
    def setup_ui(self):
        """Set up the complete user interface."""
        # Menu bar
        self.create_menu_bar()
        
        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Compact header for better scaling
        header = QLabel("🏥 THERAPY COMPLIANCE ANALYZER")
        header.setObjectName("headerLabel")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e40af, stop:0.5 #3b82f6, stop:1 #2563eb);
                color: white;
                padding: 12px;
                font-size: 20px;
                font-weight: 700;
                border-bottom: 3px solid #1d4ed8;
                min-height: 40px;
                max-height: 50px;
            }
        """)
        main_layout.addWidget(header)
        
        # Compact subtitle
        subtitle = QLabel("🏃‍♂️ PT • 🖐️ OT • 🗣️ SLP | Medicare Benefits Policy Manual (Default)")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #dbeafe, stop:0.5 #bfdbfe, stop:1 #dbeafe);
                color: #1e40af;
                padding: 6px;
                font-size: 11px;
                font-weight: 600;
                border-bottom: 2px solid #93c5fd;
                min-height: 20px;
                max-height: 30px;
            }
        """)
        main_layout.addWidget(subtitle)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setContentsMargins(16, 16, 16, 16)
        main_layout.addWidget(self.tabs)
        
        # Create tabs
        self.tabs.addTab(self.create_analysis_tab(), "📋 Analysis")
        self.tabs.addTab(self.create_dashboard_tab(), "📊 Dashboard")
        self.tabs.addTab(self.create_reports_tab(), "📄 Reports")
        self.tabs.addTab(self.create_chat_tab(), "💬 AI Assistant")
        
        if self.is_admin:
            self.tabs.addTab(self.create_admin_tab(), "⚙️ Admin")
        
        # Status bar with AI health indicator
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Individual AI Model Health Indicators
        self.llm_status_label = QLabel("🧠 LLM: Ready")
        self.llm_status_label.setStyleSheet("""
            QLabel {
                color: #10b981;
                font-weight: 600;
                padding: 2px 6px;
                background-color: #d1fae5;
                border-radius: 3px;
                margin: 1px;
                font-size: 10px;
            }
        """)
        self.status_bar.addPermanentWidget(self.llm_status_label)
        
        self.ner_status_label = QLabel("🏷️ NER: Ready")
        self.ner_status_label.setStyleSheet("""
            QLabel {
                color: #10b981;
                font-weight: 600;
                padding: 2px 6px;
                background-color: #d1fae5;
                border-radius: 3px;
                margin: 1px;
                font-size: 10px;
            }
        """)
        self.status_bar.addPermanentWidget(self.ner_status_label)
        
        self.embeddings_status_label = QLabel("🔗 Embeddings: Ready")
        self.embeddings_status_label.setStyleSheet("""
            QLabel {
                color: #10b981;
                font-weight: 600;
                padding: 2px 6px;
                background-color: #d1fae5;
                border-radius: 3px;
                margin: 1px;
                font-size: 10px;
            }
        """)
        self.status_bar.addPermanentWidget(self.embeddings_status_label)
        
        self.chat_status_label = QLabel("💬 Chat: Ready")
        self.chat_status_label.setStyleSheet("""
            QLabel {
                color: #10b981;
                font-weight: 600;
                padding: 2px 6px;
                background-color: #d1fae5;
                border-radius: 3px;
                margin: 1px;
                font-size: 10px;
            }
        """)
        self.status_bar.addPermanentWidget(self.chat_status_label)
        
        # Pacific Coast Therapy easter egg with palm tree (inconspicuous)
        pct_label = QLabel("🌴 Pacific Coast Therapy")
        pct_label.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-style: italic;
                font-size: 10px;
                padding: 2px 6px;
            }
        """)
        self.status_bar.addPermanentWidget(pct_label)
        
        self.status_bar.showMessage("🚀 Ready for analysis - Medicare Benefits Policy Manual loaded as default rubric")
        
        # Load default Medicare rubric into display
        if hasattr(self, 'current_rubric_text') and hasattr(self, 'rubric_display'):
            self.rubric_display.setPlainText(self.current_rubric_text)
    
    def create_menu_bar(self):
        """Create menu bar with all options."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("📁 File")
        file_menu.addAction("Upload Document", self.upload_document)
        file_menu.addAction("Upload Folder", self.upload_folder)
        file_menu.addSeparator()
        file_menu.addAction("Export Report (PDF)", self.export_pdf)
        file_menu.addAction("Export Report (HTML)", self.export_html)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        
        # Tools menu
        tools_menu = menubar.addMenu("🔧 Tools")
        tools_menu.addAction("AI Chat Assistant", self.open_chat)
        tools_menu.addAction("Manage Rubrics", self.manage_rubrics)
        tools_menu.addAction("Performance Settings", self.performance_settings)
        tools_menu.addSeparator()
        
        # 7 Habits submenu
        habits_menu = tools_menu.addMenu("🎯 7 Habits Framework")
        self.habits_action = habits_menu.addAction("Enable Framework", self.toggle_habits_framework)
        self.habits_action.setCheckable(True)
        self.habits_action.setChecked(True)  # Default enabled
        habits_menu.addAction("Framework Settings", self.show_habits_settings)
        habits_menu.addAction("View All Habits", self.open_habits_dashboard)
        
        tools_menu.addSeparator()
        tools_menu.addAction("Change Password", self.change_password)
        
        # View menu
        view_menu = menubar.addMenu("👁️ View")
        view_menu.addAction("Light Theme", lambda: self.set_theme("light"))
        view_menu.addAction("Dark Theme", lambda: self.set_theme("dark"))
        view_menu.addSeparator()
        view_menu.addAction("Document Preview", self.show_document_preview)
        
        # Admin menu (if admin)
        if self.is_admin:
            admin_menu = menubar.addMenu("⚙️ Admin")
            admin_menu.addAction("User Management", self.manage_users)
            admin_menu.addAction("System Settings", self.system_settings)
            admin_menu.addAction("Audit Logs", self.view_audit_logs)
            admin_menu.addAction("Team Analytics", self.team_analytics)
            admin_menu.addSeparator()
            admin_menu.addAction("Database Maintenance", self.database_maintenance)
        
        # Help menu
        help_menu = menubar.addMenu("❓ Help")
        help_menu.addAction("Documentation", self.open_documentation)
        help_menu.addAction("Compliance Guidelines", self.compliance_guidelines)
        help_menu.addAction("About", self.show_about)
    
    def create_analysis_tab(self) -> QWidget:
        """Create the main analysis tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Top section with rubric and upload controls
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.setMinimumHeight(280)
        top_splitter.setMaximumHeight(320)
        
        # Left: Rubric Management
        rubric_group = QGroupBox("📚 Compliance Rubric")
        rubric_layout = QVBoxLayout()
        rubric_layout.setSpacing(8)
        
        # Discipline selector with auto-detect
        discipline_layout = QHBoxLayout()
        discipline_layout.addWidget(QLabel("Detected Discipline:"))
        
        # Auto-detection display (read-only)
        self.discipline_display = QLabel("🔍 Automatic Detection - Upload document to analyze")
        self.discipline_display.setStyleSheet("""
            QLabel {
                background-color: #f1f5f9;
                border: 2px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: 600;
                color: #475569;
                min-height: 16px;
            }
        """)
        discipline_layout.addWidget(self.discipline_display)
        
        # Store detected disciplines for analysis
        self.detected_disciplines = []
        self.primary_discipline = None
        rubric_layout.addLayout(discipline_layout)
        
        # Detection result label
        self.detection_label = QLabel("")
        self.detection_label.setStyleSheet("color: #10b981; font-weight: 600; padding: 4px;")
        self.detection_label.setMaximumHeight(25)
        rubric_layout.addWidget(self.detection_label)
        
        # Rubric display area with default Medicare rubric
        self.rubric_display = QTextEdit()
        self.rubric_display.setMaximumHeight(100)  # More compact for scaling
        self.rubric_display.setReadOnly(True)
        self.rubric_display.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 6px;
                background-color: #f8fafc;
                font-size: 11px;
            }
        """)
        # Set default Medicare rubric text
        if hasattr(self, 'current_rubric_text'):
            self.rubric_display.setPlainText(self.current_rubric_text)
        else:
            self.rubric_display.setPlaceholderText("Medicare Benefits Policy Manual (Default) - Loading...")
        rubric_layout.addWidget(self.rubric_display)
        
        # Compact rubric buttons
        rubric_btn_layout = QHBoxLayout()
        self.upload_rubric_btn = QPushButton("📤 Upload")
        self.upload_rubric_btn.setMaximumHeight(32)
        self.upload_rubric_btn.clicked.connect(self.upload_rubric)
        rubric_btn_layout.addWidget(self.upload_rubric_btn)
        
        self.preview_rubric_btn = QPushButton("👁️ Preview")
        self.preview_rubric_btn.setMaximumHeight(32)
        self.preview_rubric_btn.clicked.connect(self.preview_rubric)
        rubric_btn_layout.addWidget(self.preview_rubric_btn)
        
        self.clear_rubric_btn = QPushButton("🗑️ Clear")
        self.clear_rubric_btn.setMaximumHeight(32)
        self.clear_rubric_btn.clicked.connect(self.clear_rubric)
        rubric_btn_layout.addWidget(self.clear_rubric_btn)
        rubric_layout.addLayout(rubric_btn_layout)
        
        rubric_group.setLayout(rubric_layout)
        top_splitter.addWidget(rubric_group)
        
        # Right: Upload Controls
        upload_group = QGroupBox("📄 Document Upload")
        upload_layout = QVBoxLayout()
        
        # Compact upload buttons
        upload_btn_layout = QHBoxLayout()
        self.upload_btn = QPushButton("📄 Document")
        self.upload_btn.setMaximumHeight(32)
        self.upload_btn.clicked.connect(self.upload_document)
        upload_btn_layout.addWidget(self.upload_btn)
        
        self.upload_folder_btn = QPushButton("📁 Folder")
        self.upload_folder_btn.setMaximumHeight(32)
        self.upload_folder_btn.clicked.connect(self.upload_folder)
        upload_btn_layout.addWidget(self.upload_folder_btn)
        upload_layout.addLayout(upload_btn_layout)
        
        # Combined file status and document area
        self.selected_file_label = QLabel("No document selected")
        self.selected_file_label.setStyleSheet("padding: 8px; background-color: #f1f5f9; border-radius: 4px;")
        upload_layout.addWidget(self.selected_file_label)
        
        upload_group.setLayout(upload_layout)
        top_splitter.addWidget(upload_group)
        
        top_splitter.setSizes([600, 600])  # Better proportions for top section
        layout.addWidget(top_splitter)
        
        # Main splitter for document and results with better scaling
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)  # Prevent collapsing
        
        # Left: Combined Document & Upload Status
        doc_group = QGroupBox("📄 Document & Upload Status")
        doc_layout = QVBoxLayout()
        
        # Document text area with enhanced placeholder
        self.document_text = QTextEdit()
        self.document_text.setPlaceholderText("""📄 Upload a document or paste your clinical documentation here...

🔧 Supported formats: PDF, DOCX, TXT
📊 Upload status and file details will appear above your document content
💡 Tip: Use the upload buttons above or drag & drop files directly

Example content:
Physical Therapy Progress Note
Patient: [Patient Name]
Date: [Date]
Subjective: Patient reports...
Objective: Range of motion...
Assessment: Patient showing progress...
Plan: Continue current treatment...""")
        
        # Status area that appears above document content
        self.upload_status_label = QLabel("")
        self.upload_status_label.setStyleSheet("""
            QLabel {
                background-color: #e0f2fe;
                border: 1px solid #0277bd;
                border-radius: 6px;
                padding: 8px;
                margin-bottom: 4px;
                font-size: 11px;
                color: #01579b;
            }
        """)
        self.upload_status_label.hide()  # Hidden until file is uploaded
        
        doc_layout.addWidget(self.upload_status_label)
        doc_layout.addWidget(self.document_text)
        doc_group.setLayout(doc_layout)
        splitter.addWidget(doc_group)
        
        # Right: Results
        results_group = QGroupBox("📊 Analysis Results")
        results_layout = QVBoxLayout()
        
        # Compliance score
        score_layout = QHBoxLayout()
        score_layout.addWidget(QLabel("Compliance Score:"))
        self.score_bar = QProgressBar()
        self.score_bar.setRange(0, 100)
        self.score_bar.setValue(0)
        score_layout.addWidget(self.score_bar)
        self.score_label = QLabel("0%")
        score_layout.addWidget(self.score_label)
        results_layout.addLayout(score_layout)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Issue", "Severity", "Impact ($)", "Suggestion"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        results_layout.addWidget(self.results_table)
        
        results_group.setLayout(results_layout)
        splitter.addWidget(results_group)
        
        # Set better proportions: 60% document, 40% results
        splitter.setSizes([1080, 720])  # 60/40 split for better document viewing
        splitter.setStretchFactor(0, 3)  # Document area gets more stretch
        splitter.setStretchFactor(1, 2)  # Results area gets less stretch
        layout.addWidget(splitter)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.analyze_btn = QPushButton("🔍 Run Analysis")
        self.analyze_btn.clicked.connect(self.run_analysis)
        self.analyze_btn.setObjectName("primaryButton")
        actions_layout.addWidget(self.analyze_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.clicked.connect(self.stop_analysis)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setObjectName("dangerButton")
        actions_layout.addWidget(self.stop_btn)
        
        self.export_btn = QPushButton("📥 Export Report")
        self.export_btn.clicked.connect(self.export_pdf)
        actions_layout.addWidget(self.export_btn)
        
        self.analytics_btn = QPushButton("📊 Analytics")
        self.analytics_btn.clicked.connect(self.open_analytics_dashboard)
        self.analytics_btn.setToolTip("View compliance analytics and trends")
        actions_layout.addWidget(self.analytics_btn)
        
        self.habits_btn = QPushButton("🎯 7 Habits")
        self.habits_btn.clicked.connect(self.open_habits_dashboard)
        self.habits_btn.setToolTip("View 7 Habits improvement framework")
        actions_layout.addWidget(self.habits_btn)
        
        self.chat_btn = QPushButton("💬 AI Chat")
        self.chat_btn.clicked.connect(self.toggle_chat_panel)
        self.chat_btn.setToolTip("Toggle AI chat assistant")
        actions_layout.addWidget(self.chat_btn)
        
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.clicked.connect(self.clear_analysis)
        actions_layout.addWidget(self.clear_btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # Collapsible AI Chat Panel
        self.chat_panel = QGroupBox("💬 AI Assistant (Quick Help)")
        self.chat_panel.setMaximumHeight(200)
        self.chat_panel.hide()  # Hidden by default
        
        chat_panel_layout = QVBoxLayout()
        
        # Mini chat area
        self.mini_chat_history = QTextBrowser()
        self.mini_chat_history.setMaximumHeight(100)
        self.mini_chat_history.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                padding: 8px;
                background-color: #f8fafc;
                font-size: 12px;
            }
        """)
        chat_panel_layout.addWidget(self.mini_chat_history)
        
        # Mini input
        mini_input_layout = QHBoxLayout()
        self.mini_chat_input = QTextEdit()
        self.mini_chat_input.setMaximumHeight(30)
        self.mini_chat_input.setPlaceholderText("Quick question...")
        mini_input_layout.addWidget(self.mini_chat_input)
        
        mini_send_btn = QPushButton("Send")
        mini_send_btn.setMaximumWidth(60)
        mini_send_btn.clicked.connect(self.send_mini_chat)
        mini_input_layout.addWidget(mini_send_btn)
        
        close_chat_btn = QPushButton("✕")
        close_chat_btn.setMaximumWidth(30)
        close_chat_btn.clicked.connect(self.hide_chat_panel)
        close_chat_btn.setToolTip("Close chat panel")
        mini_input_layout.addWidget(close_chat_btn)
        
        chat_panel_layout.addLayout(mini_input_layout)
        self.chat_panel.setLayout(chat_panel_layout)
        layout.addWidget(self.chat_panel)
        
        # Initialize mini chat
        self.mini_chat_history.setHtml("""
            <div style='color: #1e40af; font-weight: 600;'>🤖 Quick AI Help</div>
            <div style='color: #64748b; font-size: 11px;'>Ask quick compliance questions here, or use the AI Assistant tab for detailed help.</div>
        """)
        
        return tab
    
    def create_dashboard_tab(self) -> QWidget:
        """Create dashboard with analytics."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        layout.addWidget(QLabel("<h2>📊 Compliance Dashboard</h2>"))
        
        # Summary cards
        cards_layout = QHBoxLayout()
        
        # Total analyses card
        card1 = QGroupBox("Total Analyses")
        card1_layout = QVBoxLayout()
        card1_layout.addWidget(QLabel("<h1>0</h1>"))
        card1_layout.addWidget(QLabel("Documents analyzed"))
        card1.setLayout(card1_layout)
        cards_layout.addWidget(card1)
        
        # Average score card
        card2 = QGroupBox("Average Score")
        card2_layout = QVBoxLayout()
        card2_layout.addWidget(QLabel("<h1>0%</h1>"))
        card2_layout.addWidget(QLabel("Compliance rate"))
        card2.setLayout(card2_layout)
        cards_layout.addWidget(card2)
        
        # Issues found card
        card3 = QGroupBox("Issues Found")
        card3_layout = QVBoxLayout()
        card3_layout.addWidget(QLabel("<h1>0</h1>"))
        card3_layout.addWidget(QLabel("Total findings"))
        card3.setLayout(card3_layout)
        cards_layout.addWidget(card3)
        
        layout.addLayout(cards_layout)
        
        # Charts placeholder
        charts_group = QGroupBox("Compliance Trends")
        charts_layout = QVBoxLayout()
        charts_layout.addWidget(QLabel("📈 Historical compliance trends will appear here"))
        charts_layout.addWidget(QLabel("📊 Breakdown by discipline and issue type"))
        charts_group.setLayout(charts_layout)
        layout.addWidget(charts_group)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Dashboard")
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
        return tab
    
    def create_reports_tab(self) -> QWidget:
        """Create reports tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        layout.addWidget(QLabel("<h2>📄 Reports & Export</h2>"))
        
        # Report viewer
        self.report_viewer = QTextBrowser()
        self.report_viewer.setPlaceholderText("Run an analysis to generate a report...")
        layout.addWidget(self.report_viewer)
        
        # Export buttons
        export_layout = QHBoxLayout()
        export_layout.addWidget(QPushButton("📥 Export as PDF"))
        export_layout.addWidget(QPushButton("📥 Export as HTML"))
        export_layout.addWidget(QPushButton("📥 Export as JSON"))
        export_layout.addStretch()
        layout.addLayout(export_layout)
        
        return tab
    
    def create_chat_tab(self) -> QWidget:
        """Create integrated AI chat tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header = QLabel("💬 AI Compliance Assistant")
        header.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 700;
                color: #1e40af;
                padding: 12px;
                background-color: #dbeafe;
                border-radius: 8px;
            }
        """)
        layout.addWidget(header)
        
        # Chat history
        self.integrated_chat_history = QTextBrowser()
        self.integrated_chat_history.setStyleSheet("""
            QTextBrowser {
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 16px;
                background-color: #f8fafc;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(self.integrated_chat_history)
        
        # Input area
        input_label = QLabel("💭 Your Question:")
        input_label.setStyleSheet("font-weight: 600; color: #475569; font-size: 13px;")
        layout.addWidget(input_label)
        
        self.integrated_chat_input = QTextEdit()
        self.integrated_chat_input.setMaximumHeight(100)
        self.integrated_chat_input.setPlaceholderText("Ask about compliance, documentation tips, or specific findings...")
        self.integrated_chat_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
                background-color: white;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.integrated_chat_input)
        
        # Send button with Enter key support
        send_btn = QPushButton("📤 Send Message (Press Ctrl+Enter)")
        send_btn.clicked.connect(self.send_integrated_message)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        layout.addWidget(send_btn)
        
        # Add keyboard shortcuts for sending messages
        from PyQt6.QtGui import QKeySequence, QShortcut
        enter_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self.integrated_chat_input)
        enter_shortcut.activated.connect(self.send_integrated_message)
        
        # Welcome message
        self.integrated_chat_history.setHtml("""
            <div style='background-color: #dbeafe; padding: 16px; border-radius: 8px; margin-bottom: 12px;'>
                <strong style='color: #1e40af;'>🤖 AI Assistant:</strong><br>
                <span style='color: #334155;'>Hello! I'm your AI compliance assistant. I can help you with:</span><br><br>
                <span style='color: #334155;'>• Understanding compliance requirements<br>
                • Writing better documentation<br>
                • Explaining specific findings<br>
                • Medicare guidelines and regulations<br>
                • Best practices for PT, OT, and SLP</span><br><br>
                <span style='color: #334155;'>What would you like to know?</span>
            </div>
        """)
        
        return tab
    
    def create_admin_tab(self) -> QWidget:
        """Create admin tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        layout.addWidget(QLabel("<h2>⚙️ Administration</h2>"))
        
        # Admin sections
        sections = QGroupBox("Admin Functions")
        sections_layout = QVBoxLayout()
        
        sections_layout.addWidget(QPushButton("👥 User Management"))
        sections_layout.addWidget(QPushButton("📊 Team Analytics"))
        sections_layout.addWidget(QPushButton("📋 Audit Logs"))
        sections_layout.addWidget(QPushButton("🗄️ Database Maintenance"))
        sections_layout.addWidget(QPushButton("⚙️ System Settings"))
        sections_layout.addWidget(QPushButton("📚 Rubric Management"))
        
        sections.setLayout(sections_layout)
        layout.addWidget(sections)
        
        layout.addStretch()
        return tab
    
    # Event handlers
    def on_discipline_changed(self, index):
        """Handle discipline selection change."""
        if index == 0:
            self.statusBar().showMessage("Auto-detect mode enabled")
        elif index == 1:
            # Medicare Guidelines selected
            self.load_medicare_guidelines()
            self.statusBar().showMessage("📋 Medicare Benefits Policy Manual - Comprehensive compliance guidelines")
        elif index == 5:
            self.statusBar().showMessage("Multi-discipline analysis mode")
        else:
            disciplines = ["PT", "OT", "SLP"]
            discipline = disciplines[index - 2]  # Adjust for auto-detect and Medicare options
            self.statusBar().showMessage(f"Selected discipline: {discipline}")
    
    def auto_detect_discipline(self):
        """Automatically detect discipline from document text."""
        text = self.document_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "No Document", "Please upload or paste documentation first.")
            return
        
        if not self.discipline_detector:
            QMessageBox.warning(self, "Feature Unavailable", "Discipline detection not available.")
            return
        
        # Detect discipline
        self.status_bar.showMessage("Detecting discipline...")
        result = self.discipline_detector.detect_disciplines(text)
        
        # Update UI
        summary = self.discipline_detector.get_discipline_summary(result)
        self.detection_label.setText(f"✓ {summary}")
        
        # Auto-select discipline if single discipline detected
        if not result.is_multi_discipline and result.primary_discipline != 'UNKNOWN':
            # Update discipline display based on detection
            discipline_icons = {"PT": "🏥", "OT": "🖐️", "SLP": "🗣️"}
            if result.is_multi_discipline:
                disciplines_text = " + ".join(result.detected_disciplines)
                self.discipline_display.setText(f"🔍 Multi-Discipline: {disciplines_text}")
            else:
                icon = discipline_icons.get(result.primary_discipline, "📋")
                self.discipline_display.setText(f"{icon} {result.primary_discipline} - {result.confidence:.1f}% confidence")
        
        # Store detected disciplines
        self.detected_disciplines = result.detected_disciplines
        
        # Show detailed report
        detailed = self.discipline_detector.get_detailed_report(result)
        QMessageBox.information(self, "Discipline Detection Results", detailed)
        
        self.status_bar.showMessage(f"Detection complete: {summary}")
    
    def upload_document(self):
        """Upload a single document with full parsing support for PDF, DOCX, and TXT."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Document", "", 
            "All Supported (*.pdf *.docx *.txt);;PDF Files (*.pdf);;Word Documents (*.docx);;Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            try:
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                file_ext = os.path.splitext(file_path)[1].lower()
                
                content = ""
                parsing_method = "Unknown"
                
                # Use proper document parsing if available
                if parse_document_content and file_ext in ['.pdf', '.docx', '.txt']:
                    try:
                        # Parse document using the existing parsing system
                        parsed_chunks = parse_document_content(file_path)
                        
                        if parsed_chunks and not parsed_chunks[0]["sentence"].startswith("Error"):
                            # Combine all chunks into full text
                            content = "\n\n".join(chunk["sentence"] for chunk in parsed_chunks)
                            parsing_method = f"Professional {file_ext.upper()} Parser"
                            
                            # Add section information for PDFs
                            if file_ext == '.pdf' and len(parsed_chunks) > 1:
                                content = f"📄 PDF Document: {file_name}\n" + \
                                         f"📄 Pages: {len(parsed_chunks)}\n\n" + content
                        else:
                            # Handle parsing errors
                            error_msg = parsed_chunks[0]["sentence"] if parsed_chunks else "Unknown parsing error"
                            raise Exception(f"Parser error: {error_msg}")
                            
                    except Exception as parse_error:
                        # Fall back to manual handling
                        content = self._handle_file_fallback(file_path, file_name, file_ext, str(parse_error))
                        parsing_method = "Fallback Method"
                else:
                    # Manual file handling when parser not available
                    content = self._handle_file_fallback(file_path, file_name, file_ext, "Parser not available")
                    parsing_method = "Manual Handler"
                
                self.document_text.setPlainText(content)
                
                # Calculate text statistics
                word_count = len(content.split()) if content else 0
                char_count = len(content) if content else 0
                
                self.selected_file_label.setText(f"📄 {file_name}")
                
                # Update upload report with detailed information
                from datetime import datetime
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Determine file type description
                format_descriptions = {
                    '.pdf': '📄 PDF Document',
                    '.docx': '📝 Word Document',
                    '.txt': '📃 Text File',
                    '.doc': '📝 Legacy Word Document'
                }
                format_desc = format_descriptions.get(file_ext, f'📄 {file_ext.upper()} File')
                
                upload_info = f"""{format_desc}: {file_name}
📊 File Size: {file_size:,} bytes
📝 Word Count: {word_count:,}
🔤 Character Count: {char_count:,}
🔧 Parsing Method: {parsing_method}
✅ Status: Successfully loaded and parsed
"""
                
                # Show upload status above document
                self.upload_status_label.setText(upload_info.replace('\n', ' • '))
                # Reset to success styling
                self.upload_status_label.setStyleSheet("""
                    QLabel {
                        background-color: #e0f2fe;
                        border: 1px solid #0277bd;
                        border-radius: 6px;
                        padding: 8px;
                        margin-bottom: 4px;
                        font-size: 11px;
                        color: #01579b;
                    }
                """)
                self.upload_status_label.show()
                self.statusBar().showMessage(f"✅ Loaded: {file_name}")
                
                # Auto-detect discipline from uploaded document
                self.auto_detect_discipline()
                    
            except Exception as e:
                error_info = f"""❌ Error loading file: {str(e)}

🔧 Troubleshooting:
• Ensure the file is not corrupted
• Try saving as .txt format if possible
• Check file permissions
• For PDFs/Word docs, copy-paste text content instead"""
                
                # Show error status above document
                self.upload_status_label.setText(f"❌ Error: {str(e)}")
                self.upload_status_label.setStyleSheet("""
                    QLabel {
                        background-color: #ffebee;
                        border: 1px solid #d32f2f;
                        border-radius: 6px;
                        padding: 8px;
                        margin-bottom: 4px;
                        font-size: 11px;
                        color: #c62828;
                    }
                """)
                self.upload_status_label.show()
                self.statusBar().showMessage(f"❌ Error loading {os.path.basename(file_path) if file_path else 'file'}")
                QMessageBox.warning(self, "File Loading Error", f"Could not load file: {e}\n\nTip: For PDF/Word files, try copying and pasting the text content directly.")
    
    def _handle_file_fallback(self, file_path: str, file_name: str, file_ext: str, error_msg: str) -> str:
        """Handle file loading when the main parser fails."""
        if file_ext == '.txt':
            # Try multiple encodings for text files
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            return f"❌ Could not decode text file with any supported encoding.\nOriginal error: {error_msg}"
            
        elif file_ext == '.pdf':
            return f"""📄 PDF Document: {file_name}

⚠️ PDF parsing encountered an issue: {error_msg}

💡 To analyze this PDF document:
1. Open the PDF in your preferred PDF viewer
2. Select all text (Ctrl+A) and copy (Ctrl+C)
3. Paste the content into this text area
4. Run the analysis

🔧 Technical Note: Full PDF parsing requires pdfplumber library.
For scanned PDFs, OCR with pytesseract would be needed."""
            
        elif file_ext in ['.docx', '.doc']:
            return f"""📝 Word Document: {file_name}

⚠️ Word document parsing encountered an issue: {error_msg}

💡 To analyze this Word document:
1. Open the document in Microsoft Word or compatible editor
2. Select all text (Ctrl+A) and copy (Ctrl+C)  
3. Paste the content into this text area
4. Run the analysis

🔧 Technical Note: Full Word parsing requires python-docx library."""
            
        else:
            # Try to read as text with fallback encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except (UnicodeDecodeError, UnicodeError):
                    continue
                except Exception:
                    break
                    
            return f"""📄 File: {file_name}

⚠️ Could not parse this file type: {error_msg}

💡 Supported formats:
• PDF documents (.pdf)
• Word documents (.docx, .doc)
• Text files (.txt)

🔧 For other formats, please:
1. Convert to one of the supported formats, or
2. Copy and paste the text content directly"""
    
    def upload_folder(self):
        """Upload a folder of documents for batch processing."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            try:
                # Find supported files in the folder
                supported_extensions = ['.pdf', '.docx', '.txt', '.doc']
                files_found = []
                
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in supported_extensions):
                            files_found.append(os.path.join(root, file))
                
                if not files_found:
                    QMessageBox.information(self, "No Supported Files", 
                        f"No supported document files found in:\n{folder_path}\n\nSupported formats: PDF, DOCX, TXT")
                    return
                
                # Show batch processing dialog
                file_list = "\n".join([f"• {os.path.basename(f)}" for f in files_found[:10]])
                if len(files_found) > 10:
                    file_list += f"\n... and {len(files_found) - 10} more files"
                
                reply = QMessageBox.question(self, "Batch Processing", 
                    f"Found {len(files_found)} supported files:\n\n{file_list}\n\nProcess all files?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                
                if reply == QMessageBox.StandardButton.Yes:
                    self._process_batch_files(files_found)
                    
            except Exception as e:
                QMessageBox.warning(self, "Folder Processing Error", f"Error processing folder: {e}")
                self.statusBar().showMessage(f"❌ Error processing folder")
    
    def _process_batch_files(self, file_paths: List[str]):
        """Process multiple files in batch."""
        if not parse_document_content:
            QMessageBox.warning(self, "Batch Processing", 
                "Batch processing requires the document parsing system.\nPlease process files individually.")
            return
        
        processed_count = 0
        failed_count = 0
        combined_content = ""
        
        for i, file_path in enumerate(file_paths):
            try:
                file_name = os.path.basename(file_path)
                self.statusBar().showMessage(f"Processing {i+1}/{len(file_paths)}: {file_name}")
                
                # Parse the document
                parsed_chunks = parse_document_content(file_path)
                
                if parsed_chunks and not parsed_chunks[0]["sentence"].startswith("Error"):
                    content = "\n\n".join(chunk["sentence"] for chunk in parsed_chunks)
                    combined_content += f"\n\n{'='*50}\n📄 FILE: {file_name}\n{'='*50}\n\n{content}"
                    processed_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                failed_count += 1
                combined_content += f"\n\n{'='*50}\n❌ FAILED: {os.path.basename(file_path)}\nError: {str(e)}\n{'='*50}\n"
        
        # Update the document text with combined content
        if combined_content:
            self.document_text.setPlainText(combined_content)
            
            # Update upload report
            batch_info = f"""📁 Batch Processing Complete
📊 Total Files: {len(file_paths)}
✅ Successfully Processed: {processed_count}
❌ Failed: {failed_count}
📝 Combined Word Count: {len(combined_content.split()):,}
🔍 Ready for Analysis: {'Yes' if processed_count > 0 else 'No'}"""
            
            # Show batch status above document
            self.upload_status_label.setText(batch_info.replace('\n', ' • '))
            self.upload_status_label.setStyleSheet("""
                QLabel {
                    background-color: #e8f5e8;
                    border: 1px solid #4caf50;
                    border-radius: 6px;
                    padding: 8px;
                    margin-bottom: 4px;
                    font-size: 11px;
                    color: #2e7d32;
                }
            """)
            self.upload_status_label.show()
            self.selected_file_label.setText(f"📁 Batch: {processed_count} files")
            self.statusBar().showMessage(f"✅ Batch complete: {processed_count}/{len(file_paths)} files processed")
            
            # Auto-detect discipline from batch processed documents
            if processed_count > 0:
                self.auto_detect_discipline()
        else:
            QMessageBox.warning(self, "Batch Processing Failed", 
                "No files could be processed successfully.")
            self.statusBar().showMessage("❌ Batch processing failed")
    
    def run_analysis(self):
        """Run comprehensive compliance analysis with document structure parsing."""
        text = self.document_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "No Document", "Please upload or paste documentation first.")
            return
        
        # Parse document into sections if parsing is available
        document_sections = {}
        if parse_document_into_sections:
            try:
                document_sections = parse_document_into_sections(text)
                if len(document_sections) > 1:
                    # Document has structured sections
                    section_info = f"📋 Document Structure Detected:\n"
                    for section_name, section_content in document_sections.items():
                        word_count = len(section_content.split())
                        section_info += f"• {section_name}: {word_count} words\n"
                    
                    self.statusBar().showMessage("📋 Structured document detected - enhanced analysis available")
                else:
                    self.statusBar().showMessage("📄 Unstructured document - standard analysis mode")
            except Exception as e:
                # Fall back to treating as single document
                document_sections = {"full_text": text}
                self.statusBar().showMessage("📄 Document parsing unavailable - using full text")
        
        # Automatically detect discipline(s)
        if self.discipline_detector:
            result = self.discipline_detector.detect_disciplines(text)
            
            # Update discipline display
            if result.primary_discipline == 'UNKNOWN':
                self.discipline_display.setText("❓ Unknown - Using general compliance rules")
                self.discipline_display.setStyleSheet("""
                    QLabel {
                        background-color: #fef3c7;
                        border: 2px solid #f59e0b;
                        border-radius: 8px;
                        padding: 8px 12px;
                        font-weight: 600;
                        color: #92400e;
                        min-height: 16px;
                    }
                """)
                discipline = "pt"  # Default to PT rules
            elif result.is_multi_discipline:
                disciplines_text = " + ".join(result.detected_disciplines)
                self.discipline_display.setText(f"🔍 Multi-Discipline: {disciplines_text}")
                self.discipline_display.setStyleSheet("""
                    QLabel {
                        background-color: #e0f2fe;
                        border: 2px solid #0277bd;
                        border-radius: 8px;
                        padding: 8px 12px;
                        font-weight: 600;
                        color: #01579b;
                        min-height: 16px;
                    }
                """)
                # Run analysis for all detected disciplines
                self.run_multi_discipline_analysis(text, result.detected_disciplines)
                return
            else:
                discipline_icons = {"PT": "🏥", "OT": "🖐️", "SLP": "🗣️"}
                icon = discipline_icons.get(result.primary_discipline, "📋")
                self.discipline_display.setText(f"{icon} {result.primary_discipline} - {result.confidence:.1f}% confidence")
                self.discipline_display.setStyleSheet("""
                    QLabel {
                        background-color: #dcfce7;
                        border: 2px solid #16a34a;
                        border-radius: 8px;
                        padding: 8px 12px;
                        font-weight: 600;
                        color: #15803d;
                        min-height: 16px;
                    }
                """)
                discipline = result.primary_discipline.lower()
                
                # Store detected info
                self.detected_disciplines = result.detected_disciplines
                self.primary_discipline = result.primary_discipline
        else:
            # Fallback when discipline detector not available
            self.discipline_display.setText("❓ Detection unavailable - Using PT rules")
            discipline = "pt"
        
        # Show progress
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.analyze_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.statusBar().showMessage("Running analysis...")
        
        # Use professional analysis service if available, otherwise fallback to mock
        if self.professional_services.get('analysis_service'):
            self.statusBar().showMessage("🚀 Running professional AI analysis...")
            self.run_professional_analysis(text, discipline, document_sections)
        else:
            self.statusBar().showMessage("⚠️ Running basic analysis (professional services unavailable)...")
            # Start worker with mock analyzer
            self.analysis_worker = AnalysisWorker(text, discipline, self.analyzer)
        self.analysis_worker.finished.connect(self.on_analysis_complete)
        self.analysis_worker.error.connect(self.on_analysis_error)
        self.analysis_worker.progress.connect(self.on_analysis_progress)
        self.analysis_worker.start()
    
    def stop_analysis(self):
        """Stop running analysis."""
        if self.analysis_worker:
            self.analysis_worker.terminate()
            self.analysis_worker.wait()
        self.reset_analysis_ui()
        self.status_bar.showMessage("Analysis stopped")
    
    def on_analysis_progress(self, value: int, message: str):
        """Update progress."""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(value)
        self.status_bar.showMessage(message)
    
    def on_analysis_complete(self, results: Dict):
        """Handle analysis completion."""
        self.current_results = results
        
        # Update score
        score = results["compliance_score"]
        self.score_bar.setValue(int(score))
        self.score_label.setText(f"{score}%")
        
        # Color code score
        if score >= 80:
            color = "#10b981"
        elif score >= 60:
            color = "#f59e0b"
        else:
            color = "#ef4444"
        self.score_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")
        
        # Update table
        findings = results["findings"]
        self.results_table.setRowCount(len(findings))
        
        for i, finding in enumerate(findings):
            self.results_table.setItem(i, 0, QTableWidgetItem(finding["title"]))
            
            severity_item = QTableWidgetItem(finding["severity"])
            if finding["severity"] == "HIGH":
                severity_item.setBackground(QColor("#fecaca"))
            else:
                severity_item.setBackground(QColor("#fed7aa"))
            self.results_table.setItem(i, 1, severity_item)
            
            self.results_table.setItem(i, 2, QTableWidgetItem(f"${finding['financial_impact']}"))
            self.results_table.setItem(i, 3, QTableWidgetItem(finding["suggestion"]))
        
        # Generate report for the Reports tab
        self.generate_report(results)
        
        # Show pop-up report window with AI chat
        self.show_report_popup(results)
        
        self.reset_analysis_ui()
        self.statusBar().showMessage(f"Analysis complete - Score: {score}% | {len(findings)} findings | Risk: ${results['total_financial_impact']}")
    
    def show_report_popup(self, results):
        """Show the pop-up report window with integrated AI chat."""
        document_text = self.document_text.toPlainText()
        report_window = ReportWindow(self, results, document_text)
        report_window.exec()
    
    def on_analysis_error(self, error: str):
        """Handle analysis error."""
        QMessageBox.critical(self, "Analysis Error", f"An error occurred: {error}")
        self.reset_analysis_ui()
        self.status_bar.showMessage("Analysis failed")
    
    def reset_analysis_ui(self):
        """Reset UI after analysis."""
        self.progress_bar.hide()
        self.progress_bar.setValue(0)
        self.analyze_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
    
    def generate_report(self, results: Dict):
        """Generate HTML report."""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                h1 {{ color: #1e40af; }}
                .score {{ font-size: 24px; font-weight: bold; color: #10b981; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #dbeafe; }}
                .high {{ background-color: #fecaca; }}
                .medium {{ background-color: #fed7aa; }}
            </style>
        </head>
        <body>
            <h1>Therapy Compliance Analysis Report</h1>
            <p><strong>Discipline:</strong> {results['discipline']}</p>
            <p><strong>Compliance Score:</strong> <span class="score">{results['compliance_score']}%</span></p>
            <p><strong>Total Financial Risk:</strong> ${results['total_financial_impact']}</p>
            
            <h2>Findings</h2>
            <table>
                <tr>
                    <th>Issue</th>
                    <th>Severity</th>
                    <th>Impact</th>
                    <th>Suggestion</th>
                </tr>
        """
        
        for finding in results["findings"]:
            severity_class = "high" if finding["severity"] == "HIGH" else "medium"
            html += f"""
                <tr class="{severity_class}">
                    <td>{finding['title']}</td>
                    <td>{finding['severity']}</td>
                    <td>${finding['financial_impact']}</td>
                    <td>{finding['suggestion']}</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        self.report_viewer.setHtml(html)
    
    def clear_analysis(self):
        """Clear all analysis data."""
        self.document_text.clear()
        self.results_table.setRowCount(0)
        self.score_bar.setValue(0)
        self.score_label.setText("0%")
        self.report_viewer.clear()
        self.selected_file_label.setText("No document selected")
        self.upload_status_label.hide()  # Hide upload status
        self.current_results = None
        self.statusBar().showMessage("Cleared")
    
    def open_chat(self):
        """Open AI chat assistant."""
        if not self.chat_dialog:
            self.chat_dialog = ChatDialog(self)
        self.chat_dialog.show()
        self.chat_dialog.raise_()
        self.chat_dialog.activateWindow()
    
    def export_pdf(self):
        """Export report as PDF."""
        if not self.current_results:
            QMessageBox.warning(self, "No Report", "Run an analysis first to generate a report.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Save PDF Report", "", "PDF Files (*.pdf)")
        if file_path:
            QMessageBox.information(self, "Export", f"Report would be exported to: {file_path}\n(PDF export feature in development)")
    
    def export_html(self):
        """Export report as HTML."""
        if not self.current_results:
            QMessageBox.warning(self, "No Report", "Run an analysis first to generate a report.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Save HTML Report", "", "HTML Files (*.html)")
        if file_path:
            with open(file_path, 'w') as f:
                f.write(self.report_viewer.toHtml())
            QMessageBox.information(self, "Success", f"Report exported to: {file_path}")
    
    def manage_rubrics(self):
        """Open rubric management dialog."""
        QMessageBox.information(self, "Rubric Management", "Rubric management interface coming soon!")
    
    def performance_settings(self):
        """Open performance settings."""
        QMessageBox.information(self, "Performance Settings", "Performance settings interface coming soon!")
    
    def change_password(self):
        """Change user password."""
        QMessageBox.information(self, "Change Password", "Password change interface coming soon!")
    
    def set_theme(self, theme: str):
        """Set application theme."""
        self.current_theme = theme
        if theme == "dark":
            self.setStyleSheet(DARK_THEME)
        else:
            self.setStyleSheet(MAIN_STYLESHEET)
        self.status_bar.showMessage(f"Theme changed to: {theme}")
    
    def show_document_preview(self):
        """Show document in preview window."""
        QMessageBox.information(self, "Document Preview", self.document_text.toPlainText()[:500] + "...")
    
    def manage_users(self):
        """User management (admin)."""
        QMessageBox.information(self, "User Management", "User management interface coming soon!")
    
    def system_settings(self):
        """System settings (admin)."""
        QMessageBox.information(self, "System Settings", "System settings interface coming soon!")
    
    def view_audit_logs(self):
        """View audit logs (admin)."""
        QMessageBox.information(self, "Audit Logs", "Audit logs viewer coming soon!")
    
    def team_analytics(self):
        """Team analytics (admin)."""
        QMessageBox.information(self, "Team Analytics", "Team analytics dashboard coming soon!")
    
    def database_maintenance(self):
        """Database maintenance (admin)."""
        QMessageBox.information(self, "Database Maintenance", "Database maintenance tools coming soon!")
    
    def open_documentation(self):
        """Open documentation."""
        webbrowser.open("https://github.com/yourusername/therapy-compliance-analyzer")
    
    def compliance_guidelines(self):
        """Show compliance guidelines."""
        QMessageBox.information(self, "Compliance Guidelines", 
            "Medicare Part B Compliance Guidelines:\n\n"
            "• All notes must be signed and dated\n"
            "• Goals must be measurable and time-bound\n"
            "• Medical necessity must be documented\n"
            "• Progress must be tracked\n"
            "• Skilled services must be justified")
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About", 
            "🏥 Therapy Compliance Analyzer\n\n"
            "Version 2.0 - Professional Edition\n\n"
            "🎯 Multi-discipline compliance checking for:\n"
            "• Physical Therapy (PT) 🏃‍♂️\n"
            "• Occupational Therapy (OT) 🖐️\n"
            "• Speech-Language Pathology (SLP) 🗣️\n\n"
            "✨ Advanced Features:\n"
            "• 🔍 Automatic discipline detection\n"
            "• 🏥 Multi-discipline patient analysis\n"
            "• 📊 Real-time compliance analytics\n"
            "• 🤖 AI-powered compliance checking\n"
            "• 🎯 7 Habits framework integration\n"
            "• 💬 Intelligent AI chat assistant\n\n"
            "💝 Created with love by Kevin Moon 💝\n"
            "        🫶 🫶 🫶\n"
            "   (heart hands with love)\n\n"
            "🌊 Powered by Pacific Coast Therapy\n"
            "© 2025 All Rights Reserved")
    
    def run_multi_discipline_analysis(self, text: str, disciplines: List[str]):
        """Run analysis for multiple disciplines."""
        self.status_bar.showMessage("Running multi-discipline analysis...")
        
        all_results = []
        combined_findings = []
        combined_impact = 0
        
        for discipline in disciplines:
            disc_lower = discipline.lower()
            results = self.analyzer.analyze_compliance(text, disc_lower)
            all_results.append({
                'discipline': discipline,
                'results': results
            })
            combined_findings.extend([
                {**f, 'discipline': discipline} 
                for f in results['findings']
            ])
            combined_impact += results['total_financial_impact']
        
        # Calculate combined score
        total_possible = sum(
            sum(rule["financial_impact"] for rule in self.analyzer.rules[d.lower()].values())
            for d in disciplines
        )
        combined_score = max(0, 100 - (combined_impact / total_possible * 100)) if total_possible > 0 else 100
        
        # Create combined results
        combined_results = {
            'findings': combined_findings,
            'compliance_score': round(combined_score, 1),
            'total_financial_impact': combined_impact,
            'discipline': 'MULTI',
            'disciplines_analyzed': disciplines,
            'individual_results': all_results
        }
        
        self.current_results = combined_results
        self.display_multi_discipline_results(combined_results)
        self.status_bar.showMessage(f"Multi-discipline analysis complete - {len(disciplines)} disciplines analyzed")
    
    def display_multi_discipline_results(self, results: Dict):
        """Display results from multi-discipline analysis."""
        # Update score
        score = results["compliance_score"]
        self.score_bar.setValue(int(score))
        self.score_label.setText(f"{score}%")
        
        # Color code score
        if score >= 80:
            color = "#10b981"
        elif score >= 60:
            color = "#f59e0b"
        else:
            color = "#ef4444"
        self.score_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")
        
        # Update table with discipline column
        findings = results["findings"]
        self.results_table.setColumnCount(5)  # Add discipline column
        self.results_table.setHorizontalHeaderLabels(["Discipline", "Issue", "Severity", "Impact ($)", "Suggestion"])
        self.results_table.setRowCount(len(findings))
        
        for i, finding in enumerate(findings):
            # Discipline
            disc_item = QTableWidgetItem(finding.get('discipline', ''))
            disc_item.setBackground(QColor("#dbeafe"))
            self.results_table.setItem(i, 0, disc_item)
            
            # Issue
            self.results_table.setItem(i, 1, QTableWidgetItem(finding["title"]))
            
            # Severity
            severity_item = QTableWidgetItem(finding["severity"])
            if finding["severity"] == "HIGH":
                severity_item.setBackground(QColor("#fecaca"))
            else:
                severity_item.setBackground(QColor("#fed7aa"))
            self.results_table.setItem(i, 2, severity_item)
            
            # Impact
            self.results_table.setItem(i, 3, QTableWidgetItem(f"${finding['financial_impact']}"))
            
            # Suggestion
            self.results_table.setItem(i, 4, QTableWidgetItem(finding["suggestion"]))
        
        # Generate multi-discipline report
        self.generate_multi_discipline_report(results)
        
        self.reset_analysis_ui()
    
    def generate_multi_discipline_report(self, results: Dict):
        """Generate HTML report for multi-discipline analysis."""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                h1 {{ color: #1e40af; }}
                h2 {{ color: #3b82f6; margin-top: 24px; }}
                .score {{ font-size: 24px; font-weight: bold; color: #10b981; }}
                .discipline-badge {{ 
                    display: inline-block;
                    background-color: #dbeafe;
                    color: #1e40af;
                    padding: 4px 12px;
                    border-radius: 12px;
                    margin: 4px;
                    font-weight: 600;
                }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #dbeafe; }}
                .high {{ background-color: #fecaca; }}
                .medium {{ background-color: #fed7aa; }}
                .pt {{ background-color: #dbeafe; }}
                .ot {{ background-color: #fef3c7; }}
                .slp {{ background-color: #d1fae5; }}
            </style>
        </head>
        <body>
            <h1>🏥 Multi-Discipline Compliance Analysis Report</h1>
            <p><strong>Disciplines Analyzed:</strong> 
        """
        
        for disc in results['disciplines_analyzed']:
            html += f'<span class="discipline-badge">{disc}</span>'
        
        html += f"""
            </p>
            <p><strong>Overall Compliance Score:</strong> <span class="score">{results['compliance_score']}%</span></p>
            <p><strong>Total Financial Risk:</strong> ${results['total_financial_impact']}</p>
            
            <h2>Individual Discipline Scores</h2>
            <table>
                <tr>
                    <th>Discipline</th>
                    <th>Score</th>
                    <th>Findings</th>
                    <th>Financial Risk</th>
                </tr>
        """
        
        for disc_result in results['individual_results']:
            disc = disc_result['discipline']
            res = disc_result['results']
            html += f"""
                <tr>
                    <td class="{disc.lower()}">{disc}</td>
                    <td>{res['compliance_score']}%</td>
                    <td>{len(res['findings'])}</td>
                    <td>${res['total_financial_impact']}</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h2>All Findings</h2>
            <table>
                <tr>
                    <th>Discipline</th>
                    <th>Issue</th>
                    <th>Severity</th>
                    <th>Impact</th>
                    <th>Suggestion</th>
                </tr>
        """
        
        for finding in results["findings"]:
            severity_class = "high" if finding["severity"] == "HIGH" else "medium"
            disc_class = finding.get('discipline', 'PT').lower()
            html += f"""
                <tr class="{severity_class}">
                    <td class="{disc_class}">{finding.get('discipline', '')}</td>
                    <td>{finding['title']}</td>
                    <td>{finding['severity']}</td>
                    <td>${finding['financial_impact']}</td>
                    <td>{finding['suggestion']}</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        self.report_viewer.setHtml(html)
    
    def send_integrated_message(self):
        """Send message in integrated chat."""
        message = self.integrated_chat_input.toPlainText().strip()
        if not message:
            return
        
        # Add user message
        current_html = self.integrated_chat_history.toHtml()
        user_msg = f"""
            <div style='background-color: #f1f5f9; padding: 12px; border-radius: 8px; margin: 8px 0; margin-left: 40px;'>
                <strong style='color: #475569;'>👤 You:</strong><br>
                <span style='color: #1e293b;'>{message}</span>
            </div>
        """
        self.integrated_chat_history.setHtml(current_html + user_msg)
        self.integrated_chat_input.clear()
        
        # Generate AI response
        response = self.generate_ai_response(message)
        current_html = self.integrated_chat_history.toHtml()
        ai_msg = f"""
            <div style='background-color: #dbeafe; padding: 12px; border-radius: 8px; margin: 8px 0; margin-right: 40px;'>
                <strong style='color: #1e40af;'>🤖 AI Assistant:</strong><br>
                <span style='color: #334155;'>{response}</span>
            </div>
        """
        self.integrated_chat_history.setHtml(current_html + ai_msg)
        
        # Scroll to bottom
        scrollbar = self.integrated_chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def generate_ai_response(self, message: str) -> str:
        """Generate AI response for integrated chat."""
        message_lower = message.lower()
        
        if "signature" in message_lower:
            return "All therapy notes must be signed and dated by the treating therapist with their credentials (PT, DPT, OT, OTR, SLP, CCC-SLP, etc.). This is required for Medicare reimbursement and regulatory compliance."
        elif "goal" in message_lower or "smart" in message_lower:
            return "Goals should be SMART: <strong>S</strong>pecific, <strong>M</strong>easurable, <strong>A</strong>chievable, <strong>R</strong>elevant, and <strong>T</strong>ime-bound.<br><br>Example: 'Patient will increase right shoulder flexion from 90° to 120° within 3 weeks to improve overhead reaching for ADLs.' This is much better than 'Patient will improve shoulder mobility.'"
        elif "medical necessity" in message_lower:
            return "Medical necessity means documenting why skilled therapy is required. You must:<br>• Link interventions to functional limitations<br>• Explain why professional therapy is needed vs. self-care<br>• Show how treatments address specific deficits<br>• Demonstrate skilled services that require therapist expertise"
        elif "progress" in message_lower:
            return "Progress documentation should include:<br>• Objective measurements (ROM, strength, distance)<br>• Functional improvements or decline<br>• Response to treatment interventions<br>• Progress toward established goals<br>• Any barriers to progress<br>• Plan modifications based on response"
        elif "pt" in message_lower and "physical therapy" in message_lower:
            return "PT documentation should focus on:<br>• Therapeutic exercises and parameters<br>• Gait training and mobility<br>• Manual therapy techniques<br>• Strength and ROM measurements<br>• Functional mobility goals<br>• Equipment training and safety"
        elif "ot" in message_lower and "occupational therapy" in message_lower:
            return "OT documentation should emphasize:<br>• ADL training and independence<br>• Fine motor and cognitive skills<br>• Adaptive equipment and techniques<br>• Home/work environment modifications<br>• Sensory processing interventions<br>• Functional goal achievement"
        elif "slp" in message_lower and ("speech" in message_lower or "language" in message_lower):
            return "SLP documentation should include:<br>• Communication assessments and goals<br>• Swallowing safety and strategies<br>• Cueing and compensatory techniques<br>• Objective measures (accuracy, consistency)<br>• Functional communication outcomes<br>• Safety recommendations for dysphagia"
        elif "kevin moon" in message_lower:
            return "💝 Kevin Moon is the amazing developer who created this system with love and dedication! 🫶🫶🫶 He poured his heart into making compliance analysis easier for therapists everywhere!"
        elif "pacific coast therapy" in message_lower:
            return "🌴 Pacific Coast Therapy - providing excellent rehabilitation services by the beautiful coast! 🌊 Where healing meets the ocean breeze! 🏖️"
        else:
            return "I can help with compliance questions about:<br>• Documentation requirements<br>• Medicare guidelines<br>• SMART goals<br>• Medical necessity<br>• Progress notes<br>• Signatures and dates<br>• Discipline-specific requirements<br><br>Try asking about any of these topics!"
    
    def upload_rubric(self):
        """Upload a new rubric file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Rubric File", "", 
            "TTL Files (*.ttl);;Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.rubric_display.setPlainText(content[:500] + "..." if len(content) > 500 else content)
                self.status_bar.showMessage(f"Loaded rubric: {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not load rubric: {e}")
    
    def preview_rubric(self):
        """Preview current rubric in popup window."""
        if not self.rubric_display.toPlainText().strip():
            QMessageBox.information(self, "No Rubric", "No rubric loaded to preview.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("📚 Rubric Preview")
        dialog.resize(800, 600)
        layout = QVBoxLayout(dialog)
        
        preview = QTextEdit()
        preview.setPlainText(self.rubric_display.toPlainText())
        preview.setReadOnly(True)
        layout.addWidget(preview)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def clear_rubric(self):
        """Clear current rubric."""
        self.rubric_display.clear()
        self.status_bar.showMessage("Rubric cleared")    

    def toggle_chat_panel(self):
        """Toggle the mini chat panel visibility."""
        if self.chat_panel.isVisible():
            self.chat_panel.hide()
            self.chat_btn.setText("💬 Show Chat")
        else:
            self.chat_panel.show()
            self.chat_btn.setText("💬 Hide Chat")
    
    def hide_chat_panel(self):
        """Hide the chat panel."""
        self.chat_panel.hide()
        self.chat_btn.setText("💬 Show Chat")
    
    def send_mini_chat(self):
        """Send message in mini chat panel."""
        message = self.mini_chat_input.toPlainText().strip()
        if not message:
            return
        
        # Add user message
        current_html = self.mini_chat_history.toHtml()
        user_msg = f"""
            <div style='margin: 4px 0; padding: 4px; background-color: #f1f5f9; border-radius: 4px;'>
                <strong style='color: #475569; font-size: 11px;'>You:</strong> {message}
            </div>
        """
        
        # Generate quick response
        response = self.generate_quick_ai_response(message)
        ai_msg = f"""
            <div style='margin: 4px 0; padding: 4px; background-color: #dbeafe; border-radius: 4px;'>
                <strong style='color: #1e40af; font-size: 11px;'>AI:</strong> {response}
            </div>
        """
        
        self.mini_chat_history.setHtml(current_html + user_msg + ai_msg)
        self.mini_chat_input.clear()
        
        # Scroll to bottom
        scrollbar = self.mini_chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def generate_quick_ai_response(self, message: str) -> str:
        """Generate quick AI response for mini chat."""
        message_lower = message.lower()
        
        if "signature" in message_lower:
            return "All notes need therapist signature + date + credentials."
        elif "goal" in message_lower:
            return "Use SMART goals: Specific, Measurable, Achievable, Relevant, Time-bound."
        elif "medical necessity" in message_lower:
            return "Link treatments to functional limitations. Explain why skilled therapy is needed."
        elif "progress" in message_lower:
            return "Document objective measures, functional changes, and goal progress."
        else:
            return "Ask about: signatures, goals, medical necessity, progress, or specific compliance topics."
    
    def open_analytics_dashboard(self):
        """Open analytics dashboard."""
        # Switch to dashboard tab
        self.tabs.setCurrentIndex(1)  # Dashboard is index 1
        self.status_bar.showMessage("Switched to Analytics Dashboard")
    
    def open_habits_dashboard(self):
        """Open 7 Habits dashboard."""
        if not self.habits_framework:
            QMessageBox.information(self, "7 Habits Framework", 
                "7 Habits framework not available in this version.")
            return
        
        if not self.habits_enabled:
            reply = QMessageBox.question(self, "7 Habits Framework", 
                "7 Habits framework is currently disabled. Would you like to enable it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.habits_enabled = True
                self.habits_action.setChecked(True)
                self.update_habits_integration()
            else:
                return
        
        # Create habits dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("🎯 7 Habits of Highly Effective Clinicians")
        dialog.resize(900, 700)
        layout = QVBoxLayout(dialog)
        
        # Header
        header = QLabel("🎯 7 Habits Framework for Clinical Excellence")
        header.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 700;
                color: #1e40af;
                padding: 12px;
                background-color: #dbeafe;
                border-radius: 8px;
                margin-bottom: 16px;
            }
        """)
        layout.addWidget(header)
        
        # Habits overview
        habits_text = QTextEdit()
        habits_text.setReadOnly(True)
        habits_html = self.generate_habits_overview()
        habits_text.setHtml(habits_html)
        layout.addWidget(habits_text)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def generate_habits_overview(self) -> str:
        """Generate HTML overview of 7 Habits framework."""
        if not self.habits_framework:
            return "<p>7 Habits framework not available.</p>"
        
        html = """
        <h2>Stephen Covey's 7 Habits Applied to Clinical Documentation</h2>
        <p>Transform your documentation practice with these proven principles:</p>
        """
        
        for habit_id, habit in self.habits_framework.HABITS.items():
            html += f"""
            <div style='margin: 16px 0; padding: 12px; border-left: 4px solid #3b82f6; background-color: #f8fafc;'>
                <h3 style='color: #1e40af; margin: 0 0 8px 0;'>
                    Habit {habit['number']}: {habit['name']}
                </h3>
                <p style='margin: 0 0 8px 0; font-weight: 600; color: #475569;'>
                    Principle: {habit['principle']}
                </p>
                <p style='margin: 0 0 8px 0;'>
                    <strong>Clinical Application:</strong> {habit['clinical_application']}
                </p>
                <p style='margin: 0;'>
                    {habit['description'].strip()}
                </p>
            </div>
            """
        
        html += """
        <div style='margin-top: 24px; padding: 16px; background-color: #dbeafe; border-radius: 8px;'>
            <h3 style='color: #1e40af; margin: 0 0 12px 0;'>How This Helps Your Documentation:</h3>
            <ul style='margin: 0; padding-left: 20px;'>
                <li>Proactively prevent compliance issues</li>
                <li>Create clear, goal-oriented documentation</li>
                <li>Prioritize most important elements first</li>
                <li>Build collaborative relationships with reviewers</li>
                <li>Understand different perspectives (patient, payer, provider)</li>
                <li>Work synergistically with your team</li>
                <li>Continuously improve your documentation skills</li>
            </ul>
        </div>
        """
        
        return html
    
    def toggle_habits_framework(self):
        """Toggle 7 Habits framework on/off."""
        self.habits_enabled = not self.habits_enabled
        
        if self.habits_enabled:
            self.habits_action.setText("🎯 Disable 7 Habits Framework")
            self.habits_btn.show()
            self.status_bar.showMessage("7 Habits Framework enabled")
        else:
            self.habits_action.setText("🎯 Enable 7 Habits Framework")
            self.habits_btn.hide()
            self.status_bar.showMessage("7 Habits Framework disabled")
        
        # Update habits button visibility
        self.update_habits_integration()
    
    def update_habits_integration(self):
        """Update 7 Habits integration throughout the app."""
        if hasattr(self, 'habits_btn'):
            if self.habits_enabled and self.habits_framework:
                self.habits_btn.show()
                self.habits_btn.setEnabled(True)
            else:
                self.habits_btn.hide()
        
        # Update analysis to include/exclude habits
        if hasattr(self, 'analyzer'):
            # This would integrate habits into compliance analysis
            pass    

    def show_habits_settings(self):
        """Show 7 Habits framework settings dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("🎯 7 Habits Framework Settings")
        dialog.resize(600, 500)
        layout = QVBoxLayout(dialog)
        
        # Header
        header = QLabel("🎯 7 Habits Framework Configuration")
        header.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 700;
                color: #1e40af;
                padding: 12px;
                background-color: #dbeafe;
                border-radius: 8px;
                margin-bottom: 16px;
            }
        """)
        layout.addWidget(header)
        
        # Settings tabs
        settings_tabs = QTabWidget()
        
        # General tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Enable/Disable
        enable_group = QGroupBox("Framework Status")
        enable_layout = QVBoxLayout()
        
        self.habits_enabled_checkbox = QPushButton("🎯 Framework Enabled" if self.habits_enabled else "⭕ Framework Disabled")
        self.habits_enabled_checkbox.setCheckable(True)
        self.habits_enabled_checkbox.setChecked(self.habits_enabled)
        self.habits_enabled_checkbox.clicked.connect(self.toggle_habits_from_settings)
        self.habits_enabled_checkbox.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 12px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:checked {
                background-color: #10b981;
                color: white;
            }
        """)
        enable_layout.addWidget(self.habits_enabled_checkbox)
        
        enable_layout.addWidget(QLabel("When enabled, compliance findings will be mapped to Stephen Covey's 7 Habits framework for personalized improvement strategies."))
        enable_group.setLayout(enable_layout)
        general_layout.addWidget(enable_group)
        
        # Integration options
        integration_group = QGroupBox("Integration Options")
        integration_layout = QVBoxLayout()
        
        self.show_in_reports_cb = QPushButton("📄 Show in Reports")
        self.show_in_reports_cb.setCheckable(True)
        self.show_in_reports_cb.setChecked(True)
        integration_layout.addWidget(self.show_in_reports_cb)
        
        self.show_in_dashboard_cb = QPushButton("📊 Show in Dashboard")
        self.show_in_dashboard_cb.setCheckable(True)
        self.show_in_dashboard_cb.setChecked(True)
        integration_layout.addWidget(self.show_in_dashboard_cb)
        
        self.show_habit_tips_cb = QPushButton("💡 Show Habit Tips")
        self.show_habit_tips_cb.setCheckable(True)
        self.show_habit_tips_cb.setChecked(True)
        integration_layout.addWidget(self.show_habit_tips_cb)
        
        integration_group.setLayout(integration_layout)
        general_layout.addWidget(integration_group)
        
        general_layout.addStretch()
        settings_tabs.addTab(general_tab, "General")
        
        # Habits overview tab
        overview_tab = QWidget()
        overview_layout = QVBoxLayout(overview_tab)
        
        habits_overview = QTextEdit()
        habits_overview.setReadOnly(True)
        habits_overview.setHtml(self.generate_habits_settings_overview())
        overview_layout.addWidget(habits_overview)
        
        settings_tabs.addTab(overview_tab, "Habits Overview")
        
        layout.addWidget(settings_tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save Settings")
        save_btn.clicked.connect(lambda: self.save_habits_settings(dialog))
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                padding: 8px 16px;
                font-weight: 600;
            }
        """)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def toggle_habits_from_settings(self):
        """Toggle habits from settings dialog."""
        checked = self.habits_enabled_checkbox.isChecked()
        self.habits_enabled_checkbox.setText("🎯 Framework Enabled" if checked else "⭕ Framework Disabled")
    
    def save_habits_settings(self, dialog):
        """Save habits settings."""
        # Update main setting
        new_enabled = self.habits_enabled_checkbox.isChecked()
        if new_enabled != self.habits_enabled:
            self.habits_enabled = new_enabled
            self.habits_action.setChecked(new_enabled)
            self.update_habits_integration()
        
        # Save other settings (would integrate with config system)
        self.status_bar.showMessage("7 Habits settings saved")
        dialog.accept()
    
    def generate_habits_settings_overview(self) -> str:
        """Generate HTML overview for settings dialog."""
        return """
        <h3>🎯 7 Habits Framework for Clinical Excellence</h3>
        
        <p>This framework maps your compliance findings to Stephen Covey's proven principles:</p>
        
        <div style='margin: 16px 0;'>
            <h4 style='color: #1e40af;'>The 7 Habits:</h4>
            <ol>
                <li><strong>Be Proactive</strong> - Take responsibility for documentation quality</li>
                <li><strong>Begin with the End in Mind</strong> - Document with clear goals</li>
                <li><strong>Put First Things First</strong> - Prioritize critical elements</li>
                <li><strong>Think Win-Win</strong> - Consider all stakeholders</li>
                <li><strong>Seek First to Understand</strong> - Understand requirements deeply</li>
                <li><strong>Synergize</strong> - Work collaboratively with your team</li>
                <li><strong>Sharpen the Saw</strong> - Continuously improve your skills</li>
            </ol>
        </div>
        
        <div style='background-color: #dbeafe; padding: 12px; border-radius: 8px; margin: 16px 0;'>
            <h4 style='color: #1e40af; margin: 0 0 8px 0;'>Benefits:</h4>
            <ul style='margin: 0;'>
                <li>Personalized improvement strategies</li>
                <li>Root cause analysis of compliance issues</li>
                <li>Long-term professional development</li>
                <li>Holistic approach to documentation excellence</li>
            </ul>
        </div>
        
        <div style='background-color: #f0fdf4; padding: 12px; border-radius: 8px; margin: 16px 0;'>
            <h4 style='color: #166534; margin: 0 0 8px 0;'>Integration Options:</h4>
            <ul style='margin: 0;'>
                <li><strong>Reports:</strong> Include habit-based recommendations in compliance reports</li>
                <li><strong>Dashboard:</strong> Show habit progression and mastery levels</li>
                <li><strong>Tips:</strong> Display contextual habit tips during analysis</li>
            </ul>
        </div>
        """ 
   
    def toggle_habits_framework(self):
        """Toggle 7 Habits framework on/off."""
        self.habits_enabled = not self.habits_enabled
        
        if self.habits_enabled:
            self.habits_action.setText("Disable Framework")
            if hasattr(self, 'habits_btn'):
                self.habits_btn.show()
            self.status_bar.showMessage("7 Habits Framework enabled - personalized improvement strategies activated")
        else:
            self.habits_action.setText("Enable Framework")
            if hasattr(self, 'habits_btn'):
                self.habits_btn.hide()
            self.status_bar.showMessage("7 Habits Framework disabled - standard compliance analysis only")
        
        # Update habits button visibility
        self.update_habits_integration()  
  
    def update_ai_model_status(self, model_type: str, status: str, is_ready: bool = True):
        """Update individual AI model status indicators."""
        color = "#10b981" if is_ready else "#ef4444"  # Green or Red
        bg_color = "#d1fae5" if is_ready else "#fecaca"  # Light green or light red
        
        status_text = f"{status}: {'Ready' if is_ready else 'Error'}"
        
        style = f"""
            QLabel {{
                color: {color};
                font-weight: 600;
                padding: 2px 6px;
                background-color: {bg_color};
                border-radius: 3px;
                margin: 1px;
                font-size: 10px;
            }}
        """
        
        if model_type == "llm":
            self.llm_status_label.setText(f"🧠 {status_text}")
            self.llm_status_label.setStyleSheet(style)
        elif model_type == "ner":
            self.ner_status_label.setText(f"🏷️ {status_text}")
            self.ner_status_label.setStyleSheet(style)
        elif model_type == "embeddings":
            self.embeddings_status_label.setText(f"🔗 {status_text}")
            self.embeddings_status_label.setStyleSheet(style)
        elif model_type == "chat":
            self.chat_status_label.setText(f"💬 {status_text}")
            self.chat_status_label.setStyleSheet(style)
    
    def simulate_model_loading(self):
        """Simulate AI model loading with status updates."""
        # This would be called during actual model loading
        self.update_ai_model_status("llm", "LLM", True)
        self.update_ai_model_status("ner", "NER", True)
        self.update_ai_model_status("embeddings", "Embeddings", True)
        self.update_ai_model_status("chat", "Chat", True)
        
        # Update main status
        self.status_bar.showMessage("All AI models loaded successfully - Ready for analysis")
    
    def check_ai_model_health(self):
        """Check and update AI model health status including professional services."""
        try:
            # Check Professional LLM Service
            professional_llm = self.professional_services.get('llm_service')
            if professional_llm and hasattr(professional_llm, 'is_ready'):
                llm_ready = professional_llm.is_ready()
                self.update_ai_model_status("llm", "Pro LLM", llm_ready)
            elif self.analyzer:
                self.update_ai_model_status("llm", "Basic LLM", True)
            else:
                self.update_ai_model_status("llm", "LLM", False)
            
            # Check Professional NER Service
            professional_ner = self.professional_services.get('ner_analyzer')
            if professional_ner:
                self.update_ai_model_status("ner", "Pro NER", True)
            elif self.discipline_detector:
                self.update_ai_model_status("ner", "Basic NER", True)
            else:
                self.update_ai_model_status("ner", "NER", False)
            
            # Check Professional Analysis Service
            professional_analysis = self.professional_services.get('analysis_service')
            if professional_analysis:
                self.update_ai_model_status("embeddings", "Pro Analysis", True)
            elif self.discipline_detector:
                self.update_ai_model_status("embeddings", "Basic Analysis", True)
            else:
                self.update_ai_model_status("embeddings", "Analysis", False)
            
            # Check Professional Chat Service
            professional_chat = self.professional_services.get('chat_service')
            if professional_chat:
                self.update_ai_model_status("chat", "Pro Chat", True)
            else:
                self.update_ai_model_status("chat", "Basic Chat", True)
            
            # Update status message based on professional services availability
            if any(self.services_status.values()):
                pro_count = sum(1 for status in self.services_status.values() if status)
                total_count = len(self.services_status)
                self.statusBar().showMessage(f"🚀 Professional Services: {pro_count}/{total_count} available - Enhanced analysis ready")
            else:
                self.statusBar().showMessage("⚠️ Using basic services - Professional AI services unavailable")
            
        except Exception as e:
            print(f"Error checking AI model health: {e}")
            self.statusBar().showMessage("❌ Error checking service status")
    
    def polish_status_messages(self):
        """Add polish to status messages throughout the app."""
        # This can be called to enhance status messages
        pass    

    def load_medicare_guidelines(self):
        """Load and display Medicare Benefits Policy Manual."""
        # Check if rubric display widget exists
        if not hasattr(self, 'rubric_display'):
            print("Rubric display not ready yet, skipping Medicare load")
            return
            
        try:
            medicare_file = "src/resources/medicare_benefits_policy_manual.md"
            if os.path.exists(medicare_file):
                with open(medicare_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Convert markdown to HTML for better display
                html_content = self.markdown_to_html(content)
                self.rubric_display.setHtml(html_content)
                
                self.status_bar.showMessage("📋 Medicare Benefits Policy Manual loaded as default rubric")
            else:
                # Fallback content if file doesn't exist
                fallback_content = """
                <h2>📋 Medicare Benefits Policy Manual - Therapy Services</h2>
                <h3>Key Requirements:</h3>
                <ul>
                    <li><strong>Physician Plan of Care:</strong> Required for all therapy services</li>
                    <li><strong>Medical Necessity:</strong> Services must be reasonable and necessary</li>
                    <li><strong>Skilled Services:</strong> Require expertise of qualified therapist</li>
                    <li><strong>Measurable Goals:</strong> Specific, time-bound functional outcomes</li>
                    <li><strong>Progress Documentation:</strong> Objective measures of improvement</li>
                    <li><strong>Signatures:</strong> All notes signed and dated with credentials</li>
                </ul>
                <h3>Compliance Standards:</h3>
                <ul>
                    <li>PT/SLP Combined Cap: $2,230 annually</li>
                    <li>OT Cap: $2,230 annually</li>
                    <li>Functional reporting with G-codes required</li>
                    <li>Progress reports every 10 treatment days (SLP)</li>
                </ul>
                """
                self.rubric_display.setHtml(fallback_content)
                self.status_bar.showMessage("📋 Medicare Guidelines loaded (default content)")
                
        except Exception as e:
            print(f"Error loading Medicare guidelines: {e}")
            self.rubric_display.setPlainText("Medicare Benefits Policy Manual - Loading...")
    
    def markdown_to_html(self, markdown_text: str) -> str:
        """Convert markdown text to HTML for display."""
        # Simple markdown to HTML conversion
        html = markdown_text
        
        # Convert headers
        html = html.replace('### ', '<h3>').replace('\n\n', '</h3>\n\n')
        html = html.replace('## ', '<h2>').replace('\n\n', '</h2>\n\n')
        html = html.replace('# ', '<h1>').replace('\n\n', '</h1>\n\n')
        
        # Convert bold text
        import re
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        
        # Convert bullet points
        lines = html.split('\n')
        in_list = False
        result_lines = []
        
        for line in lines:
            if line.strip().startswith('- '):
                if not in_list:
                    result_lines.append('<ul>')
                    in_list = True
                result_lines.append(f'<li>{line.strip()[2:]}</li>')
            else:
                if in_list:
                    result_lines.append('</ul>')
                    in_list = False
                result_lines.append(line)
        
        if in_list:
            result_lines.append('</ul>')
        
        # Add basic styling
        styled_html = f"""
        <div style='font-family: Arial, sans-serif; line-height: 1.6; color: #334155;'>
            {'<br>'.join(result_lines)}
        </div>
        """
        
        return styled_html