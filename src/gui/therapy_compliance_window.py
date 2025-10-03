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
    QToolButton, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QColor, QAction, QFont

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
        
        # Calculate score
        total_possible = sum(r["financial_impact"] for r in rules.values())
        score = max(0, 100 - (total_impact / total_possible * 100)) if total_possible > 0 else 100
        
        return {
            "findings": findings,
            "compliance_score": round(score, 1),
            "total_financial_impact": total_impact,
            "discipline": discipline.upper()
        }
    
    def check_rule(self, text_lower: str, rule_id: str, rule: Dict) -> Optional[Dict]:
        """Check a specific compliance rule."""
        if "positive_keywords" in rule and "negative_keywords" in rule:
            has_positive = any(kw in text_lower for kw in rule["positive_keywords"])
            has_negative = any(kw in text_lower for kw in rule["negative_keywords"])
            
            if has_positive and not has_negative:
                return {
                    "rule_id": rule_id,
                    "title": rule["title"],
                    "severity": rule["severity"],
                    "financial_impact": rule["financial_impact"],
                    "suggestion": rule["suggestion"]
                }
        else:
            keywords = rule.get("keywords", [])
            missing = [kw for kw in keywords if kw not in text_lower]
            
            if len(missing) == len(keywords):
                return {
                    "rule_id": rule_id,
                    "title": rule["title"],
                    "severity": rule["severity"],
                    "financial_impact": rule["financial_impact"],
                    "suggestion": rule["suggestion"]
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
        self.setGeometry(100, 100, 1600, 1000)
        
        # Initialize
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
        
        # Apply stylesheet
        self.setStyleSheet(MAIN_STYLESHEET)
        
        self.setup_ui()
    
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
        
        # Header
        header = QLabel("🏥 Therapy Compliance Analyzer")
        header.setObjectName("headerLabel")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e40af, stop:1 #3b82f6);
                color: white;
                padding: 20px;
                font-size: 28px;
                font-weight: 700;
                border-bottom: 3px solid #2563eb;
            }
        """)
        main_layout.addWidget(header)
        
        # Subtitle
        subtitle = QLabel("Physical Therapy • Occupational Therapy • Speech-Language Pathology")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                background-color: #dbeafe;
                color: #1e40af;
                padding: 8px;
                font-size: 13px;
                font-weight: 600;
                border-bottom: 1px solid #93c5fd;
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
        
        self.status_bar.showMessage("Ready - Select discipline and upload documentation")
    
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
        
        # Left: Rubric Management
        rubric_group = QGroupBox("📚 Compliance Rubric")
        rubric_layout = QVBoxLayout()
        
        # Discipline selector with auto-detect
        discipline_layout = QHBoxLayout()
        discipline_layout.addWidget(QLabel("Discipline:"))
        self.discipline_combo = QComboBox()
        self.discipline_combo.addItems([
            "🔍 Auto-Detect",
            "📋 Medicare Guidelines (All)",
            "Physical Therapy (PT)", 
            "Occupational Therapy (OT)", 
            "Speech-Language Pathology (SLP)",
            "Multi-Discipline (All)"
        ])
        self.discipline_combo.currentIndexChanged.connect(self.on_discipline_changed)
        discipline_layout.addWidget(self.discipline_combo)
        
        # Auto-detect button
        self.auto_detect_btn = QPushButton("🔍 Detect Now")
        self.auto_detect_btn.clicked.connect(self.auto_detect_discipline)
        self.auto_detect_btn.setToolTip("Automatically detect discipline from document")
        discipline_layout.addWidget(self.auto_detect_btn)
        rubric_layout.addLayout(discipline_layout)
        
        # Detection result label
        self.detection_label = QLabel("")
        self.detection_label.setStyleSheet("color: #10b981; font-weight: 600; padding: 4px;")
        rubric_layout.addWidget(self.detection_label)
        
        # Rubric display
        self.rubric_display = QTextEdit()
        self.rubric_display.setMaximumHeight(120)
        self.rubric_display.setPlaceholderText("Selected rubric details will appear here...")
        self.rubric_display.setReadOnly(True)
        rubric_layout.addWidget(self.rubric_display)
        
        # Rubric buttons
        rubric_btn_layout = QHBoxLayout()
        self.upload_rubric_btn = QPushButton("📤 Upload Rubric")
        self.upload_rubric_btn.clicked.connect(self.upload_rubric)
        rubric_btn_layout.addWidget(self.upload_rubric_btn)
        
        self.preview_rubric_btn = QPushButton("👁️ Preview Rubric")
        self.preview_rubric_btn.clicked.connect(self.preview_rubric)
        rubric_btn_layout.addWidget(self.preview_rubric_btn)
        
        self.clear_rubric_btn = QPushButton("🗑️ Clear")
        self.clear_rubric_btn.clicked.connect(self.clear_rubric)
        rubric_btn_layout.addWidget(self.clear_rubric_btn)
        rubric_layout.addLayout(rubric_btn_layout)
        
        rubric_group.setLayout(rubric_layout)
        top_splitter.addWidget(rubric_group)
        
        # Right: Upload Controls
        upload_group = QGroupBox("📄 Document Upload")
        upload_layout = QVBoxLayout()
        
        # Upload buttons
        upload_btn_layout = QHBoxLayout()
        self.upload_btn = QPushButton("📄 Upload Document")
        self.upload_btn.clicked.connect(self.upload_document)
        upload_btn_layout.addWidget(self.upload_btn)
        
        self.upload_folder_btn = QPushButton("📁 Upload Folder")
        self.upload_folder_btn.clicked.connect(self.upload_folder)
        upload_btn_layout.addWidget(self.upload_folder_btn)
        upload_layout.addLayout(upload_btn_layout)
        
        # Selected file info
        self.selected_file_label = QLabel("No document selected")
        self.selected_file_label.setStyleSheet("padding: 8px; background-color: #f1f5f9; border-radius: 4px;")
        upload_layout.addWidget(self.selected_file_label)
        
        # Upload report display
        self.upload_report = QTextEdit()
        self.upload_report.setMaximumHeight(120)
        self.upload_report.setPlaceholderText("Upload report and file details will appear here...")
        self.upload_report.setReadOnly(True)
        upload_layout.addWidget(self.upload_report)
        
        upload_group.setLayout(upload_layout)
        top_splitter.addWidget(upload_group)
        
        top_splitter.setSizes([400, 400])
        layout.addWidget(top_splitter)
        
        # Splitter for document and results
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Document view
        doc_group = QGroupBox("📄 Document")
        doc_layout = QVBoxLayout()
        self.document_text = QTextEdit()
        self.document_text.setPlaceholderText("Upload a document or paste your documentation here...")
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
        
        splitter.setSizes([800, 800])
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
        
        # Send button
        send_btn = QPushButton("📤 Send Message")
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
            self.status_bar.showMessage("Auto-detect mode enabled")
        elif index == 4:
            self.status_bar.showMessage("Multi-discipline analysis mode")
        else:
            disciplines = ["PT", "OT", "SLP"]
            discipline = disciplines[index - 1]  # Adjust for auto-detect option
            self.status_bar.showMessage(f"Selected discipline: {discipline}")
    
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
            discipline_map = {'PT': 1, 'OT': 2, 'SLP': 3}
            if result.primary_discipline in discipline_map:
                self.discipline_combo.setCurrentIndex(discipline_map[result.primary_discipline])
        elif result.is_multi_discipline:
            self.discipline_combo.setCurrentIndex(4)  # Multi-discipline
        
        # Store detected disciplines
        self.detected_disciplines = result.detected_disciplines
        
        # Show detailed report
        detailed = self.discipline_detector.get_detailed_report(result)
        QMessageBox.information(self, "Discipline Detection Results", detailed)
        
        self.status_bar.showMessage(f"Detection complete: {summary}")
    
    def upload_document(self):
        """Upload a single document."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Document", "", 
            "All Files (*);;Text Files (*.txt);;PDF Files (*.pdf);;Word Files (*.docx)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.document_text.setPlainText(content)
                
                # Update file info
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                word_count = len(content.split())
                char_count = len(content)
                
                self.selected_file_label.setText(f"📄 {file_name}")
                
                # Update upload report
                upload_info = f"""📄 File: {file_name}
📊 Size: {file_size:,} bytes
📝 Words: {word_count:,}
🔤 Characters: {char_count:,}
✅ Status: Successfully loaded
📅 Uploaded: {QLabel().text()}"""
                
                self.upload_report.setPlainText(upload_info)
                self.status_bar.showMessage(f"Loaded: {file_name}")
                
                # Auto-detect discipline if set to auto
                if self.discipline_combo.currentIndex() == 0:  # Auto-Detect
                    self.auto_detect_discipline()
                    
            except Exception as e:
                error_info = f"❌ Error loading file: {str(e)}"
                self.upload_report.setPlainText(error_info)
                QMessageBox.warning(self, "Error", f"Could not load file: {e}")
    
    def upload_folder(self):
        """Upload a folder of documents."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.status_bar.showMessage(f"Selected folder: {folder_path}")
            QMessageBox.information(self, "Folder Upload", 
                f"Folder selected: {folder_path}\nBatch analysis feature coming soon!")
    
    def run_analysis(self):
        """Run compliance analysis."""
        text = self.document_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "No Document", "Please upload or paste documentation first.")
            return
        
        # Get discipline
        index = self.discipline_combo.currentIndex()
        
        if index == 0:  # Auto-Detect
            # Auto-detect first
            if self.discipline_detector:
                result = self.discipline_detector.detect_disciplines(text)
                if result.primary_discipline == 'UNKNOWN':
                    QMessageBox.warning(self, "Detection Failed", 
                        "Could not automatically detect discipline. Please select manually.")
                    return
                elif result.is_multi_discipline:
                    # Run analysis for all detected disciplines
                    self.run_multi_discipline_analysis(text, result.detected_disciplines)
                    return
                else:
                    discipline = result.primary_discipline.lower()
            else:
                QMessageBox.warning(self, "Auto-Detect Unavailable", 
                    "Please select a discipline manually.")
                return
        elif index == 4:  # Multi-Discipline
            # Run for all disciplines
            self.run_multi_discipline_analysis(text, ['PT', 'OT', 'SLP'])
            return
        else:
            discipline_map = {1: "pt", 2: "ot", 3: "slp"}
            discipline = discipline_map[index]
        
        # Show progress
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.analyze_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_bar.showMessage("Running analysis...")
        
        # Start worker
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
        
        # Generate report
        self.generate_report(results)
        
        self.reset_analysis_ui()
        self.status_bar.showMessage(f"Analysis complete - Score: {score}% | {len(findings)} findings | Risk: ${results['total_financial_impact']}")
    
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
        self.current_results = None
        self.status_bar.showMessage("Cleared")
    
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
            return "Pacific Coast Therapy - providing excellent rehabilitation services! 🌊"
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