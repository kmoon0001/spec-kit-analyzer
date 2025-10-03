"""
TherapySide - Multi-Discipline Therapy Compliance Analyzer
Supports PT (Physical Therapy), OT (Occupational Therapy), and SLP (Speech-Language Pathology)
"""

import sys
import os
import re
from typing import Dict

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QTextEdit, QPushButton, QLabel, QSplitter, QFrame, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor


class PTComplianceAnalyzer:
    """PT-specific compliance analyzer based on Medicare Part B requirements."""
    
    def __init__(self):
        # PT-specific compliance rules based on the TTL rubric
        self.pt_rules = {
            "signature_date": {
                "title": "Provider signature/date possibly missing",
                "keywords": ["signature", "signed", "dated", "therapist:", "pt:", "by:"],
                "severity": "HIGH",
                "financial_impact": 50,
                "suggestion": "Ensure all notes are signed and dated by the treating therapist with credentials."
            },
            "measurable_goals": {
                "title": "Goals may not be measurable/time-bound",
                "positive_keywords": ["goal", "objective", "target"],
                "negative_keywords": ["measurable", "time", "timed", "weeks", "days", "by", "within"],
                "severity": "MEDIUM",
                "financial_impact": 50,
                "suggestion": "Make goals SMART: Specific, Measurable, Achievable, Relevant, Time-bound. Example: 'Patient will increase right knee extension strength from 3/5 to 4/5 within 2 weeks to improve ambulation'."
            },
            "medical_necessity": {
                "title": "Medical necessity not explicitly supported",
                "keywords": ["medical necessity", "reasonable and necessary", "necessity", "functional limitation", "skilled therapy"],
                "severity": "HIGH",
                "financial_impact": 50,
                "suggestion": "Document how interventions address functional limitations and tie to Medicare Part B coverage criteria."
            },
            "assistant_supervision": {
                "title": "Assistant supervision context unclear",
                "positive_keywords": ["assistant", "aide", "pta", "cota"],
                "negative_keywords": ["supervis", "oversight", "under direction"],
                "severity": "MEDIUM",
                "financial_impact": 25,
                "suggestion": "When assistants provide services, document appropriate supervision per Medicare and state requirements."
            },
            "plan_of_care": {
                "title": "Plan/Certification not clearly referenced",
                "keywords": ["plan of care", "poc", "certification", "recert", "physician order", "referral"],
                "severity": "HIGH",
                "financial_impact": 50,
                "suggestion": "Reference the plan of care, certification dates, and physician orders that authorize therapy services."
            },
            "skilled_services": {
                "title": "Skilled therapy services not documented",
                "keywords": ["skilled", "therapeutic exercise", "manual therapy", "gait training", "balance training", "neuromuscular re-education"],
                "severity": "HIGH",
                "financial_impact": 75,
                "suggestion": "Document specific skilled interventions that require PT expertise and cannot be performed by non-skilled personnel."
            },
            "progress_documentation": {
                "title": "Progress toward goals not documented",
                "keywords": ["progress", "improvement", "decline", "status", "response to treatment"],
                "severity": "MEDIUM",
                "financial_impact": 40,
                "suggestion": "Document patient's response to treatment and progress (or lack thereof) toward established goals."
            }
        }
        
        # PT-specific clinical patterns
        self.pt_patterns = {
            "pt_credentials": re.compile(r"\b(?:PT|DPT|Physical Therapist)\b", re.IGNORECASE),
            "pt_interventions": re.compile(r"\b(?:therapeutic exercise|manual therapy|gait training|balance|strengthening|ROM|range of motion|mobilization)\b", re.IGNORECASE),
            "measurements": re.compile(r"\b\d+(?:/\d+)?\s*(?:degrees?|°|reps?|sets?|minutes?|feet|meters|lbs?|kg)\b", re.IGNORECASE),
            "functional_terms": re.compile(r"\b(?:ADL|activities of daily living|ambulation|transfers|mobility|functional)\b", re.IGNORECASE)
        }
    
    def analyze_pt_compliance(self, text: str) -> Dict:
        """Analyze PT documentation for compliance issues."""
        findings = []
        total_financial_impact = 0
        
        text_lower = text.lower()
        
        for rule_id, rule in self.pt_rules.items():
            finding = self._check_rule(text_lower, rule_id, rule)
            if finding:
                findings.append(finding)
                total_financial_impact += finding.get("financial_impact", 0)
        
        # Calculate compliance score
        total_possible_impact = sum(rule["financial_impact"] for rule in self.pt_rules.values())
        compliance_score = max(0, 100 - (total_financial_impact / total_possible_impact * 100))
        
        return {
            "findings": findings,
            "compliance_score": round(compliance_score, 1),
            "total_financial_impact": total_financial_impact,
            "pt_specific_analysis": self._analyze_pt_specifics(text)
        }
    
    def _check_rule(self, text_lower: str, rule_id: str, rule: Dict) -> Dict:
        """Check a specific compliance rule."""
        if "positive_keywords" in rule and "negative_keywords" in rule:
            # Rule requires positive keywords present AND negative keywords missing
            has_positive = any(keyword in text_lower for keyword in rule["positive_keywords"])
            has_negative = any(keyword in text_lower for keyword in rule["negative_keywords"])
            
            if has_positive and not has_negative:
                return {
                    "rule_id": rule_id,
                    "title": rule["title"],
                    "severity": rule["severity"],
                    "financial_impact": rule["financial_impact"],
                    "suggestion": rule["suggestion"],
                    "evidence": f"Found: {[kw for kw in rule['positive_keywords'] if kw in text_lower]}, Missing: {rule['negative_keywords']}"
                }
        else:
            # Rule checks for missing keywords
            keywords = rule.get("keywords", [])
            missing_keywords = [kw for kw in keywords if kw not in text_lower]
            
            if len(missing_keywords) == len(keywords):  # All keywords missing
                return {
                    "rule_id": rule_id,
                    "title": rule["title"],
                    "severity": rule["severity"],
                    "financial_impact": rule["financial_impact"],
                    "suggestion": rule["suggestion"],
                    "evidence": f"Missing all required keywords: {keywords}"
                }
        
        return None
    
    def _analyze_pt_specifics(self, text: str) -> Dict:
        """Analyze PT-specific elements in the documentation."""
        analysis = {
            "pt_credentials_found": bool(self.pt_patterns["pt_credentials"].search(text)),
            "pt_interventions_count": len(self.pt_patterns["pt_interventions"].findall(text)),
            "measurements_count": len(self.pt_patterns["measurements"].findall(text)),
            "functional_terms_count": len(self.pt_patterns["functional_terms"].findall(text)),
            "interventions_found": self.pt_patterns["pt_interventions"].findall(text)[:5],  # First 5
            "measurements_found": self.pt_patterns["measurements"].findall(text)[:5]  # First 5
        }
        return analysis


class PTsideWindow(QMainWindow):
    """Main window for PTside application."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PTside - Physical Therapy Compliance Analyzer")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize PT analyzer
        self.pt_analyzer = PTComplianceAnalyzer()
        
        # Set up UI
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the PT-specific user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with PT branding
        header = QLabel("🏃‍♂️ PTside - Physical Therapy Compliance Analyzer")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                font-size: 26px;
                font-weight: bold;
                color: #1e3a8a;
                padding: 20px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 #dbeafe, stop:1 #bfdbfe);
                border-radius: 12px;
                margin-bottom: 20px;
                border: 2px solid #3b82f6;
            }
        """)
        main_layout.addWidget(header)
        
        # Create tab widget
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Analysis tab
        analysis_tab = self.create_analysis_tab()
        tab_widget.addTab(analysis_tab, "📋 PT Compliance Analysis")
        
        # PT Guidelines tab
        guidelines_tab = self.create_guidelines_tab()
        tab_widget.addTab(guidelines_tab, "📚 PT Guidelines")
        
        # Status bar
        self.statusBar().showMessage("PTside Ready - Specialized for Physical Therapy compliance")
        
    def create_analysis_tab(self):
        """Create the main analysis tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create splitter for document and results
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Document input
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        
        doc_label = QLabel("📄 PT Documentation:")
        doc_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e40af;")
        left_layout.addWidget(doc_label)
        
        self.document_text = QTextEdit()
        self.document_text.setPlaceholderText(self.get_pt_sample_text())
        self.document_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #93c5fd;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                background-color: white;
            }
        """)
        left_layout.addWidget(self.document_text)
        
        # Analyze button
        analyze_btn = QPushButton("🔍 Analyze PT Compliance")
        analyze_btn.clicked.connect(self.analyze_pt_document)
        analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        left_layout.addWidget(analyze_btn)
        
        splitter.addWidget(left_panel)
        
        # Right panel - Results
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        
        # Compliance score
        score_frame = QFrame()
        score_layout = QHBoxLayout(score_frame)
        score_layout.addWidget(QLabel("PT Compliance Score:"))
        
        self.score_bar = QProgressBar()
        self.score_bar.setRange(0, 100)
        self.score_bar.setValue(0)
        self.score_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #93c5fd;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #10b981;
                border-radius: 6px;
            }
        """)
        score_layout.addWidget(self.score_bar)
        
        self.score_label = QLabel("0%")
        self.score_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        score_layout.addWidget(self.score_label)
        
        right_layout.addWidget(score_frame)
        
        # Results table
        results_label = QLabel("📊 PT Compliance Findings:")
        results_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e40af;")
        right_layout.addWidget(results_label)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Issue", "Severity", "Impact", "PT-Specific Suggestion"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setStyleSheet("""
            QTableWidget {
                border: 2px solid #93c5fd;
                border-radius: 8px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #dbeafe;
                font-weight: bold;
                border: 1px solid #93c5fd;
                padding: 8px;
            }
        """)
        right_layout.addWidget(self.results_table)
        
        # PT-specific analysis
        self.pt_analysis_text = QTextEdit()
        self.pt_analysis_text.setReadOnly(True)
        self.pt_analysis_text.setMaximumHeight(150)
        self.pt_analysis_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #93c5fd;
                border-radius: 8px;
                padding: 10px;
                background-color: #f0f9ff;
                font-size: 11px;
            }
        """)
        right_layout.addWidget(QLabel("🏃‍♂️ PT-Specific Analysis:"))
        right_layout.addWidget(self.pt_analysis_text)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([700, 700])
        
        # Load sample PT note
        self.document_text.setText(self.get_pt_sample_note())
        
        return tab
        
    def create_guidelines_tab(self):
        """Create PT guidelines reference tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        guidelines_text = QTextEdit()
        guidelines_text.setReadOnly(True)
        guidelines_text.setHtml(self.get_pt_guidelines_html())
        guidelines_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #93c5fd;
                border-radius: 8px;
                padding: 15px;
                background-color: white;
                font-size: 13px;
            }
        """)
        layout.addWidget(guidelines_text)
        
        return tab
        
    def get_pt_sample_text(self):
        """Get PT-specific placeholder text."""
        return """Enter your PT documentation here...

PT Documentation should include:
• Patient identification and diagnosis
• Skilled PT interventions performed
• Measurable, time-bound goals
• Progress toward functional outcomes
• Medical necessity justification
• Therapist signature and credentials

Example interventions:
• Therapeutic exercise for strengthening
• Gait training with assistive device
• Manual therapy for joint mobilization
• Balance training for fall prevention"""

    def get_pt_sample_note(self):
        """Get a sample PT note for testing."""
        return """PHYSICAL THERAPY PROGRESS NOTE

Patient: John Smith
DOB: 03/15/1965
Diagnosis: Right total knee replacement, post-operative
Date of Service: 10/02/2025

SUBJECTIVE:
Patient reports decreased pain from 6/10 to 4/10 since last visit.
States he can walk further distances with less fatigue.

OBJECTIVE:
Patient arrived on time for scheduled appointment.
Vital signs stable.

ROM measurements:
- Right knee flexion: 95 degrees (improved from 85 degrees)
- Right knee extension: -5 degrees (improved from -10 degrees)

Strength testing (manual muscle test):
- Right quadriceps: 4-/5 (improved from 3+/5)
- Right hamstrings: 4/5 (unchanged)

Functional assessment:
- Ambulation: 150 feet with walker, minimal assistance
- Stair climbing: Unable to attempt (goal for next week)
- Transfers: Sit to stand with minimal assistance

INTERVENTIONS:
1. Therapeutic exercise program:
   - Quad sets: 3 sets of 10 repetitions
   - Straight leg raises: 2 sets of 8 repetitions
   - Heel slides: 3 sets of 10 repetitions

2. Gait training:
   - Walker training on level surfaces: 15 minutes
   - Weight bearing as tolerated per physician orders

3. Manual therapy:
   - Passive range of motion to right knee: 10 minutes
   - Soft tissue mobilization to quadriceps

ASSESSMENT:
Patient continues to make good progress toward functional goals.
Demonstrating improved strength and range of motion.
Medical necessity supported by functional limitations requiring skilled PT intervention.

PLAN:
Continue current treatment plan 3x/week.
Progress to stair training next session.
Patient education on home exercise program compliance.
Goal: Independent ambulation 300 feet within 2 weeks.

Next appointment: 10/05/2025

Jane Smith, PT
License #: PT12345
Signature: Jane Smith, PT                    Date: 10/02/2025"""

    def get_pt_guidelines_html(self):
        """Get PT-specific guidelines in HTML format."""
        return """
        <h2>🏃‍♂️ Physical Therapy Medicare Compliance Guidelines</h2>
        
        <h3>📋 Required Documentation Elements</h3>
        <ul>
            <li><b>Patient Identification:</b> Name, DOB, diagnosis, physician referral</li>
            <li><b>Skilled Services:</b> Document interventions requiring PT expertise</li>
            <li><b>Medical Necessity:</b> Tie treatments to functional limitations</li>
            <li><b>Measurable Goals:</b> SMART goals with timeframes</li>
            <li><b>Progress Documentation:</b> Response to treatment, goal progress</li>
            <li><b>Plan of Care:</b> Reference certification and physician orders</li>
            <li><b>Signature/Date:</b> Licensed therapist signature with credentials</li>
        </ul>
        
        <h3>🎯 PT-Specific Interventions to Document</h3>
        <ul>
            <li><b>Therapeutic Exercise:</b> Strengthening, ROM, endurance</li>
            <li><b>Gait Training:</b> Ambulation, assistive devices, safety</li>
            <li><b>Manual Therapy:</b> Joint mobilization, soft tissue techniques</li>
            <li><b>Balance Training:</b> Fall prevention, proprioception</li>
            <li><b>Neuromuscular Re-education:</b> Motor control, coordination</li>
            <li><b>Functional Training:</b> ADLs, transfers, mobility</li>
        </ul>
        
        <h3>⚠️ Common PT Compliance Issues</h3>
        <ul>
            <li><b>Vague Goals:</b> "Improve strength" vs "Increase quad strength 3/5 to 4/5 in 2 weeks"</li>
            <li><b>Missing Medical Necessity:</b> Not linking treatments to functional deficits</li>
            <li><b>Inadequate Progress Notes:</b> Not documenting response to treatment</li>
            <li><b>Assistant Supervision:</b> Unclear oversight when PTAs provide services</li>
            <li><b>Maintenance Therapy:</b> Continuing without skilled need or progress</li>
        </ul>
        
        <h3>💰 Financial Impact of Non-Compliance</h3>
        <ul>
            <li><b>Missing Signatures:</b> $50+ per visit denial risk</li>
            <li><b>Lack of Medical Necessity:</b> $75+ per visit denial risk</li>
            <li><b>Inadequate Goals:</b> $50+ per visit denial risk</li>
            <li><b>Poor Progress Documentation:</b> $40+ per visit denial risk</li>
        </ul>
        
        <h3>✅ Best Practices for PT Documentation</h3>
        <ul>
            <li>Use objective measurements (ROM, strength grades, distances)</li>
            <li>Document functional improvements or lack thereof</li>
            <li>Reference specific physician orders and plan of care</li>
            <li>Include patient education and home program compliance</li>
            <li>Document safety considerations and precautions</li>
            <li>Use PT-specific terminology and intervention codes</li>
        </ul>
        """
        
    def analyze_pt_document(self):
        """Analyze the PT document for compliance."""
        text = self.document_text.toPlainText()
        if not text.strip():
            self.statusBar().showMessage("Please enter PT documentation to analyze")
            return
        
        # Perform PT compliance analysis
        results = self.pt_analyzer.analyze_pt_compliance(text)
        
        # Update compliance score
        score = results["compliance_score"]
        self.score_bar.setValue(int(score))
        self.score_label.setText(f"{score}%")
        
        # Color code the score
        if score >= 80:
            color = "#10b981"  # Green
        elif score >= 60:
            color = "#f59e0b"  # Yellow
        else:
            color = "#ef4444"  # Red
        
        self.score_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #93c5fd;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 6px;
            }}
        """)
        
        # Update results table
        findings = results["findings"]
        self.results_table.setRowCount(len(findings))
        
        for i, finding in enumerate(findings):
            self.results_table.setItem(i, 0, QTableWidgetItem(finding["title"]))
            
            severity_item = QTableWidgetItem(finding["severity"])
            if finding["severity"] == "HIGH":
                severity_item.setBackground(QColor("#fecaca"))
            elif finding["severity"] == "MEDIUM":
                severity_item.setBackground(QColor("#fed7aa"))
            self.results_table.setItem(i, 1, severity_item)
            
            self.results_table.setItem(i, 2, QTableWidgetItem(f"${finding['financial_impact']}"))
            self.results_table.setItem(i, 3, QTableWidgetItem(finding["suggestion"]))
        
        # Update PT-specific analysis
        pt_analysis = results["pt_specific_analysis"]
        analysis_text = f"""PT Credentials Found: {'✅' if pt_analysis['pt_credentials_found'] else '❌'}
PT Interventions: {pt_analysis['interventions_count']} documented
Measurements: {pt_analysis['measurements_count']} objective measures
Functional Terms: {pt_analysis['functional_terms_count']} references

Key Interventions Found: {', '.join(pt_analysis['interventions_found']) if pt_analysis['interventions_found'] else 'None documented'}
Measurements Found: {', '.join(pt_analysis['measurements_found']) if pt_analysis['measurements_found'] else 'None documented'}"""
        
        self.pt_analysis_text.setText(analysis_text)
        
        # Update status
        impact = results["total_financial_impact"]
        self.statusBar().showMessage(f"PT Analysis Complete - Score: {score}% | Financial Risk: ${impact} | {len(findings)} findings")
