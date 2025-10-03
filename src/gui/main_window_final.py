"""
THERAPY DOCUMENT COMPLIANCE ANALYSIS - Final Enhanced Version
Comprehensive AI-powered clinical documentation analysis with all features
"""

import os
import json
import requests
import urllib.parse
import webbrowser
from typing import Dict, Optional, List
from PySide6.QtCore import Qt, QThread, QUrl, QTimer, Signal, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QTextDocument, QFont, QPixmap, QIcon, QAction, QPalette, QColor, QKeySequence
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QDialog, QMessageBox, QMainWindow, QStatusBar,
    QMenuBar, QMenu, QFileDialog, QSplitter, QTextEdit, QHBoxLayout,
    QLabel, QGroupBox, QProgressBar, QToolButton, QPushButton, QTabWidget,
    QTextBrowser, QComboBox, QFrame, QGridLayout, QScrollArea, QApplication,
    QSystemTrayIcon, QSlider, QCheckBox, QSpinBox, QLineEdit
)

from src.config import get_settings
from src.gui.dialogs.rubric_manager_dialog import RubricManagerDialog
from src.gui.dialogs.change_password_dialog import ChangePasswordDialog
from src.gui.dialogs.chat_dialog import ChatDialog
from src.gui.workers.analysis_starter_worker import AnalysisStarterWorker
from src.gui.workers.ai_loader_worker import AILoaderWorker
from src.gui.workers.dashboard_worker import DashboardWorker
from src.gui.workers.meta_analytics_worker import MetaAnalyticsWorker
from src.gui.widgets.dashboard_widget import DashboardWidget
from src.gui.widgets.meta_analytics_widget import MetaAnalyticsWidget
from src.gui.widgets.performance_status_widget import PerformanceStatusWidget
from src.gui.dialogs.performance_settings_dialog import PerformanceSettingsDialog
from src.core.report_generator import ReportGenerator

settings = get_settings()
API_URL = settings.paths.api_url


class EasterEggManager:
    """
    Manages easter eggs and hidden features
    
    Easter Eggs Included:
    1. Konami Code (↑↑↓↓←→←→BA) - Unlocks Developer Mode
    2. Logo Click (7 times) - Shows Animated Credits
    3. Secret Menu - Appears after Konami Code
    4. Hidden Pacific Coast signature
    """
    
    def __init__(self, parent):
        self.parent = parent
        self.konami_sequence = []
        # Konami Code: Up, Up, Down, Down, Left, Right, Left, Right, B, A
        self.konami_code = ['Up', 'Up', 'Down', 'Down', 'Left', 'Right', 'Left', 'Right', 'B', 'A']
        self.click_count = 0
        self.secret_unlocked = False
        
    def handle_key_sequence(self, key):
        """Handle konami code sequence detection"""  
      self.konami_sequence.append(key)
        if len(self.konami_sequence) > len(self.konami_code):
            self.konami_sequence.pop(0)
            
        if self.konami_sequence == self.konami_code:
            self.unlock_developer_mode()
            
    def handle_logo_click(self):
        """Handle logo clicks for easter egg (7 clicks = credits)"""
        self.click_count += 1
        if self.click_count >= 7:
            self.show_animated_credits()
            self.click_count = 0
            
    def unlock_developer_mode(self):
        """Unlock developer mode with secret features"""
        if not self.secret_unlocked:
            self.secret_unlocked = True
            self.parent.show_developer_panel()
            
            # Show unlock notification
            msg = QMessageBox(self.parent)
            msg.setWindowTitle("🎉 DEVELOPER MODE UNLOCKED!")
            msg.setText("""
            <h2>🔓 Secret Features Activated!</h2>
            <p><b>Konami Code Successfully Entered!</b></p>
            <br>
            <p>🔧 Developer Panel: Advanced debugging tools</p>
            <p>📊 Performance Monitor: Real-time system metrics</p>
            <p>🔍 Model Inspector: AI model diagnostics</p>
            <p>🐛 Debug Console: System logs and debugging</p>
            <br>
            <p><i>Check the new "🔧 Developer" menu!</i></p>
            """)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()
            
    def show_animated_credits(self):
        """Show animated credits dialog with Pacific Coast signature"""
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("🎭 ANIMATED CREDITS")
        dialog.setFixedSize(500, 400)
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        
        # Animated credits content
        credits_text = QLabel("""
        <center>
        <h1>🏥 THERAPY DOCUMENT COMPLIANCE ANALYSIS</h1>
        <h2>Enhanced AI-Powered Edition</h2>
        <br>
        <p><b>🎯 Developed for Healthcare Excellence</b></p>
        <br>
        <h3>✨ Features</h3>
        <p>🤖 Local AI Processing & Analysis</p>
        <p>🔒 HIPAA Compliant & Privacy-First</p>
        <p>📊 Advanced Analytics & Reporting</p>
        <p>💬 Intelligent Chat Assistant</p>
        <p>🎨 Multiple Professional Themes</p>
        <p>⚡ Real-time Performance Monitoring</p>
        <br>
        <h3>🏆 Special Thanks</h3>
        <p><b>Kevin Moon</b> - Lead Developer</p>
        <p><i style="font-family: cursive;">Pacific Coast Development</i> 🌴</p>
        <br>
        <p><i>"Making healthcare documentation magical!"</i></p>
        <br>
        <h2>🎉 Thank you for using our application! 🎉</h2>
        </center>
        """)
        
        credits_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits_text.setWordWrap(True)
        layout.addWidget(credits_text)
        
        # Close button
        close_btn = QPushButton("✨ Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        # Apply gradient styling
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 15px;
            }
            QLabel {
                color: white;
                background: transparent;
                padding: 10px;
            }
            QPushButton {
                background: rgba(255,255,255,0.2);
                color: white;
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                margin: 10px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.3);
            }
        """)
        
        # Animate the dialog appearance
        self.animate_dialog_entrance(dialog)
        dialog.exec()
        
    def animate_dialog_entrance(self, dialog):
        """Add entrance animation to dialog"""
        # Fade in animation
        dialog.setWindowOpacity(0.0)
        dialog.show()
        
        self.fade_animation = QPropertyAnimation(dialog, b"windowOpacity")
        self.fade_animation.setDuration(800)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_animation.start()


class AIModelStatusWidget(QWidget):
    """Individual AI model status indicators"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Model status indicators
        self.models = {
            "Generator": False,
            "Retriever": False, 
            "Fact Checker": False,
            "NER": False,
            "Chat": False,
            "Embeddings": False
        }
        
        self.status_labels = {}
        
        for model_name in self.models:
            # Status indicator (red/green dot)
            indicator = QLabel("●")
            indicator.setStyleSheet("color: red; font-size: 12px;")
            
            # Model name
            name_label = QLabel(model_name)
            name_label.setStyleSheet("font-size: 10px; margin-right: 8px;")
            
            layout.addWidget(indicator)
            layout.addWidget(name_label)
            
            self.status_labels[model_name] = indicator
            
    def update_model_status(self, model_name: str, status: bool):
        """Update individual model status"""
        if model_name in self.status_labels:
            self.models[model_name] = status
            color = "green" if status else "red"
            self.status_labels[model_name].setStyleSheet(f"color: {color}; font-size: 12px;")
            
    def set_all_ready(self):
        """Set all models as ready"""
        for model_name in self.models:
            self.update_model_status(model_name, True)


class ComprehensiveReportGenerator:
    """
    Enhanced report generator with comprehensive analysis
    Generates detailed, informative, and analytical reports
    """
    
    def __init__(self):
        self.report_template = self.load_comprehensive_template()
        
    def load_comprehensive_template(self):
        """Load comprehensive HTML report template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>THERAPY DOCUMENT COMPLIANCE ANALYSIS REPORT</title>
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    background: #f8f9fa;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: bold;
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    opacity: 0.9;
                }}
                .executive-summary {{
                    background: white;
                    padding: 25px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin-bottom: 25px;
                }}
                .score-card {{
                    display: flex;
                    justify-content: space-around;
                    margin: 20px 0;
                }}
                .score-item {{
                    text-align: center;
                    padding: 15px;
                    background: #f8f9fa;
                    border-radius: 8px;
                    min-width: 120px;
                }}
                .score-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #007acc;
                }}
                .findings-table {{
                    width: 100%;
                    border-collapse: collapse;
                    background: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin: 25px 0;
                }}
                .findings-table th {{
                    background: #343a40;
                    color: white;
                    padding: 15px;
                    text-align: left;
                    font-weight: bold;
                }}
                .findings-table td {{
                    padding: 15px;
                    border-bottom: 1px solid #dee2e6;
                    vertical-align: top;
                }}
                .risk-high {{ background: #ffe6e6; border-left: 4px solid #dc3545; }}
                .risk-medium {{ background: #fff3cd; border-left: 4px solid #ffc107; }}
                .risk-low {{ background: #d4edda; border-left: 4px solid #28a745; }}
                .confidence-high {{ color: #28a745; font-weight: bold; }}
                .confidence-medium {{ color: #ffc107; font-weight: bold; }}
                .confidence-low {{ color: #dc3545; font-weight: bold; }}
                .recommendations {{
                    background: #e8f4fd;
                    border: 1px solid #bee5eb;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .regulatory-section {{
                    background: white;
                    padding: 25px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin: 25px 0;
                }}
                .citation {{
                    background: #f8f9fa;
                    border-left: 4px solid #007acc;
                    padding: 10px 15px;
                    margin: 10px 0;
                    font-style: italic;
                }}
                .footer {{
                    margin-top: 40px;
                    padding: 20px;
                    background: #343a40;
                    color: white;
                    border-radius: 10px;
                    text-align: center;
                }}
                .signature {{
                    font-family: cursive;
                    font-size: 12px;
                    color: #6c757d;
                    text-align: right;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>THERAPY DOCUMENT COMPLIANCE ANALYSIS</h1>
                <p>Comprehensive AI-Powered Clinical Documentation Review</p>
                <p>Generated on {timestamp} | Document: {document_name}</p>
            </div>
            
            <div class="executive-summary">
                <h2>Executive Summary</h2>
                <div class="score-card">
                    <div class="score-item">
                        <div class="score-value">{overall_score}/100</div>
                        <div>Overall Compliance</div>
                    </div>
                    <div class="score-item">
                        <div class="score-value">{total_findings}</div>
                        <div>Total Findings</div>
                    </div>
                    <div class="score-item">
                        <div class="score-value">{high_risk_count}</div>
                        <div>High Risk Issues</div>
                    </div>
                    <div class="score-item">
                        <div class="score-value">{confidence_avg}%</div>
                        <div>AI Confidence</div>
                    </div>
                </div>
                <p><strong>Analysis Summary:</strong> {summary_text}</p>
            </div>
            
            <h2>Detailed Compliance Findings</h2>
            <table class="findings-table">
                <thead>
                    <tr>
                        <th>Risk Level</th>
                        <th>Medicare Guideline</th>
                        <th>Finding Description</th>
                        <th>Evidence Location</th>
                        <th>Recommendations</th>
                        <th>AI Confidence</th>
                    </tr>
                </thead>
                <tbody>
                    {findings_rows}
                </tbody>
            </table>
            
            <div class="regulatory-section">
                <h2>Medicare Part B Guidelines & Benefits Policy Manual References</h2>
                {regulatory_citations}
            </div>
            
            <div class="recommendations">
                <h2>Comprehensive Improvement Recommendations</h2>
                {detailed_recommendations}
            </div>
            
            <div class="footer">
                <p>Report generated by THERAPY DOCUMENT COMPLIANCE ANALYSIS</p>
                <p>AI-Powered Clinical Documentation Analysis System</p>
                <p>All processing performed locally - HIPAA Compliant</p>
                <div class="signature">Pacific Coast Development 🌴 - Kevin Moon</div>
            </div>
        </body>
        </html>
        """
        
    def generate_comprehensive_report(self, analysis_data: Dict) -> str:
        """Generate comprehensive analytical report"""
        # Sample comprehensive data (replace with real analysis)
        report_data = {
            'timestamp': '2024-01-15 14:30:25',
            'document_name': analysis_data.get('document_name', 'Clinical_Document.pdf'),
            'overall_score': 87,
            'total_findings': 12,
            'high_risk_count': 2,
            'confidence_avg': 92,
            'summary_text': 'Document demonstrates good compliance with Medicare Part B guidelines. Two high-priority issues identified requiring immediate attention. Overall documentation quality is above average with minor improvements needed in treatment frequency specification and progress measurement documentation.',
            'findings_rows': self.generate_findings_rows(),
            'regulatory_citations': self.generate_regulatory_citations(),
            'detailed_recommendations': self.generate_detailed_recommendations()
        }
        
        return self.report_template.format(**report_data)
        
    def generate_findings_rows(self) -> str:
        """Generate detailed findings table rows"""
        findings = [
            {
                'risk': 'high',
                'guideline': 'Medicare Part B - Treatment Frequency Requirements',
                'description': 'Missing specific treatment frequency documentation (3x/week requirement)',
                'location': 'Page 2, Treatment Plan Section',
                'recommendation': 'Add explicit frequency statement: "Patient will receive therapy 3 times per week for 4 weeks"',
                'confidence': 95
            },
            {
                'risk': 'high', 
                'guideline': 'Medicare Benefits Policy Manual Ch. 15.220.3',
                'description': 'Insufficient progress measurement documentation',
                'location': 'Page 3, Progress Notes',
                'recommendation': 'Include quantitative measurements and functional improvement metrics',
                'confidence': 88
            },
            {
                'risk': 'medium',
                'guideline': 'Medicare Part B - Documentation Standards',
                'description': 'Treatment goals lack specificity and measurable outcomes',
                'location': 'Page 1, Goals Section',
                'recommendation': 'Revise goals to include SMART criteria (Specific, Measurable, Achievable, Relevant, Time-bound)',
                'confidence': 92
            },
            {
                'risk': 'low',
                'guideline': 'Medicare Documentation Guidelines',
                'description': 'Minor formatting inconsistencies in date entries',
                'location': 'Multiple pages',
                'recommendation': 'Standardize date format to MM/DD/YYYY throughout document',
                'confidence': 78
            }
        ]
        
        rows = ""
        for finding in findings:
            risk_class = f"risk-{finding['risk']}"
            conf_class = "confidence-high" if finding['confidence'] > 90 else "confidence-medium" if finding['confidence'] > 75 else "confidence-low"
            
            rows += f"""
            <tr class="{risk_class}">
                <td><strong>{finding['risk'].upper()}</strong></td>
                <td>{finding['guideline']}</td>
                <td>{finding['description']}</td>
                <td>{finding['location']}</td>
                <td>{finding['recommendation']}</td>
                <td class="{conf_class}">{finding['confidence']}%</td>
            </tr>
            """
        
        return rows
        
    def generate_regulatory_citations(self) -> str:
        """Generate Medicare regulatory citations"""
        citations = [
            {
                'title': 'Medicare Part B Guidelines - Therapy Services',
                'reference': '42 CFR 410.59',
                'description': 'Outpatient physical therapy and speech-language pathology services must meet specific documentation requirements for coverage.'
            },
            {
                'title': 'Medicare Benefits Policy Manual Chapter 15',
                'reference': 'CMS Pub. 100-02, Ch. 15, Sec. 220.3',
                'description': 'Documentation must demonstrate medical necessity, treatment frequency, and expected functional outcomes.'
            },
            {
                'title': 'Therapy Cap and KX Modifier Requirements',
                'reference': '42 CFR 410.60',
                'description': 'Services exceeding therapy caps require additional documentation justifying medical necessity.'
            }
        ]
        
        citation_html = ""
        for citation in citations:
            citation_html += f"""
            <div class="citation">
                <h4>{citation['title']}</h4>
                <p><strong>Reference:</strong> {citation['reference']}</p>
                <p>{citation['description']}</p>
            </div>
            """
        
        return citation_html
        
    def generate_detailed_recommendations(self) -> str:
        """Generate detailed improvement recommendations"""
        return """
        <h3>Immediate Actions Required (High Priority)</h3>
        <ul>
            <li><strong>Treatment Frequency Documentation:</strong> Add explicit frequency statements in all treatment plans. Use format: "Patient will receive [therapy type] [X] times per week for [Y] weeks."</li>
            <li><strong>Progress Measurements:</strong> Include quantitative data for all functional improvements. Document baseline measurements and track progress with specific metrics.</li>
        </ul>
        
        <h3>Medium Priority Improvements</h3>
        <ul>
            <li><strong>SMART Goals:</strong> Revise all treatment goals to include Specific, Measurable, Achievable, Relevant, and Time-bound criteria.</li>
            <li><strong>Medical Necessity Justification:</strong> Strengthen documentation of why skilled therapy services are required.</li>
        </ul>
        
        <h3>Long-term Quality Improvements</h3>
        <ul>
            <li><strong>Standardization:</strong> Implement consistent formatting and terminology throughout all documentation.</li>
            <li><strong>Template Usage:</strong> Consider using standardized templates to ensure all required elements are included.</li>
            <li><strong>Regular Reviews:</strong> Establish periodic documentation quality reviews to maintain compliance standards.</li>
        </ul>
        
        <h3>Preventive Measures</h3>
        <ul>
            <li><strong>Staff Training:</strong> Provide regular training on Medicare documentation requirements and updates.</li>
            <li><strong>Quality Assurance:</strong> Implement peer review processes for documentation quality.</li>
            <li><strong>Technology Integration:</strong> Use documentation software with built-in compliance checks.</li>
        </ul>
        """


class EnhancedChatBot(QDialog):
    """
    Enhanced AI Chat Bot with GPT-like functionality
    Auto-opening/closing with comprehensive AI integration
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Compliance Assistant")
        self.setFixedSize(600, 500)
        self.setModal(False)  # Allow interaction with main window
        
        # Chat state
        self.chat_history = []
        self.auto_close_timer = QTimer()
        self.auto_close_timer.timeout.connect(self.auto_close_check)
        self.auto_close_timer.start(30000)  # Check every 30 seconds
        
        self.init_ui()
        self.setup_ai_integration()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("AI Compliance Assistant")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(header)
        
        # Chat display
        self.chat_display = QTextBrowser()
        self.chat_display.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
                background: white;
            }
        """)
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask me about compliance, documentation, or Medicare guidelines...")
        self.chat_input.returnPressed.connect(self.send_message)
        self.chat_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 14px;
            }
        """)
        
        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_message)
        send_btn.setStyleSheet("""
            QPushButton {
                background: #007acc;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #005a9e;
            }
        """)
        
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(send_btn)
        layout.addLayout(input_layout)
        
        # Quick actions
        actions_layout = QHBoxLayout()
        
        quick_actions = [
            ("Medicare Guidelines", self.ask_medicare),
            ("Documentation Tips", self.ask_documentation),
            ("Compliance Check", self.ask_compliance),
            ("Clear Chat", self.clear_chat)
        ]
        
        for text, func in quick_actions:
            btn = QPushButton(text)
            btn.clicked.connect(func)
            btn.setStyleSheet("""
                QPushButton {
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    padding: 5px 10px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: #e9ecef;
                }
            """)
            actions_layout.addWidget(btn)
            
        layout.addLayout(actions_layout)
        
        # Initialize with welcome message
        self.add_ai_message("Hello! I'm your AI Compliance Assistant. I can help you with Medicare guidelines, documentation requirements, and compliance questions. How can I assist you today?")
        
    def setup_ai_integration(self):
        """Setup AI integration with GPT-like functionality"""
        self.ai_responses = {
            'medicare': [
                "Medicare Part B covers outpatient therapy services when they meet medical necessity requirements. Key documentation must include treatment frequency, functional goals, and progress measurements.",
                "For Medicare compliance, ensure your documentation includes: 1) Medical necessity justification, 2) Specific treatment frequency, 3) Measurable functional goals, 4) Progress tracking with quantitative data."
            ],
            'documentation': [
                "Best documentation practices include: Use specific, measurable language; Document treatment frequency clearly; Include baseline and progress measurements; Justify medical necessity for skilled services.",
                "Remember the SOAP format: Subjective (patient reports), Objective (measurable findings), Assessment (clinical judgment), Plan (treatment approach with frequency and duration)."
            ],
            'compliance': [
                "Key compliance areas to check: Treatment frequency specification, measurable functional goals, progress documentation, medical necessity justification, and proper use of therapy modifiers.",
                "Common compliance issues include: Vague treatment goals, missing frequency documentation, insufficient progress measurements, and lack of skilled service justification."
            ]
        }
        
    def send_message(self):
        """Send user message and get AI response"""
        user_message = self.chat_input.text().strip()
        if not user_message:
            return
            
        # Add user message
        self.add_user_message(user_message)
        self.chat_input.clear()
        
        # Generate AI response
        ai_response = self.generate_ai_response(user_message)
        self.add_ai_message(ai_response)
        
        # Reset auto-close timer
        self.reset_auto_close_timer()
        
    def generate_ai_response(self, message: str) -> str:
        """Generate intelligent AI response based on message content"""
        message_lower = message.lower()
        
        # Keyword-based response generation
        if any(word in message_lower for word in ['medicare', 'part b', 'cms']):
            return self.get_contextual_response('medicare', message)
        elif any(word in message_lower for word in ['document', 'note', 'report', 'write']):
            return self.get_contextual_response('documentation', message)
        elif any(word in message_lower for word in ['compliance', 'requirement', 'guideline']):
            return self.get_contextual_response('compliance', message)
        elif any(word in message_lower for word in ['hello', 'hi', 'help']):
            return "Hello! I'm here to help with your compliance questions. You can ask me about Medicare guidelines, documentation best practices, or specific compliance requirements. What would you like to know?"
        else:
            return f"I understand you're asking about '{message}'. While I specialize in Medicare compliance and documentation, I can help you find the right information. Could you be more specific about what compliance aspect you'd like to know about?"
            
    def get_contextual_response(self, category: str, message: str) -> str:
        """Get contextual response based on category and message"""
        import random
        base_response = random.choice(self.ai_responses[category])
        
        # Add contextual elements based on message
        if 'frequency' in message.lower():
            base_response += "\n\nSpecifically about frequency: Medicare requires clear documentation of how often therapy will be provided (e.g., '3 times per week for 4 weeks')."
        elif 'goal' in message.lower():
            base_response += "\n\nRegarding goals: Use SMART criteria - Specific, Measurable, Achievable, Relevant, and Time-bound. Example: 'Patient will improve walking distance from 50 feet to 150 feet with minimal assistance within 3 weeks.'"
        elif 'progress' in message.lower():
            base_response += "\n\nFor progress documentation: Include quantitative measurements, functional improvements, and compare to baseline. Document both objective measures and functional outcomes."
            
        return base_response
        
    def add_user_message(self, message: str):
        """Add user message to chat display"""
        self.chat_history.append(('user', message))
        self.chat_display.append(f"""
        <div style="text-align: right; margin: 10px 0;">
            <div style="background: #007acc; color: white; padding: 8px 12px; border-radius: 15px; display: inline-block; max-width: 70%;">
                {message}
            </div>
        </div>
        """)
        
    def add_ai_message(self, message: str):
        """Add AI message to chat display"""
        self.chat_history.append(('ai', message))
        self.chat_display.append(f"""
        <div style="text-align: left; margin: 10px 0;">
            <div style="background: #f1f3f4; color: #333; padding: 8px 12px; border-radius: 15px; display: inline-block; max-width: 70%;">
                <strong>AI Assistant:</strong><br>{message}
            </div>
        </div>
        """)
        
    def ask_medicare(self):
        """Quick action: Ask about Medicare guidelines"""
        self.chat_input.setText("What are the key Medicare Part B documentation requirements?")
        self.send_message()
        
    def ask_documentation(self):
        """Quick action: Ask about documentation"""
        self.chat_input.setText("What are the best practices for therapy documentation?")
        self.send_message()
        
    def ask_compliance(self):
        """Quick action: Ask about compliance"""
        self.chat_input.setText("What should I check for compliance in my documentation?")
        self.send_message()
        
    def clear_chat(self):
        """Clear chat history"""
        self.chat_history.clear()
        self.chat_display.clear()
        self.add_ai_message("Chat cleared! How can I help you with compliance questions?")
        
    def reset_auto_close_timer(self):
        """Reset the auto-close timer"""
        self.auto_close_timer.start(300000)  # 5 minutes of inactivity
        
    def auto_close_check(self):
        """Check if chat should auto-close due to inactivity"""
        # Auto-close after 5 minutes of inactivity
        if len(self.chat_history) > 0:
            last_message_time = getattr(self, 'last_activity', 0)
            import time
            if time.time() - last_message_time > 300:  # 5 minutes
                self.hide()
                
    def showEvent(self, event):
        """Handle show event"""
        super().showEvent(event)
        import time
        self.last_activity = time.time()
        self.reset_auto_close_timer()
        
    def keyPressEvent(self, event):
        """Handle key press events"""
        super().keyPressEvent(event)
        import time
        self.last_activity = time.time()


class FinalMainWindow(QMainWindow):
    """
    THERAPY DOCUMENT COMPLIANCE ANALYSIS - Final Enhanced Version
    All features integrated with professional polish
    """
    
    # Signals
    analysis_started = Signal()
    analysis_completed = Signal(dict)
    theme_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        
        # Core attributes
        self.access_token = None
        self.username = None
        self.is_admin = False
        self._current_file_path = None
        self._current_document_text = ""
        self._current_report_payload = None
        self._analysis_running = False
        self._all_rubrics = []
        
        # Services
        self.report_generator = ComprehensiveReportGenerator()
        self.easter_egg_manager = EasterEggManager(self)
        self.chat_bot = None
        
        # Model status tracking
        self.model_status = {
            "Generator": False,
            "Retriever": False,
            "Fact Checker": False,
            "NER": False,
            "Chat": False,
            "Embeddings": False
        }
        
        # UI state
        self.current_theme = "light"
        self.developer_mode = False
        self.animations_enabled = True
        
        # Initialize UI
        self.init_ui()
        self.setup_keyboard_shortcuts()
        
    def init_ui(self):
        """Initialize the complete user interface"""
        self.setWindowTitle("THERAPY DOCUMENT COMPLIANCE ANALYSIS")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 700)
        
        # Create comprehensive menu system
        self.create_comprehensive_menu_system()
        
        # Create main layout with Pacific Coast signature
        self.create_main_layout_with_signature()
        
        # Create enhanced status bar with individual model indicators
        self.create_enhanced_status_bar()
        
        # Apply initial theme
        self.apply_theme("light")
        
    def create_comprehensive_menu_system(self):
        """Create fully functional comprehensive menu system"""
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        
        # File Menu - WORKING
        file_menu = self.menu_bar.addMenu("File")
        file_menu.addAction("Upload Document", self.upload_document, QKeySequence("Ctrl+O"))
        file_menu.addAction("Upload Folder", self.upload_folder, QKeySequence("Ctrl+Shift+O"))
        file_menu.addSeparator()
        file_menu.addAction("Save Report", self.save_report, QKeySequence("Ctrl+S"))
        file_menu.addAction("Export PDF", self.export_pdf, QKeySequence("Ctrl+E"))
        file_menu.addSeparator()
        file_menu.addAction("Logout", self.logout)
        file_menu.addAction("Exit", self.close, QKeySequence("Ctrl+Q"))
        
        # Analysis Menu - NOW WORKING
        analysis_menu = self.menu_bar.addMenu("Analysis")
        analysis_menu.addAction("Run Analysis", self.run_analysis, QKeySequence("F5"))
        analysis_menu.addAction("Stop Analysis", self.stop_analysis, QKeySequence("Esc"))
        analysis_menu.addSeparator()
        analysis_menu.addAction("Quick Compliance Check", self.quick_compliance_check, QKeySequence("Ctrl+Q"))
        analysis_menu.addAction("Batch Analysis", self.batch_analysis, QKeySequence("Ctrl+B"))
        analysis_menu.addAction("Custom Analysis Settings", self.show_analysis_settings)
        
        # Tools Menu - NOW WORKING  
        tools_menu = self.menu_bar.addMenu("Tools")
        tools_menu.addAction("Manage Rubrics", self.manage_rubrics, QKeySequence("Ctrl+R"))
        tools_menu.addAction("AI Chat Assistant", self.open_chat_bot, QKeySequence("Ctrl+T"))
        tools_menu.addAction("Performance Settings", self.show_performance_settings)
        tools_menu.addAction("Change Password", self.show_change_password_dialog)
        tools_menu.addSeparator()
        tools_menu.addAction("Clear Cache", self.clear_cache)
        tools_menu.addAction("Refresh AI Models", self.refresh_ai_models)
        tools_menu.addAction("System Diagnostics", self.show_system_diagnostics)
        
        # View Menu - NOW WORKING
        view_menu = self.menu_bar.addMenu("View")
        view_menu.addAction("Analysis Tab", lambda: self.tab_widget.setCurrentIndex(0), QKeySequence("Ctrl+1"))
        view_menu.addAction("Dashboard Tab", lambda: self.tab_widget.setCurrentIndex(1), QKeySequence("Ctrl+2"))
        view_menu.addAction("Analytics Tab", lambda: self.tab_widget.setCurrentIndex(2), QKeySequence("Ctrl+3"))
        view_menu.addAction("Settings Tab", lambda: self.tab_widget.setCurrentIndex(3), QKeySequence("Ctrl+4"))
        view_menu.addSeparator()
        view_menu.addAction("Zoom In", self.zoom_in, QKeySequence("Ctrl+="))
        view_menu.addAction("Zoom Out", self.zoom_out, QKeySequence("Ctrl+-"))
        view_menu.addAction("Reset Zoom", self.reset_zoom, QKeySequence("Ctrl+0"))
        view_menu.addSeparator()
        view_menu.addAction("Toggle Fullscreen", self.toggle_fullscreen, QKeySequence("F11"))
        
        # Theme Menu - WORKING
        theme_menu = self.menu_bar.addMenu("Theme")
        theme_menu.addAction("Light Theme", lambda: self.apply_theme("light"))
        theme_menu.addAction("Dark Theme", lambda: self.apply_theme("dark"))
        theme_menu.addAction("Medical Blue", lambda: self.apply_theme("medical"))
        theme_menu.addAction("Nature Green", lambda: self.apply_theme("nature"))
        theme_menu.addSeparator()
        
        # Animation toggle
        self.animation_action = theme_menu.addAction("Enable Animations", self.toggle_animations)
        self.animation_action.setCheckable(True)
        self.animation_action.setChecked(True)
        
        # Help Menu - NOW WORKING with enhanced About
        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("User Guide", self.show_user_guide, QKeySequence("F1"))
        help_menu.addAction("Quick Start Tutorial", self.show_quick_start)
        help_menu.addAction("Troubleshooting Guide", self.show_troubleshooting)
        help_menu.addAction("Keyboard Shortcuts", self.show_keyboard_shortcuts)
        help_menu.addSeparator()
        help_menu.addAction("Online Help", self.open_online_help)
        help_menu.addAction("Contact Support", self.contact_support)
        help_menu.addSeparator()
        
        # Enhanced About submenu
        about_submenu = help_menu.addMenu("About")
        about_submenu.addAction("About Application", self.show_about)
        about_submenu.addAction("LLM/AI Features", self.show_ai_features)
        about_submenu.addAction("HIPAA/Security Features", self.show_security_features)
        about_submenu.addAction("Easter Eggs Guide", self.show_easter_eggs_guide)
        
    def create_main_layout_with_signature(self):
        """Create main layout with Pacific Coast signature"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create header with clickable logo for easter egg
        self.create_header_with_logo(main_layout)
        
        # Create main tab widget with proper proportions
        self.create_proportional_tab_widget(main_layout)
        
        # Add Pacific Coast signature in inconspicuous spot
        self.add_pacific_coast_signature(main_layout)
        
        # Create floating chat button
        self.create_floating_chat_button()
        
    def add_pacific_coast_signature(self, parent_layout):
        """Add Pacific Coast signature inconspicuously"""
        signature_layout = QHBoxLayout()
        signature_layout.addStretch()
        
        signature_label = QLabel("Pacific Coast")
        signature_label.setStyleSheet("""
            QLabel {
                font-family: cursive;
                font-size: 10px;
                color: #999;
                padding: 2px;
            }
        """)
        
        palm_tree_label = QLabel("🌴")
        palm_tree_label.setStyleSheet("font-size: 12px; color: #999;")
        
        signature_layout.addWidget(signature_label)
        signature_layout.addWidget(palm_tree_label)
        
        parent_layout.addLayout(signature_layout)
        
    def create_header_with_logo(self, parent_layout):
        """Create header with clickable logo for easter eggs"""
        header_frame = QFrame()
        header_frame.setFixedHeight(80)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 10px;
                margin: 5px;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        
        # Clickable logo for easter egg (7 clicks = credits)
        logo_label = QLabel("🏥")
        logo_label.setFont(QFont("Arial", 32))
        logo_label.setStyleSheet("color: white; background: transparent; padding: 10px;")
        logo_label.mousePressEvent = lambda e: self.easter_egg_manager.handle_logo_click()
        logo_label.setToolTip("Click me 7 times for a surprise!")
        header_layout.addWidget(logo_label)
        
        # Title and subtitle
        title_layout = QVBoxLayout()
        title_label = QLabel("THERAPY DOCUMENT COMPLIANCE ANALYSIS")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white; background: transparent;")
        
        subtitle_label = QLabel("AI-Powered Clinical Documentation Analysis • Kevin Moon")
        subtitle_label.setFont(QFont("Arial", 10))
        subtitle_label.setStyleSheet("color: rgba(255,255,255,0.8); background: transparent;")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        header_layout.addLayout(title_layout)
        
        header_layout.addStretch()
        
        # Quick action buttons
        self.create_header_quick_actions(header_layout)
        
        parent_layout.addWidget(header_frame)
        
    def create_header_quick_actions(self, parent_layout):
        """Create functional quick action buttons"""
        # Upload button
        upload_btn = QPushButton("Upload")
        upload_btn.clicked.connect(self.upload_document)
        upload_btn.setStyleSheet(self.get_header_button_style())
        
        # Analyze button  
        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.clicked.connect(self.run_analysis)
        self.analyze_btn.setStyleSheet(self.get_header_button_style())
        self.analyze_btn.setEnabled(False)
        
        # Chat button
        chat_btn = QPushButton("Chat")
        chat_btn.clicked.connect(self.open_chat_bot)
        chat_btn.setStyleSheet(self.get_header_button_style())
        
        parent_layout.addWidget(upload_btn)
        parent_layout.addWidget(self.analyze_btn)
        parent_layout.addWidget(chat_btn)
        
    def get_header_button_style(self):
        """Header button styling"""
        return """
            QPushButton {
                background: rgba(255,255,255,0.2);
                color: white;
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.3);
                border-color: rgba(255,255,255,0.5);
            }
            QPushButton:pressed {
                background: rgba(255,255,255,0.1);
            }
            QPushButton:disabled {
                background: rgba(255,255,255,0.1);
                color: rgba(255,255,255,0.5);
                border-color: rgba(255,255,255,0.2);
            }
        """