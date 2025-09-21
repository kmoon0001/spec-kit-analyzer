import argparse
import os
from src.ingestion import build_sentence_window_index
from src.retrieval import get_query_engine
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# --- Configuration ---
# In a real app, these would be in a config file or environment variables.
# For the purpose of this task, we will use a placeholder OpenAI API Key.
# The user would need to set their actual key as an environment variable.
os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY_HERE"
LLM = OpenAI(model="gpt-3.5-turbo")
EMBED_MODEL = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
INDEX_DIR = "sentence_index"
DOCS_DIR = "data"

def handle_ingest(args):
    """Handles the 'ingest' command."""
    docs_path = args.dir or DOCS_DIR
    if not os.path.exists(docs_path):
        print(f"Error: Document directory not found at '{docs_path}'")
        # Create a dummy data directory for the user
        os.makedirs(docs_path)
        print(f"Created a dummy directory at '{docs_path}'. Please add your documents there and run ingest again.")
        return

    print(f"Starting ingestion from directory: {docs_path}")
    build_sentence_window_index(
        documents_path=docs_path,
        llm=LLM,
        embed_model=EMBED_MODEL,
        save_dir=INDEX_DIR,
    )
    print("Ingestion complete.")

def handle_query(args):
    """Handles the 'query' command."""
    if not args.question:
        print("Error: Please provide a question with the --question flag.")
        return

    print(f"Querying with: '{args.question}'")
    try:
        query_engine = get_query_engine(index_dir=INDEX_DIR)
        response = query_engine.query(args.question)
        print("\n--- Response ---")
        print(response)
        print("\n---")
    except FileNotFoundError as e:
        print(f"Error: {e}. Please run the 'ingest' command first.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def main():
    """Main function to run the command-line interface."""
    parser = argparse.ArgumentParser(description="A command-line interface for a RAG pipeline.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # Subparser for the 'ingest' command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents from a directory into the vector store.")
    ingest_parser.add_argument("--dir", type=str, default=DOCS_DIR, help=f"The directory containing documents to ingest. Defaults to '{DOCS_DIR}'.")
    ingest_parser.set_defaults(func=handle_ingest)

    # Subparser for the 'query' command
    query_parser = subparsers.add_parser("query", help="Ask a question to the indexed documents.")
    query_parser.add_argument("--question", type=str, required=True, help="The question you want to ask.")
    query_parser.set_defaults(func=handle_query)

    args = parser.parse_args()
    args.func(args)

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
    from .ner_service import NERService
    from .entity_consolidation_service import EntityConsolidationService
    from .text_chunking import RecursiveCharacterTextSplitter
except ImportError as e:
    logger.error(f"Failed to import local modules: {e}. Ensure you're running as a package.")


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
                        TEXT,
                        file_path
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

            except Exception as e:
                self.set_error(f"An error occurred while querying the AI: {e}")
                QMessageBox.warning(self, "AI Error", f"An error occurred: {e}")
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