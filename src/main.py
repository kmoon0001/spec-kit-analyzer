# Python
from __future__ import annotations

# Standard library
from datetime import datetime
import hashlib
import html
import logging
import os
import re
import sqlite3
import sys
from typing import Callable, List, Literal, Tuple, Optional
import sys
from urllib.parse import quote, unquote

# Third-party used throughout
import pandas as pd  # type: ignore

# --- Configuration defaults and constants ---
REPORT_TEMPLATE_VERSION = "v2.0"

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
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
        log_path = os.path.join(LOGS_DIR, "app.log")
        from logging.handlers import RotatingFileHandler

        fh = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logging.getLogger().addHandler(fh)
        logger.info(f"File logging to: {log_path}")
    except Exception as _e:
        logger.warning(f"Failed to set up file logging: {_e}")

# spaCy disabled placeholder
nlp = None  # type: ignore

# --- Third-party imports (guarded) ---
try:
    import pdfplumber
except Exception as e:
    pdfplumber = None  # type: ignore
    logger.warning(f"pdfplumber unavailable: {e}")

try:
    import pytesseract
except Exception as e:
    pytesseract = None  # type: ignore
    logger.warning(f"pytesseract unavailable: {e}")

try:
    from transformers import pipeline
    from nlg_service import NLGService

except ImportError:
    pipeline = None
    logger.warning("transformers library not found. BioBERT NER will be disabled.")

try:
    from PIL import Image, UnidentifiedImageError
except Exception as e:
    Image = None  # type: ignore
    class UnidentifiedImageError(Exception): ...
    logger.warning(f"PIL unavailable: {e}")

try:
    import numpy as np
except ImportError:
    np = None
    logger.warning("Numpy unavailable. Some analytics features will be disabled.")

# --- FHIR Imports (guarded) ---
try:
    from fhir.resources.bundle import Bundle
    from fhir.resources.diagnosticreport import DiagnosticReport
    from fhir.resources.observation import Observation
    from fhir.resources.codeableconcept import CodeableConcept
    from fhir.resources.coding import Coding
    from fhir.resources.reference import Reference
    from fhir.resources.meta import Meta
except ImportError:
    class Bundle: pass
    class DiagnosticReport: pass
    class Observation: pass
    class CodeableConcept: pass
    class Coding: pass
    class Reference: pass
    class Meta: pass
    logger.warning("fhir.resources library not found. FHIR export will be disabled.")

# Matplotlib for analytics chart
import matplotlib
matplotlib.use('Agg')
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
except ImportError:
    class FigureCanvas: # type: ignore
        def __init__(self, figure=None): pass
        def mpl_connect(self, s, f): pass
        def draw(self): pass
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle


# Fairlearn for bias auditing
try:
    from fairlearn.metrics import MetricFrame, demographic_parity_difference, selection_rate
except ImportError:
    MetricFrame = None
    demographic_parity_difference = None
    selection_rate = None
    logger.warning("fairlearn library not found. Bias auditing will be disabled.")

# PyQt (guarded)
try:
    from PyQt6.QtWidgets import (
        QMainWindow, QToolBar, QLabel, QFileDialog, QMessageBox, QApplication,
        QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QPushButton,
        QSpinBox, QCheckBox, QTextEdit, QSplitter, QGroupBox, QListWidget, QWidget,
from PyQt6.QtWidgets import (
    QMainWindow, QToolBar, QLabel, QFileDialog, QMessageBox, QApplication,
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QPushButton,
    QSpinBox, QCheckBox, QTextEdit, QSplitter, QGroupBox, QListWidget, QWidget,
    QProgressDialog, QSizePolicy, QStatusBar, QProgressBar, QMenu, QTabWidget, QGridLayout,
    QTableWidget, QTableWidgetItem, QListWidgetItem, QRadioButton
)
from PyQt6.QtGui import QAction, QFont, QTextDocument, QPdfWriter, QTextCharFormat, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal as Signal, QObject, QDate
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from spellchecker import SpellChecker

spell = SpellChecker()

# Local imports
try:
    from .local_llm import LocalRAG
    from .rubric_service import RubricService, ComplianceRule
    from .guideline_service import GuidelineService
    from .ner_service import NERService
    from .entity_consolidation_service import EntityConsolidationService
    from .text_chunking import RecursiveCharacterTextSplitter
except ImportError as e:
    logger.error(f"Failed to import local modules: {e}. Ensure you're running as a package.")
    # Define dummy classes if imports fail
    class LocalRAG: pass
    class RubricService: pass
    class ComplianceRule: pass
    class GuidelineService: pass
    class NERService: pass
    class EntityConsolidationService: pass
    class RecursiveCharacterTextSplitter: pass

import logging
logger = logging.getLogger(__name__)

# --- LLM Loader Worker ---
class LLMWorker(QObject):
    """
    A worker class to load the LocalRAG model in a separate thread.
    """
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, model_repo_id: str, model_filename: str):
        super().__init__()
        self.model_repo_id = model_repo_id
        self.model_filename = model_filename

    def run(self):
        """Loads the RAG model and emits a signal when done."""
        try:
            rag_instance = LocalRAG(
                model_repo_id=self.model_repo_id,
                model_filename=self.model_filename
            )
            if rag_instance.is_ready():
                self.finished.emit(rag_instance)
            else:
                self.error.emit("RAG instance failed to initialize.")
        except Exception as e:
            logger.exception("LLMWorker failed to load model.")
            self.error.emit(f"Failed to load AI model: {e}")


class GuidelineWorker(QObject):
    """
    A worker class to load and index guidelines in a separate thread.
    """
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, rag_instance: LocalRAG):
        super().__init__()
        self.rag_instance = rag_instance

    def run(self):
        """Loads and indexes the guidelines and emits a signal when done."""
        try:
            guideline_service = GuidelineService(self.rag_instance)
            sources = [
                "https://www.cms.gov/files/document/r12532bp.pdf",
                "test_data/static_guidelines.txt"
            ]
            guideline_service.load_and_index_guidelines(sources)
            if guideline_service.is_index_ready:
                self.finished.emit(guideline_service)
            else:
                self.error.emit("Guideline index failed to build.")
        except Exception as e:
            logger.exception("GuidelineWorker failed.")
            self.error.emit(f"Failed to load guidelines: {e}")


def _generate_suggested_questions(issues: list) -> list[str]:
    """Generates a list of suggested questions based on high-priority findings."""
    suggestions = []

    QUESTION_MAP = {
        "Provider signature/date possibly missing": "Why are signatures and dates important for compliance?",
        "Goals may not be measurable/time-bound": "What makes a therapy goal 'measurable' and 'time-bound'?",
        "Medical necessity not explicitly supported": "Can you explain 'Medical Necessity' in the context of a therapy note?",
        "Assistant supervision context unclear": "What are the supervision requirements for therapy assistants?",
        "Plan/Certification not clearly referenced": "How should the Plan of Care be referenced in a note?",
    }

    # Prioritize flags, then findings
    sorted_issues = sorted(issues, key=lambda x: ({"flag": 0, "finding": 1}.get(x.get('severity'), 2)))

    for issue in sorted_issues:
        if len(suggestions) >= 3:
            break

        title = issue.get('title')
        if title in QUESTION_MAP and QUESTION_MAP[title] not in suggestions:
            suggestions.append(QUESTION_MAP[title])

    logger.info(f"Generated {len(suggestions)} suggested questions.")
    return suggestions
def _generate_suggested_questions(issues: list) -> list[str]:
    """Generates a list of suggested questions based on high-priority findings."""
    suggestions = []
    QUESTION_MAP = {
        "Provider signature/date possibly missing": "Why are signatures and dates important for compliance?",
        "Goals may not be measurable/time-bound": "What makes a therapy goal 'measurable' and 'time-bound'?",
        "Medical necessity not explicitly supported": "Can you explain 'Medical Necessity' in the context of a therapy note?",
        "Assistant supervision context unclear": "What are the supervision requirements for therapy assistants?",
        "Plan/Certification not clearly referenced": "How should the Plan of Care be referenced in a note?",
    }
    sorted_issues = sorted(issues, key=lambda x: ({"flag": 0, "finding": 1}.get(x.get('severity'), 2)))
    for issue in sorted_issues:
        if len(suggestions) >= 3:
            break
        title = issue.get('title')
        if title in QUESTION_MAP and QUESTION_MAP[title] not in suggestions:
            suggestions.append(QUESTION_MAP[title])
    logger.info(f"Generated {len(suggestions)} suggested questions.")
    return suggestions

except Exception:
    class QMainWindow: ...
    class QToolBar:
        def addWidget(self, *_, **__): ...
        def setMovable(self, *_: object) -> None: ...
    class QLabel:
        def __init__(self, *_, **__): ...
        def setText(self, *_): ...
        def setStyleSheet(self, *_): ...
    class QFileDialog:
        @staticmethod
        def getOpenFileName(*_, **__) -> Tuple[str, str]: return ("", "")
        @staticmethod
        def getExistingDirectory(*_, **__) -> str: return ""
    class QMessageBox:
        @staticmethod
        def information(*_, **__): ...
        @staticmethod
        def warning(*_, **__): ...
        @staticmethod
        def question(*_, **__): return "Yes"
    class QApplication:
        def __init__(self, *_): ...
        @staticmethod
        def instance(): return None
        @staticmethod
        def setOverrideCursor(*_): ...
        @staticmethod
        def restoreOverrideCursor(): ...
        def setStyleSheet(self, *_): ...
        def setFont(self, *_): ...
    class QAction:
        def __init__(self, *_, **__): ...
        def triggered(self, *_): ...
        def setShortcut(self, *_): ...
    class QDialog:
        def __init__(self, *_, **__): ...
        def exec(self): ...
        def setWindowTitle(self, *_): ...
        def accept(self): ...
        def reject(self): ...
        def show(self): ...
    class QVBoxLayout:
        def __init__(self, *_, **__): ...
        def addLayout(self, *_): ...
        def addWidget(self, *_): ...
        def setContentsMargins(self, *_): ...
        def setSpacing(self, *_): ...
    class QHBoxLayout:
        def addWidget(self, *_): ...
        def addStretch(self, *_): ...
        def setSpacing(self, *_): ...
    class QLineEdit:
        def __init__(self, *_, **__): ...
        def setText(self, *_): ...
        def text(self): return ""
    class QComboBox:
        def __init__(self, *_, **__): ...
        def addItems(self, *_): ...
        def setCurrentText(self, *_): ...
        def currentText(self): return ""
    class QPushButton:
        def __init__(self, *_, **__): ...
        def clicked(self): ...
        def setMinimumHeight(self, *_): ...
        def setFont(self, *_): ...
        def setText(self, *_): ...
        def setStyleSheet(self, *_): ...
        def setSizePolicy(self, *_): ...
    class QSpinBox:
        def __init__(self, *_, **__): ...
        def setRange(self, *_): ...
        def setValue(self, *_): ...
        def value(self): return 0
    class QCheckBox:
        def __init__(self, *_, **__): ...
        def setChecked(self, *_): ...
        def isChecked(self): return False
    class QTextEdit:
        def __init__(self, *_, **__): ...
        def setReadOnly(self, *_): ...
        def setPlainText(self, *_): ...
        def setPlaceholderText(self, *_): ...
        def setMinimumHeight(self, *_): ...
        def setMaximumHeight(self, *_): ...
        def setFixedHeight(self, *_): ...
        def setSizePolicy(self, *_): ...
        def append(self, *_): ...
        def toPlainText(self): return ""
    class QSplitter:
        def __init__(self, *_, **__): ...
        def addWidget(self, *_): ...
        def setChildrenCollapsible(self, *_): ...
        def setFixedHeight(self, *_): ...
    class QGroupBox:
        def __init__(self, title=""): ...
        def setLayout(self, *_): ...
    class QWidget:
        def __init__(self, *_, **__): ...
        def setLayout(self, *_): ...
    class QProgressDialog: ...
    class QSizePolicy:
        class Policy:
            Expanding = 0
            Preferred = 0
    class QStatusBar:
        def clearMessage(self): ...
        def addPermanentWidget(self, *_): ...
        def showMessage(self, *_): ...
    class QProgressBar:
        def __init__(self, *_, **__): ...
        def setRange(self, *_): ...
        def setValue(self, *_): ...
        def setFormat(self, *_): ...
        def setVisible(self, *_): ...
        def setMinimumHeight(self, *_): ...
        def setSizePolicy(self, *_): ...
    class QTabWidget:
        def __init__(self, *_, **__): ...
        def addTab(self, *_, **__): ...
    class QGridLayout: ...
    class QObject: pass
    class Signal:
        def __init__(self, *args, **kwargs): pass
        def connect(self, *args, **kwargs): pass
        def emit(self, *args, **kwargs): pass
    def pyqtSignal(*args, **kwargs): return Signal()
    class FigureCanvas: ...
    class Figure: ...
    class LocalRAG: ...
    class RubricService: ...
    class ComplianceRule: ...
    class QPdfWriter: ...
    class QTextCharFormat: ...
    class QColor: ...
    class Qt: ...
    class QThread: ...
# Local imports with error handling to ensure graceful degradation
try:
    from .entity_consolidation_service import EntityConsolidationService
    from .local_llm import LocalRAG
    from .rubric_service import RubricService, ComplianceRule
    from .guideline_service import GuidelineService
    from .text_chunking import RecursiveCharacterTextSplitter
    from .nlg_service import NLGService
except ImportError as e:
    logger.error(f"Failed to import local modules: {e}. Ensure you're running as a package.")
    # Define dummy classes if imports fail, to prevent crashing on startup
    class LocalRAG: pass
    class RubricService: pass
    class ComplianceRule: pass
    class GuidelineService: pass
    class RecursiveCharacterTextSplitter: pass
    class NLGService: pass

# Optional: dummy classes for QWebEngineView or QWebEngineSettings if really needed
class QWebEngineView: ...
class QWebEngineSettings: ...

# Service initialization
service = BiasAuditService()
report = service.run_bias_audit()


# --- LLM Loader Worker ---
class LLMWorker(QObject):
    """
    A worker class to load the LocalRAG model in a separate thread.
    """
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, model_repo_id: str, model_filename: str):
        super().__init__()
        self.model_repo_id = model_repo_id
        self.model_filename = model_filename

    def run(self):
        """Loads the RAG model and emits a signal when done."""
        try:
            rag_instance = LocalRAG(
                model_repo_id=self.model_repo_id,
                model_filename=self.model_filename
            )
            if rag_instance.is_ready():
                self.finished.emit(rag_instance)
            else:
                self.error.emit("RAG instance failed to initialize.")
        except Exception as e:
            logger.exception("LLMWorker failed to load model.")
            self.error.emit(f"Failed to load AI model: {e}")

class GuidelineWorker(QObject):
    """
    A worker class to load and index guidelines in a separate thread.
    """
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, rag_instance: LocalRAG):
        super().__init__()
        self.rag_instance = rag_instance

    def run(self):
        """Loads and indexes the guidelines and emits a signal when done."""
        try:
            guideline_service = GuidelineService(self.rag_instance)
            sources = [
                "https://www.cms.gov/files/document/r12532bp.pdf",
                "test_data/static_guidelines.txt"
            ]
            guideline_service.load_and_index_guidelines(sources)
            if guideline_service.is_index_ready:
                self.finished.emit(guideline_service)
            else:
                self.error.emit("Guideline index failed to build.")
        except Exception as e:
            logger.exception("GuidelineWorker failed.")
            self.error.emit(f"Failed to load guidelines: {e}")


class DrillDownDialog(QDialog):
    """
    A dialog to display the detailed findings from a drill-down action.
    """
    run_selected = Signal(int)

    def __init__(self, data: List[dict], category: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Drill-Down: {category.title()} Details")
        self.setMinimumSize(800, 400)

        self.data = data

        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["File Name", "Run Time", "Category", "Title", "Detail"])
        self.table.setRowCount(len(data))

        for i, row_data in enumerate(data):
            self.table.setItem(i, 0, QTableWidgetItem(row_data.get("file_name", "")))
            self.table.setItem(i, 1, QTableWidgetItem(row_data.get("run_time", "")))
            self.table.setItem(i, 2, QTableWidgetItem(row_data.get("category", "")))
            self.table.setItem(i, 3, QTableWidgetItem(row_data.get("title", "")))
            self.table.setItem(i, 4, QTableWidgetItem(row_data.get("detail", "")))

        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.resizeColumnsToContents()
        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)

    def on_item_double_clicked(self, item: QTableWidgetItem):
        """When a row is double-clicked, emit a signal with the run_id and close."""
        row_index = item.row()
        run_id = self.data[row_index].get('run_id')
        if run_id is not None:
            self.run_selected.emit(int(run_id))
            self.accept()

def _format_entities_for_rag(entities: list[NEREntity]) -> list[str]:
    """Converts a list of NEREntity objects into a list of descriptive strings."""
    if not entities:
        return []

    formatted_strings = []
    for entity in entities:
        description = (
            f"An entity of type '{entity.label}' with the text '{entity.text}' was found in the document."
        )
        if entity.context:
            description += f" It was found in a sentence related to '{entity.context}'."

        # Join models if there are multiple
        models_str = ", ".join(entity.models)
        description += f" (Detected by {models_str})"

        formatted_strings.append(description)

    logger.info(f"Formatted {len(formatted_strings)} consolidated entities for RAG context.")
    return formatted_strings

def _generate_suggested_questions(issues: list) -> list[str]:
    """Generates a list of suggested questions based on high-priority findings."""
    suggestions = []
    QUESTION_MAP = {
        "Provider signature/date possibly missing": "Why are signatures and dates important for compliance?",
        "Goals may not be measurable/time-bound": "What makes a therapy goal 'measurable' and 'time-bound'?",
        "Medical necessity not explicitly supported": "Can you explain 'Medical Necessity' in the context of a therapy note?",
        "Assistant supervision context unclear": "What are the supervision requirements for therapy assistants?",
        "Plan/Certification not clearly referenced": "How should the Plan of Care be referenced in a note?",
    }
    # Prioritize flags, then findings
    sorted_issues = sorted(issues, key=lambda x: ({"flag": 0, "finding": 1}.get(x.get('severity'), 2)))
    for issue in sorted_issues:
        if len(suggestions) >= 3:
            break
        title = issue.get('title')
        if title in QUESTION_MAP and QUESTION_MAP[title] not in suggestions:
            suggestions.append(QUESTION_MAP[title])
    logger.info(f"Generated {len(suggestions)} suggested questions.")
    return suggestions

# --- Helper Exceptions ---
class ParseError(Exception): ...
class OCRFailure(Exception): ...
class ReportExportError(Exception): ...

# --- Settings persistence (SQLite) ---
def _ensure_directories() -> None:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(DATABASE_PATH)), exist_ok=True)
        os.makedirs(os.path.abspath(REPORTS_DIR), exist_ok=True)
        os.makedirs(LOGS_DIR, exist_ok=True)
    except Exception as e:
        logger.warning(f"Failed to ensure directories: {e}")

def _is_valid_sqlite_db(file_path: str) -> bool:
    try:
        if not os.path.exists(file_path):
            return True
        if not os.path.isfile(file_path):
            return False
        with open(file_path, "rb") as f:
            header = f.read(16)
        if header != b"SQLite format 3\x00":
            return False
        with sqlite3.connect(file_path) as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA integrity_check")
            row = cur.fetchone()
            return bool(row and row[0] == "ok")
    except Exception as e:
        logger.warning(f"Failed to validate DB file {file_path}: {e}")
        return False

def _backup_corrupt_db(file_path: str) -> None:
    try:
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = f"{file_path}.corrupt-{ts}.bak"
        os.replace(file_path, backup_path)
        logger.warning(f"Backed up invalid DB: {backup_path}")
    except Exception as e:
        logger.error(f"Failed to back up invalid DB: {e}")

def _prepare_database_file() -> None:
    try:
        if not _is_valid_sqlite_db(DATABASE_PATH):
            _backup_corrupt_db(DATABASE_PATH)
    except Exception as e:
        logger.error(f"DB preparation failed: {e}")

def _ensure_core_schema(conn: sqlite3.Connection) -> None:
    try:
        cur = conn.cursor()
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS settings
                    (
                        key
                        TEXT
                        PRIMARY
                        KEY,
                        value
                        TEXT
                    )
                    """)
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_cache
                    (
                        file_fingerprint
                        TEXT
                        NOT
                        NULL,
                        settings_fingerprint
                        TEXT
                        NOT
                        NULL,
                        outputs_json
                        TEXT
                        NOT
                        NULL,
                        created_at
                        TEXT
                        NOT
                        NULL,
                        PRIMARY
                        KEY
                    (
                        file_fingerprint,
                        settings_fingerprint
                    )
                        )
                    """)
        conn.commit()
    except Exception as e:
        logger.warning(f"Ensure core schema failed: {e}")

def _get_db_connection() -> sqlite3.Connection:
    _ensure_directories()
    _prepare_database_file()
    try:
        conn = sqlite3.connect(DATABASE_PATH)
    except sqlite3.DatabaseError as e:
        logger.warning(f"sqlite connect failed: {e}; attempting recreate")
        _backup_corrupt_db(DATABASE_PATH)
        conn = sqlite3.connect(DATABASE_PATH)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON")
        cur.execute("PRAGMA journal_mode = WAL")
        cur.execute("PRAGMA synchronous = NORMAL")
        conn.commit()
        _ensure_core_schema(conn)
        _ensure_analytics_schema(conn)
    except Exception as e:
        logger.warning(f"SQLite PRAGMA/schema setup partial: {e}")
    return conn

def get_setting(key: str) -> Optional[str]:
    try:
        with _get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cur.fetchone()
            return row[0] if row else None
    except Exception:
        return None

def set_setting(key: str, value: str) -> None:
    try:
        with _get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
            conn.commit()
    except Exception:
        ...

def get_bool_setting(key: str, default: bool) -> bool:
    raw = get_setting(key)
    if raw is None:
        return default
    return str(raw).lower() in ("1", "true", "yes", "on")

def set_bool_setting(key: str, value: bool) -> None:
    set_setting(key, "1" if value else "0")

def get_int_setting(key: str, default: int) -> int:
    raw = get_setting(key)
    if raw is None:
        return default
    try:
        return int(str(raw).strip())
    except Exception:
        return default

def get_str_setting(key: str, default: str) -> str:
    raw = get_setting(key)
    return default if raw is None else str(raw)

def set_str_setting(key: str, value: str) -> None:
    set_setting(key, value)

# --- Recent files helpers ---
def _load_recent_files() -> list[str]:
    try:
        import json
        raw = get_setting("recent_files")
        if not raw:
            return []
        lst = json.loads(raw)
        if not isinstance(lst, list):
            return []
        seen: set[str] = set()
        out: list[str] = []
        for x in lst:
            if isinstance(x, str) and x not in seen:
                seen.add(x)
                out.append(x)
        limit = get_int_setting("recent_max", 20)
        return out[:max(1, limit)]
    except Exception:
        return []

def _save_recent_files(files: list[str]) -> None:
    try:
        import json
        limit = get_int_setting("recent_max", 20)
        set_setting("recent_files", json.dumps(files[:max(1, limit)], ensure_ascii=False))
    except Exception:
        ...

def add_recent_file(path: str) -> None:
    if not path:
        return
    files = _load_recent_files()
    files = [p for p in files if p != path]
    files.insert(0, path)
    _save_recent_files(files)

# --- File/report helpers ---
def ensure_reports_dir_configured() -> str:
    stored = os.getenv("SPEC_KIT_REPORTS") or get_setting("reports_dir") or REPORTS_DIR
    try:
        os.makedirs(stored, exist_ok=True)
        marker = os.path.join(stored, ".spec_kit_reports")
        if not os.path.exists(marker):
            with open(marker, "w", encoding="utf-8") as m:
                m.write("Managed by SpecKit. Safe to purge generated reports.\n")
    except Exception as e:
        logger.warning(f"Ensure reports dir failed: {e}")
    return stored

def _format_mmddyyyy(dt) -> str:
    return dt.strftime("%m%d%Y")

def _next_report_number() -> int:
    from datetime import datetime
    today = _format_mmddyyyy(datetime.now())
    last_date = get_setting("last_report_date")
    raw = get_setting("report_counter")
    if last_date != today or raw is None:
        num = 1
    else:
        try:
            num = int(raw)
        except Exception:
            num = 1
    set_setting("report_counter", str(num + 1))
    set_setting("last_report_date", today)
    return num

def generate_report_paths() -> Tuple[str, str]:
    from datetime import datetime
    base = ensure_reports_dir_configured()
    stem = f"{_format_mmddyyyy(datetime.now())}report{_next_report_number()}"
    return os.path.join(base, f"{stem}.pdf"), os.path.join(base, f"{stem}.csv")

# --- PHI scrubber ---
_PHI_PATTERNS: List[Tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
    (re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[PHONE]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[EMAIL]"),
    (re.compile(r"\b(?:0?[1-9]|1[0-2])[-/](?:0?[1-9]|[12]\d|3[01])[-/](?:\d{2}|\d{4})\b"), "[DATE]"),
    (re.compile(r"\b\d{6,10}\b"), "[MRN]"),
    (re.compile(r"\b\d{1,5}\s+[A-Za-z0-9.\- ]+\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Ln|Lane)\b", re.I),
     "[ADDR]"),
]

def scrub_phi(text: str) -> str:
    if not isinstance(text, str):
        return text  # type: ignore[return-value]
    out = text
    for pat, repl in _PHI_PATTERNS:
        out = re.sub(pat, repl, out)
    return out

# --- Utilities ---
def _now_iso() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _open_path(p: str) -> None:
    try:
        if os.name == "nt":
            os.startfile(p)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            os.system(f"open \"{p}\"")
        else:
            os.system(f"xdg-open \"{p}\"")
    except Exception as e:
        logger.warning(f"Failed to open path {p}: {e}")

# --- Parsing (PDF/DOCX/CSV/XLSX/Images with optional OCR) ---
def split_sentences(text: str) -> list[str]:
    if not text:
        return []
    sents = [p.strip() for p in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text) if p.strip()]
    if not sents:
        sents = text.splitlines()
    return [s for s in sents if s]

def _correct_spelling(text: str) -> str:
    """Corrects spelling errors in a given text, preserving punctuation."""
    if not isinstance(text, str):
        return text

    corrected_parts = []
    # Tokenize into words and non-words (punctuation, whitespace)
    # This regex finds sequences of word characters or single non-word characters.
    tokens = re.findall(r"(\w+)|([^\w])", text)

    for word, non_word in tokens:
        if word:
            # Correct the word part, or keep original if no correction found
            corrected_word = spell.correction(word) or word
            corrected_parts.append(corrected_word)
        if non_word:
            # Append the non-word part (punctuation, space, newline, etc.)
            corrected_parts.append(non_word)

    return "".join(corrected_parts)

def parse_document_content(file_path: str) -> List[Tuple[str, str]]:
    """
    Parses the content of a document and splits it into chunks.
    Uses a recursive character text splitter for more effective chunking.
    """
    if not os.path.exists(file_path):
        return [(f"Error: File not found at {file_path}", "File System")]

    ext = os.path.splitext(file_path)[1].lower()

    # Initialize the text splitter with configurable settings
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=get_int_setting("chunk_size", 1000),
        chunk_overlap=get_int_setting("chunk_overlap", 200),
    )

    try:
        chunks_with_source: list[tuple[str, str]] = []
        full_text = ""

        # --- Step 1: Extract text from the document based on its type ---
        if ext == ".pdf":
            if not pdfplumber:
                return [("Error: pdfplumber not available.", "PDF Parser")]
            with pdfplumber.open(file_path) as pdf:
                # Process page by page to maintain source information
                for i, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text() or ""
                    corrected_text = _correct_spelling(page_text)
                    page_chunks = text_splitter.split_text(corrected_text)
                    for chunk in page_chunks:
                        if chunk:
                            chunks_with_source.append((chunk, f"Page {i}"))
        elif ext == ".docx":
            try:
                from docx import Document
            except Exception:
                return [("Error: python-docx not available.", "DOCX Parser")]
            docx_doc = Document(file_path)
            # Process paragraph by paragraph
            for i, para in enumerate(docx_doc.paragraphs, start=1):
                if not para.text.strip():
                    continue
                corrected_text = _correct_spelling(para.text)
                para_chunks = text_splitter.split_text(corrected_text)
                for chunk in para_chunks:
                    if chunk:
                        chunks_with_source.append((chunk, f"Paragraph {i}"))
        elif ext in [".xlsx", ".xls", ".csv"]:
            try:
                if ext in [".xlsx", ".xls"]:
                    df = pd.read_excel(file_path)
                    if isinstance(df, dict):
                        df = next(iter(df.values()))
                else:
                    df = pd.read_csv(file_path)
                content = df.to_string(index=False)
                corrected_content = _correct_spelling(content)
                data_chunks = text_splitter.split_text(corrected_content)
                for chunk in data_chunks:
                    if chunk:
                        chunks_with_source.append((chunk, "Table"))
            except Exception as e:
                return [(f"Error: Failed to read tabular file: {e}", "Data Parser")]
        elif ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"]:
            if not Image or not pytesseract:
                return [("Error: OCR dependencies not available.", "OCR Parser")]
            try:
                img = Image.open(file_path)
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                txt = pytesseract.image_to_string(img, lang=get_str_setting("ocr_lang", "eng"))
                corrected_txt = _correct_spelling(txt or "")
                ocr_chunks = text_splitter.split_text(corrected_txt)
                for chunk in ocr_chunks:
                    if chunk:
                        chunks_with_source.append((chunk, "Image (OCR)"))
            except UnidentifiedImageError as e:
                return [(f"Error: Unidentified image: {e}", "OCR Parser")]
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                txt = f.read()
            corrected_txt = _correct_spelling(txt)
            txt_chunks = text_splitter.split_text(corrected_txt)
            for chunk in txt_chunks:
                if chunk:
                    chunks_with_source.append((chunk, "Text File"))
        else:
            return [(f"Error: Unsupported file type: {ext}", "File Handler")]

        return chunks_with_source if chunks_with_source else [("Info: No text could be extracted from the document.", "System")]

    except FileNotFoundError:
        return [(f"Error: File not found at {file_path}", "File System")]
    except Exception as e:
        logger.exception("parse_document_content failed")
        return [(f"Error: An unexpected error occurred: {e}", "System")]

# --- Dedup helpers ---
def _normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())

def _similarity(a: str, b: str) -> float:
    import difflib
    return difflib.SequenceMatcher(a=_normalize_text(a), b=_normalize_text(b)).ratio()

def collapse_similar_sentences_simple(items: list[Tuple[str, str]], threshold: float) -> list[Tuple[str, str]]:
    kept: list[Tuple[str, str]] = []
    for t, s in items:
        if not kept:
            kept.append((t, s))
            continue
        sim = max(_similarity(t, kt) for (kt, _) in kept)
        if sim < threshold:
            kept.append((t, s))
    return kept

def collapse_similar_sentences_tfidf(items: list[Tuple[str, str]], threshold: float) -> list[Tuple[str, str]]:
    texts = [t for t, _ in items]
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
        from sklearn.metrics.pairwise import cosine_similarity  # type: ignore
        vect = TfidfVectorizer(min_df=1, ngram_range=(1, 2), max_features=10000)
        X = vect.fit_transform([_normalize_text(t) for t in texts])
        sim = cosine_similarity(X)
    except Exception:
        return collapse_similar_sentences_simple(items, threshold)
    kept_idx: list[int] = []
    for i in range(len(items)):
        if not kept_idx:
            kept_idx.append(i)
            continue
        if max(sim[i, j] for j in kept_idx) < threshold:
            kept_idx.append(i)
    return [items[i] for i in kept_idx]

def build_rich_summary(original: list[Tuple[str, str]], collapsed: list[Tuple[str, str]]) -> dict:
    from collections import Counter

    def tok(text: str) -> list[str]:
        tokens = re.findall(r"[A-Za-z']+", text.lower())
        stop = {"the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "is", "are", "was", "were", "be",
                "as", "at", "by", "from", "that"}
        return [t for t in tokens if t not in stop]

    total_raw = len(original)
    total_final = len(collapsed)
    by_source = Counter(s for _, s in collapsed)
    lengths = [len(t) for t, _ in collapsed]
    avg_len = (sum(lengths) / len(lengths)) if lengths else 0
    p95 = (sorted(lengths)[int(0.95 * (len(lengths) - 1))] if lengths else 0)
    all_text = " ".join(t for t, _ in collapsed)
    tokens = tok(all_text)
    top_tokens = Counter(tokens).most_common(15)
    return {
        "total_sentences_raw": total_raw,
        "total_sentences_final": total_final,
        "dedup_removed": max(0, total_raw - total_final),
        "avg_sentence_length_chars": round(avg_len, 1),
        "p95_sentence_length_chars": p95,
        "total_words": len(tokens),
        "by_source": dict(by_source),
        "top_tokens": top_tokens,
    }

def count_categories(issues: list[dict]) -> dict:
    from collections import Counter
    c = Counter((i.get("category") or "General") for i in issues)
    return dict(c)

def _ensure_analytics_schema(conn: sqlite3.Connection) -> None:
    try:
        cur = conn.cursor()
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_runs
                    (
                        id
                        INTEGER
                        PRIMARY
                        KEY
                        AUTOINCREMENT,
                        file_name
                        TEXT
                        NOT
                        NULL,
                        run_time
                        TEXT
                        NOT
                        NULL,
                        pages_est
                        INTEGER,
                        flags
                        INTEGER,
                        findings
                        INTEGER,
                        suggestions
                        INTEGER,
                        notes
                        INTEGER,
                        sentences_final
                        INTEGER,
                        dedup_removed
                        INTEGER,
                        compliance_score
                        REAL,
                        mode
                        TEXT,
                        file_path TEXT
                    )
                    """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_runs_time ON analysis_runs(run_time)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_runs_file ON analysis_runs(file_name)")
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_issues
                    (
                        id
                        INTEGER
                        PRIMARY
                        KEY
                        AUTOINCREMENT,
                        run_id
                        INTEGER
                        NOT
                        NULL,
                        severity
                        TEXT
                        NOT
                        NULL,
                        category
                        TEXT,
                        title
                        TEXT,
                        detail
                        TEXT,
                        confidence
                        REAL,
                        FOREIGN
                        KEY
                    (
                        run_id
                    ) REFERENCES analysis_runs
                    (
                        id
                    ) ON DELETE CASCADE
                        )
                    """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_issues_run ON analysis_issues(run_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_issues_sev ON analysis_issues(severity)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_issues_cat ON analysis_issues(category)")

        # --- Simple schema migration for label column ---
        cur.execute("PRAGMA table_info(analysis_issues)")
        columns = [row[1] for row in cur.fetchall()]
        if "label" not in columns:
            cur.execute("ALTER TABLE analysis_issues ADD COLUMN label TEXT")
            logger.info("Upgraded analysis_issues table to include 'label' column.")
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_snapshots
                    (
                        file_fingerprint
                        TEXT
                        NOT
                        NULL,
                        settings_fingerprint
                        TEXT
                        NOT
                        NULL,
                        summary_json
                        TEXT
                        NOT
                        NULL,
                        created_at
                        TEXT
                        NOT
                        NULL,
                        PRIMARY
                        KEY
                    (
                        file_fingerprint,
                        settings_fingerprint
                    )
                        )
                    """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_time ON analysis_snapshots(created_at)")

        # --- Simple schema migration for compliance_score and json_report_path ---
        cur.execute("PRAGMA table_info(analysis_runs)")
        columns = [row[1] for row in cur.fetchall()]
        if "compliance_score" not in columns:
            cur.execute("ALTER TABLE analysis_runs ADD COLUMN compliance_score REAL")
            logger.info("Upgraded analysis_runs table to include 'compliance_score' column.")
QProgressDialog, QSizePolicy, QStatusBar, QProgressBar, QMenu, QTabWidget, QGridLayout, \
QTableWidget, QTableWidgetItem, QListWidgetItem


        cur.execute("""
                    CREATE TABLE IF NOT EXISTS reviewed_findings
                    (
                        id
                        INTEGER
                        PRIMARY
                        KEY
                        AUTOINCREMENT,
                        analysis_issue_id
                        INTEGER
                        NOT
                        NULL,
                        user_feedback
                        TEXT
                        NOT
                        NULL,
                        reviewed_at
                        TEXT
                        NOT
                        NULL,
                        notes
                        TEXT,
                        citation_text
                        TEXT,
                        model_prediction
                        TEXT,
                        FOREIGN
                        KEY
                    (
                        analysis_issue_id
                    ) REFERENCES analysis_issues
                    (
                        id
                    ) ON DELETE CASCADE
                        )
                    """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_reviews_issue ON reviewed_findings(analysis_issue_id)")

        cur.execute("""
cur.execute("""
    CREATE TABLE IF NOT EXISTS annotations
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        analysis_issue_id INTEGER NOT NULL,
        note TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (analysis_issue_id) REFERENCES analysis_issues (id) ON DELETE CASCADE
    )
""")
cur.execute("CREATE INDEX IF NOT EXISTS idx_annotations_issue ON annotations(analysis_issue_id)")

cur.execute("""
    CREATE TABLE IF NOT EXISTS ner_model_performance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_name TEXT NOT NULL,
        entity_label TEXT NOT NULL,
        confirmations INTEGER DEFAULT 0,
        rejections INTEGER DEFAULT 0,
        UNIQUE(model_name, entity_label)
    )
""")
cur.execute("CREATE INDEX IF NOT EXISTS idx_ner_perf_model_label ON ner_model_performance(model_name, entity_label)")

cur.execute("""
    CREATE TABLE IF NOT EXISTS adjudication_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        analysis_issue_id INTEGER NOT NULL,
        user_decision TEXT NOT NULL,
        corrected_label TEXT,
        notes TEXT,
        adjudicated_at TEXT NOT NULL,
        FOREIGN KEY(analysis_issue_id) REFERENCES analysis_issues(id) ON DELETE CASCADE
    )
""")
cur.execute("CREATE INDEX IF NOT EXISTS idx_adjudication_log_issue ON adjudication_log(analysis_issue_id)")

        cur.execute("""
                    CREATE TABLE IF NOT EXISTS reviewed_findings
                    (
                        id
                        INTEGER
                        PRIMARY
                        KEY
                        AUTOINCREMENT,
                        analysis_issue_id
                        INTEGER
                        NOT
                        NULL,
                        user_feedback
                        TEXT
                        NOT
                        NULL,
                        reviewed_at
                        TEXT
                        NOT
                        NULL,
                        notes
                        TEXT,
                        citation_text
                        TEXT,
                        model_prediction
                        TEXT,
                        FOREIGN
                        KEY
                    (
                        analysis_issue_id
                    ) REFERENCES analysis_issues
                    (
                        id
                    ) ON DELETE CASCADE
                        )
                    """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_reviews_issue ON reviewed_findings(analysis_issue_id)")

        conn.commit()
    except Exception as e:
        logger.warning(f"Ensure analytics schema failed: {e}")

def persist_analysis_run(file_path: str, run_time: str, metrics: dict, issues_scored: list[dict],
if "json_report_path" not in columns:
    cur.execute("ALTER TABLE analysis_runs ADD COLUMN json_report_path TEXT")
    logger.info("Upgraded analysis_runs table to include 'json_report_path' column.")

if "disciplines" not in columns:
    cur.execute("ALTER TABLE analysis_runs ADD COLUMN disciplines TEXT")
    logger.info("Upgraded analysis_runs table to include 'disciplines' column.")

if "file_path" not in columns:
    cur.execute("ALTER TABLE analysis_runs ADD COLUMN file_path TEXT")
    logger.info("Upgraded analysis_runs table to include 'file_path' column.")

    try:
        import json
        disciplines_json = json.dumps(disciplines)
        with _get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                        INSERT INTO analysis_runs (file_name, run_time, pages_est, flags, findings, suggestions, notes,
..., mode, json_report_path, disciplines, file_path)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            os.path.basename(file_path), run_time,
                            int(metrics.get("pages", 0)), int(metrics.get("flags", 0)), int(metrics.get("findings", 0)),
                            int(metrics.get("suggestions", 0)), int(metrics.get("notes", 0)),
                            int(metrics.get("sentences_final", 0)), int(metrics.get("dedup_removed", 0)),
float(compliance.get("score", 0.0)), mode, json_path, disciplines_json, file_path

                        ))
            run_id = int(cur.lastrowid)
            if issues_scored:
                cur.executemany("""
                                INSERT INTO analysis_issues (run_id, severity, category, title, detail, confidence, label)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, [(run_id, it.get("severity", ""), it.get("category", ""), it.get("title", ""),
                                       it.get("detail", ""), float(it.get("confidence", 0.0)), it.get("label")) for it in issues_scored])
            conn.commit()
            return run_id
    except Exception as e:
        logger.warning(f"persist_analysis_run failed: {e}")
        return None


def update_ner_performance(model_name: str, entity_label: str, validation_status: str) -> None:
    """
    Updates the performance table for a given NER model and entity label.
    """
    if validation_status not in ("Confirmed", "Rejected"):
        return

    update_column = "confirmations" if validation_status == "Confirmed" else "rejections"

    try:
        with _get_db_connection() as conn:
            cur = conn.cursor()
            # Use INSERT OR IGNORE to ensure the row exists before updating.
            cur.execute("""
                INSERT OR IGNORE INTO ner_model_performance (model_name, entity_label, confirmations, rejections)
                VALUES (?, ?, 0, 0)
            """, (model_name, entity_label))

            # Now, increment the appropriate counter.
            cur.execute(f"""
                UPDATE ner_model_performance
                SET {update_column} = {update_column} + 1
                WHERE model_name = ? AND entity_label = ?
            """, (model_name, entity_label))
            conn.commit()
            logger.info(f"Updated NER performance for {model_name} on label {entity_label} with a {validation_status}.")
    except Exception as e:
        logger.warning(f"Failed to update NER performance for {model_name}: {e}")


class AdjudicationService:
    """
    Handles fetching and saving of adjudication data.
    """
    def __init__(self, db_connection_provider: Callable[[], sqlite3.Connection]):
        self.get_db_connection = db_connection_provider

    def get_adjudication_items(self) -> list[dict]:
        """
        Fetches all findings marked as 'DISAGREEMENT' that haven't been adjudicated yet.
        """
        items = []
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                # Select issues that are disagreements and are not already in the adjudication log
                cur.execute("""
                    SELECT
                        i.id,
                        i.title,
                        i.detail,
                        i.confidence,
                        r.file_name,
                        r.run_time,
                        i.label
                    FROM analysis_issues i
                    JOIN analysis_runs r ON i.run_id = r.id
                    LEFT JOIN adjudication_log a ON i.id = a.analysis_issue_id
                    WHERE i.label = 'DISAGREEMENT' AND a.id IS NULL
                    ORDER BY r.run_time DESC, i.id
                """)
                rows = cur.fetchall()
                for row in rows:
                    items.append({
                        "issue_id": row[0],
                        "title": row[1],
                        "detail": row[2],
                        "confidence": row[3],
                        "file_name": row[4],
                        "run_time": row[5],
                        "label": row[6]
                    })
        except Exception as e:
            logger.error(f"Failed to get adjudication items: {e}")
        return items

    def save_adjudication(self, issue_id: int, decision: str, corrected_label: Optional[str], notes: Optional[str]) -> bool:
        """Saves an adjudication decision to the database."""
        try:
            with self.get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT OR REPLACE INTO adjudication_log (analysis_issue_id, user_decision, corrected_label, notes, adjudicated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (issue_id, decision, corrected_label, notes, _now_iso()))
                conn.commit()
                logger.info(f"Saved adjudication for issue {issue_id}: {decision}")
                return True
        except Exception as e:
            logger.error(f"Failed to save adjudication for issue {issue_id}: {e}")
            return False



def _compute_recent_trends(max_runs: int = 10) -> dict:
    out = {
        "recent_scores": [],
        "score_delta": 0.0,
        "avg_score": 0.0,
        "avg_flags": 0.0,
        "avg_findings": 0.0,
        "avg_suggestions": 0.0,
    }
    try:
        with _get_db_connection() as conn:
            runs = pd.read_sql_query(
                "SELECT compliance_score, flags, findings, suggestions FROM analysis_runs ORDER BY run_time ASC", conn
            )
        if runs.empty:
            return out
        sub = runs.tail(max_runs).copy()
        scores = [float(x) for x in sub["compliance_score"].tolist()]
        out["recent_scores"] = scores
        out["avg_score"] = round(float(sum(scores) / len(scores)), 1) if scores else 0.0
        out["score_delta"] = round((scores[-1] - scores[0]) if len(scores) >= 2 else 0.0, 1)
        out["avg_flags"] = round(float(sub["flags"].mean()), 2)
        out["avg_findings"] = round(float(sub["findings"].mean()), 2)
        out["avg_suggestions"] = round(float(sub["suggestions"].mean()), 2)
    except Exception:
        ...
    return out

# --- Caching helpers ---
def _file_fingerprint(path: str) -> str:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        st = os.stat(path)
        h.update(str(st.st_size).encode())
        h.update(str(int(st.st_mtime)).encode())
        return h.hexdigest()
    except Exception:
        return ""

def _settings_fingerprint(scrub: bool, review_mode: str, dedup: str) -> str:
    import json
    key_parts = {
        "scrub": "1" if scrub else "0",
        "review_mode": review_mode,
        "dedup": dedup,
        "ocr_lang": get_str_setting("ocr_lang", "eng"),
        "logic_v": "4",
    }
    s = json.dumps(key_parts, sort_keys=True)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _load_cached_outputs(file_fp: str, settings_fp: str) -> Optional[dict]:
    try:
        with _get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT outputs_json FROM analysis_cache WHERE file_fingerprint=? AND settings_fingerprint=?",
                        (file_fp, settings_fp))
            row = cur.fetchone()
            if not row:
                return None
            import json
            return json.loads(row[0])
    except Exception:
        return None

def _save_cached_outputs(file_fp: str, settings_fp: str, outputs: dict) -> None:
    try:
        with _get_db_connection() as conn:
            cur = conn.cursor()
            import json
            from datetime import datetime
            cur.execute(
                "INSERT OR REPLACE INTO analysis_cache (file_fingerprint, settings_fingerprint, outputs_json, created_at) VALUES (?, ?, ?, ?)",
                (file_fp, settings_fp, json.dumps(outputs, ensure_ascii=False),
                 datetime.now().isoformat(timespec="seconds")),
            )
            conn.commit()
    except Exception:
        ...

# --- Rule-based audit (interpretive only) ---
_RUBRIC_DEFAULT = "MEDICARE PART B REHABILITATION RUBRIC – SKILLED NURSING FACILITY (SNF)"

def _audit_from_rubric(text: str, selected_disciplines: List[str], strict: bool | None = None) -> list[dict]:
    """
    Performs a dynamic audit based on the selected discipline rubrics.
    """
    if not selected_disciplines:
        return []

def _audit_from_rubric(text: str, selected_disciplines: List[str], strict: bool | None = None) -> list[dict]:
    """
    Performs a dynamic audit based on the selected discipline rubrics.
    """
    if not selected_disciplines:
        return []


    rubric_map = {
        "pt": os.path.join(BASE_DIR, "pt_compliance_rubric.ttl"),
        "ot": os.path.join(BASE_DIR, "ot_compliance_rubric.ttl"),
        "slp": os.path.join(BASE_DIR, "slp_compliance_rubric.ttl"),
    }

    all_rules = []
    for discipline in selected_disciplines:
        path = rubric_map.get(discipline)
        if path and os.path.exists(path):
            try:
                service = RubricService(path)
                all_rules.extend(service.get_rules())
            except Exception as e:
                logger.warning(f"Failed to load rubric for {discipline}: {e}")

    # Remove duplicate rules by title, as some may be shared across rubrics
    seen_titles = set()
    unique_rules = []
    for rule in all_rules:
        if rule.issue_title not in seen_titles:
            unique_rules.append(rule)
            seen_titles.add(rule.issue_title)

    t_lower = text.lower()
    issues = []
    s = bool(strict)

    for rule in unique_rules:
        positive_kws = [kw.lower() for kw in rule.positive_keywords]
        negative_kws = [kw.lower() for kw in rule.negative_keywords]

        triggered = False
        # Case 1: Rule triggers if a positive keyword is found AND a negative keyword is NOT found.
        if rule.positive_keywords and rule.negative_keywords:
            if any(kw in t_lower for kw in positive_kws) and not any(kw in t_lower for kw in negative_kws):
                triggered = True
        # Case 2: Rule triggers if a positive keyword is found (and there are no negative keywords).
        elif rule.positive_keywords and not rule.negative_keywords:
            if any(kw in t_lower for kw in positive_kws):
                triggered = True
        # Case 3: Rule triggers if a negative keyword is NOT found (and there are no positive keywords).
        elif not rule.positive_keywords and rule.negative_keywords:
            if not any(kw in t_lower for kw in negative_kws):
                triggered = True

        if triggered:
            severity = rule.strict_severity if s else rule.severity
            issues.append({
                "severity": severity,
                "title": rule.issue_title,
                "detail": rule.issue_detail,
                "category": rule.issue_category,
                "trigger_keywords": rule.positive_keywords
            })

    return issues


    for rule in unique_rules:
        positive_kws = [kw.lower() for kw in rule.positive_keywords]
        negative_kws = [kw.lower() for kw in rule.negative_keywords]

        triggered = False
        # Case 1: Rule triggers if a positive keyword is found AND a negative keyword is NOT found.
        if rule.positive_keywords and rule.negative_keywords:
            if any(kw in t_lower for kw in positive_kws) and not any(kw in t_lower for kw in negative_kws):
                triggered = True
        # Case 2: Rule triggers if a positive keyword is found (and there are no negative keywords).
        elif rule.positive_keywords and not rule.negative_keywords:
            if any(kw in t_lower for kw in positive_kws):
                triggered = True
        # Case 3: Rule triggers if a negative keyword is NOT found (and there are no positive keywords).
        elif not rule.positive_keywords and rule.negative_keywords:
            if not any(kw in t_lower for kw in negative_kws):
                triggered = True

        if triggered:
            severity = rule.strict_severity if s else rule.severity
            issues.append({
                "severity": severity,
                "title": rule.issue_title,
                "detail": rule.issue_detail,
                "category": rule.issue_category,
                "trigger_keywords": rule.positive_keywords,
                "discipline": rule.discipline
            })

    return issues

def _attach_issue_citations(issues_in: list[dict], records: list[tuple[str, str]], cap: int = 3) -> list[dict]:
    out: list[dict] = []
    for it in issues_in:
        q = (it.get("title", "") + " " + it.get("detail", "")).lower()
        tok = [w for w in re.findall(r"[a-z]{4,}", q)]
        cites: list[tuple[str, str]] = []
        trigger_keywords = it.get("trigger_keywords")

        for (text, src) in records:
            tl = text.lower()
            score = sum(1 for w in tok if w in tl)

            is_citation = score >= max(1, len(tok) // 4)
            if not is_citation and trigger_keywords:
                if any(kw.lower() in tl for kw in trigger_keywords):
                    is_citation = True

            if is_citation:
                text_to_cite = text.strip()

                if trigger_keywords:
                    # Sort keywords by length, descending, to handle cases like "plan of care" vs "plan"
                    sorted_kws = sorted(trigger_keywords, key=len, reverse=True)
                    # Build a single regex for all keywords, with word boundaries
                    pattern = r'(' + '|'.join(r'\b' + re.escape(kw) + r'\b' for kw in sorted_kws) + r')'

                    parts = re.split(pattern, text_to_cite, flags=re.IGNORECASE)

                    result_parts = []
                    for i, part in enumerate(parts):
                        # Matched keywords are at odd indices
                        if i % 2 == 1:
                            result_parts.append(f"<b>{html.escape(part)}</b>")
                        else:
                            result_parts.append(html.escape(part))

                    final_text = "".join(result_parts)
                    cites.append((final_text, src))
                else:
                    cites.append((html.escape(text_to_cite), src))

            if len(cites) >= cap:
                break
        out.append({**it, "citations": cites})
    return out

def _get_shap_prediction_wrapper(rule_title: str) -> Callable[[list[str]], list[float]]:
    """
    Creates a prediction function for a specific rule that SHAP can use.
    """
    def predict(texts: list[str]) -> list[float]:
        scores = []
        for text in texts:
            # We run a "strict" audit because we want to know if the rule *could* be triggered.
            issues = _audit_from_rubric(text, strict=True)
            if any(issue['title'] == rule_title for issue in issues):
                scores.append(1.0)
            else:
                scores.append(0.0)
        return scores
    return predict

def _get_shap_prediction_wrapper(rule_title: str) -> Callable[[list[str]], list[float]]:
    """
    Creates a prediction function for a specific rule that SHAP can use.
    """
    def predict(texts: list[str]) -> list[float]:
        scores = []
        for text in texts:
            # We run a "strict" audit because we want to know if the rule *could* be triggered.
            issues = _audit_from_rubric(text, strict=True)
            if any(issue['title'] == rule_title for issue in issues):
                scores.append(1.0)
            else:
                scores.append(0.0)
        return scores
    return predict

def _score_issue_confidence(issues_in: list[dict], records: list[tuple[str, str]]) -> list[dict]:
    all_text = " ".join(t for t, _ in records).lower()
    doc_tok = set(re.findall(r"[a-z]{4,}", all_text))
    out: list[dict] = []
    for it in issues_in:
        q = (it.get("title", "") + " " + it.get("detail", "")).lower()
        q_tok = set(re.findall(r"[a-z]{4,}", q))
        conf = 0.3 if not q_tok else 0.25 + 0.75 * min(1.0, len(q_tok & doc_tok) / max(1, len(q_tok)))
        if it.get("citations"):
            conf = min(1.0, conf + 0.15)
        out.append({**it, "confidence": round(float(conf), 2)})
    return out

# --- Exports ---
def export_report_json(obj: dict, json_path: str) -> bool:
    try:
        import json
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to export JSON: {e}")
        return False

def export_report_pdf(lines: list[str], pdf_path: str, meta: Optional[dict] = None,
                      chart_data: Optional[dict] = None,
                      sev_counts: Optional[dict] = None,
                      cat_counts: Optional[dict] = None) -> bool:
    try:
        if not QApplication.instance():
            import matplotlib
            matplotlib.use("Agg")
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        import math, textwrap
        import matplotlib.pyplot as plt  # type: ignore
        from matplotlib.backends.backend_pdf import PdfPages  # type: ignore
        from matplotlib.patches import FancyBboxPatch  # type: ignore

        theme = (get_str_setting("pdf_chart_theme", "dark") or "dark").lower()
        if theme == "light":
            chart_colors = ["#b91c1c", "#b45309", "#047857", "#374151"]
            xtick = ytick = "#111827"
            spine = "#6b7280"
            fig_face = "#ffffff"
            ax_face = "#ffffff"
            ylabel_color = "#111827"
        else:
            chart_colors = ["#ef4444", "#f59e0b", "#10b981", "#9ca3af"]
            xtick = ytick = "#e5e7eb"
            spine = "#9aa1a8"
            fig_face = "#2b2b2b"
            ax_face = "#2b2b2b"
            ylabel_color = "#e5e7eb"

        font_family = REPORT_FONT_FAMILY
        font_size = REPORT_FONT_SIZE

        page_w, page_h = REPORT_PAGE_SIZE
        margin_top, margin_right, margin_bottom, margin_left = REPORT_MARGINS
        usable_width_in = page_w - (margin_left + margin_right)
        approx_char_width_in = max(0.12, (font_size * 0.56) / 72.0)
        chars_per_line = max(56, int(usable_width_in / approx_char_width_in))

        wrapped: list[str] = []
        for ln in lines:
            s = "" if ln is None else str(ln)
            s = s.replace("<b>", "*").replace("</b>", "*")
            if not s:
                wrapped.append("")
                continue
            for block in textwrap.wrap(s, width=chars_per_line, replace_whitespace=False, drop_whitespace=False):
                wrapped.append(block)
            if s.endswith(":") or s.istitle():
                wrapped.append("")

        line_height_in = (font_size / 72.0) * 2.0
        usable_height_in = page_h - (margin_top + margin_bottom)
        header_lines = REPORT_HEADER_LINES
        footer_lines = REPORT_FOOTER_LINES

        chart_enabled = get_bool_setting("pdf_chart_enabled", True)
        chart_position = (get_str_setting("pdf_chart_position", "bottom") or "bottom").lower()
        if not chart_enabled or chart_position == "none":
            chart_data = None
            sev_counts = None
            cat_counts = None

        top_chart_h = 0.12
        bottom_charts_h = 0.26
        chart_on_top = (chart_data is not None) and (chart_position == "top")
        chart_on_bottom = (chart_data is not None) and (chart_position == "bottom")

        reserved_top = top_chart_h if chart_on_top else 0.0
        reserved_bottom = bottom_charts_h if chart_on_bottom else 0.0

        header_reserve_in = header_lines * line_height_in
        footer_reserve_in = footer_lines * line_height_in
        text_area_height_in = usable_height_in * (
                1.0 - reserved_top - reserved_bottom) - header_reserve_in - footer_reserve_in
        if text_area_height_in < (12 * line_height_in):
            chart_on_top = False
            chart_on_bottom = False
            reserved_top = reserved_bottom = 0.0
            text_area_height_in = usable_height_in - header_reserve_in - footer_reserve_in

        lines_per_page = max(10, int(text_area_height_in / line_height_in))

        risk_label = (meta or {}).get("risk_label", "")
        risk_color = (meta or {}).get("risk_color", "#6b7280")
        header_left = meta.get("file_name", "") if meta else ""
        header_right = f"{meta.get('run_time', _now_iso())} | Template {REPORT_TEMPLATE_VERSION}" if meta else _now_iso()

        with PdfPages(pdf_path) as pdf:
            total_lines = len(wrapped)
            total_pages = max(1, math.ceil(total_lines / lines_per_page))
            for page_idx in range(total_pages):
                start = page_idx * lines_per_page
                end = min(start + lines_per_page, total_lines)
                page_lines = wrapped[start:end]

                fig = plt.figure(figsize=(page_w, page_h))
                fig.patch.set_facecolor(fig_face)
                ax = fig.add_axes([
                    margin_left / page_w,
                    margin_bottom / page_h,
                    (page_w - margin_left - margin_right) / page_w,
                    (page_h - margin_top - margin_bottom) / page_h,
                ])
                ax.set_facecolor(ax_face)
                ax.axis("off")

                ax.text(0, 1, header_left, va="top", ha="left", family=font_family, fontsize=font_size + 1.0,
                        color=xtick)
                ax.text(1, 1, header_right, va="top", ha="right", family=font_family, fontsize=font_size + 1.0,
                        color=xtick)

                try:
                    if risk_label:
                        ax.add_patch(FancyBboxPatch(
                            (0.82, 0.965), 0.16, 0.05, boxstyle="round,pad=0.008,rounding_size=0.01",
                            linewidth=0.0, facecolor=risk_color, transform=ax.transAxes
                        ))
                        ax.text(0.90, 0.99, f"Risk: {risk_label}", va="top", ha="center",
                                family=font_family, fontsize=font_size + 0.6,
                                color="#111827" if risk_label != "High" else "#ffffff",
                                transform=ax.transAxes)
                except Exception:
                    ...

                if page_idx == 0 and chart_on_top:
                    try:
                        cats = ["Flags", "Findings", "Suggestions", "Notes"]
                        vals = [sev_counts.get("flag", 0), sev_counts.get("finding", 0),
                                sev_counts.get("suggestion", 0), sev_counts.get("auditor_note", 0)] if sev_counts else [
                            0, 0, 0, 0]
                        ax_chart = fig.add_axes([0.07, 0.81, 0.86, 0.12])
                        ax_chart.bar(cats, vals, color=chart_colors)
                        ax_chart.set_ylabel("Count", fontsize=font_size + 0.6, color=ylabel_color)
                        ax_chart.set_facecolor(ax_face)
                        for lab in ax_chart.get_xticklabels():
                            lab.set_fontsize(font_size + 0.3)
                            lab.set_color(xtick)
                        for lab in ax_chart.get_yticklabels():
                            lab.set_fontsize(font_size - 0.1)
                            lab.set_color(ytick)
                        for sp in ax_chart.spines.values():
                            sp.set_color(spine)
                    except Exception:
                        ...

                ax.text(0.5, 0, f"Page {page_idx + 1} / {total_pages}", va="bottom", ha="center",
                        family=font_family, fontsize=font_size, color=xtick)

                y_text_top = 1 - ((REPORT_HEADER_LINES * line_height_in) / (page_h - (margin_top + margin_bottom)))
                if page_idx == 0 and chart_on_top:
                    y_text_top -= (top_chart_h + 0.02)

                cursor_y = y_text_top
                y_step = line_height_in / (page_h - (margin_top + margin_bottom))
                for ln in page_lines:
                    is_section_header = bool(ln and ln.startswith("---") and ln.endswith("---"))

                    if is_section_header:
                        cursor_y -= y_step * 0.5
                        ax.axhline(y=cursor_y + (y_step * 0.2), xmin=0, xmax=1, color=spine, linewidth=0.7)
                        cursor_y -= y_step * 0.2
                        ax.text(0.5, cursor_y, ln.strip("- "), va="top", ha="center", family=font_family,
                                fontsize=font_size + 1.5, color=xtick, weight="bold")
                        cursor_y -= y_step * 1.2
                        ax.axhline(y=cursor_y + (y_step * 0.5), xmin=0, xmax=1, color=spine, linewidth=0.7)
                        cursor_y -= y_step * 0.5
                    else:
                        is_finding_header = bool(ln and ln.startswith("["))
                        weight = "bold" if is_finding_header else "normal"
                        size = font_size + (0.5 if is_finding_header else 0)
                        ax.text(0, cursor_y, ln, va="top", ha="left", family=font_family,
                                fontsize=size, color=xtick, weight=weight)

                    cursor_y -= y_step

                if (page_idx == total_pages - 1) and chart_on_bottom and (sev_counts or cat_counts):
                    try:
                        y0 = 0.08
                        h = 0.16
                        if sev_counts:
                            cats = ["Flags", "Findings", "Suggestions", "Notes"]
                            vals = [sev_counts.get("flag", 0), sev_counts.get("finding", 0),
                                    sev_counts.get("suggestion", 0), sev_counts.get("auditor_note", 0)]
                            ax_s = fig.add_axes([0.07, y0, 0.40, h])
                            ax_s.bar(cats, vals, color=["#ef4444", "#f59e0b", "#10b981", "#9ca3af"])
                            ax_s.set_title("Findings by Severity", fontsize=font_size + 0.8, color=xtick)
                            ax_s.set_facecolor(ax_face)
                            for lab in ax_s.get_xticklabels():
                                lab.set_fontsize(font_size)
                                lab.set_color(xtick)
                                lab.set_rotation(20)
                            for lab in ax_s.get_yticklabels():
                                lab.set_fontsize(font_size - 0.2)
                                lab.set_color(ytick)
                            for sp in ax_s.spines.values():
                                sp.set_color(spine)
                        if cat_counts:
                            cats = list(cat_counts.keys())[:8]
                            vals = [cat_counts[c] for c in cats]
                            ax_c = fig.add_axes([0.55, y0, 0.38, h])
                            ax_c.bar(cats, vals, color="#60a5fa")
                            ax_c.set_title("Top Categories", fontsize=font_size + 0.8, color=xtick)
                            ax_c.set_facecolor(ax_face)
                            for lab in ax_c.get_xticklabels():
                                lab.set_fontsize(font_size)
                                lab.set_color(xtick)
                                lab.set_rotation(20)
                            for lab in ax_c.get_yticklabels():
                                lab.set_fontsize(font_size - 0.2)
                                lab.set_color(ytick)
                            for sp in ax_c.spines.values():
                                sp.set_color(spine)
                    except Exception:
                        ...
                pdf.savefig(fig, bbox_inches="tight")
                plt.close(fig)
        return True
    except Exception as e:
        logger.error(f"Failed to export PDF: {e}")
        return False

# --- Analytics export fix ---
def export_analytics_csv(dest_csv: str) -> bool:
    try:
        with _get_db_connection() as conn:
            runs = pd.read_sql_query("SELECT * FROM analysis_runs ORDER BY run_time DESC", conn)
            issues = pd.read_sql_query("SELECT run_id, severity, category, confidence FROM analysis_issues", conn)
        agg = issues.groupby(["run_id", "severity"]).size().unstack(fill_value=0).reset_index()
        df = runs.merge(agg, left_on="id", right_on="run_id", how="left").drop(columns=["run_id"])
        os.makedirs(os.path.dirname(dest_csv), exist_ok=True)
        df.to_csv(dest_csv, index=False, encoding="utf-8")
        return True
    except Exception as e:
        logger.error(f"export_analytics_csv failed: {e}")
        return False

def export_report_fhir_json(data: dict, fhir_path: str) -> bool:
    try:
        # Check if the dummy classes are being used, which indicates fhir.resources is not installed.
        if 'Bundle' in globals() and not hasattr(globals()['Bundle'], 'construct'):
             logger.error("fhir.resources library not found. Please install it to use FHIR export.")
             QMessageBox.warning(None, "FHIR Library Not Found", "The 'fhir.resources' library is required for FHIR export. Please install it (`pip install fhir.resources`).")
             return False

        bundle = Bundle(type="collection", entry=[])

        report = DiagnosticReport(
            status="final",
            meta=Meta(profile=["http://hl7.org/fhir/us/core/StructureDefinition/us-core-diagnosticreport-note"]),
            code=CodeableConcept(coding=[Coding(system="http://loinc.org", code="LP296840-5", display="Clinical Note Analysis")]),
            subject=Reference(display="Anonymous Patient"),
            effectiveDateTime=data.get("generated", _now_iso()),
            issued=data.get("generated", _now_iso()),
            performer=[Reference(display="Spec Kit Analyzer")],
            conclusion=f"Compliance Score: {data.get('compliance', {}).get('score', 0.0)}/100.0"
        )

        # We need a stable, unique ID to reference the report within the bundle
        report.id = "diagnostic-report-1"
        report_ref = f"DiagnosticReport/{report.id}"
        bundle.entry.append({"fullUrl": f"urn:uuid:{report.id}", "resource": report})

        for i, issue in enumerate(data.get("issues", [])):
            obs = Observation(
                id=f"observation-{i+1}",
                status="final",
                partOf=[Reference(reference=report_ref)],
                code=CodeableConcept(coding=[Coding(
                    system="http://example.com/speckit-findings",
                    code=str(issue.get("category", "general")).replace(" ", "-"),
                    display=issue.get("title")
                )]),
                subject=Reference(display="Anonymous Patient"),
                valueString=issue.get("detail"),
                interpretation=[CodeableConcept(coding=[Coding(
                    system="http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    code=str(issue.get("severity", "NOTE")).upper(),
                    display=str(issue.get("severity"))
                )])]
            )
            bundle.entry.append({"fullUrl": f"urn:uuid:{obs.id}", "resource": obs})

        os.makedirs(os.path.dirname(fhir_path), exist_ok=True)
        with open(fhir_path, "w", encoding="utf-8") as f:
            f.write(bundle.json(indent=2))

        return True
    except Exception as e:
        logger.error(f"Failed to export FHIR JSON: {e}")
        return False

ReviewMode = Literal["Moderate", "Strict"]
CURRENT_REVIEW_MODE: ReviewMode = "Moderate"
DEDUP_DEFAULTS = {"Moderate": {"method": "tfidf", "threshold": 0.50},
                  "Strict": {"method": "tfidf", "threshold": 0.70}}

def get_similarity_threshold() -> float:
    raw = get_setting("dup_threshold")
    if raw:
        try:
            return float(raw)
        except Exception:
            ...
    return float(DEDUP_DEFAULTS.get(CURRENT_REVIEW_MODE, {"threshold": 0.50})["threshold"])

def _generate_risk_dashboard(compliance_score: float, sev_counts: dict) -> list[str]:
    lines = ["--- Risk Dashboard ---"]
    score = compliance_score
    flags = sev_counts.get("flag", 0)
    findings = sev_counts.get("finding", 0)

    if score >= 90 and flags == 0:
        risk = "Low"
        summary = "Good compliance posture."
    elif score >= 70 and flags <= 1:
        risk = "Medium"
        summary = "Key areas require review."
    else:
        risk = "High"
        summary = "Critical issues require attention."

    lines.append(f"Overall Risk: {risk}")
    lines.append(f"Compliance Score: {score:.1f}/100")
    lines.append(f"Summary: {summary}")
    lines.append(f"Critical Findings (Flags): {flags}")
    lines.append(f"Areas of Concern (Findings): {findings}")
    lines.append("")
    return lines

def _generate_compliance_checklist(strengths: list[str], weaknesses: list[str]) -> list[str]:
    lines = ["<h3>Compliance Checklist</h3>"]

    checklist_items = {
        "Provider Authentication": "Provider authentication (signature/date)",
        "Measurable Goals": "Goals appear to be measurable",
        "Medical Necessity": "Medical necessity is explicitly discussed",
        "Assistant Supervision": "Assistant involvement includes supervision context",
        "Plan/Certification": "Plan/certification is referenced"
    }

    def get_status_icon(key, text):
        if any(text in s for s in strengths):
            return "<span style='color: #28a745; font-weight: bold;'>✔</span>"
        elif any(text in w for w in weaknesses):
            return "<span style='color: #dc3545; font-weight: bold;'>❌</span>"
        else:
            simplified_weakness_text = text.split('(')[0].strip()
            if any(simplified_weakness_text in w for w in weaknesses):
                return "<span style='color: #dc3545; font-weight: bold;'>❌</span>"
            else:
                return "<span style='color: #6c757d; font-weight: bold;'>○</span>"

    lines.append("<table>")
    for key, text in checklist_items.items():
        icon = get_status_icon(key, text)
        lines.append(f"<tr><td style='padding-right: 10px;'>{icon}</td><td>{key}</td></tr>")
    lines.append("</table>")

    lines.append("")
    return lines

def run_analyzer(self, file_path: str,
                 selected_disciplines: List[str],
                 entity_consolidation_service: EntityConsolidationService,
                 scrub_override: Optional[bool] = None,
                 review_mode_override: Optional[str] = None,
                 dedup_method_override: Optional[str] = None,
                 progress_cb: Optional[Callable[[int, str], None]] = None,
                 cancel_cb: Optional[Callable[[], bool]] = None,
                 main_window_instance=None) -> dict:
    def report(pct: int, msg: str):
        if progress_cb:
            try:
                progress_cb(max(0, min(100, int(pct))), msg)
            except Exception:
                ...

    def check_cancel():
        if cancel_cb:
            try:
                if cancel_cb():
                    raise KeyboardInterrupt("Operation cancelled")
            except KeyboardInterrupt:
                raise
            except Exception:
                ...

    result_info = {"csv": None, "html": None, "json": None, "pdf": None, "summary": None}
    try:
        set_bool_setting("last_analysis_from_cache", False)
        if not file_path or not os.path.isfile(file_path):
            logger.error(f"File not found: {file_path}")
            return result_info
        logger.info(f"Analyzing: {file_path}")
        report(5, "Initializing settings")

        scrub_enabled = scrub_override if scrub_override is not None else get_bool_setting("scrub_phi", True)
        if scrub_override is not None:
            set_bool_setting("scrub_phi", scrub_override)

        global CURRENT_REVIEW_MODE
        if review_mode_override in ("Moderate", "Strict"):
            CURRENT_REVIEW_MODE = review_mode_override  # type: ignore[assignment]

        threshold = get_similarity_threshold()
        dedup_method = (dedup_method_override or get_str_setting("dedup_method", "tfidf")).lower()
        if dedup_method_override:
            set_str_setting("dedup_method", dedup_method)

        try:
            add_recent_file(file_path)
        except Exception:
            ...

        allow_cache = get_bool_setting("allow_cache", True)
        fp = _file_fingerprint(file_path)
        sp = _settings_fingerprint(scrub_enabled, CURRENT_REVIEW_MODE, dedup_method)

        if allow_cache and fp and sp:
            cached = _load_cached_outputs(fp, sp)
            if cached and cached.get("pdf"):
                report(100, "Done (cached)")
                set_bool_setting("last_analysis_from_cache", True)
                logger.info("Served from cache.")
                return cached

        check_cancel()
        report(10, "Parsing document")
        original = parse_document_content(file_path)
        if len(original) == 1 and original[0][0].startswith(("Error:", "Info:")):
            logger.warning(f"{original[0][1]}: {original[0][0]}")
            return result_info

        check_cancel()
        report(30, "Scrubbing PHI" if scrub_enabled else "Skipping PHI scrubbing")
        processed = [(scrub_phi(t) if scrub_enabled else t, s) for (t, s) in original]

        check_cancel()
        report(50, f"Reducing near-duplicates ({dedup_method})")
        if dedup_method == "tfidf":
            collapsed = collapse_similar_sentences_tfidf(processed, threshold)
        else:
            collapsed = collapse_similar_sentences_simple(processed, threshold)
        collapsed = list(collapsed)

ner_results = []
formatted_entities = []

if get_bool_setting("enable_ner_ensemble", True) and self.ner_service and self.entity_consolidation_service:
    if self.ner_service.is_ready():
        report(65, "Running NER Ensemble")
        ner_sentences = [text for text, src in collapsed]
        raw_ner_results = self.ner_service.extract_entities(full_text, ner_sentences)
        embedding_model = self.local_rag.embedding_model if self.local_rag else None
        ner_results = self.entity_consolidation_service.consolidate_entities(
            raw_ner_results, full_text, embedding_model=embedding_model
        )
        if ner_results:
            logger.info(f"Consolidated NER results: {len(ner_results)} entities found.")

            # LLM-based Fact-Checking
            if self.local_rag and self.local_rag.is_ready():
                report(68, "Fact-checking NER findings with AI")
                for entity in ner_results:
                    if entity.label == "DISAGREEMENT":
                        continue
                    prompt = (
                        "You are a clinical documentation expert. Based on the document context, "
                        "is the following finding plausible and correctly labeled?\n\n"
                        f"Finding: \"{entity.text}\"\n"
                        f"Label: \"{entity.label}\"\n\n"
                        "Answer with only one word: 'Confirmed', 'Rejected', or 'Uncertain'."
                    )
                    try:
                        response = self.local_rag.query(prompt, k=2)
                        validation_status = "Uncertain"
                        if "confirmed" in response.lower():
                            validation_status = "Confirmed"
                        elif "rejected" in response.lower():
                            validation_status = "Rejected"
                        entity.llm_validation = validation_status
                        logger.info(f"LLM validation for '{entity.text}' ({entity.label}): {validation_status}")

                        # Update NER Performance DB
                        if validation_status in ("Confirmed", "Rejected"):
                            for model_name in entity.models:
                                update_ner_performance(model_name, entity.label, validation_status)
                    except Exception as e:
                        logger.warning(f"LLM fact-checking failed for entity '{entity.text}': {e}")

            # Formatting extracted entities as in main branch
            formatted_entities = _format_entities_for_rag(ner_results)
            logger.info(f"Formatted {len(formatted_entities)} entities for downstream use.")
    else:
        logger.warning("NER service was enabled but not ready. Skipping NER.")

        check_cancel()
        report(60, "Computing summary")
        summary = build_rich_summary(processed, collapsed)

        report(70, "Analyzing compliance")

        full_text = "\n".join(t for t, _ in collapsed)
        strict_flag = (CURRENT_REVIEW_MODE == "Strict")
        issues_base = _audit_from_rubric(full_text, selected_disciplines, strict=strict_flag)

        # Convert NER disagreements into issues so they can be adjudicated
        for entity in ner_results:
            if entity.label == "DISAGREEMENT":
                issues_base.append({
                    "severity": "finding",
                    "title": "NER Model Disagreement",
                    "detail": f"Models disagreed on the label for text: '{entity.text}'. Context: {entity.context}",
                    "category": "AI Finding",
                    "confidence": entity.score,
                    "citations": [], # This can be enhanced later if needed
                    "label": "DISAGREEMENT"
                })


        issues_scored = _score_issue_confidence(_attach_issue_citations(issues_base, collapsed), collapsed)


        use_llm_analysis = get_bool_setting("use_llm_analysis", True)
        llm_is_ready = main_window_instance and main_window_instance.local_rag and main_window_instance.local_rag.is_ready()

        if use_llm_analysis and llm_is_ready:
            logger.info("--- Using LLM-based compliance analysis ---")
            report(71, "Analyzing compliance with LLM...")

            rubric_map = {
                "pt": os.path.join(BASE_DIR, "pt_compliance_rubric.ttl"),
                "ot": os.path.join(BASE_DIR, "ot_compliance_rubric.ttl"),
                "slp": os.path.join(BASE_DIR, "slp_compliance_rubric.ttl"),
            }
            all_rules = []
            for discipline in selected_disciplines:
                path = rubric_map.get(discipline)
                if path and os.path.exists(path):
                    try:
                        service = RubricService(path)
                        all_rules.extend(service.get_rules())
                    except Exception as e:
                        logger.warning(f"Failed to load rubric for {discipline}: {e}")

            seen_titles = set()
            unique_rules = []
            for rule in all_rules:
                if rule.issue_title not in seen_titles:
                    unique_rules.append(rule)
                    seen_titles.add(rule.issue_title)

            rules_as_dicts = [r.__dict__ for r in unique_rules]

            issues_scored = run_llm_analysis(
                llm=main_window_instance.local_rag.llm,
                chunks=[text for text, src in collapsed],
                rules=rules_as_dicts,
                file_path=file_path
            )
            logger.info(f"LLM analysis found {len(issues_scored)} issues.")

        else:
            if not llm_is_ready:
                logger.warning("LLM not ready, falling back to keyword-based audit.")
            logger.info("--- Using keyword-based compliance analysis ---")
            report(71, "Analyzing compliance with keywords...")
            full_text = "\n".join(t for t, _ in collapsed)
            strict_flag = (CURRENT_REVIEW_MODE == "Strict")
            issues_base = _audit_from_rubric(full_text, selected_disciplines, strict=strict_flag)
            issues_scored = _score_issue_confidence(_attach_issue_citations(issues_base, collapsed), collapsed)

        full_text_for_loc = "\n".join(t for t, _ in collapsed)
        for issue in issues_scored:
            if issue.get("citations"):
                cite_text_html = issue["citations"][0][0]
                cite_text = re.sub('<[^<]+?>', '', cite_text_html)
                try:
                    start_index = full_text_for_loc.index(cite_text)
                    end_index = start_index + len(cite_text)
                    issue['location'] = {'start': start_index, 'end': end_index}
                except ValueError:
                    logger.warning(f"Could not find citation text in document: '{cite_text[:50]}...'")
                    issue['location'] = None

        sev_order = {"flag": 0, "finding": 1, "suggestion": 2, "auditor_note": 3}
        issues_scored.sort(key=lambda x: (sev_order.get(str(x.get("severity")), 9),
                                          str(x.get("category", "")),
                                          str(x.get("title", ""))))


        # I'll inject the details into the issue object itself for easier rendering later.
        # This is not in the original code, but it's a good refactoring.

        # --- SHAP Integration ---
        # Generate explanations for issues that have citations
        for issue in issues_scored:
            if issue.get("citations"):
                try:
                    # We can only explain rules with a clear title
                    rule_title = issue.get("title")
                    if not rule_title:
                        continue

                    # Create a prediction function for the specific rule
                    prediction_fn = _get_shap_prediction_wrapper(rule_title)

                    # Use the first citation as the text to explain
                    text_to_explain = issue["citations"][0][0].replace("<b>", "").replace("</b>", "")

                    # Create a SHAP explainer
                    explainer = shap.Explainer(prediction_fn, shap.maskers.Text(r"\W+"))

                    # Generate SHAP values
                    shap_values = explainer([text_to_explain])

                    # Store the explanation object to be used later for visualization
                    issue['shap_explanation'] = shap_values

                except Exception as e:
                    logger.warning(f"SHAP explanation failed for issue '{issue.get('title')}': {e}")
        # --- End SHAP Integration ---

        # --- NLG Integration ---

        nlg_service = NLGService()
        for issue in issues_scored:
            prompt = f"Generate a brief, actionable tip for a physical therapist to address this finding: {issue.get('title', '')} ({issue.get('severity', '')}) - {issue.get('detail', '')}"
            tip = nlg_service.generate_tip(prompt)
            issue['nlg_tip'] = tip

        # --- End NLG Integration ---

        issue_details_map = {
            "Provider signature/date possibly missing": {
                "action": "Ensure all entries are signed and dated by the qualified provider.",
                "why": "Signatures and dates are required by Medicare to authenticate that services were rendered as billed.",
                "good_example": "'Patient seen for 30 minutes of therapeutic exercise. [Provider Name], PT, DPT. 09/14/2025'",
                "bad_example": "An unsigned, undated note."
            },
            "Goals may not be measurable/time-bound": {
                "action": "Rewrite goals to include a baseline, specific target, and a clear timeframe (e.g., 'improve from X to Y in 2 weeks').",
                "why": "Measurable goals are essential to demonstrate progress and justify the need for skilled intervention.",
                "good_example": "'Patient will improve shoulder flexion from 90 degrees to 120 degrees within 2 weeks to allow for independent overhead dressing.'",
                "bad_example": "'Patient will improve shoulder strength.'"
            },
            "Medical necessity not explicitly supported": {
                "action": "Clearly link each intervention to a specific functional deficit and explain why the skill of a therapist is required.",
                "why": "Medicare only pays for services that are reasonable and necessary for the treatment of a patient's condition.",
                "good_example": "'...skilled verbal and tactile cues were required to ensure proper form and prevent injury.'",
                "bad_example": "'Patient tolerated treatment well.'"
            },
            "Assistant supervision context unclear": {
                "action": "Document the level of supervision provided to the assistant, in line with state and Medicare guidelines.",
                "why": "Proper supervision of therapy assistants is a condition of payment and ensures quality of care.",
                "good_example": "'PTA provided services under the direct supervision of the physical therapist who was on-site.'",
                "bad_example": "No mention of supervision when a PTA is involved."
            },
            "Plan/Certification not clearly referenced": {
                "action": "Explicitly reference the signed Plan of Care and certification/recertification dates in progress notes.",
                "why": "Services must be provided under a certified Plan of Care to be eligible for reimbursement.",
                "good_example": "'Treatment provided as per Plan of Care certified on 09/01/2025.'",
                "bad_example": "No reference to the POC or certification period."
            },
            "General auditor checks": {
                "action": "Perform a general review of the note for clarity, consistency, and completeness. Ensure the 'story' of the patient's care is clear.",
                "why": "A well-documented note justifies skilled care, supports medical necessity, and ensures accurate billing.",
                "good_example": "A note that provides a clear picture of the patient's journey from evaluation to discharge.",
                "bad_example": "A note with jargon, undefined abbreviations, or that simply lists exercises without clinical reasoning."
            }
        }
        for issue in issues_scored:
            issue['details'] = issue_details_map.get(issue.get('title', ''), {})
# --- Guideline Search Integration ---
        if self.guideline_service and self.guideline_service.is_index_ready:
            self.log("Searching for relevant guidelines for each finding...")
            for issue in issues_scored:
                query = f"{issue.get('title', '')}: {issue.get('detail', '')}"
                guideline_results = self.guideline_service.search(query, top_k=2)
                issue['guidelines'] = guideline_results
        # --- End Guideline Search Integration ---

        pages_est = len({s for _, s in collapsed if s.startswith("Page ")}) or 1

        full_text = "\n".join(t for t, _ in collapsed)
        strengths, weaknesses, missing = [], [], []
        tl = full_text.lower()
        if any(k in tl for k in ("signed", "signature", "dated")):
            strengths.append("Provider authentication appears present.")
        else:
            weaknesses.append("Provider authentication is unclear or missing.")
            missing.append("Signatures/Dates")

        if "goal" in tl and any(k in tl for k in ("measurable", "time", "timed", "by ")):
            strengths.append("Goals appear measurable and time-bound.")
        elif "goal" in tl:
            weaknesses.append("Goals may not be measurable or time-bound.")
            missing.append("Measurable/Time-bound Goals")

        if any(k in tl for k in ("medical necessity", "reasonable and necessary", "necessity")):
            strengths.append("Medical necessity is explicitly discussed.")
        else:
            weaknesses.append("Medical necessity is not explicitly supported.")
            missing.append("Medical Necessity")

        if "assistant" in tl and "supervis" in tl:
            strengths.append("Assistant involvement includes supervision context.")
        elif "assistant" in tl:
            weaknesses.append("Assistant supervision is not clearly documented.")
            missing.append("Assistant Supervision Context")

        if any(k in tl for k in ("plan of care", "poc", "certification", "recert")):
            strengths.append("Plan/certification is referenced.")
        else:
            weaknesses.append("Plan/certification is not clearly referenced.")
            missing.append("Plan/Certification Reference")

        sev_counts = {
            "flag": sum(1 for i in issues_scored if i.get("severity") == "flag"),
            "finding": sum(1 for i in issues_scored if i.get("severity") == "finding"),
            "suggestion": sum(1 for i in issues_scored if i.get("severity") == "suggestion"),
            "auditor_note": sum(1 for i in issues_scored if i.get("severity") == "auditor_note"),
        }
        cat_counts = count_categories(issues_scored)

        def compute_compliance_score(issues: list[dict], strengths_in: list[str], missing_in: list[str],
                                     mode: ReviewMode) -> dict:
        total_financial_impact = sum(issue.get("financial_impact", 0) for issue in issues)

            # Normalize the financial impact to a penalty score out of 100.
            # The MAX_FINANCIAL_IMPACT can be adjusted based on expected impact values.
            MAX_FINANCIAL_IMPACT = 500
            financial_penalty = (total_financial_impact / MAX_FINANCIAL_IMPACT) * 100

            base = 100.0 - financial_penalty

            # The 'missing' and 'strengths' can act as adjustments on top of the financial impact score.
            base -= len(missing_in) * (4.0 if mode == "Strict" else 2.5)
            base += min(5.0, len(strengths_in) * 0.5)

            score = max(0.0, min(100.0, base))

            flags = sum(1 for i in issues if i.get("severity") == "flag")
            findings = sum(1 for i in issues if i.get("severity") == "finding")
            suggestions = sum(1 for i in issues if i.get("severity") == "suggestion")

            breakdown = f"Flags={flags}, Findings={findings}, Suggestions={suggestions}, Missing={len(missing_in)}, Strengths={len(strengths_in)}, Financial Impact={total_financial_impact}; Mode={mode}"
            return {"score": round(score, 1), "breakdown": breakdown}

        compliance = compute_compliance_score(issues_scored, strengths, missing, CURRENT_REVIEW_MODE)

        trends = _compute_recent_trends(max_runs=get_int_setting("trends_window", 10))

        def _risk_level(score: float, flags: int) -> tuple[str, str]:
            if score >= 90 and flags == 0:
                return ("Low", "#10b981")
            if score >= 70 and flags <= 1:
                return ("Medium", "#f59e0b")
            return ("High", "#ef4444")

        risk_label, risk_color = _risk_level(float(compliance["score"]), sev_counts["flag"])

        tips = []
        if sev_counts["flag"] > 0:
            tips.append("Resolve flags first, then clarify grey areas.")
        if "Medical Necessity" in missing:
            tips.append("Link skilled interventions to functional limitations and outcomes.")
        if "Measurable/Time-bound Goals" in missing:
            tips.append("Rewrite goals with baselines, specific targets, and timelines.")
        if not strengths:
            tips.append("Improve specificity with objective measures and clear clinical reasoning.")

        try:
            with _get_db_connection() as conn:
                pass
        except Exception:
            ...

        def _load_last_snapshot(file_fp: str, settings_fp: str) -> Optional[dict]:
            try:
                with _get_db_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("""
                                SELECT summary_json
                                FROM analysis_snapshots
                                WHERE file_fingerprint = ?
                                  AND settings_fingerprint = ?
                                """, (file_fp, settings_fp))
                    row = cur.fetchone()
                    if not row:
                        return None
                    import json as _json
                    return _json.loads(row[0])
            except Exception:
                return None

        def _save_snapshot(file_fp: str, settings_fp: str, payload: dict) -> None:
            try:
                with _get_db_connection() as conn:
                    cur = conn.cursor()
                    import json as _json
                    from datetime import datetime
                    cur.execute("""
                                CREATE TABLE IF NOT EXISTS analysis_snapshots
                                (
                                    file_fingerprint
                                    TEXT
                                    NOT
                                    NULL,
                                    settings_fingerprint
                                    TEXT
                                    NOT
                                    NULL,
                                    summary_json
                                    TEXT
                                    NOT
                                    NULL,
                                    created_at
                                    TEXT
                                    NOT
                                    NULL,
                                    PRIMARY
                                    KEY
                                (
                                    file_fingerprint,
                                    settings_fingerprint
                                )
                                    )
                                """)
                    cur.execute("""
                        INSERT OR REPLACE INTO analysis_snapshots
                        (file_fingerprint, settings_fingerprint, summary_json, created_at)
                        VALUES (?,?,?,?)
                    """, (file_fp, settings_fp, _json.dumps(payload, ensure_ascii=False),
                          datetime.now().isoformat(timespec="seconds")))
                    conn.commit()
            except Exception:
                ...

        last_snap = _load_last_snapshot(fp, sp)
        change_summary = {}
        if last_snap and isinstance(last_snap, dict):
            prev = last_snap.get("metrics") or {}
            change_summary = {
                "score_delta": round(
                    float(compliance["score"]) - float(last_snap.get("compliance", {}).get("score", 0.0)), 1),
                "flags_delta": sev_counts["flag"] - int(prev.get("flags", 0)),
                "findings_delta": sev_counts["finding"] - int(prev.get("findings", 0)),
                "suggestions_delta": sev_counts["suggestion"] - int(prev.get("suggestions", 0)),
            }

        narrative_lines = []
        narrative_lines.extend(_generate_risk_dashboard(compliance['score'], sev_counts))
        narrative_lines.extend(_generate_compliance_checklist(strengths, weaknesses))

        narrative_lines.append("--- Detailed Findings ---")
        if issues_scored:
            issue_details = {
                "Provider signature/date possibly missing": {
                    "action": "Ensure all entries are signed and dated by the qualified provider.",
                    "why": "Signatures and dates are required by Medicare to authenticate that services were rendered as billed.",
                    "good_example": "'Patient seen for 30 minutes of therapeutic exercise. [Provider Name], PT, DPT. 09/14/2025'",
                    "bad_example": "An unsigned, undated note."
                },
                "Goals may not be measurable/time-bound": {
                    "action": "Rewrite goals to include a baseline, specific target, and a clear timeframe (e.g., 'improve from X to Y in 2 weeks').",
                    "why": "Measurable goals are essential to demonstrate progress and justify the need for skilled intervention.",
                    "good_example": "'Patient will improve shoulder flexion from 90 degrees to 120 degrees within 2 weeks to allow for independent overhead dressing.'",
                    "bad_example": "'Patient will improve shoulder strength.'"
                },
                "Medical necessity not explicitly supported": {
                    "action": "Clearly link each intervention to a specific functional deficit and explain why the skill of a therapist is required.",
                    "why": "Medicare only pays for services that are reasonable and necessary for the treatment of a patient's condition.",
                    "good_example": "'...skilled verbal and tactile cues were required to ensure proper form and prevent injury.'",
                    "bad_example": "'Patient tolerated treatment well.'"
                },
                "Assistant supervision context unclear": {
                    "action": "Document the level of supervision provided to the assistant, in line with state and Medicare guidelines.",
                    "why": "Proper supervision of therapy assistants is a condition of payment and ensures quality of care.",
                    "good_example": "'PTA provided services under the direct supervision of the physical therapist who was on-site.'",
                    "bad_example": "No mention of supervision when a PTA is involved."
                },
                "Plan/Certification not clearly referenced": {
                    "action": "Explicitly reference the signed Plan of Care and certification/recertification dates in progress notes.",
                    "why": "Services must be provided under a certified Plan of Care to be eligible for reimbursement.",
                    "good_example": "'Treatment provided as per Plan of Care certified on 09/01/2025.'",
                    "bad_example": "No reference to the POC or certification period."
                },
                "General auditor checks": {
                    "action": "Perform a general review of the note for clarity, consistency, and completeness. Ensure the 'story' of the patient's care is clear.",
                    "why": "A well-documented note justifies skilled care, supports medical necessity, and ensures accurate billing.",
                "good_example": "A note that paints a clear picture of the patient's journey from evaluation to discharge.",
                "bad_example": "A note with jargon, undefined abbreviations, or one that simply lists exercises without clinical reasoning."
                }
            }
            for it in issues_scored:
                sev = str(it.get("severity", "")).title()
                cat = it.get("category", "") or "General"
                title = it.get("title", "") or "Finding"
                narrative_lines.append(f"[{sev}][{cat}] {title}")

                details = issue_details.get(title, {})
                if details:
                    action_text = it.get("nlg_tip") or details.get("action")
                    if action_text:
                        narrative_lines.append(f"  - Recommended Action: {action_text}")
                    narrative_lines.append(f"  - Why it matters: {details['why']}")
                    narrative_lines.append(f"  - Good Example: {details['good_example']}")
                    narrative_lines.append(f"  - Bad Example: {details['bad_example']}")

                cites = it.get("citations") or []
                if cites:
                    narrative_lines.append("  - Evidence in Document:")
                    for (qt, src) in cites[:2]:
                        q = (qt or "").strip().replace("\n", " ")
                        if len(q) > 100:
                            q = q[:97].rstrip() + "..."
                        narrative_lines.append(f"    - [{src}] “{q}”")
                narrative_lines.append("")
        else:
            narrative_lines.append("No specific audit findings were identified.")

        narrative_lines.append("")
        narrative_lines.append("--- General Recommendations ---")
        narrative_lines.append(" • Ensure all notes follow a standard format for consistency.")
        narrative_lines.append(" • Be specific and objective, using numbers and standardized tests to measure progress.")
        narrative_lines.append(" • Always link treatment to function by explaining how therapy helps the patient achieve their functional goals.")
        narrative_lines.append(" • Tell a story. The documentation should paint a clear picture of the patient's journey, from evaluation to discharge.")
        narrative_lines.append("")

        # --- Generate and add suggested questions ---
        suggested_questions = _generate_suggested_questions(issues_scored)
        if suggested_questions:
            narrative_lines.append("--- Suggested Questions for Follow-up ---")
            for q in suggested_questions:
                narrative_lines.append(f" • {q}")
            narrative_lines.append("")
        # --- End suggested questions ---

# --- Bias Auditing with Fairlearn ---
        fairness_metrics = {}
        if MetricFrame is not None and issues_scored:
            try:
                audit_df = pd.DataFrame(issues_scored)
                # Ensure 'discipline' column exists and handle missing values
                if 'discipline' not in audit_df.columns:
                    audit_df['discipline'] = 'unknown'
                audit_df['discipline'] = audit_df['discipline'].fillna('unknown')

                y_true = (audit_df['severity'] == 'flag').astype(int) # Ground truth (same as prediction for this metric)
                y_pred = (audit_df['severity'] == 'flag').astype(int) # Model's prediction
                sensitive_features = audit_df['discipline']

                if selection_rate and demographic_parity_difference:
                    # We use a MetricFrame to compute metrics across sensitive features
                    gm = MetricFrame(metrics=selection_rate,
                                     y_true=y_true,
                                     y_pred=y_pred,
                                     sensitive_features=sensitive_features)

                    fairness_metrics['demographic_parity_difference'] = demographic_parity_difference(
                        y_true,
                        y_pred,
                        sensitive_features=sensitive_features
                    )
                    fairness_metrics['by_group'] = gm.by_group

            except Exception as e:
                logger.warning(f"Fairlearn audit failed: {e}")
        # --- End Bias Auditing ---
        
        narrative_lines.append("--- Trends & Analytics (Last 10 Runs) ---")
        if trends.get("recent_scores"):
            sc = trends["recent_scores"]
            narrative_lines.append(f" • Recent scores (oldest to newest): {', '.join(str(round(s, 1)) for s in sc)}")
            narrative_lines.append(
                f" • Score delta: {trends['score_delta']:+.1f} | Average score: {trends['avg_score']:.1f}")
            narrative_lines.append(
                f" • Average Flags: {trends['avg_flags']:.2f} | Average Findings: {trends['avg_findings']:.2f} | Average Suggestions: {trends['avg_suggestions']:.2f}")
        else:
            narrative_lines.append(" • Not enough history to compute trends yet.")
        narrative_lines.append("")

        narrative_lines.append("--- Model Information & Limitations ---")
        narrative_lines.append(" • NLG Model: t5-small")
        narrative_lines.append(" • Embedding Model: all-MiniLM-L6-v2")
        narrative_lines.append(" • LLM Model: Mistral-7B-Instruct-v0.2-GGUF (Q4_K_M)")
        narrative_lines.append(" • This report was generated by an AI-powered system. The findings are based on a combination of rule-based analysis and machine learning models. While this tool is designed to assist in identifying potential compliance issues, it is not a substitute for professional judgment. The models may not be perfect and can make mistakes. All findings should be reviewed by a qualified professional.")
        narrative_lines.append("")

        metrics = {
            "pages": pages_est,
            "findings_total": len(issues_scored),
            "flags": sev_counts["flag"],
            "findings": sev_counts["finding"],
            "suggestions": sev_counts["suggestion"],
            "notes": sev_counts["auditor_note"],
            "sentences_raw": summary["total_sentences_raw"],
            "sentences_final": summary["total_sentences_final"],
            "dedup_removed": summary["dedup_removed"],
        }

        try:
persist_analysis_run(
    file_path,
    _now_iso(),
    metrics,
    issues_scored,
    compliance,
    CURRENT_REVIEW_MODE,
    json_path=json_path,
    selected_disciplines=selected_disciplines
)

        except Exception:
            ...
        try:
            snap_payload = {
                "metrics": metrics,
                "compliance": compliance,
                "sev_counts": sev_counts,
                "cat_counts": cat_counts,
            }
            _save_snapshot(fp, sp, snap_payload)
        except Exception:
            ...

        report(86, "Writing JSON/PDF")
        pdf_path, csv_path = generate_report_paths()
        json_path = pdf_path[:-4] + ".json"

        try:
            from dataclasses import asdict
            json_ner_results = {model: [asdict(e) for e in entities] for model, entities in ner_results.items()} if ner_results else {}

            export_report_json({
                "json_schema_version": 6,
                "report_template_version": REPORT_TEMPLATE_VERSION,
                "file": file_path,
                "generated": _now_iso(),
                "scrub_phi": scrub_enabled,
                "review_mode": CURRENT_REVIEW_MODE,
                "dup_threshold": threshold,
                "dedup_method": dedup_method,
                "metrics": metrics,
                "summary": summary,
                "issues": issues_scored,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "missing": missing,
                "compliance": compliance,
                "executive_status": ("Pass" if compliance["score"] >= 90 and sev_counts["flag"] == 0
                                     else "At-Risk" if (compliance["score"] >= 70 and sev_counts["flag"] <= 1)
                else "Fail"),
                "change_summary": change_summary,
                "narrative": "\n".join(narrative_lines),
                "tips": tips,
                "report_style": "condensed",
                "report_include_citations": get_bool_setting("show_citations", True),
                "pdf_chart_position": get_str_setting("pdf_chart_position", "bottom"),
                "pdf_chart_theme": get_str_setting("pdf_chart_theme", "dark"),
                "report_severity_ordering": "flags_first",
"clinical_ner_enabled": get_bool_setting("enable_ner_ensemble", True),
"ner_results": json_ner_results,
                "source_sentences": collapsed,
                "sev_counts": sev_counts,
                "cat_counts": cat_counts,
                "trends": trends,
                "suggested_questions": suggested_questions,
            }, json_path)
            result_info["json"] = json_path
        except Exception as e:
            logger.error(f"Failed to write JSON: {e}")

        try:
            meta = {"file_name": os.path.basename(file_path), "run_time": _now_iso(),
                    "risk_label": risk_label, "risk_color": risk_color}
            export_report_pdf(
                lines=narrative_lines,
                pdf_path=pdf_path,
                meta=meta,
                chart_data=sev_counts,
                sev_counts=sev_counts,
                cat_counts=cat_counts
            )
            result_info["pdf"] = pdf_path
        except Exception as e:
            logger.error(f"Failed to write PDF: {e}")

        try:
            flat = {
                "file_name": os.path.basename(file_path),
                "generated": _now_iso(),
                "review_mode": CURRENT_REVIEW_MODE,
                "dup_threshold": threshold,
                "dedup_method": dedup_method,
                "pages_est": pages_est,
                "flags": sev_counts["flag"],
                "findings": sev_counts["finding"],
                "suggestions": sev_counts["suggestion"],
                "notes": sev_counts["auditor_note"],
                "sentences_raw": summary["total_sentences_raw"],
                "sentences_final": summary["total_sentences_final"],
                "dedup_removed": summary["dedup_removed"],
                "compliance_score": compliance["score"],
                "risk_label": risk_label,
            }
            df = pd.DataFrame([flat])
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            df.to_csv(csv_path, index=False, encoding="utf-8")
            result_info["csv"] = csv_path
        except Exception as e:
            logger.error(f"Failed to write CSV: {e}")

        if allow_cache and fp and sp:
            try:
                _save_cached_outputs(fp, sp, {"csv": result_info["csv"], "html": result_info["html"],
                                              "json": result_info["json"], "pdf": result_info["pdf"],
                                              "summary": result_info["summary"]})
            except Exception:
                ...
        try:
            if result_info["pdf"]:
                set_setting("last_report_pdf", result_info["pdf"])
            if result_info["csv"]:
                set_setting("last_report_csv", result_info["csv"])
            if result_info["json"]:
                set_setting("last_report_json", result_info["json"])
            set_setting("last_analyzed_file", file_path)
        except Exception:
            ...

        report(100, "Done")
        logger.info("Report saved:")
        if result_info["csv"]:
            logger.info(f" - CSV:  {result_info['csv']}")
        if result_info["json"]:
            logger.info(f" - JSON: {result_info['json']}")
        if result_info["pdf"]:
            logger.info(f" - PDF:  {result_info['pdf']}")
        logger.info(f"(Reports directory: {os.path.dirname(pdf_path)})")
        result_info["fairness_metrics"] = fairness_metrics
        result_info["formatted_entities"] = formatted_entities
        return result_info
    except KeyboardInterrupt:
        logger.info("Analysis cancelled by user.")
        return result_info
    except Exception:
        logger.exception("Analyzer failed")
        return result_info


def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spec Kit Analyzer")
        try:
            self.setMinimumSize(1000, 700)
        except Exception:
            ...
        self._current_report_path: Optional[str] = None
        self._last_error: Optional[str] = None
        self._batch_cancel = False
        self.current_report_data: Optional[dict] = None
        self.local_rag: Optional[LocalRAG] = None
        self.guideline_service: Optional[GuidelineService] = None
        self.llm_compliance_service: Optional[LlmComplianceService] = None
        self._analytics_severity_filter = None
        self.chat_history: list[tuple[str, str]] = []

        # --- Initialize Services ---
        self.entity_consolidation_service = EntityConsolidationService(db_connection_provider=_get_db_connection)
        self.adjudication_service = AdjudicationService(db_connection_provider=_get_db_connection)
        ner_model_configs = {
            "biobert": "longluu/Clinical-NER-MedMentions-GatorTronBase",
            "biomed_ner": "d4data/biomedical-ner-all",
            "jsl_clinical_ner": "JSL_MODEL_PLACEHOLDER"
        }
        self.ner_service = NERService(model_configs=ner_model_configs)

        # --- Toolbar Setup ---
        tb = QToolBar("Main")
        try:
            tb.setMovable(False)
        except Exception:
            ...
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)

        # --- Actions ---
        act_open = QAction("Open File...", self)
        act_open.triggered.connect(self.action_open_report)
        tb.addAction(act_open)

        act_analyze = QAction("Analyze", self)
        act_analyze.triggered.connect(self.action_analyze_combined)
        tb.addAction(act_analyze)
        
        # ... Add other actions like logs, settings, etc. ...
        
        act_export_feedback = QAction("Export Feedback...", self)
        act_export_feedback.triggered.connect(self.action_export_feedback)
        tb.addAction(act_export_feedback)

        act_analyze_performance = QAction("Analyze Performance", self)
        act_analyze_performance.triggered.connect(self.action_analyze_performance)
        tb.addAction(act_analyze_performance)

        # --- Main Layout ---
        central = QWidget()
        self.setCentralWidget(central)
        vmain = QVBoxLayout(central)
        vmain.setContentsMargins(12, 12, 12, 12)
        vmain.setSpacing(14)

        # --- Create Tab Widget and Tabs ---
        self.tabs = QTabWidget()
        setup_tab = QWidget()
        results_tab = QWidget()
        logs_tab = QWidget()

        self.tabs.addTab(setup_tab, "Setup & File Queue")
        self.tabs.addTab(results_tab, "Analysis Results")
        self.tabs.addTab(logs_tab, "Application Logs")

        # --- Analytics Tab ---
        analytics_tab = QWidget()
        self.tabs.addTab(analytics_tab, "Analytics Dashboard")
        analytics_layout = QVBoxLayout(analytics_tab)

        analytics_controls = QHBoxLayout()
        btn_refresh_analytics = QPushButton("Refresh Analytics")
        self._style_action_button(btn_refresh_analytics, font_size=11, bold=True, height=32)
        try:
            btn_refresh_analytics.clicked.connect(self._update_analytics_tab)
        except Exception:
            pass
        analytics_controls.addWidget(btn_refresh_analytics)
        analytics_controls.addStretch(1)
        analytics_layout.addLayout(analytics_controls)
        
        self.analytics_figure = Figure(figsize=(5, 3))
        self.analytics_canvas = FigureCanvas(self.analytics_figure)
        analytics_layout.addWidget(self.analytics_canvas)

        stats_group = QGroupBox("Summary Statistics")
        stats_layout = QGridLayout(stats_group)
        self.lbl_total_runs = QLabel("N/A")
        self.lbl_avg_score = QLabel("N/A")
        self.lbl_avg_flags = QLabel("N/A")
        self.lbl_top_category = QLabel("N/A")
        stats_layout.addWidget(QLabel("Total Runs Analyzed:"), 0, 0)
        stats_layout.addWidget(self.lbl_total_runs, 0, 1)
        stats_layout.addWidget(QLabel("Average Compliance Score:"), 1, 0)
        stats_layout.addWidget(self.lbl_avg_score, 1, 1)
        stats_layout.addWidget(QLabel("Average Flags per Run:"), 2, 0)
        stats_layout.addWidget(self.lbl_avg_flags, 2, 1)
        stats_layout.addWidget(QLabel("Most Frequent Finding Category:"), 3, 0)
        stats_layout.addWidget(self.lbl_top_category, 3, 1)
        analytics_layout.addWidget(stats_group)

        # --- Setup Tab Layout ---
        setup_layout = QVBoxLayout(setup_tab)
        top_setup_layout = QHBoxLayout()
        rubric_panel = QGroupBox("Rubric")
        rubric_layout = QVBoxLayout(rubric_panel)

        row_rubric_btns = QHBoxLayout()
        self.btn_upload_rubric = QPushButton("Upload Rubric")
        self.btn_manage_rubrics = QPushButton("Manage Rubrics")
        for b in (self.btn_upload_rubric, self.btn_manage_rubrics):
            self._style_action_button(b, font_size=11, bold=True, height=32, padding="6px 10px")
            row_rubric_btns.addWidget(b)
        row_rubric_btns.addStretch(1)

        try:
            self.btn_upload_rubric.clicked.connect(self.action_upload_rubric)
            self.btn_manage_rubrics.clicked.connect(self.action_manage_rubrics)
        except Exception:
            ...
        rubric_layout.addLayout(row_rubric_btns)

        discipline_group = QGroupBox("Select Disciplines for Analysis")
        discipline_layout = QHBoxLayout(discipline_group)
        discipline_layout.setSpacing(15)
        self.chk_pt = QCheckBox("Physical Therapy")
        self.chk_ot = QCheckBox("Occupational Therapy")
        self.chk_slp = QCheckBox("Speech-Language Pathology")
        self.chk_all_disciplines = QCheckBox("All")
        self.chk_all_disciplines.setTristate(True)
        discipline_layout.addWidget(self.chk_pt)
        discipline_layout.addWidget(self.chk_ot)
        discipline_layout.addWidget(self.chk_slp)
        discipline_layout.addStretch(1)
        discipline_layout.addWidget(self.chk_all_disciplines)

        try:
            self.chk_all_disciplines.stateChanged.connect(self._toggle_all_disciplines)
            self.chk_pt.stateChanged.connect(self._update_all_checkbox_state)
            self.chk_ot.stateChanged.connect(self._update_all_checkbox_state)
            self.chk_slp.stateChanged.connect(self._update_all_checkbox_state)
        except Exception:
            pass
        rubric_layout.addWidget(discipline_group)

        self.lbl_rubric_file = QLabel("(No rubric selected)")
        self.lbl_rubric_file.setWordWrap(True)
        rubric_layout.addWidget(self.lbl_rubric_file)

        self.txt_rubric = QTextEdit()
        self.txt_rubric.setVisible(False) # Not shown in main UIreplace-wobbler-with-finding-1
        top_setup_layout.addWidget(rubric_panel)

        # Right: Report panel
        report_panel = QGroupBox("File Selection")
        report_layout = QVBoxLayout(report_panel)

        row_report_btns = QHBoxLayout()
        self.btn_upload_report = QPushButton("Open File")
        self.btn_upload_folder = QPushButton("Open Folder")
        for b in (self.btn_upload_report, self.btn_upload_folder):
            self._style_action_button(b, font_size=11, bold=True, height=32, padding="6px 10px")
            row_report_btns.addWidget(b)
        row_report_btns.addStretch(1)

        try:
            self.btn_upload_report.clicked.connect(self.action_open_report)
            self.btn_upload_folder.clicked.connect(self.action_open_folder)
        except Exception:
            ...
        report_layout.addLayout(row_report_btns)

        self.lbl_report_name = QLabel("(No file selected for single analysis)")

        self.lbl_report_name.setWordWrap(True)
        report_layout.addWidget(self.lbl_report_name)

        top_setup_layout.addWidget(report_panel)
        setup_layout.addLayout(top_setup_layout)

        # File Queue
        queue_group = QGroupBox("File Queue (for batch analysis)")
        queue_layout = QVBoxLayout(queue_group)

        queue_actions_layout = QHBoxLayout()
        self.btn_analyze_all = QPushButton("Analyze All in Queue")
        self.btn_cancel_batch = QPushButton("Cancel Batch")
        self.btn_remove_file = QPushButton("Remove Selected")
        self.btn_clear_all = QPushButton("Clear Queue")
        self._style_action_button(self.btn_analyze_all, font_size=11, bold=True, height=32)
        self._style_action_button(self.btn_cancel_batch, font_size=11, bold=True, height=32)
        self._style_action_button(self.btn_remove_file, font_size=11, bold=True, height=32)
        self._style_action_button(self.btn_clear_all, font_size=11, bold=True, height=32)

        queue_actions_layout.addWidget(self.btn_analyze_all)
        queue_actions_layout.addWidget(self.btn_cancel_batch)
        queue_actions_layout.addStretch(1)
        queue_actions_layout.addWidget(self.btn_remove_file)
        queue_actions_layout.addWidget(self.btn_clear_all)

        self.list_folder_files = QListWidget()
        queue_layout.addLayout(queue_actions_layout)
        queue_layout.addWidget(self.list_folder_files)

        setup_layout.addWidget(queue_group)

        # --- Results Tab Layout ---
        results_layout = QVBoxLayout(results_tab)
        results_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side: Analysis Report
        self.txt_chat = QTextEdit()
        self.txt_chat.setPlaceholderText("Analysis summary will appear here.")
        self.txt_chat.setReadOnly(True)
        if hasattr(self.txt_chat, 'anchorClicked'):
            self.txt_chat.anchorClicked.connect(self.handle_anchor_clicked)

        # Right side: Full Note Text
        self.txt_full_note = QTextEdit()
        self.txt_full_note.setPlaceholderText("Full note text will appear here after analysis.")
        self.txt_full_note.setReadOnly(True)

        results_splitter.addWidget(self.txt_chat)
        results_splitter.addWidget(self.txt_full_note)
        results_splitter.setSizes([400, 600]) # Initial sizing

        results_layout.addWidget(results_splitter)

        # --- Logs Tab Layout ---
        logs_layout = QVBoxLayout(logs_tab)
        log_actions_layout = QHBoxLayout()
        self.btn_clear_recent_files = QPushButton("Clear Recent Files History")
        self._style_action_button(self.btn_clear_recent_files, font_size=11, bold=True, height=28, padding="4px 10px")
        log_actions_layout.addStretch(1)
        log_actions_layout.addWidget(self.btn_clear_recent_files)

        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        flog = QFont(); flog.setPointSize(11); self.txt_logs.setFont(flog)

        logs_layout.addLayout(log_actions_layout)
        logs_layout.addWidget(self.txt_logs)

        # --- Main Layout Assembly ---
        vmain.addWidget(self.tabs)
        try:
            self.tabs.currentChanged.connect(self._on_tab_changed)
        except Exception: pass

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Ready")
        self.progress_bar.setVisible(False)
        vmain.addWidget(self.progress_bar)

        # Bottom AI chat input row
        input_row_bottom = QHBoxLayout()
        input_row_bottom.setSpacing(8)
        self.input_query_te = QTextEdit()
        self.input_query_te.setPlaceholderText("Ask a question about the analysis...")
        self.input_query_te.setFixedHeight(56)
        self.input_query_te.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        finput = QFont();
        finput.setPointSize(12)
        self.input_query_te.setFont(finput)
        btn_send = QPushButton("Send")
        fsend = QFont();
        fsend.setPointSize(13);
        fsend.setBold(True)
        btn_send.setFont(fsend)
        btn_send.setMinimumHeight(40)
        btn_send.setStyleSheet("text-align:center; padding:8px 12px;")
        try:
            btn_send.clicked.connect(self.action_send)  # type: ignore[attr-defined]
        except Exception:
            ...
        input_row_bottom.addWidget(self.input_query_te, 1)
        input_row_bottom.addWidget(btn_send, 0)

        btn_reset = QPushButton("Reset Chat")
        self._style_action_button(btn_reset, font_size=13, bold=False, height=40, padding="8px 12px")
        try:
            btn_reset.clicked.connect(self.action_reset_chat)
        except Exception:
            ...
        input_row_bottom.addWidget(btn_reset, 0)

        vmain.addLayout(input_row_bottom)

        # Status bar
        try:
            sb: QStatusBar = self.statusBar()
            sb.clearMessage()
            self.lbl_brand = QLabel("Pacific Coast Therapy 🏝️")
            brand_font = QFont("cursive")
            brand_font.setPointSize(12)
            self.lbl_brand.setFont(brand_font)
            self.lbl_brand.setStyleSheet("color:#93c5fd; padding-left:8px; font-weight:700;")
            self.lbl_brand.setToolTip("𝔎𝔢𝔳𝔦𝔫 𝔐𝔬𝔬𝔫")
            self.lbl_err = QLabel(" Status: OK ")
            self.lbl_err.setStyleSheet("background:#10b981; color:#111; padding:3px 8px; border-radius:12px;")
            self.lbl_rag_status = QLabel(" AI: Loading... ")
            self.lbl_rag_status.setStyleSheet("background:#6b7280; color:#fff; padding:3px 8px; border-radius:12px;")
            self.lbl_ner_status = QLabel(" NER: Loading... ")
            self.lbl_ner_status.setStyleSheet("background:#6b7280; color:#fff; padding:3px 8px; border-radius:12px;")
            sb.addPermanentWidget(self.lbl_brand)
            sb.addPermanentWidget(self.lbl_rag_status)
            sb.addPermanentWidget(self.lbl_ner_status)
            sb.addPermanentWidget(self.lbl_err)
        except Exception:
            ...

        # Init
        try:
            self._current_report_path = None
            self.lbl_report_name.setText("(No report selected)")
            self.refresh_llm_indicator()
            self.refresh_recent_files()
            self._update_analytics_tab() # Initial load
            self._init_llm_thread()
        except Exception as e:
            self.log(f"Error during initialization: {e}")

    def _toggle_all_disciplines(self, state):
        # Block signals to prevent infinite loops
        self.chk_pt.blockSignals(True)
        self.chk_ot.blockSignals(True)
        self.chk_slp.blockSignals(True)

        is_checked = (state == Qt.CheckState.Checked.value)
        self.chk_pt.setChecked(is_checked)
        self.chk_ot.setChecked(is_checked)
        self.chk_slp.setChecked(is_checked)

        self.chk_pt.blockSignals(False)
        self.chk_ot.blockSignals(False)
        self.chk_slp.blockSignals(False)

    def _update_all_checkbox_state(self):
        # This function is triggered when an individual discipline checkbox changes.
        # It updates the "All" checkbox to be checked, unchecked, or partially checked.

        # Block signals on the "All" checkbox to prevent recursive calls
        self.chk_all_disciplines.blockSignals(True)

        states = [self.chk_pt.isChecked(), self.chk_ot.isChecked(), self.chk_slp.isChecked()]

        if all(states):
            self.chk_all_disciplines.setCheckState(Qt.CheckState.Checked)
        elif any(states):
            self.chk_all_disciplines.setCheckState(Qt.CheckState.PartiallyChecked)
        else:
            self.chk_all_disciplines.setCheckState(Qt.CheckState.Unchecked)

        # Re-enable signals
        self.chk_all_disciplines.blockSignals(False)

    def _clear_previous_analysis_state(self):
        """Resets UI and state variables before a new analysis."""
        self.log("Clearing previous analysis state.")
        self.current_report_data = None
        self.chat_history = []
        self.txt_chat.clear()
        self.txt_full_note.clear()
        # Clear any highlighting or specific formatting
        self.txt_chat.setHtml("")
        self.txt_full_note.setPlainText("")
        self.txt_chat.setPlaceholderText("Analysis summary will appear here.")
        self.txt_full_note.setPlaceholderText("Full note text will appear here after analysis.")


    def _auto_select_discipline(self, text_to_analyze: str):
        if not self.local_rag or not self.local_rag.embedding_model:
            return

        try:
            from sklearn.metrics.pairwise import cosine_similarity

            self.log("Auto-detecting discipline from text...")

            prototypes = {
                "pt": "Physical therapy, gross motor skills, mobility, strength, balance, range of motion, gait training, therapeutic exercise.",
                "ot": "Occupational therapy, fine motor skills, activities of daily living (ADLs), sensory integration, self-care, functional independence, assistive technology.",
                "slp": "Speech-language pathology, communication, language, cognition, voice, fluency, dysphagia, swallowing, aphasia, articulation."
            }

            # Create embeddings for the prototype descriptions
            proto_embeddings = self.local_rag.embedding_model.encode(list(prototypes.values()))

            # Use the first 500 characters of the document for a quick classification
            doc_embedding = self.local_rag.embedding_model.encode([text_to_analyze[:500]])

            # Calculate similarities
            similarities = cosine_similarity(doc_embedding, proto_embeddings)[0]

            best_match_index = np.argmax(similarities)
            best_score = similarities[best_match_index]

            # Reset all checkboxes first
            self.chk_pt.setChecked(False)
            self.chk_ot.setChecked(False)
            self.chk_slp.setChecked(False)

            if best_score > 0.2: # Confidence threshold
                best_discipline = list(prototypes.keys())[best_match_index]
                if best_discipline == "pt":
                    self.chk_pt.setChecked(True)
                    self.log("Auto-selected: Physical Therapy")
                elif best_discipline == "ot":
                    self.chk_ot.setChecked(True)
                    self.log("Auto-selected: Occupational Therapy")
                elif best_discipline == "slp":
                    self.chk_slp.setChecked(True)
                    self.log("Auto-selected: Speech-Language Pathology")

        except Exception as e:
            self.log(f"Auto-discipline detection failed: {e}")


    def _init_llm_thread(self):
        """Initializes and starts the LLM loading worker thread."""
        self.llm_thread = QThread()
        self.llm_worker = LLMWorker(
            model_repo_id="TheBloke/TinyLlama-1.1B-1T-OpenOrca-GGUF",
            model_filename="tinyllama-1.1b-1t-openorca.Q4_K_M.gguf"
        )
        self.llm_worker.moveToThread(self.llm_thread)
        self.llm_thread.started.connect(self.llm_worker.run)
        self.llm_worker.finished.connect(self._on_rag_load_finished)
        self.llm_worker.error.connect(self._on_rag_load_error)
        self.llm_thread.finished.connect(self.llm_thread.deleteLater)
        self.llm_thread.start()

    def _on_rag_load_finished(self, rag_instance: LocalRAG):
        """Handles the successful loading of the RAG instance."""
        self.local_rag = rag_instance
        self.lbl_rag_status.setText(" AI: Ready ")
        self.lbl_rag_status.setStyleSheet("background:#10b981; color:#111; padding:3px 8px; border-radius:12px;")
        self.log("Local RAG AI is ready.")
        self.llm_thread.quit()

        # Now that the RAG instance is ready, we can load the guidelines
        self.log("Loading compliance guidelines...")
        self.guideline_thread = QThread()
        self.guideline_worker = GuidelineWorker(self.local_rag)
        self.guideline_worker.moveToThread(self.guideline_thread)
        self.guideline_thread.started.connect(self.guideline_worker.run)
        self.guideline_worker.finished.connect(self._on_guideline_load_finished)
        self.guideline_worker.error.connect(self._on_guideline_load_error)
        self.guideline_thread.finished.connect(self.guideline_thread.deleteLater)
        self.guideline_thread.start()


    def _on_guideline_load_finished(self, guideline_service: GuidelineService):
        """Handles the successful loading of the guidelines."""
        self.guideline_service = guideline_service
        self.log("Compliance guidelines loaded and indexed successfully.")
        # You could add another status label for guidelines if desired
        self.guideline_thread.quit()

    def _on_guideline_load_error(self, error_message: str):
        """Handles errors during guideline loading."""
        self.guideline_service = None
        self.log(f"Error loading guidelines: {error_message}")
        # You could add another status label for guidelines if desired
        self.guideline_thread.quit()

    def _on_rag_load_error(self, error_message: str):
        """Handles errors during RAG model loading."""
        self.local_rag = None
        self.lbl_rag_status.setText(" AI: Error ")
        self.lbl_rag_status.setStyleSheet("background:#ef4444; color:#fff; padding:3px 8px; border-radius:12px;")
        self.log(f"Error loading RAG AI: {error_message}")
        self.llm_thread.quit()

    def _on_tab_changed(self, index):
        if self.tabs.tabText(index) == "Analytics Dashboard":
            self._update_analytics_tab()

    def _fetch_analytics_data(self):
        try:
            with _get_db_connection() as conn:
                runs = pd.read_sql_query("SELECT run_time, compliance_score, flags FROM analysis_runs ORDER BY run_time ASC", conn)
                issues = pd.read_sql_query("SELECT category FROM analysis_issues", conn)
            return {"runs": runs, "issues": issues}
        except Exception as e:
            self.log(f"Failed to fetch analytics data: {e}")
            return None

    def _update_analytics_tab(self):
        data = self._fetch_analytics_data()
        if data is None or data["runs"].empty:
            self.log("No analytics data found to generate dashboard.")
            # Clear the chart and stats if no data
            self.analytics_figure.clear()
            self.analytics_canvas.draw()
            self.lbl_total_runs.setText("0")
            self.lbl_avg_score.setText("N/A")
            self.lbl_avg_flags.setText("N/A")
            self.lbl_top_category.setText("N/A")
            return

        runs_df = data["runs"]
        issues_df = data["issues"]

        # Update summary stats
        total_runs = len(runs_df)
        avg_score = runs_df["compliance_score"].mean()
        avg_flags = runs_df["flags"].mean()
        top_category = "N/A"
        if not issues_df.empty and not issues_df["category"].empty:
            top_category = issues_df["category"].mode()[0]

        self.lbl_total_runs.setText(str(total_runs))
        self.lbl_avg_score.setText(f"{avg_score:.1f} / 100.0")
        self.lbl_avg_flags.setText(f"{avg_flags:.2f}")
        self.lbl_top_category.setText(top_category)

        # Update chart
        self.analytics_figure.clear()
        ax = self.analytics_figure.add_subplot(111)

        scores = runs_df["compliance_score"].tolist()
        ax.plot(range(total_runs), scores, marker='o', linestyle='-', label="Compliance Score")

        # Add a trend line
        if total_runs > 1 and np:
            x = list(range(total_runs))
            try:
                z = np.polyfit(x, scores, 1)
                p = np.poly1d(z)
                ax.plot(x, p(x), "r--", label="Trend")
            except Exception as e:
                logger.warning(f"Could not compute trendline: {e}")


        ax.set_title("Compliance Score Trend")
        ax.set_xlabel("Analysis Run")
        ax.set_ylabel("Score")
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend()

        self.analytics_figure.tight_layout()
        self.analytics_canvas.draw()

    # Helpers and actions
    def _style_action_button(self, button: QPushButton, font_size: int = 11, bold: bool = True, height: int = 28, padding: str = "4px 10px"):
        try:
            f = QFont()
            f.setPointSize(font_size)
            f.setBold(bold)
            button.setFont(f)
            button.setMinimumHeight(height)
            button.setStyleSheet(f"text-align:center; padding:{padding};")
            button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        except Exception:
            ...

    def _show_admin_settings_dialog(self):
        from PyQt6.QtWidgets import QInputDialog

        password, ok = QInputDialog.getText(self, "Admin Access", "Enter Admin Password:", QLineEdit.EchoMode.Password)
        if not ok:
            return

        # Simple hardcoded password check
        if password != get_str_setting("admin_password", "admin123"):
            QMessageBox.warning(self, "Admin Access", "Incorrect password.")
            return

        # --- Admin Dialog ---
        dlg = QDialog(self)
        dlg.setWindowTitle("Admin Settings")
        vbox = QVBoxLayout(dlg)

        # NER Ensemble Setting
        chk_ner_ensemble = QCheckBox("Enable NER Ensemble (requires restart)")
        chk_ner_ensemble.setChecked(get_bool_setting("enable_ner_ensemble", True))
        vbox.addWidget(chk_ner_ensemble)

        # Trial period setting
        row_trial = QHBoxLayout()
        row_trial.addWidget(QLabel("Trial Duration (days, 0=unlimited):"))
        sp_trial_days = QSpinBox()
        sp_trial_days.setRange(0, 3650)
        sp_trial_days.setValue(get_int_setting("trial_duration_days", 30))
        row_trial.addWidget(sp_trial_days)
        vbox.addLayout(row_trial)

        btn_box = QHBoxLayout()
        btn_ok = QPushButton("Save")
        btn_cancel = QPushButton("Cancel")
        btn_box.addStretch(1)
        btn_box.addWidget(btn_ok)
        btn_box.addWidget(btn_cancel)
        vbox.addLayout(btn_box)

        def on_save():
            set_bool_setting("enable_ner_ensemble", chk_ner_ensemble.isChecked())
            set_setting("trial_duration_days", str(sp_trial_days.value()))
            self.refresh_llm_indicator() # Refresh the status bar
            dlg.accept()

        btn_ok.clicked.connect(on_save)
        btn_cancel.clicked.connect(dlg.reject)

        dlg.exec()

    def reapply_theme(self):
        try:
            app = QApplication.instance()
            if app:
                apply_theme(app)
                self.update()
        except Exception:
            ...

    def action_clear_recent_files(self):
        try:
            _save_recent_files([])
            self.log("Recent files cleared.")
            self.refresh_recent_files()
        except Exception as e:
            self.set_error(str(e))

    def log(self, msg: str):
        try:
            self.txt_logs.append(msg)
        except Exception:
            ...

    def set_error(self, msg: Optional[str]):
        self._last_error = msg
        if msg:
            self.lbl_err.setText(" Error ")
            self.lbl_err.setStyleSheet("background:#ef4444; color:#fff; padding:3px 8px; border-radius:12px;")
            self.log(f"Error: {msg}")
        else:
            self.lbl_err.setText(" Status: OK ")
            self.lbl_err.setStyleSheet("background:#10b981; color:#111; padding:3px 8px; border-radius:12px;")

    def refresh_recent_files(self):
        try:
            files = _load_recent_files()
            self.log("--- Recent Files ---")
            if files:
                for f in files:
                    self.log(f)
            else:
                self.log("(No recent files)")
            self.log("--------------------")
        except Exception:
            ...

    def action_upload_rubric(self):
        try:
            path, _ = QFileDialog.getOpenFileName(self, "Select rubric text file", "",
                                                  "Text files (*.txt);;All Files (*)")
            if not path:
                return
            set_setting("rubric_path", path)
            with open(path, "r", encoding="utf-8") as f:
                txt = f.read()
            self.txt_rubric.setPlainText(txt)
            self.lbl_rubric_file.setText(os.path.basename(path) if txt.strip() else "(No rubric selected)")
            if txt.strip():
                self.lbl_rubric_file.setStyleSheet("color:#60a5fa; font-weight:700;")
            self.log(f"Loaded rubric from: {path}")
            self.set_error(None)
        except Exception as e:
            logger.exception("Upload rubric failed")
            self.set_error(str(e))
            QMessageBox.warning(self, "Rubric", f"Failed to load rubric:\n{e}")

    def action_save_rubric_app_only(self):
        try:
            set_setting("rubric_current_text", self.txt_rubric.toPlainText())
            self.lbl_rubric_file.setText("Rubric Loaded")
            self.lbl_rubric_file.setStyleSheet("color:#60a5fa; font-weight:700;")
            self.log("Rubric saved (application-only).")
            QMessageBox.information(self, "Rubric", "Saved in application (does not modify the original file).")
        except Exception as e:
            logger.exception("Save rubric failed")
            self.set_error(str(e))
            QMessageBox.warning(self, "Rubric", f"Failed to save rubric:\n{e}")

    def action_manage_rubrics(self):
        try:
            dlg = QDialog(self)
            dlg.setWindowTitle("Manage Rubrics")
            dlg.setMinimumSize(600, 500)

            main_layout = QHBoxLayout(dlg)
            main_layout.setContentsMargins(12, 12, 12, 12)
            main_layout.setSpacing(8)

            # Left side: List and controls
            left_vbox = QVBoxLayout()

            lst = QListWidget()
            import json
            raw = get_setting("rubric_catalog") or "[]"
            catalog = json.loads(raw) if raw else []
            if not isinstance(catalog, list): catalog = []

            for it in catalog:
                lst.addItem(it.get("name", "Untitled"))
            left_vbox.addWidget(lst)

            # Right side: Editor
            right_vbox = QVBoxLayout()
            editor = QTextEdit()
            editor.setPlaceholderText("Select a rubric to view or edit its content.")
            right_vbox.addWidget(editor)

            # Bottom buttons
            bottom_hbox = QHBoxLayout()
            btn_add = QPushButton("Add From File...")
            btn_remove = QPushButton("Remove Selected")
            btn_save = QPushButton("Save Changes")
            btn_set_active = QPushButton("Set Active & Close")

            bottom_hbox.addWidget(btn_add)
            bottom_hbox.addWidget(btn_remove)
            bottom_hbox.addStretch(1)
            bottom_hbox.addWidget(btn_save)
            bottom_hbox.addWidget(btn_set_active)

            left_vbox.addLayout(bottom_hbox)

            main_layout.addLayout(left_vbox, 1)
            main_layout.addLayout(right_vbox, 2)

            def populate_editor():
                rowi = lst.currentRow()
                if rowi < 0 or rowi >= len(catalog):
                    editor.setPlainText("")
                    return
                editor.setPlainText(catalog[rowi].get("content", ""))

            def add_file():
                path, _ = QFileDialog.getOpenFileName(self, "Select rubric text file", "", "Text files (*.txt);;All Files (*)")
                if not path: return
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        txt = f.read()
                    name = os.path.basename(path)
                    if any(item.get("name") == name for item in catalog):
                        QMessageBox.warning(self, "Rubric", "A rubric with this name already exists.")
                        return
                    catalog.append({"name": name, "path": path, "content": txt})
                    set_setting("rubric_catalog", json.dumps(catalog, ensure_ascii=False))
                    lst.addItem(name)
                except Exception as e:
                    QMessageBox.warning(self, "Rubrics", f"Failed to add rubric:\n{e}")

            def remove_selected():
                rowi = lst.currentRow()
                if rowi < 0 or rowi >= len(catalog): return

                name = catalog[rowi].get("name", "")
                reply = QMessageBox.question(self, "Remove Rubric", f"Are you sure you want to remove '{name}'?")
                if not str(reply).lower().endswith("yes"): return

                del catalog[rowi]
                set_setting("rubric_catalog", json.dumps(catalog, ensure_ascii=False))
                lst.takeItem(rowi)
                editor.clear()

                if get_setting("rubric_active_name") == name:
                    set_setting("rubric_active_name", "")
                    self.lbl_rubric_file.setText("(No rubric selected)")
                    self.lbl_rubric_file.setStyleSheet("")
                QMessageBox.information(self, "Rubrics", f"Removed: {name}")

            def save_changes():
                rowi = lst.currentRow()
                if rowi < 0 or rowi >= len(catalog):
                    QMessageBox.warning(self, "Rubric", "Select a rubric to save.")
                    return
                catalog[rowi]["content"] = editor.toPlainText()
                set_setting("rubric_catalog", json.dumps(catalog, ensure_ascii=False))
                QMessageBox.information(self, "Rubrics", f"Changes to '{catalog[rowi]['name']}' saved.")

            def set_active():
                rowi = lst.currentRow()
                if rowi < 0 or rowi >= len(catalog):
                    QMessageBox.information(self, "Rubrics", "Select a rubric first.")
                    return

                save_changes() # Save changes before setting active
                it = catalog[rowi]
                set_setting("rubric_active_name", it.get("name", ""))
                set_setting("rubric_current_text", it.get("content", ""))
                self.txt_rubric.setPlainText(it.get("content", ""))
                self.lbl_rubric_file.setText(it.get("name", "Rubric Loaded"))
                self.lbl_rubric_file.setStyleSheet("color:#60a5fa; font-weight:700;")
                dlg.accept()

            try:
                lst.currentRowChanged.connect(populate_editor)
                btn_add.clicked.connect(add_file)
                btn_remove.clicked.connect(remove_selected)
                btn_save.clicked.connect(save_changes)
                btn_set_active.clicked.connect(set_active)
            except Exception: ...

            dlg.exec()
        except Exception as e:
            self.set_error(str(e))

    def action_toggle_rubric_preview(self):
        try:
            is_visible = self.txt_rubric.isVisible()
            self.txt_rubric.setVisible(not is_visible)
        except Exception as e:
            self.set_error(f"Failed to toggle rubric preview: {e}")

    def action_remove_rubric(self):
        try:
            reply = QMessageBox.question(self, "Remove Rubric",
                                         "Remove the current rubric from the app?\n(This does not delete any file.)")  # type: ignore
            if not str(reply).lower().endswith("yes"):
                return
            set_setting("rubric_current_text", "")
            set_setting("rubric_path", "")
            set_setting("rubric_active_name", "")
            self.txt_rubric.setPlainText("")
            self.lbl_rubric_file.setText("(No rubric selected)")
            self.lbl_rubric_file.setStyleSheet("")
            self.log("Rubric removed from app.")
            self.set_error(None)
        except Exception as e:
            self.set_error(str(e))

    def action_open_report(self):
        try:
            path, _ = QFileDialog.getOpenFileName(
                self, "Select a document to analyze", "",
                "All Files (*);;PDF (*.pdf);;Word (*.docx);;CSV (*.csv);;Excel (*.xlsx *.xls);;Images (*.png *.jpg *.jpeg *.bmp *.tiff)"
            )
            if not path:
                return
            self._current_report_path = path
            add_recent_file(path)
            self.refresh_recent_files()
            self.lbl_report_name.setText(os.path.basename(path))
            self.lbl_report_name.setStyleSheet("color:#60a5fa; font-weight:700;")
            self.set_error(None)

            # Auto-select discipline
            try:
                parsed_content = parse_document_content(path)
                full_text = " ".join([t for t, s in parsed_content])
                if full_text:
                    self._auto_select_discipline(full_text)
            except Exception as e:
                self.log(f"Failed to auto-select discipline during file open: {e}")

        except Exception as e:
            logger.exception("Open report failed")
            self.set_error(str(e))
            QMessageBox.warning(self, "Open", f"Failed to open file:\n{e}")

    def action_open_folder(self):
        try:
            folder = QFileDialog.getExistingDirectory(self,
                                                      "Select folder with documents")  # type: ignore[attr-defined]
            if not folder:
                return
            exts = {".pdf", ".docx", ".csv", ".xlsx", ".xls", ".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
            files = []
            for name in os.listdir(folder):
                p = os.path.join(folder, name)
                if os.path.isfile(p) and os.path.splitext(p)[1].lower() in exts:
                    files.append(p)
            files.sort()
            self.list_folder_files.clear()
            if files:
                self.list_folder_files.addItems(files)
                self.log(f"Loaded folder with {len(files)} files.")
                reply = QMessageBox.question(self, "Batch Analysis",
                                             f"{len(files)} supported files were found in the folder.\n\nDo you want to start the analysis for all of them now?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    self.action_analyze_batch()
            else:
                self.log("No supported documents found in the selected folder.")
        except Exception as e:
            logger.exception("Open folder failed")
            self.set_error(str(e))

    def action_remove_file(self):
        try:
            items = self.list_folder_files.selectedItems()
            if not items:
                QMessageBox.information(self, "Remove File", "Please select a file from the list to remove.")
                return
            for item in items:
                self.list_folder_files.takeItem(self.list_folder_files.row(item))
        except Exception as e:
            self.set_error(str(e))

    def action_clear_all(self):
=======
        tb = QToolBar("Main")
        try:
            tb.setMovable(False)
        except Exception:
            ...
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)

        act_open = QAction("Open File...", self)
        # act_open.triggered.connect(self.action_open_report)  # Placeholder
        tb.addAction(act_open)

        act_analyze = QAction("Analyze", self)
        act_analyze.triggered.connect(self.action_analyze_combined)
        tb.addAction(act_analyze)

        act_logs = QAction("Open Logs Folder", self)
        act_logs.triggered.connect(self.action_open_logs)
        tb.addAction(act_logs)

        act_analytics = QAction("Export Analytics CSV", self)
        act_analytics.triggered.connect(lambda: self._export_analytics_csv())
        tb.addAction(act_analytics)

        act_settings = QAction("Settings", self)
        act_settings.triggered.connect(lambda: _show_settings_dialog(self))
        tb.addAction(act_settings)

        act_admin_settings = QAction("Admin Settings...", self)
        # act_admin_settings.triggered.connect(self._show_admin_settings_dialog) # Placeholder
        tb.addAction(act_admin_settings)

        act_exit = QAction("Exit", self)
        act_exit.triggered.connect(self.close)
        tb.addAction(act_exit)

        tb.addSeparator()

        act_export_feedback = QAction("Export Feedback...", self)
        # act_export_feedback.triggered.connect(self.action_export_feedback) # Placeholder
        tb.addAction(act_export_feedback)

        act_analyze_performance = QAction("Analyze Performance", self)
        # act_analyze_performance.triggered.connect(self.action_analyze_performance) # Placeholder
        tb.addAction(act_analyze_performance)

        act_bias_audit = QAction("Bias Audit", self)
        act_bias_audit.triggered.connect(self.action_run_bias_audit)
        tb.addAction(act_bias_audit)

        central = QWidget()
        self.setCentralWidget(central)
        vmain = QVBoxLayout(central)
        vmain.setContentsMargins(12, 12, 12, 12)
        vmain.setSpacing(14)

        # --- Create Tab Widget and Tabs ---
        self.tabs = QTabWidget()
        setup_tab = QWidget()
        results_tab = QWidget()
        search_tab = QWidget()
        logs_tab = QWidget()

        self.tabs.addTab(setup_tab, "Setup & File Queue")
        self.tabs.addTab(results_tab, "Analysis Results")
        self.tabs.addTab(logs_tab, "Application Logs")


        # --- Logs Tab Layout ---
        logs_layout = QVBoxLayout(logs_tab)
        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setFontFamily("monospace")
        self.txt_logs.setPlaceholderText("Application events will be logged here.")
        logs_layout.addWidget(self.txt_logs)


        # --- Analytics Tab ---
        analytics_tab = QWidget()
        self.tabs.addTab(analytics_tab, "Analytics Dashboard")
        analytics_layout = QVBoxLayout(analytics_tab)

        analytics_controls = QHBoxLayout()
        analytics_controls.addWidget(QLabel("From:"))
        self.date_edit_from = QDateEdit(calendarPopup=True)
        self.date_edit_from.setDate(QDate.currentDate().addMonths(-1))
        analytics_controls.addWidget(self.date_edit_from)
        analytics_controls.addWidget(QLabel("To:"))
        self.date_edit_to = QDateEdit(calendarPopup=True)
        self.date_edit_to.setDate(QDate.currentDate())
        analytics_controls.addWidget(self.date_edit_to)

        btn_refresh_analytics = QPushButton("Refresh Analytics")
btn_refresh_analytics = QPushButton("Refresh Analytics")
self._style_action_button(btn_refresh_analytics, font_size=11, bold=True, height=32)
btn_refresh_analytics.clicked.connect(self._update_analytics_tab)

        btn_refresh_analytics.clicked.connect(self._update_analytics_tab)
        analytics_controls.addWidget(btn_refresh_analytics)

        self.discipline_filter_combo = QComboBox()
        self.discipline_filter_combo.addItems(["All", "pt", "ot", "slp"])
        self.discipline_filter_combo.currentTextChanged.connect(self._update_analytics_tab)
        analytics_controls.addWidget(QLabel("Filter by Discipline:"))
        analytics_controls.addWidget(self.discipline_filter_combo)

        analytics_controls.addStretch(1)
        analytics_layout.addLayout(analytics_controls)

analytics_layout.addLayout(analytics_controls)

# Plotly chart via QWebEngineView
self.analytics_view = QWebEngineView()
analytics_layout.addWidget(self.analytics_view)

# --- Bias Audit Tab ---
bias_audit_tab = QWidget()
self.tabs.addTab(bias_audit_tab, "Bias Audit")
bias_audit_layout = QVBoxLayout(bias_audit_tab)

bias_audit_controls = QHBoxLayout()
btn_run_bias_audit = QPushButton("Run Bias Audit")
self._style_action_button(btn_run_bias_audit, font_size=11, bold=True, height=32)
btn_run_bias_audit.clicked.connect(self._run_bias_audit)
bias_audit_controls.addWidget(btn_run_bias_audit)
bias_audit_controls.addStretch(1)
bias_audit_layout.addLayout(bias_audit_controls)

self.bias_audit_figure = Figure(figsize=(5, 3))
self.bias_audit_canvas = FigureCanvas(self.bias_audit_figure)
bias_audit_layout.addWidget(self.bias_audit_canvas)

        # Heatmap chart
        self.heatmap_figure = Figure(figsize=(5, 4))
        self.heatmap_canvas = FigureCanvas(self.heatmap_figure)
        analytics_layout.addWidget(self.heatmap_canvas)

        # --- Bias Audit Tab ---
        bias_audit_tab = QWidget()
        self.tabs.addTab(bias_audit_tab, "Bias Audit")
        self.bias_audit_layout = QVBoxLayout(bias_audit_tab)
        self.bias_audit_results_text = QTextEdit()
        self.bias_audit_results_text.setReadOnly(True)
        self.bias_audit_layout.addWidget(self.bias_audit_results_text)

        # Summary stats
        stats_group = QGroupBox("Summary Statistics")
        stats_layout = QGridLayout(stats_group)
        self.lbl_total_runs = QLabel("N/A")
        self.lbl_avg_score = QLabel("N/A")
        self.lbl_avg_flags = QLabel("N/A")
        self.lbl_top_category = QLabel("N/A")

        stats_layout.addWidget(QLabel("Total Runs Analyzed:"), 0, 0)
        stats_layout.addWidget(self.lbl_total_runs, 0, 1)
        stats_layout.addWidget(QLabel("Average Compliance Score:"), 1, 0)
        stats_layout.addWidget(self.lbl_avg_score, 1, 1)
        stats_layout.addWidget(QLabel("Average Flags per Run:"), 2, 0)
        stats_layout.addWidget(self.lbl_avg_flags, 2, 1)
        stats_layout.addWidget(QLabel("Most Frequent Finding Category:"), 3, 0)
        stats_layout.addWidget(self.lbl_top_category, 3, 1)

        analytics_layout.addWidget(stats_group)


        # --- Adjudication Tab ---
        adjudication_tab = QWidget()
        self.tabs.addTab(adjudication_tab, "Adjudication")
        adjudication_layout = QVBoxLayout(adjudication_tab)

        # Top controls
        adjudication_controls = QHBoxLayout()
        btn_refresh_adjudication = QPushButton("Refresh Queue")
        self._style_action_button(btn_refresh_adjudication, font_size=11, bold=True, height=32)
        try:
            btn_refresh_adjudication.clicked.connect(self._update_adjudication_tab)
        except Exception:
            pass
        adjudication_controls.addWidget(btn_refresh_adjudication)
        adjudication_controls.addStretch(1)
        adjudication_layout.addLayout(adjudication_controls)

        # Main splitter for table and details
        adjudication_splitter = QSplitter(Qt.Orientation.Vertical)

        # Table for items
        self.tbl_adjudication = QTableWidget()
        self.tbl_adjudication.setColumnCount(5)
        self.tbl_adjudication.setHorizontalHeaderLabels(["File", "Run Time", "Details", "Confidence", "Issue ID"])
        self.tbl_adjudication.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_adjudication.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_adjudication.setColumnHidden(4, True) # Hide issue ID
        try:
            self.tbl_adjudication.itemSelectionChanged.connect(self._on_adjudication_item_selected)
        except Exception:
            pass

        adjudication_splitter.addWidget(self.tbl_adjudication)

        # Adjudication controls panel
        details_group = QGroupBox("Review Selected Disagreement")
        self.review_details_group = details_group # Keep a reference
        details_layout = QGridLayout(details_group)

        details_layout.addWidget(QLabel("<b>Text:</b>"), 0, 0)
        self.lbl_adjudication_text = QLabel("<i>Select an item from the queue above.</i>")
        self.lbl_adjudication_text.setWordWrap(True)
        details_layout.addWidget(self.lbl_adjudication_text, 0, 1, 1, 3)

        details_layout.addWidget(QLabel("<b>Your Decision:</b>"), 1, 0, alignment=Qt.AlignmentFlag.AlignTop)

        self.rad_confirm_a = QRadioButton()
        self.rad_confirm_b = QRadioButton()
        self.rad_reject_both = QRadioButton("Neither is Correct")

        decision_box = QVBoxLayout()
        decision_box.addWidget(self.rad_confirm_a)
        decision_box.addWidget(self.rad_confirm_b)
        decision_box.addWidget(self.rad_reject_both)
        decision_box.addStretch(1)
        details_layout.addLayout(decision_box, 1, 1)

        details_layout.addWidget(QLabel("Corrected Label:"), 2, 0)
        self.txt_corrected_label = QLineEdit()
        self.txt_corrected_label.setPlaceholderText("Enter correct label if neither model was right")
        self.txt_corrected_label.setEnabled(False)
        details_layout.addWidget(self.txt_corrected_label, 2, 1, 1, 3)

        try:
            self.rad_reject_both.toggled.connect(self.txt_corrected_label.setEnabled)
        except Exception:
            pass

        details_layout.addWidget(QLabel("Notes:"), 3, 0, alignment=Qt.AlignmentFlag.AlignTop)
        self.txt_adjudication_notes = QTextEdit()
        self.txt_adjudication_notes.setPlaceholderText("Optional notes about your decision.")
        self.txt_adjudication_notes.setFixedHeight(80)
        details_layout.addWidget(self.txt_adjudication_notes, 3, 1, 1, 3)

        btn_save_adjudication = QPushButton("Save Adjudication")
        self._style_action_button(btn_save_adjudication, font_size=11, bold=True, height=32)
        try:
            btn_save_adjudication.clicked.connect(self._save_current_adjudication)
        except Exception:
            pass
        details_layout.addWidget(btn_save_adjudication, 4, 3)

        details_group.setEnabled(False) # Disabled until an item is selected
        adjudication_splitter.addWidget(details_group)
        adjudication_splitter.setSizes([400, 300])

        adjudication_layout.addWidget(adjudication_splitter)

bias_group = QGroupBox("Bias Auditing (by Discipline)")
bias_layout = QVBoxLayout(bias_group)

# Overall demographic parity labels (from feature branch)
overall_bias_layout = QHBoxLayout()
overall_bias_layout.addWidget(QLabel("<b>Overall Demographic Parity Difference:</b>"))
self.lbl_demographic_parity = QLabel("N/A")
self.lbl_demographic_parity.setStyleSheet("font-weight: bold;")
overall_bias_layout.addWidget(self.lbl_demographic_parity)
overall_bias_layout.addStretch(1)
bias_layout.addLayout(overall_bias_layout)

# Grid layout for by-group metrics (from feature branch)
self.bias_grid_layout = QGridLayout()
self.bias_grid_layout.setContentsMargins(10, 10, 10, 10)
self.bias_grid_layout.addWidget(QLabel("<b>Discipline</b>"), 0, 0)
self.bias_grid_layout.addWidget(QLabel("<b>Selection Rate (Flagged)</b>"), 0, 1)
self.bias_grid_layout.setColumnStretch(2, 1)
bias_layout.addLayout(self.bias_grid_layout)

# Matplotlib Canvas for visual bias audit (from main branch)
self.bias_figure = Figure(figsize=(5, 2.5))
self.bias_canvas = FigureCanvas(self.bias_figure)
bias_layout.addWidget(self.bias_canvas)

        analytics_layout.addWidget(bias_group)


        # --- Setup Tab Layout ---
        setup_layout = QVBoxLayout(setup_tab)

        top_setup_layout = QHBoxLayout()

        # Left: Rubric panel
        rubric_panel = QGroupBox("Rubric")
        rubric_layout = QVBoxLayout(rubric_panel)

        row_rubric_btns = QHBoxLayout()
        self.btn_upload_rubric = QPushButton("Upload Rubric")
        self.btn_manage_rubrics = QPushButton("Manage Rubrics")
        for b in (self.btn_upload_rubric, self.btn_manage_rubrics):
            row_rubric_btns.addWidget(b)
        row_rubric_btns.addStretch(1)

        try:
            self.btn_upload_rubric.clicked.connect(self.action_upload_rubric)
            self.btn_manage_rubrics.clicked.connect(self.action_manage_rubrics)
        except Exception:
            ...
        rubric_layout.addLayout(row_rubric_btns)

        # --- Discipline Selection Checkboxes ---
        discipline_group = QGroupBox("Select Disciplines for Analysis")
        discipline_layout = QHBoxLayout(discipline_group)
        discipline_layout.setSpacing(15)

        self.chk_pt = QCheckBox("Physical Therapy")
        self.chk_ot = QCheckBox("Occupational Therapy")
        self.chk_slp = QCheckBox("Speech-Language Pathology")
        self.chk_all_disciplines = QCheckBox("All")
        self.chk_all_disciplines.setTristate(True)

        discipline_layout.addWidget(self.chk_pt)
        discipline_layout.addWidget(self.chk_ot)
        discipline_layout.addWidget(self.chk_slp)
        discipline_layout.addStretch(1)
        discipline_layout.addWidget(self.chk_all_disciplines)

        try:
            self.chk_all_disciplines.stateChanged.connect(self._toggle_all_disciplines)
            self.chk_pt.stateChanged.connect(self._update_all_checkbox_state)
            self.chk_ot.stateChanged.connect(self._update_all_checkbox_state)
            self.chk_slp.stateChanged.connect(self._update_all_checkbox_state)
        except Exception:
            pass

        rubric_layout.addWidget(discipline_group)
        # --- End Discipline Selection ---

        self.lbl_rubric_file = QLabel("(No rubric selected)")

        self.lbl_rubric_file.setWordWrap(True)
        rubric_layout.addWidget(self.lbl_rubric_file)

        self.txt_rubric = QTextEdit()
        self.txt_rubric.setVisible(False) # Not shown in main UI


        top_setup_layout.addWidget(rubric_panel)

        # Right: Report panel
        report_panel = QGroupBox("File Selection")
        report_layout = QVBoxLayout(report_panel)

        row_report_btns = QHBoxLayout()
        self.btn_upload_report = QPushButton("Open File")
        self.btn_upload_folder = QPushButton("Open Folder")
        for b in (self.btn_upload_report, self.btn_upload_folder):
            self._style_action_button(b, font_size=11, bold=True, height=32, padding="6px 10px")
            row_report_btns.addWidget(b)
        row_report_btns.addStretch(1)

        try:
            self.btn_upload_report.clicked.connect(self.action_open_report)
            self.btn_upload_folder.clicked.connect(self.action_open_folder)
        except Exception:
            ...
        report_layout.addLayout(row_report_btns)

        self.lbl_report_name = QLabel("(No file selected for single analysis)")

        self.lbl_report_name.setWordWrap(True)
        report_layout.addWidget(self.lbl_report_name)

        top_setup_layout.addWidget(report_panel)
        setup_layout.addLayout(top_setup_layout)

        # File Queue
        queue_group = QGroupBox("File Queue (for batch analysis)")
        queue_layout = QVBoxLayout(queue_group)

        queue_actions_layout = QHBoxLayout()
        self.btn_analyze_all = QPushButton("Analyze All in Queue")
        self.btn_cancel_batch = QPushButton("Cancel Batch")
        self.btn_remove_file = QPushButton("Remove Selected")
        self.btn_clear_all = QPushButton("Clear Queue")
        self._style_action_button(self.btn_analyze_all, font_size=11, bold=True, height=32)
        self._style_action_button(self.btn_cancel_batch, font_size=11, bold=True, height=32)
        self._style_action_button(self.btn_remove_file, font_size=11, bold=True, height=32)
        self._style_action_button(self.btn_clear_all, font_size=11, bold=True, height=32)

        queue_actions_layout.addWidget(self.btn_analyze_all)
        queue_actions_layout.addWidget(self.btn_cancel_batch)
        queue_actions_layout.addStretch(1)
        queue_actions_layout.addWidget(self.btn_remove_file)
        queue_actions_layout.addWidget(self.btn_clear_all)

        self.list_folder_files = QListWidget()
        queue_layout.addLayout(queue_actions_layout)
        queue_layout.addWidget(self.list_folder_files)

        setup_layout.addWidget(queue_group)

        # --- Results Tab Layout ---
        results_layout = QVBoxLayout(results_tab)
        results_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side: Analysis Report
        self.txt_chat = QTextEdit()
        self.txt_chat.setPlaceholderText("Analysis summary will appear here.")
        self.txt_chat.setReadOnly(True)
        self.txt_chat.anchorClicked.connect(self.handle_anchor_clicked)

        # Right side: Full Note Text
        self.txt_full_note = QTextEdit()
        self.txt_full_note.setPlaceholderText("Full note text will appear here after analysis.")
        self.txt_full_note.setReadOnly(True)

        results_splitter.addWidget(self.txt_chat)
        results_splitter.addWidget(self.txt_full_note)
        results_splitter.setSizes([400, 600]) # Initial sizing

        results_layout.addWidget(results_splitter)

        # --- Logs Tab Layout ---
        logs_layout = QVBoxLayout(logs_tab)
        log_actions_layout = QHBoxLayout()
        self.btn_clear_recent_files = QPushButton("Clear Recent Files History")
        self._style_action_button(self.btn_clear_recent_files, font_size=11, bold=True, height=28, padding="4px 10px")
        log_actions_layout.addStretch(1)
        log_actions_layout.addWidget(self.btn_clear_recent_files)

        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        flog = QFont(); flog.setPointSize(11); self.txt_logs.setFont(flog)

        logs_layout.addLayout(log_actions_layout)
        logs_layout.addWidget(self.txt_logs)

        # --- Main Layout Assembly ---
        vmain.addWidget(self.tabs)
        try:
            self.tabs.currentChanged.connect(self._on_tab_changed)
        except Exception: pass

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Ready")
        self.progress_bar.setVisible(False)
        vmain.addWidget(self.progress_bar)

        # Bottom AI chat input row
        input_row_bottom = QHBoxLayout()
        input_row_bottom.setSpacing(8)
        self.input_query_te = QTextEdit()
        self.input_query_te.setPlaceholderText("Ask a question about the analysis...")
        self.input_query_te.setFixedHeight(56)
        self.input_query_te.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        finput = QFont();
        finput.setPointSize(12)
        self.input_query_te.setFont(finput)
        btn_send = QPushButton("Send")
        fsend = QFont();
        fsend.setPointSize(13);
        fsend.setBold(True)
        btn_send.setFont(fsend)
        btn_send.setMinimumHeight(40)
        btn_send.setStyleSheet("text-align:center; padding:8px 12px;")
        try:
            btn_send.clicked.connect(self.action_send)  # type: ignore[attr-defined]
        except Exception:
            ...
        input_row_bottom.addWidget(self.input_query_te, 1)
        input_row_bottom.addWidget(btn_send, 0)

        btn_reset = QPushButton("Reset Chat")
        self._style_action_button(btn_reset, font_size=13, bold=False, height=40, padding="8px 12px")
        try:
            btn_reset.clicked.connect(self.action_reset_chat)
        except Exception:
            ...
        input_row_bottom.addWidget(btn_reset, 0)

        vmain.addLayout(input_row_bottom)

        # Status bar
        try:
            sb: QStatusBar = self.statusBar()
            sb.clearMessage()
            self.lbl_brand = QLabel("Pacific Coast Therapy 🏝️")
            brand_font = QFont("cursive")
            brand_font.setPointSize(12)
            self.lbl_brand.setFont(brand_font)
            self.lbl_brand.setStyleSheet("color:#93c5fd; padding-left:8px; font-weight:700;")
            self.lbl_brand.setToolTip("𝔎𝔢𝔳𝔦𝔫 𝔐𝔬𝔬𝔫")
            self.lbl_err = QLabel(" Status: OK ")
            self.lbl_err.setStyleSheet("background:#10b981; color:#111; padding:3px 8px; border-radius:12px;")
            self.lbl_rag_status = QLabel(" AI: Loading... ")
            self.lbl_rag_status.setStyleSheet("background:#6b7280; color:#fff; padding:3px 8px; border-radius:12px;")
            self.lbl_ner_status = QLabel(" NER: Loading... ")
            self.lbl_ner_status.setStyleSheet("background:#6b7280; color:#fff; padding:3px 8px; border-radius:12px;")
            sb.addPermanentWidget(self.lbl_brand)
            sb.addPermanentWidget(self.lbl_rag_status)
            sb.addPermanentWidget(self.lbl_ner_status)
            sb.addPermanentWidget(self.lbl_err)
        except Exception:
            ...

        # Init

# Automatically load analytics on startup
self._update_analytics_tab()
    def action_clear_all(self):

        try:
            self._current_report_path = None
            self.lbl_report_name.setText("(No report selected)")
            self.lbl_report_name.setStyleSheet("")
            try:
                self.list_folder_files.clear()
            except Exception:
                ...
            try:
                self.txt_chat.clear()
            except Exception:
                ...
            self.log("Cleared all selections.")
        except Exception as e:
            self.set_error(str(e))

def _update_analytics_tab(self):
        """Queries the database for analytics data and updates the chart and summary stats."""
        try:
            start_date = self.date_edit_from.date().toString("yyyy-MM-dd")
            end_date = self.date_edit_to.date().addDays(1).toString("yyyy-MM-dd")

            with _get_db_connection() as conn:
                # Fetch data for the chart
                query = """
                    SELECT i.severity
                    FROM analysis_issues i
                    JOIN analysis_runs r ON i.run_id = r.id
                    WHERE r.run_time >= ? AND r.run_time < ?
                """
                df = pd.read_sql_query(query, conn, params=(start_date, end_date))

                # Fetch data for summary stats
                query_runs = "SELECT COUNT(id), AVG(compliance_score), AVG(flags) FROM analysis_runs WHERE run_time >= ? AND run_time < ?"
                summary_df = pd.read_sql_query(query_runs, conn, params=(start_date, end_date))

                query_top_cat = """
                    SELECT category, COUNT(id) as count
                    FROM analysis_issues
                    WHERE run_id IN (SELECT id FROM analysis_runs WHERE run_time >= ? AND run_time < ?)
                    GROUP BY category ORDER BY count DESC LIMIT 1
                """
                top_cat_df = pd.read_sql_query(query_top_cat, conn, params=(start_date, end_date))

            # --- Update Summary Stats ---
            if not summary_df.empty:
                self.lbl_total_runs.setText(str(summary_df.iloc[0, 0] or 0))
                self.lbl_avg_score.setText(f"{summary_df.iloc[0, 1] or 0:.1f}")
                self.lbl_avg_flags.setText(f"{summary_df.iloc[0, 2] or 0:.2f}")
            if not top_cat_df.empty:
                self.lbl_top_category.setText(top_cat_df.iloc[0, 0] or "N/A")

            # --- Update Chart ---
            self.analytics_figure.clear()
            ax = self.analytics_figure.add_subplot(111)

            severities = ["flags", "findings", "suggestions"]
            counts = [
                df[df["severity"] == "flag"].shape[0],
                df[df["severity"] == "finding"].shape[0],
                df[df["severity"] == "suggestion"].shape[0],
            ]

            bars = ax.bar(severities, counts, color=["#ef4444", "#f59e0b", "#10b981"], picker=5)
            for i, bar in enumerate(bars):
                bar.set_gid(severities[i])

            ax.set_ylabel("Count")
            ax.set_title("Findings by Severity")
            self.analytics_figure.tight_layout()
            self.analytics_canvas.draw()

        except Exception as e:
            self.log(f"Error updating analytics tab: {e}")
            logger.exception("Failed to update analytics tab")

    def on_chart_pick(self, event):
        """Handles clicks on the analytics chart to trigger a drill-down."""
        if not (hasattr(event, 'artist') and event.artist):
            self.log("Chart clicked, but no specific bar was picked.")
            return

        category = event.artist.get_gid()
        if not category:
            return

        self.log(f"Chart category clicked: {category}")
        
        try:
            start_date = self.date_edit_from.date().toString("yyyy-MM-dd")
            end_date = self.date_edit_to.date().addDays(1).toString("yyyy-MM-dd")
            severity = category.rstrip('s') # "flags" -> "flag", etc.

            with _get_db_connection() as conn:
                query = """
                    SELECT r.file_name, r.run_time, i.category, i.title, i.detail, r.id as run_id
                    FROM analysis_issues i
                    JOIN analysis_runs r ON i.run_id = r.id
                    WHERE r.run_time >= ? AND r.run_time < ? AND i.severity = ?
                    ORDER BY r.run_time DESC
                """
                df = pd.read_sql_query(query, conn, params=(start_date, end_date, severity))

            if not df.empty:
                data_list = df.to_dict('records')
                dialog = DrillDownDialog(data_list, category, self)
                dialog.run_selected.connect(self.load_report_from_run_id)
                dialog.exec()
            else:
                QMessageBox.information(self, "Drill-Down", f"No '{category}' found in the selected date range.")

        except Exception as e:
            self.log(f"Error during drill-down: {e}")
            logger.exception("Drill-down failed")
            QMessageBox.warning(self, "Error", f"Could not perform drill-down.\n{e}")
    
    # ... and so on for the rest of the new methods from the main branch ...
            def _cancel():
                return self._progress_was_canceled()

            selected_disciplines = []
            if self.chk_pt.isChecked(): selected_disciplines.append('pt')
            if self.chk_ot.isChecked(): selected_disciplines.append('ot')
            if self.chk_slp.isChecked(): selected_disciplines.append('slp')

            if not selected_disciplines:
                QMessageBox.warning(self, "No Discipline Selected", "Please select at least one discipline (e.g., PT, OT, SLP) to analyze.")
                return

res = run_analyzer(self, self._current_report_path, selected_disciplines=selected_disciplines, entity_consolidation_service=self.entity_consolidation_service, progress_cb=_cb, cancel_cb=_cancel, main_window_instance=self)
            outs = []
            if res.get("pdf"):
                outs.append(f"PDF: {res['pdf']}")
            if res.get("csv"):
                outs.append(f"CSV: {res['csv']}")
            if res.get("json"):
                outs.append(f"JSON: {res['json']}")
            if outs:
                cache_hit = get_bool_setting("last_analysis_from_cache", False)
                if cache_hit:
                    self.log("Served from cache.")
                    try:
                        self.txt_chat.append("Note: Served from cache for faster results.\n")
                    except Exception:
                        ...
                self.log("Analysis complete:\n" + "\n".join(" - " + x for x in outs))
                try:
                    import json
                    with open(res["json"], "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.render_analysis_to_results(data, fairness_metrics=res.get("fairness_metrics", {}))

                    # --- Create and index the context for the AI ---
                    if self.local_rag and self.local_rag.is_ready():
                        self.log("Creating AI context index for in-document chat...")
                        context_chunks = self._create_context_chunks(data, res.get("formatted_entities", []))
                        self.local_rag.create_index(context_chunks)
                        self.log("AI context index created successfully.")
                    else:
                        self.log("AI not ready, skipping context indexing.")
                    # --- End AI context indexing ---

                except Exception:
                    ...
                try:
                    _open_path(res["pdf"])
                except Exception:
                    ...
            else:
                self.log("Analysis finished, but no outputs were generated. See logs.")
                QMessageBox.warning(self, "Analysis", "Finished, but no outputs were generated. See logs.")

            self._progress_finish()
            self.statusBar().showMessage("Ready")
            self.set_error(None)
        except Exception as e:
            logger.exception("Analyze failed")
            self._progress_finish()
            self.set_error(str(e))
            QMessageBox.warning(self, "Error", f"Failed to analyze file:\n{e}")
        finally:
            try:
                QApplication.restoreOverrideCursor()
                self.btn_analyze_all.setDisabled(False)
            except Exception:
                ...

    def _create_context_chunks(self, data: dict, formatted_entities: list[str]) -> list[tuple[str, str]]:
        """Creates a list of text chunks from the analysis data for the RAG index."""
        chunks = []

        # 1. Add summary information
        if 'compliance' in data and 'score' in data['compliance']:
            chunks.append((f"The overall compliance score is {data['compliance']['score']}/100.", "Summary"))
        if 'executive_status' in data:
            chunks.append((f"The executive status is '{data['executive_status']}'.", "Summary"))

        # 2. Add each issue as a detailed chunk, enriched with rubric data
        for issue in data.get('issues', []):
            issue_title = issue.get('title')
            # Find the corresponding full rule from the rubric
            matching_rule = next((r for r in self.compliance_rules if r.issue_title == issue_title), None)

            if matching_rule:
                # If we found the rule, create a detailed, structured chunk
                issue_str = (
                    f"A finding with severity '{matching_rule.severity}' was identified.\n"
                    f"Category: {matching_rule.issue_category}\n"
                    f"Title: {matching_rule.issue_title}\n"
                    f"Why it matters: {matching_rule.issue_detail}"
                )
                chunks.append((issue_str, "Finding"))
            else:
                # Fallback to the basic information if no rule is found
                sev = issue.get('severity', 'N/A').title()
                cat = issue.get('category', 'N/A')
                detail = issue.get('detail', 'N/A')
                chunks.append((f"Severity: {sev}. Category: {cat}. Title: {issue_title}. Detail: {detail}.", "Finding"))
            # Add citations as separate, clearly linked chunks
            for i, (citation_text, source) in enumerate(issue.get('citations', [])[:2]):
                clean_citation = re.sub('<[^<]+?>', '', citation_text)
chunks.append((f"The finding '{issue_title}' is supported by evidence: \"{clean_citation}\"", source))

        # 3. Add the original document sentences
        for text, source in data.get('source_sentences', []):
            chunks.append((f"\"{text}\"", source))

        # 4. Add formatted entities
        for entity in formatted_entities:
            chunks.append((entity, "Named Entity"))

        self.log(f"Generated {len(chunks)} text chunks for AI context.")
        return chunks

    def action_analyze_batch(self):
        try:
            n = self.list_folder_files.count()
            if n == 0:
                QMessageBox.information(self, "Analyze Batch", "Please upload a folder with documents first.")
                return
            reply = QMessageBox.question(self, "Analyze Batch",
                                         f"Process {n} file(s) sequentially?")
            if not str(reply).lower().endswith("yes"):
                return

            selected_disciplines = []
            if self.chk_pt.isChecked(): selected_disciplines.append('pt')
            if self.chk_ot.isChecked(): selected_disciplines.append('ot')
            if self.chk_slp.isChecked(): selected_disciplines.append('slp')

            if not selected_disciplines:
                QMessageBox.warning(self, "No Discipline Selected", "Please select at least one discipline (e.g., PT, OT, SLP) to run a batch analysis.")
                return

            self._clear_previous_analysis_state()
            self._batch_cancel = False
            self.btn_cancel_batch.setDisabled(False)
            self._progress_start("Batch analyzing...")
            ok_count = 0
            fail_count = 0
            for i in range(n):
                if self._progress_was_canceled() or self._batch_cancel:
                    break
                try:
                    item = self.list_folder_files.item(i)
                    path = item.text()
                    if not os.path.isfile(path):
                        continue
                    self.lbl_report_name.setText(os.path.basename(path))
                    self.statusBar().showMessage(f"Analyzing ({i + 1}/{n}): {os.path.basename(path)}")

                    def _cb(p, m):
                        overall = int(((i + (p / 100.0)) / max(1, n)) * 100)
                        self._progress_update(overall, f"File {i + 1}/{n}: {m}")

                    def _cancel():
                        return self._progress_was_canceled() or self._batch_cancel

                    res = run_analyzer(self, path, selected_disciplines=selected_disciplines, entity_consolidation_service=self.entity_consolidation_service, progress_cb=_cb, cancel_cb=_cancel, main_window_instance=self)
                    
                    if res.get("pdf") or res.get("json") or res.get("csv"):
                        ok_count += 1
                    else:
                        fail_count += 1
                except Exception:
                    fail_count += 1

            self.btn_cancel_batch.setDisabled(True)
            self._progress_finish()
            self.statusBar().showMessage("Ready")

            try:
                cancelled = self._batch_cancel or self._progress_was_canceled()
                folder = ensure_reports_dir_configured()
                if cancelled:
                    title = "Batch Cancelled"
                    body_top = f"Batch cancelled. Finished {ok_count} out of {n} file(s)."
                else:
                    title = "Batch Complete"
                    body_top = f"All set! Your batch is complete.\n\nSummary:\n- Success: {ok_count}\n- Failed:  {fail_count}"
                
                msg = [body_top, "", f"Location: {folder}", "", "Open that folder now?"]
                reply2 = QMessageBox.question(self, title, "\n".join(msg))
                if str(reply2).lower().endswith("yes"):
                    _open_path(folder)
            except Exception:
                ...
            self.log(f"Batch finished. Success={ok_count}, Failed={fail_count}, Cancelled={self._batch_cancel}")
        except Exception as e:
            logger.exception("Analyze batch failed")
            self.btn_cancel_batch.setDisabled(True)
            self._progress_finish()
            self.set_error(str(e))

    def action_analyze_combined(self):
        try:
            if self.list_folder_files.count() > 0:
                self.action_analyze_batch()
            elif self._current_report_path:
                self.action_analyze()
            else:
                QMessageBox.information(self, "Analyze", "Please upload/select a report or upload a folder first.")
        except Exception as e:
            self.set_error(str(e))

    def _export_analytics_csv(self):
        try:
            dest = os.path.join(ensure_reports_dir_configured(), "SpecKit-Analytics.csv")
            if export_analytics_csv(dest):
                _open_path(dest)
                self.log(f"Exported analytics CSV: {dest}")
            else:
                QMessageBox.information(self, "Analytics", "No analytics available yet.")
        except Exception as e:
            self.set_error(str(e))

def action_export_view_to_pdf(self):
        """Exports the current content of the main chat/analysis view to a PDF."""
        if not self.current_report_data:
            QMessageBox.warning(self, "Export Error", "Please analyze a document first.")
            return

        default_filename = os.path.basename(self.current_report_data.get('file', 'report.pdf'))
        default_filename = os.path.splitext(default_filename)[0] + "_annotated.pdf"

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", default_filename, "PDF Files (*.pdf)"
        )

        if not save_path:
            return

        try:
            self.statusBar().showMessage("Exporting to PDF...")
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

            html_content = self.txt_chat.toHtml()
            doc = QTextDocument()
            doc.setHtml(html_content)

            writer = QPdfWriter(save_path)
            writer.setPageSize(QPdfWriter.PageSize.A4)
            doc.print_(writer)

            self.log(f"Successfully exported view to {save_path}")
            QMessageBox.information(self, "Export Successful", f"The current view has been exported to:\n{save_path}")

        except Exception as e:
            self.set_error(f"Failed to export view to PDF: {e}")
            QMessageBox.critical(self, "Export Error", f"An error occurred while exporting to PDF:\n{e}")
        finally:
            self.statusBar().showMessage("Ready")
            QApplication.restoreOverrideCursor()

    def render_analysis_to_results(self, data: dict, highlight_range: Optional[Tuple[int, int]] = None, fairness_metrics: Optional[dict] = None) -> None:
        try:
            # --- Update Fairness Metrics ---
            if fairness_metrics and fairness_metrics.get('by_group') is not None:
                dpd = fairness_metrics.get('demographic_parity_difference')
                by_group = fairness_metrics.get('by_group')
                if dpd is not None: self.lbl_demographic_parity.setText(f"{dpd:.4f}")
                else: self.lbl_demographic_parity.setText("N/A")
                while self.bias_layout.rowCount() > 1:
                    # ... (code to clear bias layout) ...
                    self.bias_layout.removeRow(1)
                row = 1
                if isinstance(by_group, pd.Series):
                    for group, rate in by_group.items():
                        self.bias_layout.addWidget(QLabel(f"{str(group).upper()}"), row, 0)
                        self.bias_layout.addWidget(QLabel(f"{rate:.4f}"), row, 1)
                        row += 1
            else:
                self.lbl_demographic_parity.setText("N/A")
                while self.bias_layout.rowCount() > 1:
                    # ... (code to clear bias layout) ...
                    self.bias_layout.removeRow(1)

            # --- Clear on New Analysis Prompt ---
            if self.chat_history:
                reply = QMessageBox.question(self, "Clear Chat History", "You have an existing conversation. Would you like to clear it for this new analysis?")
                if str(reply).lower().endswith("yes"):
                    self.chat_history = []
                    self.log("Chat history cleared for new analysis.")

            # --- Bug Fix: Ensure issue IDs are present ---
            issues = data.get("issues", [])
            if issues and 'id' not in issues[0]:
                try:
                    with _get_db_connection() as conn:
                        run_df = pd.read_sql_query("SELECT id FROM analysis_runs WHERE file_name = ? AND run_time = ? LIMIT 1", conn, params=(os.path.basename(data.get("file")), data.get("generated")))
                        if not run_df.empty:
                            run_id = run_df.iloc[0]['id']
                            issues_from_db_df = pd.read_sql_query("SELECT id, title, detail FROM analysis_issues WHERE run_id = ?", conn, params=(run_id,))
                            issue_map = { (row['title'], row['detail']): row['id'] for _, row in issues_from_db_df.iterrows() }
                            for issue in issues:
                                issue['id'] = issue_map.get((issue.get('title'), issue.get('detail')))
                except Exception as e:
                    self.log(f"Could not enrich loaded report with issue IDs: {e}")

            self.current_report_data = data
            self.tabs.setCurrentIndex(1) # Switch to results tab

            file_name = os.path.basename(data.get("file", "Unknown File"))
            report_html_lines = [f"<h2>Analysis for: {file_name}</h2>"]
            report_html_lines.extend(_generate_risk_dashboard(data['compliance']['score'], data['sev_counts']))
            report_html_lines.extend(_generate_compliance_checklist(data['strengths'], data['weaknesses']))
            report_html_lines.append("<h3>Detailed Findings</h3>")
            
            if issues:
                for issue in issues:
                    loc = issue.get('location')
                    link = f"<a href='highlight:{loc['start']}:{loc['end']}'>Show in text</a>" if loc else ""
                    sev_color = {"Flag": "#dc3545", "Finding": "#ffc107", "Suggestion": "#17a2b8"}.get(issue.get("severity", "").title(), "#6c757d")
                    report_html_lines.append(f"<div style='border-left: 3px solid {sev_color}; padding-left: 10px; margin-bottom: 15px;'>")
                    report_html_lines.append(f"<strong>{issue.get('title', 'Finding')}</strong><br>")
                    report_html_lines.append(f"<small>Severity: {issue.get('severity', '').title()} | Category: {issue.get('category', 'General')} | {link}</small>")

                    # Add review links
                    issue_id = issue.get('id')
                    if issue_id:
                        encoded_title = quote(issue.get('title', ''))
                        report_html_lines.append(f"""
                        <a href='review:{issue_id}:correct' style='text-decoration:none; color:green;'>✔️ Correct</a>
                        <a href='review:{issue_id}:incorrect' style='text-decoration:none; color:red;'>❌ Incorrect</a>
                        <a href='educate:{encoded_title}' style='text-decoration:none; color:#60a5fa; margin-left: 10px;'>🎓 Learn More</a>
                        """)

                    # --- Guideline Display ---
                    if issue.get('guidelines'):
                        report_html_lines.append("<p><strong>Relevant Guidelines:</strong></p><ul>")
                        for guideline in issue['guidelines']:
                            text = html.escape(guideline.get('text', ''))
                            source = html.escape(guideline.get('source', ''))
                            report_html_lines.append(f"<li><i>“{text}”</i> (Source: {source})</li>")
                        report_html_lines.append("</ul>")

                    report_html_lines.append("</div>")
            else:
                report_html_lines.append("<p>No specific audit findings were identified.</p>")

            # --- Add Suggested Questions ---
            suggested_questions = data.get('suggested_questions', [])
            if suggested_questions:
                report_html_lines.append("<hr><h2>Suggested Questions</h2>")
                suggestions_html = "<ul>"
                for q in suggested_questions:
                    encoded_q = quote(q)
                    suggestions_html += f"<li><a href='ask:{encoded_q}' class='suggestion-link'>{html.escape(q)}</a></li>"
                suggestions_html += "</ul>"
                report_html_lines.append(suggestions_html)

            self.txt_chat.setHtml("".join(report_html_lines))
            full_text = "\n".join(s[0] for s in data.get('source_sentences', []))
            self.txt_full_note.setPlainText(full_text)

        except Exception as e:
            self.log(f"Failed to render analysis results: {e}")
            logger.exception("Render analysis failed")

    def highlight_text_in_note(self, start: int, end: int):
        try:
            full_text = self.txt_full_note.toPlainText()
            pre_text = html.escape(full_text[:start])
            highlighted_text = html.escape(full_text[start:end])
            post_text = html.escape(full_text[end:])
            highlight_color = "yellow"
            text_color = "black"
            full_text_html = (f"<pre>{pre_text}"
                              f"<span style='background-color: {highlight_color}; color: {text_color};'>{highlighted_text}</span>"
                              f"{post_text}</pre>")
            self.txt_full_note.setHtml(full_text_html)
            cursor = self.txt_full_note.textCursor()
            cursor.setPosition(start)
            self.txt_full_note.setTextCursor(cursor)
            self.txt_full_note.ensureCursorVisible()
        except Exception as e:
             self.log(f"Failed to highlight text: {e}")

    def handle_anchor_clicked(self, url):
        url_str = url.toString()
        if url_str.startswith("highlight:"):
            parts = url_str.split(':')
            if len(parts) == 3:
                try:
                    start = int(parts[1])
                    end = int(parts[2])
                    self.highlight_text_in_note(start, end)
                except (ValueError, IndexError) as e:
                    self.log(f"Invalid highlight URL: {url_str} - {e}")
        elif url_str.startswith("review:"):
            parts = url_str.split(':')
            if len(parts) == 3:
                try:
                    issue_id = int(parts[1])
                    feedback = parts[2]
                    issue_to_review = None
                    if self.current_report_data and self.current_report_data.get('issues'):
                        for issue in self.current_report_data['issues']:
                            if issue.get('id') == issue_id:
                                issue_to_review = issue
                                break
                    if issue_to_review:
                        citation_text = ""
                        if issue_to_review.get('citations'):
                            raw_citation_html = issue_to_review['citations'][0][0]
                            citation_text = re.sub('<[^<]+?>', '', raw_citation_html)
                        model_prediction = issue_to_review.get('severity', 'unknown')
                        self.save_finding_feedback(issue_id, feedback, citation_text, model_prediction)
                    else:
                        self.log(f"Could not find issue with ID {issue_id} to save feedback.")
                except (ValueError, IndexError) as e:
                    self.log(f"Invalid review URL: {url_str} - {e}")
                        model_prediction = issue_to_review.get('severity', 'unknown')
                        self.save_finding_feedback(issue_id, feedback, citation_text, model_prediction)
                    else:
                        self.log(f"Could not find issue with ID {issue_id} to save feedback.")
                        QMessageBox.warning(self, "Feedback", f"Could not find issue with ID {issue_id} in the current report.")

                except (ValueError, IndexError) as e:
                    self.log(f"Invalid review URL: {url_str} - {e}")
        elif url_str.startswith("ask:"):
            try:
elif url_str.startswith("educate:"):
            try:
                issue_title = unquote(url_str[8:])
                self._display_educational_content(issue_title)
            except Exception as e:
                self.log(f"Failed to handle educate link: {url_str} - {e}")
        elif url_str.startswith("annotate:"):
            try:
                issue_id = int(url_str.split(':')[1])
                self._prompt_for_annotation(issue_id)
            except (ValueError, IndexError) as e:
                self.log(f"Invalid annotate URL: {url_str} - {e}")

    def _prompt_for_annotation(self, issue_id: int):
        """Opens a dialog to add/edit a note for a given issue."""
        dialog = AnnotationDialog(self)
        if dialog.exec():
            note = dialog.get_note()
            if note:
                self._save_annotation(issue_id, note)

    def _save_annotation(self, issue_id: int, note: str):
        """Saves an annotation to the database."""
        try:
            with _get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO annotations (analysis_issue_id, note, created_at) VALUES (?, ?, ?)",
                    (issue_id, note, _now_iso())
                )
                conn.commit()
            self.log(f"Saved note for issue {issue_id}.")
            QMessageBox.information(self, "Note Saved", "Your note has been saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save annotation for issue {issue_id}: {e}")
            self.set_error(f"Failed to save note: {e}")

    def _display_educational_content(self, issue_title: str):
        """Generates educational content and appends it to the main view."""
        if not self.local_rag or not self.local_rag.is_ready():
            QMessageBox.warning(self, "AI Not Ready", "The AI model is not available. Please wait for it to load or check the logs for errors.")
            return

        rule = next((r for r in self.compliance_rules if r.issue_title == issue_title), None)
        issue = next((i for i in self.current_report_data.get('issues', []) if i.get('title') == issue_title), None)

        if not rule or not issue:
            QMessageBox.critical(self, "Error", "Could not find the details for this issue.")
            return

        user_text_html = issue.get('citations', [("No citation found.", "")])[0][0]
        user_text = re.sub('<[^<]+?>', '', user_text_html)

        prompt = (
            "You are an expert on clinical documentation compliance. Your task is to create a personalized educational "
            "example based on a compliance rule and a user's text that violated that rule.\n\n"
            f"THE RULE:\nTitle: {rule.issue_title}\n"
            f"Explanation: {rule.issue_detail}\n\n"
            f"THE USER'S TEXT (which was flagged):\n\"{user_text}\"\n\n"
            "YOUR TASK:\n"
            "Create a clear, educational response with exactly two sections. Use the following format:\n"
            "1. **A Good Example:** Provide a textbook-perfect example of a note that correctly follows this rule.\n"
            "2. **Corrected Version:** Rewrite the user's original text to be compliant. Change only what is necessary to fix the error.\n"
        )

        try:
            self.statusBar().showMessage("AI is generating educational content...")
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            education_text = self.local_rag.query(prompt)
            self.chat_history.append(('education', (issue_title, education_text)))
            self._render_chat_history()
        except Exception as e:
            self.set_error(f"An error occurred while generating educational content: {e}")
            QMessageBox.warning(self, "AI Error", f"An error occurred: {e}")
        finally:
            self.statusBar().showMessage("Ready")
            QApplication.restoreOverrideCursor()

    def save_finding_feedback(self, issue_id: int, feedback: str, citation_text: str, model_prediction: str):
        try:
            with _get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO reviewed_findings (analysis_issue_id, user_feedback, reviewed_at, citation_text, model_prediction)
                    VALUES (?, ?, ?, ?, ?)
                """, (issue_id, feedback, _now_iso(), citation_text, model_prediction))
                conn.commit()
            self.log(f"Saved feedback for finding {issue_id}: {feedback}")
            self.statusBar().showMessage(f"Feedback '{feedback}' saved for finding {issue_id}.", 3000)
        except Exception as e:
            self.set_error(f"Failed to save feedback: {e}")

    def refresh_llm_indicator(self):
        """Updates the status bar indicators for AI services."""
        try:
            if get_bool_setting("enable_ner_ensemble", True):
                if self.ner_service and self.ner_service.is_ready():
                    self.lbl_ner_status.setText(" NER: Ready ")
                    self.lbl_ner_status.setStyleSheet("background:#10b981; color:#111; padding:3px 8px; border-radius:12px;")
                else:
                    self.lbl_ner_status.setText(" NER: Loading... ")
                    self.lbl_ner_status.setStyleSheet("background:#6b7280; color:#fff; padding:3px 8px; border-radius:12px;")
            else:
                self.lbl_ner_status.setText(" NER: Disabled ")
                self.lbl_ner_status.setStyleSheet("background:#ef4444; color:#fff; padding:3px 8px; border-radius:12px;")
        except Exception as e:
            self.log(f"Failed to refresh NER status: {e}")

    def action_export_fhir(self):
        # ... (Implementation of action_export_fhir) ...

    def action_send(self):
        question = self.input_query_te.toPlainText().strip()
        if not question:
            return
        if not self.local_rag or not self.local_rag.is_ready() or not getattr(self.local_rag, "index", None):
            QMessageBox.warning(self, "AI Not Ready", "Please analyze a document before starting the chat.")
            return

        try:
            self.statusBar().showMessage("AI is thinking...")
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

            # This is a placeholder for a more advanced query router
            # For now, we assume all queries are about the document.
            context_chunks_with_sources = self.local_rag.search_index(question, k=3)

            if not context_chunks_with_sources:
                answer = "I could not find any relevant information in the current document to answer your question."
                sources = []
            else:
                answer, sources = self.local_rag.query(question, context_chunks=context_chunks_with_sources, chat_history=self.chat_history)

            self.chat_history.append(("user", question, []))
            self.chat_history.append(("ai", answer, sources))
            self._render_chat_history()
            self.input_query_te.setPlainText("")

        except Exception as e:
            self.set_error(f"An error occurred while querying the AI: {e}")
            QMessageBox.warning(self, "AI Error", f"An error occurred: {e}")
        finally:
            self.statusBar().showMessage("Ready")
            QApplication.restoreOverrideCursor()

    def action_reset_chat(self):
        """Clears the chat history and resets the chat view to the base report."""
        if not self.chat_history: return
        reply = QMessageBox.question(self, "Reset Chat", "Are you sure you want to clear the current conversation?")
        if str(reply).lower().endswith("yes"):
            self.chat_history = []
            self.log("Chat history has been manually reset.")
            if self.current_report_data:
                self._render_chat_history()
            else:
                self.txt_chat.clear()
            self.statusBar().showMessage("Chat Reset", 3000)
    
    # ... (Keep all other methods like _render_chat_history, action_export_feedback, _update_analytics_tab, etc.) ...
        finally:
            QApplication.restoreOverrideCursor()

# --- Settings dialog ---
def _show_settings_dialog(parent=None) -> None:
    try:
        _ = QDialog
    except Exception:
        return
    dlg = QDialog(parent)
    dlg.setWindowTitle("Settings")
    vbox = QVBoxLayout(dlg)
    vbox.setContentsMargins(12, 12, 12, 12)
    vbox.setSpacing(10)

    # General Settings
    row_flags = QHBoxLayout()
    chk_cache = QCheckBox("Enable analysis cache")
    chk_cache.setChecked(get_bool_setting("allow_cache", True))
    row_flags.addWidget(chk_cache)
    vbox.addLayout(row_flags)

    # UI Theme
    row_theme = QHBoxLayout()
    row_theme.addWidget(QLabel("UI Theme:"))
    cmb_theme = QComboBox()
    cmb_theme.addItems(["dark", "light"])
    cmb_theme.setCurrentText(get_str_setting("ui_theme", "dark"))
    row_theme.addWidget(cmb_theme)
    vbox.addLayout(row_theme)

    # ... other settings widgets like dedup, reports size, etc. ...

    # PDF Chart Settings
    row_pdf = QHBoxLayout()
    chk_pdf_chart = QCheckBox("Show mini chart in PDF")
    chk_pdf_chart.setChecked(get_bool_setting("pdf_chart_enabled", True))
    row_pdf.addWidget(chk_pdf_chart)
    # ... other PDF settings ...
    vbox.addLayout(row_pdf)

    # Save/Cancel Buttons
    row_btn = QHBoxLayout()
    btn_ok = QPushButton("Save")
    btn_cancel = QPushButton("Cancel")
    # ... button styling ...
    row_btn.addStretch(1)
    row_btn.addWidget(btn_ok)
    row_btn.addWidget(btn_cancel)
    vbox.addLayout(row_btn)

    def on_save():
        set_bool_setting("allow_cache", chk_cache.isChecked())
        set_str_setting("ui_theme", cmb_theme.currentText().strip().lower())
        # ... save other settings ...
        dlg.accept()

    try:
        btn_ok.clicked.connect(on_save)
        btn_cancel.clicked.connect(dlg.reject)
    except Exception:
        ...
    dlg.exec()


def _run_gui() -> Optional[int]:
    try:
        _ = QApplication
    except Exception as e:
        logger.warning(f"PyQt6 not available for GUI: {e}")
        print("PyQt6 is not installed. Please install PyQt6 to run the GUI.")
        return 0

    # --- Trial Period Check ---
    from datetime import date, timedelta

    app = QApplication.instance() or QApplication(sys.argv)
    trial_duration_days = get_int_setting("trial_duration_days", 30)
    if trial_duration_days > 0:
        first_run_str = get_setting("first_run_date")
        if not first_run_str:
            first_run_date = date.today()
            set_setting("first_run_date", first_run_date.isoformat())
        else:
            try:
                first_run_date = date.fromisoformat(first_run_str)
            except (ValueError, TypeError):
                first_run_date = date.today()
                set_setting("first_run_date", first_run_date.isoformat())
        
        expiration_date = first_run_date + timedelta(days=trial_duration_days)

        if date.today() > expiration_date:
            QMessageBox.critical(None, "Trial Expired",
                                 f"Your trial period of {trial_duration_days} days has expired.\n"
                                 "Please contact the administrator to continue using the application.")
            return 0 # Exit cleanly

    def _read_stylesheet(filename: str) -> str:
        """Reads a stylesheet from the src/ directory."""
        try:
            path = os.path.join(BASE_DIR, filename)
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Could not load stylesheet {filename}: {e}")
            return ""

    def apply_theme(app: QApplication):
        theme = (get_str_setting("ui_theme", "dark") or "dark").lower()
        stylesheet = ""
        if theme == "light":
            stylesheet = _read_stylesheet("light_theme.qss")
        else:
            stylesheet = _read_stylesheet("dark_theme.qss")

        if stylesheet:
            app.setStyleSheet(stylesheet)
        else:
            # Fallback to original hardcoded styles if files are missing
            if theme == "light":
                app.setStyleSheet("""
                    QMainWindow { background: #f3f4f6; color: #111827; }
                    /* ... other light theme styles ... */
                """)
            else:
                app.setStyleSheet("""
                    QMainWindow { background: #1f2937; color: #e5e7eb; }
                    /* ... other dark theme styles ... */
                """)

        f = QFont()
        f.setPointSize(14)
        app.setFont(f)

    apply_theme(app)
    win = MainWindow()
    try:
        win.resize(1100, 780)
        act_folder = QAction("Open Folder", win)
        act_folder.setShortcut("Ctrl+Shift+O")
        act_folder.triggered.connect(win.action_open_folder)  # type: ignore[attr-defined]
        win.addAction(act_folder)

        act_open = QAction("Open File", win)
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(win.action_open_report)  # type: ignore[attr-defined]
        win.addAction(act_open)

        act_prev = QAction("Preview/Edit (Rubric)", win)
        act_prev.setShortcut("Ctrl+Shift+V")
        act_prev.triggered.connect(win.action_upload_rubric)  # type: ignore[attr-defined]
        win.addAction(act_prev)

        act_batch = QAction("Analyze Batch", win)
        act_batch.setShortcut("Ctrl+B")
        act_batch.triggered.connect(win.action_analyze_batch)  # type: ignore[attr-defined]
        win.addAction(act_batch)

        act_batchc = QAction("Cancel Batch", win)
        act_batchc.setShortcut("Ctrl+Shift+B")
        act_batchc.triggered.connect(win.action_cancel_batch)  # type: ignore[attr-defined]
        win.addAction(act_batchc)
    except Exception:
        ...
    win.show()
    try:
        return app.exec()
    except Exception:
        return 0


if __name__ == "__main__":
    try:
        code = _run_gui()
        sys.exit(code if code is not None else 0)
    except Exception:
        logger.exception("GUI failed")
        sys.exit(1)
