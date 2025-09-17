# Python
from __future__ import annotations

# Standard library
import hashlib
import html
import logging
import os
import re
import sqlite3
import sys
from typing import Callable, List, Literal, Tuple, Optional
from urllib.parse import quote, unquote
import base64

# Third-party used throughout
import pandas as pd  # type: ignore

# --- Configuration defaults and constants ---
REPORT_TEMPLATE_VERSION = "v2.2"

# Paths and environment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_default_db_dir = os.path.join(os.path.expanduser("~"), "Documents", "SpecKitData")
DATABASE_PATH = os.getenv("SPEC_KIT_DB", os.path.join(_default_db_dir, "spec_kit.db"))
REPORTS_DIR = os.getenv("SPEC_KIT_REPORTS", os.path.join(os.path.expanduser("~"), "Documents", "SpecKitReports"))
LOGS_DIR = os.path.join(os.path.expanduser("~"), "Documents", "SpecKitData", "logs")

# PDF report defaults
REPORT_FONT_FAMILY = "DejaVu Sans"
REPORT_FONT_SIZE = 8.5

REPORT_STYLESHEET = """
    body { font-family: DejaVu Sans, Arial, sans-serif; font-size: 10pt; line-height: 1.4; }
    h1 { font-size: 18pt; color: #1f4fd1; margin-bottom: 20px; }
    h2 { font-size: 14pt; color: #111827; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 25px; }
    h3 { font-size: 12pt; color: #374151; margin-top: 20px; }
    .user-message { margin-top: 15px; }
    .ai-message { margin-top: 5px; padding: 8px; background-color: #f3f4f6; border-radius: 8px; }
    .education-block {
        margin-top: 15px;
        padding: 12px;
        background-color: #eef6ff;
        border-left: 5px solid #60a5fa;
        border-radius: 8px;
    }
    .education-block h3 {
        margin-top: 0;
        color: #1f4fd1;
    }
    hr { border: none; border-top: 1px solid #ccc; margin: 20px 0; }
    ul { padding-left: 20px; }
    li { margin-bottom: 5px; }
    .suggestion-link { text-decoration: none; color: #1f4fd1; }
    .suggestion-link:hover { text-decoration: underline; }
"""
REPORT_PAGE_SIZE = (8.27, 11.69)  # A4 inches
REPORT_MARGINS = (1.1, 1.0, 1.3, 1.0)  # top, right, bottom, left inches
REPORT_HEADER_LINES = 2
REPORT_FOOTER_LINES = 1

# --- Logging setup ---
logger = logging.getLogger(__name__)
# ... (logging setup)

# --- Guarded Imports ---
# ... (all guarded imports)
from .ui_components import SetupTab, ResultsTab, AnalyticsTab

# ... (All other functions and classes from main.py, like workers, helpers, run_analyzer, etc.)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spec Kit Analyzer")
        self.setMinimumSize(1200, 800)

        # Initialize state
        self._current_report_path: Optional[str] = None
        self._last_error: Optional[str] = None
        self._batch_cancel = False
        self.current_report_data: Optional[dict] = None
        self.local_rag: Optional[LocalRAG] = None
        self.doc_rag: Optional[LocalRAG] = None
        self.guideline_service: Optional[GuidelineService] = None
        self.chat_history: list[tuple[str, str]] = []
        self.compliance_rules: list[ComplianceRule] = []

        self._create_actions()
        self._create_toolbars()
        self._create_central_widget()
        self._create_status_bar()

        self.refresh_llm_indicator()
        self.refresh_recent_files()
        self._init_llm_thread()

    def _create_actions(self):
        # ... (action creation logic)
        self.act_open = QAction("Open File...", self)
        # ... etc.

    def _create_toolbars(self):
        # ... (toolbar creation logic)
        tb = QToolBar("Main")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)
        # ... add actions to toolbar

    def _create_central_widget(self):
        central = QWidget()
        self.setCentralWidget(central)
        vmain = QVBoxLayout(central)

        self.tabs = QTabWidget()
        self.setup_tab = SetupTab()
        self.results_tab = ResultsTab()
        self.analytics_tab = AnalyticsTab()
        self.logs_tab = QTextEdit()
        self.logs_tab.setReadOnly(True)

        self.tabs.addTab(self.setup_tab, "Setup & File Queue")
        self.tabs.addTab(self.results_tab, "Analysis Results")
        self.tabs.addTab(self.analytics_tab, "Analytics Dashboard")
        self.tabs.addTab(self.logs_tab, "Application Logs")

        vmain.addWidget(self.tabs)

        # Connect signals from tabs
        self.setup_tab.open_file_requested.connect(self.action_open_report)
        # ... (connect all other signals)
        self.analytics_tab.refresh_requested.connect(self._update_analytics_tab)

        self.progress_bar = QProgressBar()
        # ... (progress bar setup)
        vmain.addWidget(self.progress_bar)

        # ... (chat input setup)

    def _create_status_bar(self):
        # ... (status bar setup)

    # ... (All other methods of MainWindow, like action handlers, etc.)
    # ... (The logic from these methods will remain, but UI widget access
    #      will be through self.setup_tab, self.results_tab, etc.)

    def _update_analytics_tab(self):
        # ... (This logic now gets filter values from self.analytics_tab)
        start_date = self.analytics_tab.date_start.date().toString("yyyy-MM-dd")
        # ...
        # And updates widgets on self.analytics_tab
        self.analytics_tab.lbl_total_runs.setText(str(total_runs))
        # ...

# ... (rest of the file, _run_gui, if __name__ == "__main__":, etc.)
if __name__ == "__main__":
    # ...
    sys.exit(0)
