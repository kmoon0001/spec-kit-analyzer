"""
Therapy Compliance Analyzer - Complete Multi-Discipline Interface
Supports PT, OT, and SLP with full enterprise features
"""

import os
import json
import webbrowser
from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QTextEdit, QComboBox, QSplitter, QTableWidget,
    QTableWidgetItem, QProgressBar, QMenuBar, QMenu, QFileDialog,
    QMessageBox, QGroupBox, QTextBrowser, QHeaderView, QStatusBar,
    QToolButton, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QColor, QAction


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
        self.setWindowTitle("AI Chat Assistant")
        self.resize(600, 500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Chat history
        self.chat_history = QTextBrowser()
        self.chat_history.setStyleSheet("""
            QTextBrowser {
                border: 2px solid #93c5fd;
                border-radius: 8px;
                padding: 10px;
                background-color: white;
            }
        """)
        layout.addWidget(QLabel("💬 Chat History:"))
        layout.addWidget(self.chat_history)
        
        # Input area
        self.chat_input = QTextEdit()
        self.chat_input.setMaximumHeight(100)
        self.chat_input.setPlaceholderText("Ask about compliance, documentation tips, or specific findings...")
        layout.addWidget(QLabel("Your Question:"))
        layout.addWidget(self.chat_input)
        
        # Send button
        send_btn = QPushButton("Send Message")
        send_btn.clicked.connect(self.send_message)
        layout.addWidget(send_btn)
        
        # Welcome message
        self.chat_history.append("<b>AI Assistant:</b> Hello! I can help you with compliance questions, documentation tips, and clarify specific findings. What would you like to know?")
    
    def send_message(self):
        message = self.chat_input.toPlainText().strip()
        if not message:
            return
        
        self.chat_history.append(f"<br><b>You:</b> {message}")
        self.chat_input.clear()
        
        # Simulate AI response (in real app, call LLM service)
        response = self.generate_response(message)
        self.chat_history.append(f"<br><b>AI Assistant:</b> {response}")
    
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
        self.current_document = ""
        self.current_results = None
        self.analysis_worker = None
        self.chat_dialog = None
        self.is_admin = True  # Set based on user role
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the complete user interface."""
        # Menu bar
        self.create_menu_bar()
        
        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create tabs
        self.tabs.addTab(self.create_analysis_tab(), "📋 Analysis")
        self.tabs.addTab(self.create_dashboard_tab(), "📊 Dashboard")
        self.tabs.addTab(self.create_reports_tab(), "📄 Reports")
        
        if self.is_admin:
            self.tabs.addTab(self.create_admin_tab(), "⚙️ Admin")
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
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
        
        # Controls group
        controls = QGroupBox("Analysis Setup")
        controls_layout = QVBoxLayout()
        
        # Discipline selector
        discipline_layout = QHBoxLayout()
        discipline_layout.addWidget(QLabel("Discipline:"))
        self.discipline_combo = QComboBox()
        self.discipline_combo.addItems(["Physical Therapy (PT)", "Occupational Therapy (OT)", "Speech-Language Pathology (SLP)"])
        self.discipline_combo.currentIndexChanged.connect(self.on_discipline_changed)
        discipline_layout.addWidget(self.discipline_combo)
        controls_layout.addLayout(discipline_layout)
        
        # Upload buttons
        upload_layout = QHBoxLayout()
        self.upload_btn = QPushButton("📄 Upload Document")
        self.upload_btn.clicked.connect(self.upload_document)
        upload_layout.addWidget(self.upload_btn)
        
        self.upload_folder_btn = QPushButton("📁 Upload Folder")
        self.upload_folder_btn.clicked.connect(self.upload_folder)
        upload_layout.addWidget(self.upload_folder_btn)
        
        self.selected_file_label = QLabel("No document selected")
        upload_layout.addWidget(self.selected_file_label, 1)
        controls_layout.addLayout(upload_layout)
        
        controls.setLayout(controls_layout)
        layout.addWidget(controls)
        
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
        self.analyze_btn.setStyleSheet("QPushButton { background-color: #2563eb; color: white; padding: 10px; font-weight: bold; }")
        actions_layout.addWidget(self.analyze_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.clicked.connect(self.stop_analysis)
        self.stop_btn.setEnabled(False)
        actions_layout.addWidget(self.stop_btn)
        
        self.chat_btn = QPushButton("💬 AI Chat")
        self.chat_btn.clicked.connect(self.open_chat)
        actions_layout.addWidget(self.chat_btn)
        
        self.export_btn = QPushButton("📥 Export Report")
        self.export_btn.clicked.connect(self.export_pdf)
        actions_layout.addWidget(self.export_btn)
        
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
        disciplines = ["PT", "OT", "SLP"]
        discipline = disciplines[index]
        self.status_bar.showMessage(f"Selected discipline: {discipline}")
    
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
                self.selected_file_label.setText(os.path.basename(file_path))
                self.status_bar.showMessage(f"Loaded: {os.path.basename(file_path)}")
            except Exception as e:
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
        discipline_map = {0: "pt", 1: "ot", 2: "slp"}
        discipline = discipline_map[self.discipline_combo.currentIndex()]
        
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
            "Therapy Compliance Analyzer\n\n"
            "Version 2.0\n\n"
            "Multi-discipline compliance checking for:\n"
            "• Physical Therapy (PT)\n"
            "• Occupational Therapy (OT)\n"
            "• Speech-Language Pathology (SLP)\n\n"
            "© 2025 All Rights Reserved")
