# Python
import sys
import sqlite3
import os
import re
from typing import List, Tuple
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
    QMainWindow,
    QStatusBar,
    QMenuBar,
    QFileDialog, 
    QTextEdit,
    QHBoxLayout,
    QProgressBar,
    QListWidget,
    QDialog,
    QDialogButtonBox,
    QListWidgetItem,
    QInputDialog,
    QCheckBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from cryptography.hazmat.primitives.hashes import SHA256
from .workers.api_worker import ApiAnalysisWorker
from .dialogs.add_rubric_source_dialog import AddRubricSourceDialog
from .dialogs.library_selection_dialog import LibrarySelectionDialog
from .dialogs.rubric_manager_dialog import RubricManagerDialog
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# The following libraries are for direct document parsing, which will be moved to the backend.
# They are kept here for now to prevent the DocumentWorker from breaking until it is replaced.
import pdfplumber.utils
import docx.opc.exceptions
import pdfplumber
from docx import Document  # python-docx
import pytesseract
from PIL import Image  # Pillow for image processing with Tesseract
import pandas as pd  # Pandas for Excel and CSV

# NLP libraries removed.

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, '..', 'data', 'compliance.db')
HASH_ALGORITHM = SHA256()
ITERATIONS = 100000
OFFLINE_ONLY = True

# --- Tesseract OCR Path (Optional, Windows offline) ---
tess_env = os.environ.get("TESSERACT_EXE")
if tess_env and os.path.isfile(tess_env):
    pytesseract.pytesseract.tesseract_cmd = tess_env

# --- AI Model Loading Sections Removed ---

# --- PHI Scrubber (basic, extendable) ---
def scrub_phi(text: str) -> str:
    if not isinstance(text, str):
        return text
    patterns = [
        (r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', '[EMAIL]'),
        (r'(\+?\d{1,2}[\s\-.]?)?(\(?\d{3}\)?[ \-.]?\d{3}[\-.]?\d{4})', '[PHONE]'),
        (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
        (r'\bMRN[:\s]*[A-Za-z0-9\-]{4,}\b', '[MRN]'),
        (r'\b(19|20)\d{2}-/ (0?[1-9]|1[0-2])-/ (0?[1-g]|[12]\d|3[01])\b', '[DATE]'),
        (r'\b(Name|Patient|DOB|Address)[:\s]+[^\n]+', r'\1: [REDACTED]'),
    ]
    out = text
    for pat, repl in patterns:
        out = re.sub(pat, repl, out)
    return out

# --- Helpers: chunking for long texts ---
def chunk_text(text: str, max_chars: int = 4000):
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        newline_pos = text.rfind("\n", start, end)
        if newline_pos != -1 and newline_pos > start + 1000:
            end = newline_pos
        chunks.append(text[start:end])
        start = end
    return chunks

# This function will be moved to the backend.
# from src.parsing import parse_document_content

# --- Helpers: Database Initialization ---
def initialize_database():
    try:
        os.makedirs(os.path.dirname(os.path.abspath(DATABASE_PATH)), exist_ok=True)
        with sqlite3.connect(DATABASE_PATH) as conn:
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash BLOB NOT NULL, salt BLOB NOT NULL)")
            cur.execute("CREATE TABLE IF NOT EXISTS rubrics (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, content TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            cur.execute("SELECT COUNT(*) FROM rubrics")
            if cur.fetchone()[0] == 0:
                default_rubric_name = "Default Best Practices"
                default_rubric_content = """# General Documentation Best Practices
- All entries must be dated and signed.
- Patient identification must be clear on every page.
- Use of approved abbreviations only.
- Document skilled intervention, not just patient performance.
- Goals must be measurable and time-bound."""
                cur.execute("INSERT INTO rubrics (name, content) VALUES(?, ?)", (default_rubric_name, default_rubric_content))
            username = "test"
            password = "test123"
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(algorithm=HASH_ALGORITHM, length=32, salt=salt, iterations=ITERATIONS)
            password_hash = kdf.derive(password.encode())
            cur.execute("INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?) ON CONFLICT(username) DO UPDATE SET password_hash=excluded.password_hash, salt=excluded.salt", (username, password_hash, salt))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Failed to initialize database: {e}")

# --- Background Workers & Dialogs (Moved to separate modules) ---

class MainApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Therapy Compliance Analyzer')
        self.setGeometry(100, 100, 1024, 768)
        self.scrub_before_display = True
        self._current_raw_text = ""
        self._current_file_path = ""
        self.analysis_results = None
        self._current_sentences_with_source: List[Tuple[str, str]] = []
        self.setAcceptDrops(True)
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        self.file_menu = self.menu_bar.addMenu('File')
        self.file_menu.addAction('Exit', self.close)
        self.tools_menu = self.menu_bar.addMenu('Tools')
        self.tools_menu.addAction('Initialize Database', initialize_database)
        self.tools_menu.addAction('Quickstart', self.show_quickstart)
        self.admin_menu = self.menu_bar.addMenu('Admin Options')
        self.toggle_scrub_action = self.admin_menu.addAction('Scrub PHI before display (recommended)')
        self.toggle_scrub_action.setCheckable(True)
        self.toggle_scrub_action.setChecked(self.scrub_before_display)
        self.toggle_scrub_action.toggled.connect(self._toggle_scrub_setting)
        self.help_menu = self.menu_bar.addMenu('Help')
        self.help_menu.addAction('Show Paths', self.show_paths)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('Ready')
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        button_layout = QHBoxLayout()
        self.upload_button = QPushButton('Upload Document')
        self.upload_button.clicked.connect(self.open_file_dialog)
        button_layout.addWidget(self.upload_button)
        self.clear_button = QPushButton('Clear Display')
        self.clear_button.clicked.connect(self.clear_document_display)
        button_layout.addWidget(self.clear_button)
        self.generate_pdf_button = QPushButton('Generate Report (PDF)')
        self.generate_pdf_button.clicked.connect(self.generate_report_pdf)
        button_layout.addWidget(self.generate_pdf_button)
        self.print_button = QPushButton('Print Report')
        self.print_button.clicked.connect(self.print_report)
        button_layout.addWidget(self.print_button)
        main_layout.addLayout(button_layout)
        rubric_layout = QHBoxLayout()
        self.manage_rubrics_button = QPushButton("Manage Rubrics")
        self.manage_rubrics_button.clicked.connect(self.manage_rubrics)
        rubric_layout.addWidget(self.manage_rubrics_button)
        self.run_analysis_button = QPushButton("Run Analysis")
        self.run_analysis_button.clicked.connect(self.run_analysis)
        rubric_layout.addWidget(self.run_analysis_button)
        self.rubric_list_widget = QListWidget()
        self.rubric_list_widget.setPlaceholderText("Available Rubrics")
        self.rubric_list_widget.setMaximumHeight(100)
        rubric_layout.addWidget(self.rubric_list_widget)
        main_layout.addLayout(rubric_layout)
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)
        progress_layout.addWidget(self.progress_bar)
        self.cancel_button = QPushButton('Cancel Analysis')
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_analysis)
        progress_layout.addWidget(self.cancel_button)
        main_layout.addLayout(progress_layout)
        self.document_display_area = QTextEdit()
        self.document_display_area.setPlaceholderText("Drag and drop documents here, or use the 'Upload Document' button.")
        self.document_display_area.setReadOnly(True)
        self.document_display_area.setAcceptDrops(True)
        main_layout.addWidget(self.document_display_area)
        self.analysis_results_area = QTextEdit()
        self.analysis_results_area.setPlaceholderText("Rubric analysis results will appear here.")
        self.analysis_results_area.setReadOnly(True)
        main_layout.addWidget(self.analysis_results_area)
        self.central_widget.setLayout(main_layout)
        self.load_rubrics_to_main_list()

    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Select Document', '', 'Supported Files (*.pdf *.docx *.xlsx *.xls *.csv *.png *.jpg *.jpeg *.gif *.bmp *.tiff);;All Files (*.*)')
        if file_name:
            self.process_document(file_name)

    def _toggle_scrub_setting(self, checked: bool):
        self.scrub_before_display = checked
        if self._current_raw_text:
            shown = scrub_phi(self._current_raw_text) if self.scrub_before_display else self._current_raw_text
            self.document_display_area.setText(shown)
            self.status_bar.showMessage(f"Scrub before display set to {'ON' if checked else 'OFF'}.")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                self.process_document(file_path)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def _set_busy(self, busy: bool):
        if busy:
            self.progress_bar.setRange(0, 0)
            self.cancel_button.setEnabled(True)
        else:
            self.progress_bar.setRange(0, 1)
            self.cancel_button.setEnabled(False)

    def process_document(self, file_path: str):
        """
        Stores the path of the selected document and updates the UI.
        """
        self._current_file_path = file_path
        self._current_raw_text = f"File loaded: {os.path.basename(file_path)}"
        self.document_display_area.setText(f"Loaded '{os.path.basename(file_path)}'.\n\nClick 'Run Analysis' to process.")
        self.analysis_results_area.clear()
        self.analysis_results = None
        self.status_bar.showMessage(f"Loaded document: {os.path.basename(file_path)}")

    def run_analysis(self):
        """
        Triggers the backend analysis in a background thread.
        """
        if not self._current_file_path:
            QMessageBox.warning(self, "Analysis Error", "Please upload a document to analyze first.")
            return

        self._set_busy(True)
        self.status_bar.showMessage("Sending document to backend for analysis...")
        self.analysis_results_area.setText("Analysis in progress...")

        self.thread = QThread()
        self.worker = ApiAnalysisWorker(file_path=self._current_file_path)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.handle_analysis_finished)
        self.worker.error.connect(self.handle_analysis_error)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def handle_analysis_finished(self, result: dict):
        """
        Handles the successful completion of the backend analysis.
        """
        self._set_busy(False)
        self.status_bar.showMessage("Analysis complete.")

        self.analysis_results = result
        self._current_raw_text = result.get("document", {}).get("text", "")
        self.document_display_area.setText(self._current_raw_text)

        # This will be implemented in the next step
        report_html = self._format_results_as_html(result)
        self.analysis_results_area.setHtml(report_html)

    def _format_results_as_html(self, result: dict) -> str:
        """
        Formats the JSON analysis result into a user-friendly HTML report.
        """
        if not result:
            return "<p>No analysis results received.</p>"

        metrics = result.get("metrics", {})
        analysis = result.get("analysis", {})
        findings = analysis.get("findings", [])

        document = result.get("document", {})
        html = f"<h1>Compliance Analysis Report</h1>"
        html += f"<h2>Document Type: {document.get('document_type', 'Unknown')}</h2>"

        # --- Metrics Summary ---
        html += "<h2>Summary</h2>"
        score = metrics.get('compliance_score', 'N/A')
        html += f"<h3>Overall Compliance Score: {score}/100</h3>"
        html += f"<p><b>Total Risks Found:</b> {metrics.get('risk_count', 0)}</p>"

        html += "<b>Risks by Category:</b><ul>"
        for category, count in metrics.get('by_category', {}).items():
            html += f"<li>{category}: {count}</li>"
        html += "</ul>"

        html += "<b>Risks by Severity:</b><ul>"
        for severity, count in metrics.get('by_severity', {}).items():
            html += f"<li>{severity}: {count}</li>"
        html += "</ul>"

        # --- Detailed Findings ---
        html += "<h2>Detailed Findings & Suggestions</h2>"
        if not findings:
            html += "<p>No specific compliance risks were found based on the rubric.</p>"
        else:
            for finding in findings:
                html += "<div style='border: 1px solid #ccc; padding: 10px; margin-bottom: 10px;'>"
                html += f"<h4>{finding.get('issue_title', 'N/A')}</h4>"
                html += f"<p><b>Severity:</b> {finding.get('severity', 'N/A')} | <b>Category:</b> {finding.get('issue_category', 'N/A')}</p>"
                html += f"<p><b>Details:</b> {finding.get('issue_detail', 'N/A')}</p>"
                html += "<div style='background-color: #e6f7ff; border-left: 3px solid #007bff; padding: 5px; margin-top: 5px;'>"
                html += f"<p><b>Suggestion:</b> {finding.get('suggestion', 'No suggestion available.')}</p>"
                html += "</div></div>"

        return html

    def handle_analysis_error(self, error_message: str):
        """
        Handles errors from the analysis worker.
        """
        self._set_busy(False)
        self.status_bar.showMessage("Analysis failed.")
        self.analysis_results_area.setText(f"An error occurred:\n\n{error_message}")
        QMessageBox.critical(self, "Analysis Error", error_message)

    def clear_document_display(self):
        self.document_display_area.clear()
        self.analysis_results_area.clear()
        self._current_raw_text = ""
        self._current_file_path = ""
        self.analysis_results = None
        self.status_bar.showMessage('Display cleared.')

    def manage_rubrics(self):
        dialog = RubricManagerDialog(self)
        dialog.exec()
        self.load_rubrics_to_main_list()

    def load_rubrics_to_main_list(self):
        self.rubric_list_widget.clear()
        try:
            if not os.path.exists(DATABASE_PATH):
                return
            with sqlite3.connect(DATABASE_PATH) as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, name FROM rubrics ORDER BY name ASC")
                for rubric_id, name in cur.fetchall():
                    item = QListWidgetItem(name)
                    item.setData(Qt.ItemDataRole.UserRole, rubric_id)
                    self.rubric_list_widget.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load rubrics into main list:\n{e}")

    def run_rubric_analysis(self):
        if not self._current_sentences_with_source:
            QMessageBox.warning(self, "Analysis Error", "Please upload a document to analyze first.")
            return
        selected_items = self.rubric_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Analysis Error", "Please select a rubric from the list to run the analysis.")
            return
        try:
            rubric_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
            with sqlite3.connect(DATABASE_PATH) as conn:
                cur = conn.cursor()
                cur.execute("SELECT content FROM rubrics WHERE id = ?", (rubric_id,))
                result = cur.fetchone()
            if not result:
                QMessageBox.critical(self, "Database Error", "Could not find the selected rubric in the database.")
                return
            rubric_content = result[0]
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to retrieve rubric content:\n{e}")
            return
        QMessageBox.information(self, "Analysis", "This feature is currently disabled pending new model integration.")

    def _build_report_html(self) -> str:
        text_for_report = scrub_phi(self._current_raw_text or "")
        html = f"""<html><head><meta charset=\"utf-8\"><style>body {{ font-family: Arial, sans-serif; }} h1 {{ font-size: 18pt; }} h2 {{ font-size: 14pt; margin-top: 12pt; }} pre {{ white-space: pre-wrap; font-family: Consolas, monospace; background: #f4f4f4; padding: 8px; }}</style></head><body><h1>Therapy Compliance Analysis Report</h1><p><b>Mode:</b> Offline | <b>PHI Scrubbing:</b> Enabled for export</p><h2>Extracted Text (scrubbed)</h2><pre>{text_for_report}</pre></body></html>"""
        return html

    def generate_report_pdf(self):
        if not self._current_raw_text:
            QMessageBox.information(self, "Generate Report", "No document data to export.")
            return
        save_path, _ = QFileDialog.getSaveFileName(self, 'Save Report as PDF', '', 'PDF Files (*.pdf)')
        if not save_path:
            return
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            if not save_path.lower().endswith(".pdf"):
                save_path += ".pdf"
            printer.setOutputFileName(save_path)
            from PyQt6.QtGui import QTextDocument
            doc = QTextDocument()
            doc.setHtml(self._build_report_html())
            doc.print(printer)
            QMessageBox.information(self, "Generate Report", f"PDF saved to:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Generate Report", f"Failed to create PDF:\n{e}")

    def print_report(self):
        if not self._current_raw_text:
            QMessageBox.information(self, "Print Report", "No document data to print.")
            return
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                from PyQt6.QtGui import QTextDocument
                doc = QTextDocument()
                doc.setHtml(self._build_report_html())
                doc.print(printer)
                self.status_bar.showMessage("Report sent to printer.")
        except Exception as e:
            QMessageBox.critical(self, "Print Report", f"Failed to print:\n{e}")

    def show_paths(self):
        msg = f"App path:\n{os.path.abspath(__file__)}\n\nDatabase path:\n{os.path.abspath(DATABASE_PATH)}"
        QMessageBox.information(self, "Paths", msg)
