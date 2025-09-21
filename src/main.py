import argparse
import os
import yaml
from src.ingestion import build_sentence_window_index
from src.retrieval import get_query_engine
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
def load_config(config_path="config.yaml"):
    """Loads the YAML configuration file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)
def handle_ingest(args, config):
    """Handles the 'ingest' command."""
    docs_path = args.dir or config["paths"]["docs_dir"]
    if not os.path.exists(docs_path):
        print(f"Error: Document directory not found at '{docs_path}'")
        os.makedirs(docs_path)
        print(f"Created a dummy directory at '{docs_path}'. Please add your documents there and run ingest again.")
        return
    print(f"Starting ingestion from directory: {docs_path}")
    # Set up models from config
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "YOUR_API_KEY_HERE")
    llm = OpenAI(model=config["models"]["llm"]["model_name"])
    embed_model = HuggingFaceEmbedding(model_name=config["models"]["embed_model"]["model_name"])
    build_sentence_window_index(
        documents_path=docs_path,
        llm=llm,
        embed_model=embed_model,
        save_dir=config["paths"]["index_dir"],
    )
    print("Ingestion complete.")
def handle_query(args, config):
    """Handles the 'query' command."""
    if not args.question:
        print("Error: Please provide a question with the --question flag.")
        return
    print(f"Querying with: '{args.question}'")
    try:
        # Set up models from config for retrieval
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "YOUR_API_KEY_HERE")
        llm = OpenAI(model=config["models"]["llm"]["model_name"])
        query_engine = get_query_engine(
            index_dir=config["paths"]["index_dir"],
            llm=llm,
            embed_model_name=config["models"]["embed_model"]["model_name"],
            reranker_config=config["models"]["reranker"],
            retrieval_config=config["retrieval"],
        )
        streaming_response = query_engine.query(args.question)
        print("\n--- Response ---")
        for token in streaming_response.response_gen:
            print(token, end="", flush=True)
        print("\n---")
    except FileNotFoundError as e:
        print(f"Error: {e}. Please run the 'ingest' command first.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
def main():
    """Main function to run the command-line interface."""
    parser = argparse.ArgumentParser(description="A command-line interface for a RAG pipeline.")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to the configuration file.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # Load configuration to get default values
    # This is a bit of a trick to show defaults in help messages
    try:
        config = load_config()
    except FileNotFoundError:
        config = {"paths": {"docs_dir": "data"}} # default fallback

    # Subparser for the 'ingest' command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents from a directory into the vector store.")
    ingest_parser.add_argument(
        "--dir",
        type=str,
        default=config["paths"]["docs_dir"],
        help=f"The directory containing documents to ingest. Defaults to '{config['paths']['docs_dir']}'."
    )
    ingest_parser.set_defaults(func=handle_ingest)

    # Subparser for the 'query' command
    query_parser = subparsers.add_parser("query", help="Ask a question to the indexed documents.")
    query_parser.add_argument("--question", type=str, required=True, help="The question you want to ask.")
    query_parser.set_defaults(func=handle_query)

    args = parser.parse_args()

    # Load the config specified by the user, or the default
    final_config = load_config(args.config)

    # Call the appropriate handler with the args and config
    args.func(args, final_config)

if __name__ == "__main__":
    main()

# --- Configuration defaults and constants ---
REPORT_TEMPLATE_VERSION = "v2.0"

# Paths and environment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_default_db_dir = os.path.join(
    os.path.expanduser("~"), "Documents", "SpecKitData"
)
DATABASE_PATH = os.getenv(
    "SPEC_KIT_DB", os.path.join(_default_db_dir, "spec_kit.db")
)
REPORTS_DIR = os.getenv(
    "SPEC_KIT_REPORTS",
    os.path.join(os.path.expanduser("~"), "Documents", "SpecKitReports"),
)
LOGS_DIR = os.path.join(
    os.path.expanduser("~"), "Documents", "SpecKitData", "logs"
)

# PDF report defaults
REPORT_FONT_FAMILY = "DejaVu Sans"
REPORT_FONT_SIZE = 8.5

REPORT_STYLESHEET = """
    body {
        font-family: DejaVu Sans, Arial, sans-serif;
        font-size: 10pt;
        line-height: 1.4;
    }
    h1 { font-size: 18pt; color: #1f4fd1; margin-bottom: 20px; }
    h2 {
        font-size: 14pt;
        color: #111827;
        border-bottom: 1px solid #ccc;
        padding-bottom: 5px;
        margin-top: 25px;
    }
    h3 { font-size: 12pt; color: #374151; margin-top: 20px; }
    .user-message { margin-top: 15px; }
    .ai-message {
        margin-top: 5px;
        padding: 8px;
        background-color: #f3f4f6;
        border-radius: 8px;
    }
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
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
os.makedirs(LOGS_DIR, exist_ok=True)
log_path = os.path.join(LOGS_DIR, "app.log")
from logging.handlers import RotatingFileHandler

fh = RotatingFileHandler(
    log_path, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
)
fh.setLevel(logging.INFO)
fh.setFormatter(
    logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
)
logging.getLogger().addHandler(fh)
logger.info(f"File logging to: {log_path}")
except Exception as _e:
logger.warning(f"Failed to set up file logging: {_e}")

# spaCy disabled placeholder
nlp = None

# --- Third-party imports (guarded) ---
try:
    import pdfplumber
except Exception as e:
    pdfplumber = None
    logger.warning(f"pdfplumber unavailable: {e}")

try:
    import pytesseract
except Exception as e:
    pytesseract = None
    logger.warning(f"pytesseract unavailable: {e}")

try:
    from transformers import pipeline
except ImportError:
    pipeline = None
    logger.warning(
        "transformers library not found. BioBERT NER will be disabled."
    )

try:
    from PIL import Image, UnidentifiedImageError
except ImportError as e:
    Image = None  # type: ignore


    class UnidentifiedImageError(Exception):
        pass


    logger.warning(f"PIL unavailable: {e}")

try:
    import numpy as np
except ImportError:
    np = None
    logger.warning(
        "Numpy unavailable. Some analytics features will be disabled."
    )

try:
    import shap
except ImportError:
    shap = None
    logger.warning(
        "shap unavailable. Some analytics features will be disabled."
    )

try:
    import slicer
except ImportError:
    slicer = None
    logger.warning(
        "slicer unavailable. Some analytics features will be disabled."
    )

try:
    import jsonschema
except ImportError:
    jsonschema = None
    logger.warning(
        "jsonschema unavailable. Report validation will be disabled."
    )

# --- FHIR Imports (guarded) ---
try:
    from fhir.resources.bundle import Bundle
    from fhir.resources.documentreference import DocumentReference
    from fhir.resources.diagnosticreport import DiagnosticReport
    from fhir.resources.observation import Observation
    from fhir.resources.codeableconcept import CodeableConcept
    from fhir.resources.coding import Coding
    from fhir.resources.reference import Reference
    from fhir.resources.meta import Meta
except ImportError:
    class Bundle:
        pass


    class DocumentReference:
        pass


    class DiagnosticReport:
        pass


    class Observation:
        pass


    class CodeableConcept:
        pass


    class Coding:
        pass


    class Reference:
        pass


    class Meta:
        pass


    logger.warning("fhir.resources library not found. FHIR export will be disabled.")

# Matplotlib for analytics chart
import matplotlib

matplotlib.use('Agg')
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
except ImportError:
    class FigureCanvas:  # type: ignore
        def __init__(self, figure=None): pass

        def mpl_connect(self, s, f): pass

        def draw(self): pass
from matplotlib.figure import Figure

# PyQt (guarded)
try:
    from PyQt6.QtWidgets import (
        QMainWindow, QToolBar, QLabel, QFileDialog, QMessageBox, QApplication,
        QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QPushButton,
        QSpinBox, QCheckBox, QTextEdit, QSplitter, QGroupBox, QListWidget, QWidget,
        QProgressDialog, QSizePolicy, QStatusBar, QProgressBar, QMenu, QTabWidget, QGridLayout,
        QDateEdit
    )
    from PyQt6.QtGui import QAction, QFont, QTextDocument, QPdfWriter
    from PyQt6.QtCore import Qt, QThread, pyqtSignal as Signal, QObject, QDate
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
    class QDate:
        @staticmethod
        def currentDate(): return QDate()
        def addMonths(self, *_, **__): return QDate()
        def addDays(self, *_, **__): return QDate()
        def toString(self, *_, **__): return ""
    class QDateEdit:
        def __init__(self, *_, **__): ...
        def setDate(self, *_, **__): ...
        def setCalendarPopup(self, *_, **__): ...
        def date(self): return QDate()
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
    class Qt: ...
    class QThread: ...
from matplotlib.patches import Rectangle
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

# Fairlearn for bias auditing
try:
    from fairlearn.metrics import MetricFrame, demographic_parity_difference, selection_rate
except ImportError:
    MetricFrame = None
    demographic_parity_difference = None
    selection_rate = None
    logger.warning("fairlearn library not found. Bias auditing will be disabled.")

# Local imports
try:
    from .local_llm import LocalRAG
    from .rubric_service import RubricService, ComplianceRule
    from .guideline_service import GuidelineService
    from .text_chunking import RecursiveCharacterTextSplitter, SemanticTextSplitter
    from .nlg_service import NLGService
    from .bias_audit_service import run_bias_audit
    from .jsl_ner_service import JSLNERService
    from .entity_consolidation_service import EntityConsolidationService, NEREntity
    from .ner_service import NERService
    from .entity_consolidation_service import EntityConsolidationService
    from .text_chunking import RecursiveCharacterTextSplitter

except ImportError as e:
    logger.error(f"Failed to import local modules: {e}. Ensure you're running as a package.")
    # Define dummy classes if imports fail, to prevent crashing on startup
    class LocalRAG: pass
    class RubricService: pass
    class ComplianceRule: pass
    class GuidelineService: pass
    class RecursiveCharacterTextSplitter: pass
    class SemanticTextSplitter: pass
    class NLGService: pass
    def run_bias_audit(): return {"error": "Bias audit service not loaded."}
    class JSLNERService: pass
    class EntityConsolidationService: pass
    class NEREntity: pass


    # Define dummy classes if imports fail
    class LocalRAG:
        pass


    class RubricService:
        pass


    class ComplianceRule:
        pass


    class GuidelineService:
        pass


    class NERService:
        pass


    class EntityConsolidationService:
        pass


    class RecursiveCharacterTextSplitter:
        pass


# --- LLM Loader Worker ---
class LLMWorker(QObject):
    """A worker class to load the LocalRAG model in a separate thread."""
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


# --- Guideline Loader Worker ---
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
class ParseError(Exception):
    ...


class OCRFailure(Exception):
    ...


class ReportExportError(Exception):
    ...


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


def _validate_report_data(data: dict, schema: dict) -> bool:
    """Validates report data against the JSON schema."""
    if not jsonschema:
        return True  # Skip if library is unavailable
    try:
        jsonschema.validate(instance=data, schema=schema)
        logger.info("Report data passed schema validation.")
        return True
    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"Report data failed schema validation: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during schema validation: {e}")
        return False


def _hash_password(
        password: str, salt: Optional[bytes] = None) -> Tuple[str, bytes]:
    """Hashes a password with a salt. Generates a new salt if not provided."""
    if salt is None:
        salt = os.urandom(16)
    hashed_password = hashlib.pbkdf2_hmac(
        'sha256', password.encode('utf-8'), salt, 100000
    )
    return hashed_password.hex(), salt


def _verify_password(
        stored_password_hex: str, salt_hex: str, provided_password: str
) -> bool:
    """Verifies a provided password against a stored hash and salt."""
    try:
        salt = bytes.fromhex(salt_hex)
    except (ValueError, TypeError):
        return False
    hashed_password, _ = _hash_password(provided_password, salt)
    return hashed_password == stored_password_hex


# --- Parsing (PDF/DOCX/CSV/XLSX/Images with optional OCR) ---
def split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    if not text:
        return []
    sents = [
        p.strip()
        for p in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text)
        if p.strip()
    ]
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
                return [(f"Error: Failed to read tabular file: {e}",
                         "Data Parser")]
        elif ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"]:
            if not Image or not pytesseract:
                return [("Error: OCR dependencies not available.",
                         "OCR Parser")]
            try:
                img = Image.open(file_path)
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                txt = pytesseract.image_to_string(
                    img, lang=get_str_setting("ocr_lang", "eng")
                )
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

        return chunks_with_source if chunks_with_source else [
            ("Info: No text could be extracted from the document.", "System")]

    except FileNotFoundError:
        return [(f"Error: File not found at {file_path}", "File System")]
    except Exception as e:
        logger.exception("parse_document_content failed")
        return [(f"Error: An unexpected error occurred: {e}", "System")]


def run_biobert_ner(sentences: List[str]) -> List[dict]:
    """
    Performs Named Entity Recognition on a list of sentences using a
    BioBERT model.
    """
    if not pipeline:
        logger.warning(
            "Transformers pipeline is not available. Skipping BioBERT NER."
        )
        return []

    try:
        # Using a pipeline for NER
        # The 'simple' aggregation strategy groups subword tokens into whole
        # words.
        ner_pipeline = pipeline(
            "ner",
            model="longluu/Clinical-NER-MedMentions-GatorTronBase",
            aggregation_strategy="simple"
        )
        results = ner_pipeline(sentences)
        return results
    except Exception as e:
        logger.error(f"BioBERT NER failed: {e}")
        return []


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


try:
    import shap
    import slicer
except ImportError:
    shap = None
    slicer = None
    logger.warning("SHAP or Slicer unavailable. Advanced analytics will be disabled.")


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
                        TEXT
                    )
                    """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_runs_time ON analysis_runs(run_time)")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_runs_file ON analysis_runs(file_name)")
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

        # --- Simple schema migration for new columns ---
        cur.execute("PRAGMA table_info(analysis_runs)")
        columns = [row[1] for row in cur.fetchall()]
        if "compliance_score" not in columns:
            cur.execute("ALTER TABLE analysis_runs ADD COLUMN compliance_score REAL")
            logger.info("Upgraded analysis_runs table to include 'compliance_score' column.")
        if "file_path" not in columns:
            cur.execute("ALTER TABLE analysis_runs ADD COLUMN file_path TEXT")
            logger.info("Upgraded analysis_runs table to include 'file_path' column.")
        if "disciplines" not in columns:
            cur.execute("ALTER TABLE analysis_runs ADD COLUMN disciplines TEXT")
            logger.info("Upgraded analysis_runs table to include 'disciplines' column.")

def parse_document_content(file_path: str) -> List[Tuple[str, str]]:
"""


Parses
the
content
of
a
document and splits
it
into
chunks.
Uses
a
recursive
character
text
splitter
for more effective chunking.
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

    # --- Step 1: Extract text from the document based on its type ---
    if ext == ".pdf":
        if not pdfplumber:
            return [("Error: pdfplumber not available.", "PDF Parser")]
        with pdfplumber.open(file_path) as pdf:
            # Process page by page to maintain source information
            for i, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                page_chunks = text_splitter.split_text(page_text)
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
            para_chunks = text_splitter.split_text(para.text)
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
            return [(f"Error: Failed to read tabular file: {e}",
                     "Data Parser")]
    elif ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"]:
        if not Image or not pytesseract:
            return [("Error: OCR dependencies not available.",
                     "OCR Parser")]
        try:
            img = Image.open(file_path)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            txt = pytesseract.image_to_string(
                img, lang=get_str_setting("ocr_lang", "eng")
            )
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
        try:
            if ext in [".xlsx", ".xls"]:
                df = pd.read_excel(file_path)
                if isinstance(df, dict):
                    df = next(iter(df.values()))
            else:
                df = pd.read_csv(file_path)
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
] main
    cur.execute("""
CREATE
TABLE
IF
NOT
EXISTS
reviewed_findings
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
)
REFERENCES
analysis_issues
    (
    id
)
ON
DELETE
CASCADE
)
""")
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
                         compliance: dict, mode: str, disciplines: List[str]) -> Optional[int]:
    try:
        import json
        with _get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                        INSERT INTO analysis_runs (file_name, file_path, run_time, pages_est, flags, findings, suggestions, notes,
                                                   sentences_final, dedup_removed, compliance_score, mode, disciplines)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            os.path.basename(file_path), file_path, run_time,
                            int(metrics.get("pages", 0)), int(metrics.get("flags", 0)), int(metrics.get("findings", 0)),
                            int(metrics.get("suggestions", 0)), int(metrics.get("notes", 0)),
                            int(metrics.get("sentences_final", 0)), int(metrics.get("dedup_removed", 0)),
                            float(compliance.get("score", 0.0)), mode, json.dumps(disciplines)
                        ))
            run_id = int(cur.lastrowid)
            if issues_scored:
                cur.executemany("""
                                INSERT INTO analysis_issues (run_id, severity, category, title, detail, confidence)
                                VALUES (?, ?, ?, ?, ?, ?)
                                """, [(run_id, it.get("severity", ""), it.get("category", ""), it.get("title", ""),
                                       it.get("detail", ""), float(it.get("confidence", 0.0))) for it in issues_scored])
            conn.commit()
            return run_id
    except Exception as e:
        logger.warning(f"persist_analysis_run failed: {e}")
        return None

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
def _audit_from_rubric(text: str, selected_disciplines: List[str], strict: bool | None = None) -> list[dict]:
"""
Performs
a
dynamic
audit
based
on
the
selected
discipline
rubrics.
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

issues = []
t_lower = text.lower()

unique_rules = []
seen_titles = set()
for rule in all_rules:
    if rule.issue_title not in seen_titles:
        unique_rules.append(rule)
        seen_titles.add(rule.issue_title)

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
        severity = rule.strict_severity if strict else rule.severity
        issues.append({
            "severity": severity,
            "title": rule.issue_title,
            "detail": rule.issue_detail,
            "category": rule.issue_category,
            "trigger_keywords": rule.positive_keywords,
            "discipline": rule.discipline
        })

return issues
def add_rubric_from_library(self):
    lib_dialog = LibrarySelectionDialog(self)
    if not lib_dialog.exec():
        return
    rubric_name = lib_dialog.selected_name
    rubric_path = lib_dialog.selected_path
    content = parse_document_content(rubric_path)
    if content[0][0].startswith("Error:"):
        QMessageBox.critical(self, "Error", f"Failed to parse library rubric:\n{content[0][0]}")
        return
    content_str = "\n".join([text for text, source in content])
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO rubrics (name, content) VALUES(?, ?)", (rubric_name, content_str))
            conn.commit()
            QMessageBox.information(self, "Success", f"Rubric '{rubric_name}' added from library.")
            self.load_rubrics()
    except sqlite3.IntegrityError:
        QMessageBox.warning(self, "Already Exists", f"The library rubric '{rubric_name}' is already in your database.")
    except sqlite3.Error as e:
        QMessageBox.critical(self, "Database Error", f"Failed to save rubric to database:\n{e}")

def remove_rubric(self):
    selected_items = self.rubric_list.selectedItems()
    if not selected_items:
        QMessageBox.warning(self, "Remove Rubric", "Please select a rubric to remove.")
        return
    item = selected_items[0]
    rubric_id = item.data(Qt.ItemDataRole.UserRole)
    rubric_name = item.text()
    reply = QMessageBox.question(self, "Confirm Deletion", f"Are you sure you want to permanently delete the rubric '{rubric_name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
    if reply == QMessageBox.StandardButton.Yes:
        try:
def _audit_from_rubric(text: str, selected_disciplines: List[str],
                   strict: bool | None = None) -> list[dict]:
    """
Performs
a
dynamic
audit
based
on
the
selected
discipline
rubrics.
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
            # Case 1: Positive keyword found AND negative keyword NOT found.
            if rule.positive_keywords and rule.negative_keywords:
                if (any(kw in t_lower for kw in positive_kws) and
                        not any(kw in t_lower for kw in negative_kws)):
                    triggered = True
            # Case 2: Positive keyword found (no negative keywords).
            elif rule.positive_keywords and not rule.negative_keywords:
                if any(kw in t_lower for kw in positive_kws):
                    triggered = True
            # Case 3: Negative keyword NOT found (no positive keywords).
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
                    "discipline": rule.discipline, # Added discipline for context in UI/analytics
                })

        # General auditor note (can be kept outside the rubric for consistency)
        issues.append({
            "severity": "auditor_note",
            "title": "General Auditor Checks",
            "detail": "Review compliance with Medicare Part B (qualified personnel, plan establishment/recert, timings/units, documentation integrity).",
            "category": "General",
            "trigger_keywords": []
        })

        return issues
        sev_counts = {
            "flag": sum(1 for i in issues_scored if i.get("severity") == "flag"),
            "wobbler": sum(1 for i in issues_scored if i.get("severity") == "wobbler"),
            "suggestion": sum(1 for i in issues_scored if i.get("severity") == "suggestion"),
            "auditor_note": sum(1 for i in issues_scored if i.get("severity") == "auditor_note"),
        }
        cat_counts = count_categories(issues_scored)

def _audit_from_rubric(text: str, selected_disciplines: List[str],
                           strict: bool | None = None) -> list[dict]:
        """
Performs
a
dynamic
audit
based
on
the
selected
discipline
rubrics.
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
            # Case 1: Positive keyword found AND negative keyword NOT found.
            if rule.positive_keywords and rule.negative_keywords:
                if (any(kw in t_lower for kw in positive_kws) and
                        not any(kw in t_lower for kw in negative_kws)):
                    triggered = True
            # Case 2: Positive keyword found (no negative keywords).
            elif rule.positive_keywords and not rule.negative_keywords:
                if any(kw in t_lower for kw in positive_kws):
                    triggered = True
            # Case 3: Negative keyword NOT found (no positive keywords).
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
                    "discipline": rule.discipline, # Added discipline for context in UI/analytics
                })

        # General auditor note (can be kept outside the rubric for consistency)
        issues.append({
            "severity": "auditor_note",
            "title": "General Auditor Checks",
            "detail": "Review compliance with Medicare Part B (qualified personnel, plan establishment/recert, timings/units, documentation integrity).",
            "category": "General",
            "trigger_keywords": []
        })

        return issues
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
                CURRENT_REVIEW_MODE = review_mode_override

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

            # This is the merged section
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

            # The rest of the `run_analyzer` function would follow here...
            self.btn_export_view = QPushButton("Export View to PDF")
            self._style_action_button(self.btn_export_view, font_size=11, bold=True, height=28, padding="4px 10px")
            self.btn_export_view.clicked.connect(self.action_export_view_to_pdf)
            row_results_actions.addWidget(self.btn_export_view)

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
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_pdf import PdfPages
            from matplotlib.patches import FancyBboxPatch

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
            font_size = float(get_str_setting("pdf_font_size", REPORT_FONT_SIZE))

            page_w, page_h = REPORT_PAGE_SIZE
            margin_top = float(get_str_setting("pdf_margin_top", "1.1"))
            margin_right = float(get_str_setting("pdf_margin_right", "1.0"))
            margin_bottom = float(get_str_setting("pdf_margin_bottom", "1.3"))
            margin_left = float(get_str_setting("pdf_margin_left", "1.0"))
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

def action_export_view_to_pdf(self):
        """
Exports
the
current
content
of
the
main
chat / analysis
view
to
a
PDF.
"""
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
            # ... The rest of the PDF export logic would go here ...
            self.statusBar().showMessage("PDF exported successfully.")
            QMessageBox.information(self, "Export Successful", f"PDF saved to:\n{save_path}")
        except Exception as e:
            self.set_error(str(e))
            QMessageBox.critical(self, "Export Error", f"Failed to export PDF:\n{e}")
        finally:
            QApplication.restoreOverrideCursor()
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
            CURRENT_REVIEW_MODE = review_mode_override

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

        # This is the merged section
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
        sev_order = {"flag": 0, "finding": 1, "suggestion": 2, "auditor_note": 3}
        issues_scored.sort(key=lambda x: (sev_order.get(str(x.get("severity")), 9),
                                          str(x.get("category", "")),
                                          str(x.get("title", ""))))

        nlg_service = NLGService()
        for issue in issues_scored:
            prompt = f"Generate a brief, actionable tip for a physical therapist to address this finding: {issue.get('title', '')} ({issue.get('severity', '')}) - {issue.get('detail', '')}"
            tip = nlg_service.generate_tip(prompt)
            issue['nlg_tip'] = tip

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
                "good_example": "A note that clearly links interventions to functional goals and documents the patient's progress over time.",
                "bad_example": "A note with jargon, undefined abbreviations, or that simply lists exercises without clinical reasoning."
            }
        }
        for issue in issues_scored:
            issue['details'] = issue_details_map.get(issue.get('title', ''), {})

        if main_window_instance and main_window_instance.guideline_service and main_window_instance.guideline_service.is_index_ready:
            main_window_instance.log("Searching for relevant guidelines for each finding...")
            for issue in issues_scored:
                query = f"{issue.get('title', '')}: {issue.get('detail', '')}"
                guideline_results = main_window_instance.guideline_service.search(query, top_k=2)
                issue['guidelines'] = guideline_results

        pages_est = len({s for _, s in collapsed if s.startswith("Page ")}) or 1

        full_text = "\n".join(t for t, _ in collapsed)
        strengths, weaknesses, missing = [], [], []
        tl = full_text.lower()
        if any(k in tl for k in ("signed", "signature", "dated")):
            strengths.append("Provider authentication (signature/date) appears to be present.")
        else:
            weaknesses.append("Provider authentication (signature/date) unclear or missing.")
            missing.append("Signatures/Dates")

        if "goal" in tl and any(k in tl for k in ("measurable", "time", "timed", "by ")):
            strengths.append("Goals appear to be measurable and time-bound, with baseline/targets.")
        elif "goal" in tl:
            weaknesses.append("Goals present but may not be measurable/time-bound.")
            missing.append("Measurable/Time-bound Goals")

        if any(k in tl for k in ("medical necessity", "reasonable and necessary", "necessity")):
            strengths.append("Medical necessity is explicitly discussed.")
        else:
            weaknesses.append("Medical necessity is not explicitly supported throughout the documentation.")
            missing.append("Medical Necessity")

        if "assistant" in tl and "supervis" in tl:
            strengths.append("Assistant involvement includes supervision context.")
        elif "assistant" in tl:
            weaknesses.append("Assistant activity is present; however, the supervision/oversight context is not clearly documented.")
            missing.append("Assistant Supervision Context")

        if any(k in tl for k in ("plan of care", "poc", "certification", "recert")):
            strengths.append("Plan/certification is referenced in the record.")
        else:
            weaknesses.append("Plan/certification is not clearly referenced with dates and signatures.")
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
            flags = sum(1 for i in issues if i.get("severity") == "flag")
            findings = sum(1 for i in issues if i.get("severity") == "finding")
            sug = sum(1 for i in issues if i.get("severity") == "suggestion")
            base = 100.0
            if mode == "Strict":
                base -= flags * 6.0
                base -= findings * 3.0
                base -= sug * 1.5
                base -= len(missing_in) * 4.0
            else:
                base -= flags * 4.0
                base -= findings * 2.0
                base -= sug * 1.0
                base -= len(missing_in) * 2.5
            base += min(5.0, len(strengths_in) * 0.5)
            score = max(0.0, min(100.0, base))
            breakdown = f"Flags={flags}, Findings={findings}, Suggestions={sug}, Missing={len(missing_in)}, Strengths={len(strengths_in)}; Mode={mode}"
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
            tips.append("Resolve flags first (signatures/dates, plan/certification), then clarify gray areas.")
        if "Medical Necessity" in missing:
            tips.append("Tie each skilled intervention to functional limitations and expected outcomes.")
        if "Measurable/Time-bound Goals" in missing:
            tips.append("Rewrite goals to include baselines, specific targets, and timelines.")
        if not strengths:
            tips.append("Increase specificity with objective measures and clear clinical reasoning.")

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
                    "good_example": "A note that provides a clear picture of the patient's journey from evaluation to discharge.",
                    "bad_example": "A note with jargon, undefined abbreviations, or that simply lists exercises without clinical reasoning."
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
                        narrative_lines.append(f"    - [{src}] \"{q}\"")
                narrative_lines.append("")
        else:
            narrative_lines.append("No specific audit findings were identified.")

        narrative_lines.append("")
        narrative_lines.append("--- General Recommendations ---")
        narrative_lines.append(" • Consistency is key. Ensure all notes follow a standard format.")
        narrative_lines.append(" • Be specific and objective. Use numbers and standardized tests to measure progress.")
        narrative_lines.append(" • Always link treatment to function. Explain how the therapy helps the patient achieve their functional goals.")
        narrative_lines.append(" • Tell a story. The documentation should paint a clear picture of the patient's journey from evaluation to discharge.")
        narrative_lines.append("")

        # --- Generate and add suggested questions ---
        suggested_questions = _generate_suggested_questions(issues_scored)
        if suggested_questions:
            narrative_lines.append("--- Suggested Questions for Follow-up ---")
            for q in suggested_questions:
                narrative_lines.append(f" • {q}")
            narrative_lines.append("")
        # --- End suggested questions ---

        narrative_lines.append("--- Trends & Analytics (Last 10 Runs) ---")
        if trends.get("recent_scores"):
            sc = trends["recent_scores"]
            narrative_lines.append(f" • Recent scores (oldest→newest): {', '.join(str(round(s, 1)) for s in sc)}")
            narrative_lines.append(
                f" • Score delta: {trends['score_delta']:+.1f} | Average score: {trends['avg_score']:.1f}")
            narrative_lines.append(
                f" • Average Flags: {trends['avg_flags']:.2f} | Average Findings: {trends['avg_findings']:.2f} | Average Suggestions: {trends['avg_suggestions']:.2f}")
        else:
            narrative_lines.append(" • Not enough history to compute trends yet.")
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
            persist_analysis_run(file_path, _now_iso(), metrics, issues_scored, compliance, CURRENT_REVIEW_MODE, selected_disciplines)
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
                "clinical_ner_enabled": get_bool_setting("enable_biobert_ner", True),
                "ner_results": ner_results,
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
        result_info["formatted_entities"] = formatted_entities
        return result_info
    except KeyboardInterrupt:
        logger.info("Analysis cancelled by user.")
        return result_info
    except Exception:
        logger.exception("Analyzer failed")
        return result_info


class MainWindow(QMainWindow):
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
        self.entity_consolidation_service: EntityConsolidationService = EntityConsolidationService()
        self.chat_history: list[tuple[str, str]] = []
        self.compliance_rules: list[ComplianceRule] = []

        tb = QToolBar("Main")
        try:
            tb.setMovable(False)
        except Exception:
            ...
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)

        act_open = QAction("Open File...", self)
        act_open.triggered.connect(self.action_open_report)  # type: ignore[attr-defined]
        tb.addAction(act_open)

        act_analyze = QAction("Analyze", self)
        act_analyze.triggered.connect(self.action_analyze_combined)  # type: ignore[attr-defined]
        tb.addAction(act_analyze)

        act_logs = QAction("Open Logs Folder", self)
        act_logs.triggered.connect(self.action_open_logs)  # type: ignore[attr-defined]
        tb.addAction(act_logs)

        act_analytics = QAction("Export Analytics CSV", self)
        act_analytics.triggered.connect(lambda: self._export_analytics_csv())  # type: ignore[attr-defined]
        tb.addAction(act_analytics)

        act_settings = QAction("Settings", self)
        act_settings.triggered.connect(
            lambda: (_show_settings_dialog(self), self.reapply_theme()))  # type: ignore[attr-defined]
        tb.addAction(act_settings)

        act_admin_settings = QAction("Admin Settings...", self)
        act_admin_settings.triggered.connect(self._show_admin_settings_dialog)
        tb.addAction(act_admin_settings)

        act_exit = QAction("Exit", self)
        act_exit.triggered.connect(self.close)  # type: ignore[attr-defined]
        tb.addAction(act_exit)

        tb.addSeparator()

        act_export_feedback = QAction("Export Feedback...", self)
        act_export_feedback.triggered.connect(self.action_export_feedback)
        tb.addAction(act_export_feedback)

        act_analyze_performance = QAction("Analyze Performance", self)
        act_analyze_performance.triggered.connect(self.action_analyze_performance)
        tb.addAction(act_analyze_performance)

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

        analytics_controls.addWidget(QLabel("From:"))
        self.analytics_start_date = QDateEdit()
        self.analytics_start_date.setDate(QDate.currentDate().addMonths(-3))
        self.analytics_start_date.setCalendarPopup(True)
        analytics_controls.addWidget(self.analytics_start_date)

        analytics_controls.addWidget(QLabel("To:"))
        self.analytics_end_date = QDateEdit()
        self.analytics_end_date.setDate(QDate.currentDate())
        self.analytics_end_date.setCalendarPopup(True)
        analytics_controls.addWidget(self.analytics_end_date)

        btn_refresh_analytics = QPushButton("Filter & Refresh")
        self._style_action_button(btn_refresh_analytics, font_size=11, bold=True, height=32)
        try:
            btn_refresh_analytics.clicked.connect(self._update_analytics_tab)
        except Exception:
            pass
        analytics_controls.addWidget(btn_refresh_analytics)
        analytics_controls.addStretch(1)

        self.btn_export_data = QPushButton("Export Data (CSV)")
        self.btn_export_chart = QPushButton("Export Chart (PNG)")
        try:
            self.btn_export_data.clicked.connect(self.action_export_analytics_data)
            self.btn_export_chart.clicked.connect(self.action_export_analytics_chart)
        except Exception:
            pass # Headless
        analytics_controls.addWidget(self.btn_export_data)
        analytics_controls.addWidget(self.btn_export_chart)

        analytics_layout.addLayout(analytics_controls)

        # Matplotlib chart
        self.analytics_figure = Figure(figsize=(5, 3))
        self.analytics_canvas = FigureCanvas(self.analytics_figure)
        try:
            self.analytics_canvas.mpl_connect('pick_event', self.on_analytics_pick)
        except Exception:
            pass # For headless environments
        analytics_layout.addWidget(self.analytics_canvas)

        # Drill-down results
        drilldown_group = QGroupBox("Drill-Down: Files with Selected Finding Type")
        drilldown_layout = QVBoxLayout(drilldown_group)
        self.drilldown_list = QListWidget()
        try:
            self.drilldown_list.itemDoubleClicked.connect(self.action_open_drilldown_file)
        except Exception:
            pass
        drilldown_layout.addWidget(self.drilldown_list)
        analytics_layout.addWidget(drilldown_group)

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

        # --- Bias Audit Tab ---
        bias_audit_tab = QWidget()
        self.tabs.addTab(bias_audit_tab, "Bias Audit")
        bias_audit_layout = QVBoxLayout(bias_audit_tab)

        bias_controls_layout = QHBoxLayout()
        self.bias_group_by_combo = QComboBox()
        self.bias_group_by_combo.addItems(["Discipline", "Finding Type"])
        self.btn_run_bias_audit = QPushButton("Run Bias Audit")
        try:
            self.btn_run_bias_audit.clicked.connect(self.action_run_bias_audit)
        except Exception:
            pass # For headless environments

        bias_controls_layout.addWidget(QLabel("Audit Sensitive Feature:"))
        bias_controls_layout.addWidget(self.bias_group_by_combo)
        bias_controls_layout.addWidget(self.btn_run_bias_audit)
        bias_controls_layout.addStretch(1)
        bias_audit_layout.addLayout(bias_controls_layout)

        self.bias_figure = Figure(figsize=(5, 4))
        self.bias_canvas = FigureCanvas(self.bias_figure)
        bias_audit_layout.addWidget(self.bias_canvas)

        self.bias_results_text = QTextEdit()
        self.bias_results_text.setReadOnly(True)
        self.bias_results_text.setPlaceholderText("Bias audit results will be displayed here.")
        bias_audit_layout.addWidget(self.bias_results_text)

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
            self._style_action_button(b, font_size=11, bold=True, height=32, padding="6px 10px")
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

    def action_open_logs(self):
        try:
            _open_path(LOGS_DIR)
        except Exception as e:
            self.set_error(str(e))

    def _progress_start(self, title: str = "Analyzing..."):
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat(title + " (%p%)")
        except Exception:
            ...

    def _progress_update(self, pct: int, msg: str = ""):
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(max(0, min(100, int(pct))))
            if msg:
                self.progress_bar.setFormat(f"{msg} (%p%)")
            QApplication.processEvents()
        except Exception:
            ...

    def _progress_finish(self):
        try:
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("Done")
            QApplication.processEvents()
        except Exception:
            ...

    def _progress_was_canceled(self) -> bool:
        try:
            return bool(self._batch_cancel)
        except Exception:
            return False

    def action_cancel_batch(self):
        try:
            self._batch_cancel = True
            self.btn_cancel_batch.setDisabled(True)
            self.statusBar().showMessage("Cancelling batch...")
        except Exception:
            ...

    def action_analyze(self):
        if not self._current_report_path:
            QMessageBox.information(self, "Analyze", "Please upload or select a report first.")
            return

        self._clear_previous_analysis_state()

        try:
            self.btn_analyze_all.setDisabled(True)
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self.statusBar().showMessage("Analyzing...")

            self._progress_start("Analyzing...")

            def _cb(p, m):
                self._progress_update(p, m)

            def _cancel():
                return self._progress_was_canceled()

            selected_disciplines = []
            if self.chk_pt.isChecked(): selected_disciplines.append('pt')
            if self.chk_ot.isChecked(): selected_disciplines.append('ot')
            if self.chk_slp.isChecked(): selected_disciplines.append('slp')

            if not selected_disciplines:
                QMessageBox.warning(self, "No Discipline Selected", "Please select at least one discipline (e.g., PT, OT, SLP) to be analyzed.")
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
                    self.render_analysis_to_results(data)

                    # --- Create and index the context for the AI ---
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
                        self.log("Creating AI context index...")
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

    def _create_context_chunks(self, data: dict, formatted_entities: list[str]) -> list[str]:
        """Creates a list of text chunks from the analysis data for the RAG index."""
        chunks = []

        # 1. Add summary information
        if 'compliance' in data and 'score' in data['compliance']:
            chunks.append(f"[Summary] The overall compliance score is {data['compliance']['score']}/100.")
        if 'executive_status' in data:
             chunks.append(f"[Summary] The executive status is '{data['executive_status']}'.")

        # 2. Add each issue as a detailed chunk, enriched with rubric data
        for issue in data.get('issues', []):
            issue_title = issue.get('title')
            # Find the corresponding full rule from the rubric
            matching_rule = next((r for r in self.compliance_rules if r.issue_title == issue_title), None)

            if matching_rule:
                # If we found the rule, create a detailed, structured chunk
                issue_str = (
                    f"[Finding] A finding with severity '{matching_rule.severity}' was identified.\n"
                    f"Category: {matching_rule.issue_category}\n"
                    f"Title: {matching_rule.issue_title}\n"
                    f"Why it matters: {matching_rule.issue_detail}"
                )
                chunks.append(issue_str)
            else:
                # Fallback to the basic information if no rule is found
                sev = issue.get('severity', 'N/A').title()
                cat = issue.get('category', 'N/A')
                detail = issue.get('detail', 'N/A')
                chunks.append(f"[Finding] Severity: {sev}. Category: {cat}. Title: {issue_title}. Detail: {detail}.")

            # Add citations as separate, clearly linked chunks
            for i, (citation_text, source) in enumerate(issue.get('citations', [])[:2]):
                clean_citation = re.sub('<[^<]+?>', '', citation_text)
                chunks.append(f"[Evidence] The finding '{issue_title}' is supported by evidence from '{source}': \"{clean_citation}\"")

        # 3. Add the original document sentences
        for text, source in data.get('source_sentences', []):
             chunks.append(f"[Document Text] From {source}: \"{text}\"")

        # 4. Add formatted entities
        chunks.extend(formatted_entities)

        self.log(f"Generated {len(chunks)} text chunks for AI context.")
        return chunks

    def action_analyze_batch(self):
        try:
            n = self.list_folder_files.count()
            if n == 0:
                QMessageBox.information(self, "Analyze Batch", "Please upload a folder with the documents first.")
                return
            reply = QMessageBox.question(self, "Analyze Batch",
                                         f"Process {n} file(s) sequentially?")  # type: ignore
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
                reply2 = QMessageBox.question(self, title, "\n".join(msg))  # type: ignore
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

                    # Formatting extracted entities as in main branch
                    formatted_entities = _format_entities_for_rag(ner_results)
                    logger.info(f"Formatted {len(formatted_entities)} entities for downstream use.")
            else:
                logger.warning("NER service was enabled but not ready. Skipping NER.")

        # The rest of the `run_analyzer` function would follow here...

            except Exception as e:
                self.set_error(f"An error occurred while querying the AI: {e}")
                QMessageBox.warning(self, "AI Error", f"An error occurred: {e}")
            finally:
                self.statusBar().showMessage("Ready")
                QApplication.restoreOverrideCursor()
                QMessageBox.information(self, "Analyze", "Please upload or select a report or upload a folder first.")
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

    def action_run_bias_audit(self):
        """
        Runs the bias audit on reviewed findings and displays the results.
        """
        try:
            from fairlearn.metrics import MetricFrame, selection_rate, false_positive_rate
            import json
        except ImportError:
            self.set_error("Fairlearn is not installed. Please run 'pip install fairlearn'.")
            QMessageBox.warning(self, "Library Not Found", "The 'fairlearn' library is required for this feature.")
            return

        group_by = self.bias_group_by_combo.currentText()

        self.statusBar().showMessage("Running bias audit...")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.bias_figure.clear()
        self.bias_canvas.draw()
        self.bias_results_text.clear()


        try:
            with _get_db_connection() as conn:
                df = pd.read_sql_query("""
                    SELECT
                        r.user_feedback,
                        i.severity,
                        i.title,
                        a.disciplines
                    FROM reviewed_findings r
                    JOIN analysis_issues i ON r.analysis_issue_id = i.id
                    JOIN analysis_runs a ON i.run_id = a.id
                """, conn)

            if df.empty or len(df) < 5:
                self.bias_results_text.setPlainText("Not enough reviewed findings available to run a meaningful bias audit. Please review more findings first.")
                return

            # --- Data Preparation ---
            df['y_true'] = df['user_feedback'].apply(lambda x: 1 if x == 'correct' else 0)
            df['y_pred'] = 1  # We are analyzing the set of findings that were *raised* by the model.

            if group_by == "Discipline":
                # Handle single and multi-discipline runs by "exploding" the dataframe
                def parse_disciplines(d_str):
                    try:
                        disciplines = json.loads(d_str)
                        return disciplines if isinstance(disciplines, list) and disciplines else None
                    except (json.JSONDecodeError, TypeError):
                        return None

                df['disciplines_list'] = df['disciplines'].apply(parse_disciplines)
                df.dropna(subset=['disciplines_list'], inplace=True)
                df = df.explode('disciplines_list')
                df.rename(columns={'disciplines_list': 'sensitive_features'}, inplace=True)

            elif group_by == "Finding Type":
                df.rename(columns={'title': 'sensitive_features'}, inplace=True)

            else: # Should not happen with the current UI
                return

            df.dropna(subset=['sensitive_features'], inplace=True)

            if df.empty or df['sensitive_features'].nunique() < 2:
                self.bias_results_text.setPlainText(f"Not enough data across different '{group_by}' groups to perform a comparative bias audit.")
                return

            y_true = df['y_true']
            y_pred = df['y_pred']
            sensitive_features = df['sensitive_features']

            # --- Fairlearn MetricFrame ---
            metrics = {
                'count': 'count',
                'false_positive_rate': false_positive_rate
            }

            grouped_on_feature = MetricFrame(metrics=metrics,
                                               y_true=y_true,
                                               y_pred=y_pred,
                                               sensitive_features=sensitive_features)

            results_df = grouped_on_feature.by_group
            results_df.index.name = group_by


            # --- Display Results ---
            results_text = f"Bias Audit Results (by {group_by}):\n\n"
            results_text += "This audit analyzes findings that users have marked as 'correct' or 'incorrect'.\n\n"
            results_text += f" - Count: The number of reviewed findings for that {group_by}.\n"
            results_text += " - False Positive Rate: The proportion of *incorrect* findings within the group. A high rate suggests the model is flagging non-issues for a specific group more often.\n\n"
            results_text += results_df.to_string()

            self.bias_results_text.setPlainText(results_text)

            # --- Generate Chart ---
            self.bias_figure.clear()
            ax = self.bias_figure.add_subplot(111)
            # Take top 10 for finding types to keep chart readable
            plot_df = results_df if group_by == "Discipline" else results_df.nlargest(10, 'count')
            plot_df[['false_positive_rate']].plot(kind='bar', ax=ax, legend=False, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
            ax.set_title(f'False Positive Rate by {group_by}')
            ax.set_ylabel('Rate (Proportion of Incorrect Findings)')
            ax.set_xlabel('')
            ax.tick_params(axis='x', rotation=45, ha='right')
            self.bias_figure.tight_layout()
            self.bias_canvas.draw()

        except Exception as e:
            self.set_error(f"Failed to run bias audit: {e}")
            logger.exception("Bias audit failed")
            QMessageBox.critical(self, "Audit Error", f"An error occurred during the bias audit:\n{e}")
        finally:
            self.statusBar().showMessage("Ready")
            QApplication.restoreOverrideCursor()

    def _update_analytics_tab(self):
        """
        Fetches the latest analytics data and updates the dashboard tab.
        """
        self.statusBar().showMessage("Refreshing analytics...")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.drilldown_list.clear()
        try:
            with _get_db_connection() as conn:
                start_date = self.analytics_start_date.date().toString("yyyy-MM-dd")
                # Add a day to the end date to make it inclusive in the query
                end_date = self.analytics_end_date.date().addDays(1).toString("yyyy-MM-dd")

                # Cache DFs on the instance to prevent re-querying in the pick event
                self.runs_df = pd.read_sql_query(
                    "SELECT * FROM analysis_runs WHERE run_time >= ? AND run_time < ?",
                    conn,
                    params=(start_date, end_date)
                )

                # Fetch all issues and then filter in memory, which is safer than a huge IN clause
                all_issues_df = pd.read_sql_query("SELECT * FROM analysis_issues", conn)

                if not self.runs_df.empty:
                    self.issues_df = all_issues_df[all_issues_df['run_id'].isin(self.runs_df['id'])]
                else:
                    self.issues_df = pd.DataFrame() # Ensure issues_df is an empty DataFrame if no runs found

            self.analytics_figure.clear()
            if self.runs_df.empty:
                self.statusBar().showMessage("No analytics data to display for the selected date range.", 4000)
                self.analytics_canvas.draw()
                return

            # --- Update Summary Stats ---
            self.lbl_total_runs.setText(str(len(self.runs_df)))
            avg_score = self.runs_df['compliance_score'].mean()
            self.lbl_avg_score.setText(f"{avg_score:.1f}" if pd.notna(avg_score) else "N/A")
            avg_flags = self.runs_df['flags'].mean()
            self.lbl_avg_flags.setText(f"{avg_flags:.2f}" if pd.notna(avg_flags) else "N/A")


            if not self.issues_df.empty:
                top_cat = self.issues_df['category'].mode()
                self.lbl_top_category.setText(top_cat[0] if not top_cat.empty else "N/A")
            else:
                self.lbl_top_category.setText("N/A")

            # --- Update Charts ---
            (ax1, ax2) = self.analytics_figure.subplots(2, 1, gridspec_kw={'height_ratios': [2, 1.5]})
            self.analytics_figure.subplots_adjust(hspace=0.4)


            # --- Chart 1: Findings by Severity ---
            if not self.issues_df.empty:
                self.severity_counts = self.issues_df['severity'].value_counts().reindex(['flag', 'finding', 'suggestion', 'auditor_note']).fillna(0)
                colors = {'flag': '#ef4444', 'finding': '#f59e0b', 'suggestion': '#10b981', 'auditor_note': '#9ca3af'}
                bar_colors = [colors.get(sev, '#374151') for sev in self.severity_counts.index]
                ax1.bar(self.severity_counts.index, self.severity_counts.values, color=bar_colors, picker=5)
                ax1.set_title('Total Findings by Severity (Click a bar to drill down)')
                ax1.set_ylabel('Total Count')
            else:
                ax1.text(0.5, 0.5, 'No findings data in selected range', ha='center', va='center')
                ax1.set_title('Total Findings by Severity')

            # --- Chart 2: Compliance Score Over Time ---
            if len(self.runs_df) > 1:
                # Convert run_time to datetime and sort
                self.runs_df['run_time_dt'] = pd.to_datetime(self.runs_df['run_time'])
                self.runs_df.sort_values('run_time_dt', inplace=True)

                # Group by day and get mean score
                daily_scores = self.runs_df.groupby(self.runs_df['run_time_dt'].dt.date)['compliance_score'].mean()

                ax2.plot(daily_scores.index, daily_scores.values, marker='o', linestyle='-')
                ax2.set_title('Compliance Score Trend')
                ax2.set_ylabel('Avg. Score')
                ax2.tick_params(axis='x', rotation=45)
                ax2.set_ylim(0, 105)
            else:
                ax2.text(0.5, 0.5, 'Not enough data to show a trend', ha='center', va='center')
                ax2.set_title('Compliance Score Trend')

            self.analytics_figure.tight_layout()
            self.analytics_canvas.draw()

            self.statusBar().showMessage("Analytics refreshed.", 4000)

        except Exception as e:
            self.set_error(f"Failed to refresh analytics: {e}")
            logger.exception("Analytics refresh failed")
        finally:
            QApplication.restoreOverrideCursor()

    def on_analytics_pick(self, event):
        """
        Handles click events on the analytics chart for drill-down.
        """
        if not hasattr(self, 'severity_counts') or event.mouseevent.xdata is None:
            return

        # Ensure the click was on the top subplot (severity chart)
        if len(self.analytics_figure.axes) < 2 or event.mouseevent.inaxes != self.analytics_figure.axes[0]:
            return

        try:
            # Figure out which bar was clicked based on x-coordinate
            x_index = int(round(event.mouseevent.xdata))
            severity = self.severity_counts.index[x_index]

            self.drilldown_list.clear()
            self.drilldown_list.parent().setTitle(f"Drill-Down: Files with '{severity}' findings")


            # Find all run_ids that have an issue with this severity
            run_ids_with_severity = self.issues_df[self.issues_df['severity'] == severity]['run_id'].unique()

            if len(run_ids_with_severity) > 0:
                # Get the file names and paths for these runs
                docs_df = self.runs_df[self.runs_df['id'].isin(run_ids_with_severity)]

                for index, row in docs_df.iterrows():
                    file_path = row.get('file_path')
                    # Use basename for display, but store full path in UserRole data
                    item = QListWidgetItem(os.path.basename(file_path) if file_path else "Unknown File")
                    item.setData(Qt.ItemDataRole.UserRole, file_path)
                    self.drilldown_list.addItem(item)
            else:
                self.drilldown_list.addItem("No documents found for this severity.")
        except IndexError:
            pass # Ignore clicks outside of bars
        except Exception as e:
            logger.error(f"Error during analytics pick event: {e}")

    def action_open_drilldown_file(self, item):
        """
        Opens the file associated with a double-clicked item in the drill-down list.
        """
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path and os.path.exists(file_path):
            _open_path(file_path)
        elif file_path:
            QMessageBox.warning(self, "File Not Found", f"The file could not be found at the stored path:\n{file_path}")

    def action_export_analytics_data(self):
        """
        Exports the currently displayed analytics data to a CSV file.
        """
        if not hasattr(self, 'runs_df') or self.runs_df.empty:
            QMessageBox.information(self, "Export Error", "No data to export. Please refresh the analytics first.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Save Analytics Data", "filtered_analytics.csv", "CSV Files (*.csv)")

        if not save_path:
            return

        try:
            # We need to merge the runs and issues dfs to get a complete picture
            if hasattr(self, 'issues_df') and not self.issues_df.empty:
                agg = self.issues_df.groupby(["run_id", "severity"]).size().unstack(fill_value=0).reset_index()
                df_to_export = self.runs_df.merge(agg, left_on="id", right_on="run_id", how="left").drop(columns=["run_id"])
            else:
                df_to_export = self.runs_df.copy()

            # Remove any temporary columns before exporting
            if 'run_time_dt' in df_to_export.columns:
                df_to_export = df_to_export.drop(columns=['run_time_dt'])

            df_to_export.to_csv(save_path, index=False, encoding="utf-8")
            self.log(f"Successfully exported filtered data to {save_path}")
            QMessageBox.information(self, "Export Successful", f"The filtered analytics data has been exported to:\n{save_path}")

        except Exception as e:
            self.set_error(f"Failed to export data: {e}")
            QMessageBox.critical(self, "Export Error", f"An error occurred while exporting data:\n{e}")

    def action_export_analytics_chart(self):
        """
        Exports the currently displayed analytics charts to a PNG image file.
        """
        if not self.analytics_figure.axes:
            QMessageBox.information(self, "Export Error", "No chart to export. Please refresh the analytics first.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Save Chart Image", "analytics_chart.png", "PNG Files (*.png)")

        if not save_path:
            return

        try:
            self.analytics_figure.savefig(save_path, dpi=300, bbox_inches='tight')
            self.log(f"Successfully exported chart to {save_path}")
            QMessageBox.information(self, "Export Successful", f"The chart image has been exported to:\n{save_path}")
        except Exception as e:
            self.set_error(f"Failed to export chart: {e}")
            QMessageBox.critical(self, "Export Error", f"An error occurred while exporting the chart:\n{e}")

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
            # Set margins if needed: writer.setPageMargins(...)

            doc.print_(writer)

            self.log(f"Successfully exported view to {save_path}")
            QMessageBox.information(self, "Export Successful", f"The current view has been exported to:\n{save_path}")

        except Exception as e:
            self.set_error(f"Failed to export view to PDF: {e}")
            QMessageBox.critical(self, "Export Error", f"An error occurred while exporting to PDF:\n{e}")
        finally:
            self.statusBar().showMessage("Ready")
            QApplication.restoreOverrideCursor()

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
            return 0

                except (ValueError, IndexError) as e:
                    self.log(f"Invalid review URL: {url_str} - {e}")
        elif url_str.startswith("ask:"):
            try:
                question_text = unquote(url_str[4:])
                self.input_query_te.setPlainText(question_text)
                self.action_send()
            except Exception as e:
                self.log(f"Failed to handle ask link: {url_str} - {e}")
        elif url_str.startswith("educate:"):
            try:
                issue_title = unquote(url_str[8:])
                self._display_educational_content(issue_title)
            except Exception as e:
                self.log(f"Failed to handle educate link: {url_str} - {e}")

    def _display_educational_content(self, issue_title: str):
        """Generates educational content and appends it to the main view."""
        if not self.local_rag or not self.local_rag.is_ready():
            QMessageBox.warning(self, "AI Not Ready", "The AI model is not available. Please wait for it to load, or check the logs.")
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

    def action_send(self):
        question = self.input_query_te.toPlainText().strip()
        if not question:
            return
        if not self.local_rag or not self.local_rag.is_ready() or not self.local_rag.index:
            QMessageBox.warning(self, "AI Not Ready", "Please analyze a document first to activate the AI chat.")
            return
        try:
            self.statusBar().showMessage("The AI is thinking...")
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            answer = self.local_rag.query(question, chat_history=self.chat_history)
            self.chat_history.append(("user", question))
            self.chat_history.append(("ai", answer))
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
        if not self.chat_history:
            return
        reply = QMessageBox.question(self, "Reset Chat", "Are you sure you want to clear the current conversation?")
        if str(reply).lower().endswith("yes"):
            self.chat_history = []
            self.log("Chat history has been manually reset.")
            if self.current_report_data:
                self._render_chat_history()
            else:
                self.txt_chat.clear()
            self.statusBar().showMessage("Chat Reset", 3000)

    def _render_chat_history(self):
        """Renders the analysis report and the full chat history."""
        if not self.current_report_data:
            self.txt_chat.setHtml("<div>Please analyze a file to get started.</div>")
            return
        # Start with the base analysis report
        base_html = self.current_report_data.get("narrative_html", "")
        # Append chat history
        chat_html = ""
        for sender, message in self.chat_history:
            if sender == "user":
                chat_html += f"<div class='user-message'><b>You:</b> {html.escape(message)}</div>"
            elif sender == "ai":
                chat_html += f"<div class='ai-message'><b>AI:</b> {html.escape(message)}</div>"
            elif sender == "education":
                issue_title, education_text = message
                formatted_edu_text = education_text.replace("\n", "<br>").replace(
                    "1. **A Good Example:**", "<b>A Good Example:</b>"
                ).replace(
                    "2. **Corrected Version:**", "<b>Corrected Version:</b>"
                )
                chat_html += (
                    f"<div class='education-block'>"
                    f"<h3>🎓 Learning Opportunity: {html.escape(issue_title)}</h3>"
                    f"<p>{formatted_edu_text}</p>"
                    f"</div>"
                )
        title_page_html = ""
        if self.current_report_data:
            file_name = os.path.basename(self.current_report_data.get('file', 'N/A'))
            run_time = self.current_report_data.get('generated', 'N/A')
            score = self.current_report_data.get('compliance', {}).get('score', 'N/A')
            title_page_html = f"""
            <div style="text-align: center; page-break-after: always;">
                <h1>Compliance Analysis Report</h1>
                <hr>
                <h2 style="font-size: 14pt;">File: {html.escape(file_name)}</h2>
                <p><b>Analysis Date:</b> {html.escape(run_time)}</p>
                <p><b>Compliance Score:</b> {score} / 100.0</p>
            </div>
            """
        body_content = base_html
        if chat_html:
            body_content += f"<h2>Conversation</h2>{chat_html}"
        body_with_title = title_page_html + body_content
        full_html = f"""
        <html>
            <head>
                <style>{REPORT_STYLESHEET}</style>
            </head>
            <body>
                {body_with_title}
            </body>
        </html>
        """
        self.txt_chat.setHtml(full_html)
        self.txt_chat.verticalScrollBar().setValue(self.txt_chat.verticalScrollBar().maximum())

# --- Settings dialog (main branch format, robust) ---
def _show_settings_dialog(parent=None) -> None:
    apply_theme(app)
    win = MainWindow()
    try:
        win.resize(1100, 780)
        act_folder = QAction("Open Folder", win)
        act_folder.setShortcut("Ctrl+Shift+O")
        act_folder.triggered.connect(win.action_open_folder)
        win.addAction(act_folder)

        act_open = QAction("Open File", win)
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(win.action_open_report)
        win.addAction(act_open)

        act_prev = QAction("Preview/Edit (Rubric)", win)
        act_prev.setShortcut("Ctrl+Shift+V")
        act_prev.triggered.connect(win.action_upload_rubric)
        win.addAction(act_prev)

        act_batch = QAction("Analyze Batch", win)
        act_batch.setShortcut("Ctrl+B")
        act_batch.triggered.connect(win.action_analyze_batch)
        win.addAction(act_batch)

        act_batchc = QAction("Cancel Batch", win)
        act_batchc.setShortcut("Ctrl+Shift+B")
        act_batchc.triggered.connect(win.action_cancel_batch)
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
    try:
        _ = QApplication
    except Exception as e:
        logger.warning(f"PyQt6 not available for GUI: {e}")
        print("PyQt6 is not installed. Please install PyQt6 to run the GUI.")
        return 0
    # --- Trial Period Check ---
    from datetime import datetime, date, timedelta
    app = QApplication.instance() or QApplication(sys.argv)
    trial_duration_days = get_int_setting("trial_duration_days", 30)
    if trial_duration_days > 0:
        first_run_str = get_setting("first_run_date")
        if not first_run_str:
            today = date.today()
            set_setting("first_run_date", today.isoformat())
            first_run_date = today
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

    win = MainWindow()
    win.show()
    return app.exec()


def _read_stylesheet(filename: str) -> str:
    """
Reads
a
stylesheet
from the src / directory.
"""
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
QMainWindow
{background:  # f3f4f6; color: #111827; }
     QWidget {background:  # f3f4f6; color: #111827; }
                  QTextEdit,
              QLineEdit {background:  # ffffff; color: #111827; border: 1px solid #d1d5db; border-radius: 4px; }
                             QPushButton{
                             background - color:  # 3b82f6; color: white; border: none; padding: 8px 12px; border-radius: 4px; }
                                 QPushButton: hover {background - color:  # 2563eb; }
                                                         QToolBar
                                                     {background:  # e5e7eb; border-bottom: 1px solid #d1d5db; }
                                                          QStatusBar {background:  # e5e7eb; color: #111827; }
                                                                          QGroupBox
                                                                      {border: 1px solid  # d1d5db; margin-top: 1em; }
                                                                       QGroupBox:: title {subcontrol - origin: margin;
left: 10
px;
padding: 0
3
px
0
3
px;}
""")
else: # dark theme
app.setStyleSheet("""
QMainWindow
{background:  # 1f2937; color: #e5e7eb; }
     QWidget {background:  # 1f2937; color: #e5e7eb; }
                  QTextEdit,
              QLineEdit {background:  # 111827; color: #e5e7eb; border: 1px solid #4b5563; border-radius: 4px; }
                             QPushButton{
                             background - color:  # 3b82f6; color: white; border: none; padding: 8px 12px; border-radius: 4px; }
                                 QPushButton: hover {background - color:  # 2563eb; }
                                                         QToolBar
                                                     {background:  # 111827; border-bottom: 1px solid #4b5563; }
                                                          QStatusBar {background:  # 111827; color: #e5e7eb; }
                                                                          QGroupBox
                                                                      {border: 1px solid  # 4b5563; margin-top: 1em; }
                                                                       QGroupBox:: title {subcontrol - origin: margin;
left: 10
px;
padding: 0
3
px
0
3
px;}
""")
f = QFont()
f.setPointSize(14)
app.setFont(f)


if __name__ == "__main__":
try:
code = _run_gui()
sys.exit(code if code is not None else 0)
except Exception:
logger.exception("GUI failed")
sys.exit(1)