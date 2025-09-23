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
from collections import Counter
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from cryptography.hazmat.primitives.hashes import SHA256

from src.entity import NEREntity
from src.gui.workers.document_worker import DocumentWorker
from src.gui.workers.ner_worker import NERWorker
from src.gui.workers.generator_worker import GeneratorWorker
from src.gui.workers.kb_worker import KBWorker
from src.gui.workers.model_check_worker import ModelCheckWorker
from src.knowledge_base_service import KnowledgeBaseService
from src.gui.dialogs.add_rubric_source_dialog import AddRubricSourceDialog
from src.gui.dialogs.library_selection_dialog import LibrarySelectionDialog
from src.gui.dialogs.rubric_manager_dialog import RubricManagerDialog
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

import pdfplumber.utils
import docx.opc.exceptions

# Document parsing libraries
import pdfplumber
from docx import Document  # python-docx
import pytesseract
from PIL import Image  # Pillow for image processing with Tesseract
import pandas as pd  # Pandas for Excel and CSV

from src.parsing import parse_document_content

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

class MainApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Therapy Compliance Analyzer')
        self.setGeometry(100, 100, 1024, 768)
        self.scrub_before_display = True
        self._current_raw_text = ""
        self._current_sentences_with_source: List[Tuple[str, str]] = []
        self._extracted_entities: List[NEREntity] = []

        # Service and Worker Management
        self.knowledge_base_service = None
        self._doc_thread = None
        self._doc_worker = None
        self._kb_thread = None
        self._kb_worker = None
        self._ner_thread = None
        self._ner_worker = None
        self._generator_thread = None
        self._generator_worker = None

        self.setAcceptDrops(True)
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        self.file_menu = self.menu_bar.addMenu('File')
        self.file_menu.addAction('Exit', self.close)
        self.tools_menu = self.menu_bar.addMenu('Tools')
        self.tools_menu.addAction('Initialize Database', initialize_database)
        self.tools_menu.addAction('Check Model Status', self.run_model_check)
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
        self.run_analysis_button.clicked.connect(self.run_rubric_analysis)
        rubric_layout.addWidget(self.run_analysis_button)
        self.rubric_list_widget = QListWidget()
        self.rubric_list_widget.setPlaceholderText("Available Rubrics")
        self.rubric_list_widget.setMaximumHeight(100)
        rubric_layout.addWidget(self.rubric_list_widget)
        main_layout.addLayout(rubric_layout)

        # --- Q&A Layout ---
        qa_layout = QHBoxLayout()
        qa_layout.addWidget(QLabel("Ask a question about the document:"))
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("e.g., What are the requirements for skilled nursing care?")
        qa_layout.addWidget(self.question_input)
        self.ask_button = QPushButton("Ask")
        self.ask_button.clicked.connect(self.run_qa_pipeline)
        self.ask_button.setEnabled(False) # Disabled until KB is ready
        qa_layout.addWidget(self.ask_button)
        main_layout.addLayout(qa_layout)

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
        self.analysis_results_area.setPlaceholderText("Analysis results will appear here.")
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

    def process_document(self, file_path):
        self.clear_document_display()
        self.status_bar.showMessage(f"Processing: {os.path.basename(file_path)}")
        self.document_display_area.setText("Processing document in background...")
        self._set_busy(True)

        self._doc_thread = QThread()
        self._doc_worker = DocumentWorker(file_path)
        self._doc_worker.moveToThread(self._doc_thread)
        self._doc_thread.started.connect(self._doc_worker.run)
        self._doc_worker.finished.connect(self._handle_doc_finished)
        self._doc_worker.error.connect(self._handle_doc_error)
        self._doc_worker.progress.connect(lambda p: self.status_bar.showMessage(f"Document processing... {p}%"))
        self._doc_worker.finished.connect(self._doc_thread.quit)
        self._doc_worker.finished.connect(self._doc_worker.deleteLater)
        self._doc_thread.finished.connect(self._doc_thread.deleteLater)
        self._doc_thread.start()

    def cancel_analysis(self):
        workers = [self._doc_worker, self._kb_worker, self._ner_worker, self._generator_worker]
        canceled = False
        for worker in workers:
            if worker:
                try:
                    worker.cancel()
                    canceled = True
                except RuntimeError:
                    pass
        if canceled:
            self.status_bar.showMessage("Cancel requested...")
        else:
            self.status_bar.showMessage("Nothing to cancel.")

    def _handle_doc_finished(self, sentences_with_source: List[Tuple[str, str]]):
        self._current_sentences_with_source = sentences_with_source
        self._current_raw_text = "\n".join([text for text, source in sentences_with_source])

        display_text = self._current_raw_text
        if len(display_text) > 100000:
            display_text = display_text[:100000] + "\n...[truncated for display]"

        self.document_display_area.setText(scrub_phi(display_text) if self.scrub_before_display else display_text)

        self.start_kb_build(self._current_raw_text)

    def _handle_doc_error(self, message: str):
        self._set_busy(False)
        self.document_display_area.setText(message)
        self.status_bar.showMessage(f"Error: {message}")

    def start_kb_build(self, text: str):
        self.status_bar.showMessage("Building knowledge base from document...")
        self.analysis_results_area.setText("Building knowledge base...")
        self.ask_button.setEnabled(False)

        self.knowledge_base_service = KnowledgeBaseService()
        self._kb_thread = QThread()
        self._kb_worker = KBWorker(text, self.knowledge_base_service)
        self._kb_worker.moveToThread(self._kb_thread)

        self._kb_thread.started.connect(self._kb_worker.run)
        self._kb_worker.finished.connect(self._handle_kb_finished)
        self._kb_worker.error.connect(self._handle_doc_error)

        self._kb_worker.finished.connect(self._kb_thread.quit)
        self._kb_worker.finished.connect(self._kb_worker.deleteLater)
        self._kb_thread.finished.connect(self._kb_thread.deleteLater)

        self._kb_thread.start()

    def _handle_kb_finished(self, kb_service: KnowledgeBaseService):
        self.knowledge_base_service = kb_service
        self.status_bar.showMessage("Knowledge base ready. Starting NER analysis...")
        self.analysis_results_area.append("\nKnowledge base ready. Starting NER analysis...")
        self.start_ner_analysis(self._current_raw_text)

    def start_ner_analysis(self, text: str):
        self._ner_thread = QThread()
        self._ner_worker = NERWorker(text)
        self._ner_worker.moveToThread(self._ner_thread)

        self._ner_thread.started.connect(self._ner_worker.run)
        self._ner_worker.finished.connect(self._handle_ner_finished)
        self._ner_worker.error.connect(self._handle_ner_error)
        self._ner_worker.progress.connect(lambda p, msg: self.status_bar.showMessage(f"NER: {msg} ({p}%)"))

        self._ner_worker.finished.connect(self._ner_thread.quit)
        self._ner_worker.finished.connect(self._ner_worker.deleteLater)
        self._ner_thread.finished.connect(self._ner_thread.deleteLater)

        self._ner_thread.start()

    def _handle_ner_finished(self, entities: List[NEREntity]):
        self._set_busy(False)
        self.ask_button.setEnabled(True)
        self._extracted_entities = entities
        self.status_bar.showMessage(f"NER analysis complete. Found {len(entities)} entities.")

        if not entities:
            self.analysis_results_area.append("\n\n--- NER Analysis ---\nNo entities were found.")
            return

        entity_counts = Counter(e.label for e in entities)
        summary_header = "\n\n--- NER Analysis Summary ---\n"
        summary_body = "\n".join([f"- {label}: {count}" for label, count in entity_counts.most_common()])
        self.analysis_results_area.append(summary_header + summary_body)

    def _handle_ner_error(self, message: str):
        self._set_busy(False)
        self.status_bar.showMessage(f"NER Error: {message}")
        QMessageBox.critical(self, "NER Error", message)

    def run_qa_pipeline(self):
        question = self.question_input.text()
        if not question:
            QMessageBox.warning(self, "Question Error", "Please enter a question.")
            return

        if not self.knowledge_base_service or not self.knowledge_base_service.is_ready():
            QMessageBox.warning(self, "Knowledge Base Error", "The knowledge base for this document is not ready.")
            return

        self._set_busy(True)
        self.status_bar.showMessage("Finding relevant documents...")
        self.analysis_results_area.setText(f"Question: {question}\n\nFinding relevant information...")

        context_chunks = self.knowledge_base_service.find_relevant_chunks(question)
        context_texts = [chunk['text'] for chunk in context_chunks]

        self.status_bar.showMessage("Found context. Starting generator...")
        self.analysis_results_area.append("\nFound relevant context. Generating answer...")

        self._generator_thread = QThread()
        self._generator_worker = GeneratorWorker(question, context_texts)
        self._generator_worker.moveToThread(self._generator_thread)

        self._generator_thread.started.connect(self._generator_worker.run)
        self._generator_worker.finished.connect(self._handle_generator_finished)
        self._generator_worker.error.connect(self._handle_generator_error)
        self._generator_worker.progress.connect(lambda p, msg: self.status_bar.showMessage(f"Generator: {msg} ({p}%)"))

        self._generator_worker.finished.connect(self._generator_thread.quit)
        self._generator_worker.finished.connect(self._generator_worker.deleteLater)
        self._generator_thread.finished.connect(self._generator_thread.deleteLater)

        self._generator_thread.start()

    def _handle_generator_finished(self, answer: str):
        self._set_busy(False)
        self.status_bar.showMessage("Q&A complete.")
        self.analysis_results_area.append(f"\n\n--- Answer ---\n{answer}")

    def _handle_generator_error(self, message: str):
        self._set_busy(False)
        self.status_bar.showMessage(f"Generator Error: {message}")
        QMessageBox.critical(self, "Generator Error", message)

    def clear_document_display(self):
        self.document_display_area.clear()
        self.analysis_results_area.clear()
        self._current_raw_text = ""
        self._current_sentences_with_source = []
        self._extracted_entities = []
        self.ask_button.setEnabled(False)
        self.knowledge_base_service = None
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
        if not self._current_raw_text:
            QMessageBox.warning(self, "Analysis Error", "Please upload a document to analyze first.")
            return

        if not self._extracted_entities:
            QMessageBox.warning(self, "Analysis Error", "Please run NER analysis before rubric analysis.")
            return

        selected_items = self.rubric_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Analysis Error", "Please select a rubric from the list.")
            return

        # This is where the rubric analysis logic would go.
        QMessageBox.information(self, "Analysis", "This feature is currently disabled.")

    def _build_report_html(self) -> str:
        text_for_report = scrub_phi(self._current_raw_text or "")

        ner_html = "<h2>Named Entity Recognition Results</h2>"
        if self._extracted_entities:
            entity_counts = Counter(e.label for e in self._extracted_entities)
            ner_html += "<h3>Summary</h3><ul>"
            for label, count in entity_counts.most_common():
                ner_html += f"<li><b>{label}:</b> {count}</li>"
            ner_html += "</ul><h3>Details</h3><ul>"
            for entity in self._extracted_entities:
                ner_html += f"<li>{entity.text} (<i>{entity.label}</i>, score: {entity.score:.2f})</li>"
            ner_html += "</ul>"
        else:
            ner_html += "<p>No entities were extracted.</p>"

        html = f"""<html><head><meta charset=\"utf-8\"><style>
            body {{ font-family: Arial, sans-serif; }}
            h1 {{ font-size: 18pt; }}
            h2 {{ font-size: 14pt; margin-top: 12pt; border-bottom: 1px solid #ccc; }}
            h3 {{ font-size: 12pt; margin-top: 10pt; }}
            pre {{ white-space: pre-wrap; font-family: Consolas, monospace; background: #f4f4f4; padding: 8px; border-radius: 4px; }}
            ul {{ list-style-type: none; padding-left: 0; }}
            li {{ margin-bottom: 4px; }}
            i {{ color: #555; }}
            </style></head><body>
            <h1>Therapy Compliance Analysis Report</h1>
            <p><b>Mode:</b> Offline | <b>PHI Scrubbing:</b> Enabled for export</p>
            {ner_html}
            <h2>Extracted Text (scrubbed)</h2>
            <pre>{text_for_report}</pre>
            </body></html>"""
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

    def run_model_check(self):
        """
        Starts the ModelCheckWorker to verify AI model loading.
        """
        self._set_busy(True)
        self.status_bar.showMessage("Checking status of all AI models...")
        self._model_check_thread = QThread()
        self._model_check_worker = ModelCheckWorker()
        self._model_check_worker.moveToThread(self._model_check_thread)

        self._model_check_thread.started.connect(self._model_check_worker.run)
        self._model_check_worker.finished.connect(self._handle_model_check_finished)
        self._model_check_worker.progress.connect(self.status_bar.showMessage)

        self._model_check_worker.finished.connect(self._model_check_thread.quit)
        self._model_check_worker.finished.connect(self._model_check_worker.deleteLater)
        self._model_check_thread.finished.connect(self._model_check_thread.deleteLater)

        self._model_check_thread.start()

    def _handle_model_check_finished(self, message: str, success: bool):
        """
        Displays the result of the model check.
        """
        self._set_busy(False)
        self.status_bar.showMessage("Model check complete.")
        if success:
            QMessageBox.information(self, "Model Status", message)
        else:
            QMessageBox.critical(self, "Model Status Error", message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    initialize_database()
    main_win = MainApplicationWindow()
    main_win.show()
    sys.exit(app.exec())
