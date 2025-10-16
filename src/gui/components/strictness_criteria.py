"""
Strictness Criteria Definitions and Display

Provides detailed strictness level criteria and a rich display widget
showing exactly what each strictness level means.
"""

from typing import Any
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextBrowser


# Comprehensive strictness criteria definitions
STRICTNESS_CRITERIA: dict[str, dict[str, Any]] = {
    "lenient": {
        "name": "Lenient",
        "emoji": "🟢",
        "threshold": 70,
        "min_words": 200,
        "max_critical_errors": 5,
        "max_warnings": 10,
        "scoring_logic": "Basic compliance check focusing on essential elements only. Weighted scoring with high tolerance for minor issues.",
        "use_cases": [
            "Quick progress notes",
            "Internal documentation",
            "Routine session summaries",
            "Progress tracking",
        ],
        "why_use": "Provides fast turnaround for routine documentation with lower regulatory risk. Best for internal records where full compliance isn't legally required.",
        "detailed_criteria": [
            "Minimum 200 words required",
            "70% compliance score to pass",
            "Up to 5 critical errors allowed",
            "Up to 10 warnings tolerated",
            "Essential sections must be present",
            "Minor formatting issues ignored",
        ],
    },
    "balanced": {
        "name": "Balanced",
        "emoji": "🟡",
        "threshold": 80,
        "min_words": 350,
        "max_critical_errors": 3,
        "max_warnings": 7,
        "scoring_logic": "Standard compliance check with moderate rigor. All sections weighted equally with moderate penalties for errors.",
        "use_cases": [
            "Standard therapy notes",
            "Regular client assessments",
            "Treatment plans",
            "Session documentation",
        ],
        "why_use": "Optimal balance of thoroughness and efficiency for routine clinical work. Ensures good documentation quality without excessive overhead.",
        "detailed_criteria": [
            "Minimum 350 words required",
            "80% compliance score to pass",
            "Up to 3 critical errors allowed",
            "Up to 7 warnings tolerated",
            "All major sections required",
            "Proper clinical terminology expected",
            "Formatting standards enforced",
        ],
    },
    "strict": {
        "name": "Strict",
        "emoji": "🔴",
        "threshold": 90,
        "min_words": 500,
        "max_critical_errors": 2,
        "max_warnings": 5,
        "scoring_logic": "Comprehensive compliance check with all criteria weighted and strict penalties. Full regulatory alignment required.",
        "use_cases": [
            "Billing and insurance submissions",
            "Legal documentation",
            "High-risk case documentation",
            "Audit-ready records",
            "Medicare/Medicaid claims",
        ],
        "why_use": "Ensures full regulatory compliance to avoid claim denials, legal issues, or audit failures. Required for maximum reimbursement and legal protection.",
        "detailed_criteria": [
            "Minimum 500 words required",
            "90% compliance score to pass",
            "Maximum 2 critical errors allowed",
            "Maximum 5 warnings tolerated",
            "ALL required sections must be present",
            "Precise clinical terminology mandatory",
            "Full regulatory alignment (HIPAA, state laws)",
            "Detailed treatment rationale required",
            "Clear progress documentation needed",
        ],
    },
}


class StrictnessDescriptionWidget(QWidget):
    """
    Rich display widget for strictness level criteria.

    Shows comprehensive details about each strictness level including:
        - Threshold and requirements
        - Scoring logic
        - Use cases
        - Why to use this level
        - Detailed criteria checklist
    """

    def __init__(self, parent=None):
        """Initialize strictness description widget."""
        super().__init__(parent)

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title label
        self.title_label = QLabel()
        self.title_label.setStyleSheet("""
            QLabel {
                background: #3A3A3A;
                color: #A9B7C6;
                padding: 8px;
                font-weight: bold;
                font-size: 13px;
                border-bottom: 2px solid #4A9FD8;
            }
        """)
        layout.addWidget(self.title_label)

        # Description browser
        self.description_browser = QTextBrowser()
        self.description_browser.setOpenExternalLinks(False)
        self.description_browser.setStyleSheet("""
            QTextBrowser {
                background: #2B2B2B;
                color: #A9B7C6;
                border: 1px solid #323232;
                padding: 10px;
                font-size: 11px;
            }
            QScrollBar:vertical {
                background: #2B2B2B;
                width: 12px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background: #4D4D4D;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #5D5D5D;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        layout.addWidget(self.description_browser)

        # Set initial content
        self.set_strictness_level("balanced")

    def set_strictness_level(self, level: str):
        """
        Update displayed strictness level.

        Args:
            level: Strictness level key ('lenient', 'balanced', 'strict')
        """
        if level not in STRICTNESS_CRITERIA:
            level = "balanced"

        criteria = STRICTNESS_CRITERIA[level]

        # Update title
        self.title_label.setText(f"{criteria['emoji']} {criteria['name']} Mode - Detailed Criteria")

        # Build rich HTML description
        html = self._build_html_description(criteria)
        self.description_browser.setHtml(html)

    def _build_html_description(self, criteria: dict) -> str:
        """
        Build rich HTML description.

        Args:
            criteria: Strictness criteria dict

        Returns:
            HTML string
        """
        # Use cases list
        use_cases_html = "".join(f"<li>{case}</li>" for case in criteria["use_cases"])

        # Detailed criteria list
        detailed_html = "".join(f"<li>{item}</li>" for item in criteria["detailed_criteria"])

        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    color: #A9B7C6;
                    margin: 0;
                    padding: 0;
                }}
                h3 {{
                    color: #4A9FD8;
                    margin-top: 15px;
                    margin-bottom: 8px;
                    font-size: 13px;
                }}
                .metric {{
                    background: #3A3A3A;
                    padding: 8px;
                    margin: 8px 0;
                    border-left: 3px solid #4A9FD8;
                    border-radius: 3px;
                }}
                .metric-label {{
                    color: #6A8759;
                    font-weight: bold;
                }}
                .metric-value {{
                    color: #FFC66D;
                    font-weight: bold;
                }}
                ul {{
                    margin: 8px 0;
                    padding-left: 25px;
                }}
                li {{
                    margin: 4px 0;
                    color: #A9B7C6;
                }}
                .why-box {{
                    background: #214283;
                    padding: 10px;
                    margin: 10px 0;
                    border-radius: 5px;
                    border: 1px solid #4A9FD8;
                }}
                .scoring-box {{
                    background: #3A3A3A;
                    padding: 10px;
                    margin: 10px 0;
                    border-radius: 5px;
                    font-style: italic;
                }}
            </style>
        </head>
        <body>
            <div class="metric">
                <span class="metric-label">Compliance Threshold:</span> 
                <span class="metric-value">{criteria["threshold"]}% score required to pass</span>
            </div>
            
            <div class="metric">
                <span class="metric-label">Word Count Requirement:</span> 
                <span class="metric-value">Minimum {criteria["min_words"]} words</span>
            </div>
            
            <div class="metric">
                <span class="metric-label">Error Tolerance:</span> 
                <span class="metric-value">
                    Max {criteria["max_critical_errors"]} critical errors, 
                    {criteria["max_warnings"]} warnings
                </span>
            </div>
            
            <div class="scoring-box">
                <span class="metric-label">Scoring Logic:</span><br>
                {criteria["scoring_logic"]}
            </div>
            
            <h3>📋 Detailed Criteria</h3>
            <ul>
                {detailed_html}
            </ul>
            
            <h3>💼 Use Cases</h3>
            <ul>
                {use_cases_html}
            </ul>
            
            <div class="why-box">
                <span class="metric-label">Why Use {criteria["name"]}?</span><br>
                {criteria["why_use"]}
            </div>
        </body>
        </html>
        """

        return html
