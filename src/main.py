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
    from PIL import Image, UnidentifiedImageError
except Exception as e:
    Image = None  # type: ignore


    class UnidentifiedImageError(Exception):
        ...


    logger.warning(f"PIL unavailable: {e}")

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

# PyQt (guarded)
try:
    from PyQt6.QtWidgets import (
        QMainWindow, QToolBar, QLabel, QFileDialog, QMessageBox, QApplication,
        QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QPushButton,
        QSpinBox, QCheckBox, QTextEdit, QSplitter, QGroupBox, QListWidget, QWidget,
        QProgressDialog, QSizePolicy, QStatusBar, QProgressBar, QMenu, QTabWidget
    )
    from PyQt6.QtGui import QAction, QFont, QTextDocument
    from PyQt6.QtCore import Qt
except Exception:
    class QMainWindow:
        ...


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


    class QProgressDialog:
        ...


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


def parse_document_content(file_path: str) -> List[Tuple[str, str]]:
    ext = os.path.splitext(file_path)[1].lower()
    try:
        sentences: list[tuple[str, str]] = []
        if ext == ".pdf":
            if not pdfplumber:
                return [("Error: pdfplumber not available.", "PDF Parser")]
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    txt = page.extract_text() or ""
                    for s in split_sentences(txt):
                        if s:
                            sentences.append((s, f"Page {i}"))
        elif ext == ".docx":
            try:
                from docx import Document
            except Exception:
                return [("Error: python-docx not available.", "DOCX Parser")]
            docx_doc = Document(file_path)
            for i, para in enumerate(docx_doc.paragraphs, start=1):
                if not para.text.strip():
                    continue
                for s in split_sentences(para.text):
                    if s:
                        sentences.append((s, f"Paragraph {i}"))
        elif ext in [".xlsx", ".xls", ".csv"]:
            try:
                if ext in [".xlsx", ".xls"]:
                    df = pd.read_excel(file_path)
                    if isinstance(df, dict):
                        df = next(iter(df.values()))
                else:
                    df = pd.read_csv(file_path)
                content = df.to_string(index=False)
                for s in split_sentences(content):
                    if s:
                        sentences.append((s, "Table"))
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
                for s in split_sentences(txt or ""):
                    if s:
                        sentences.append((s, "Image (OCR)"))
            except UnidentifiedImageError as e:
                return [(f"Error: Unidentified image: {e}", "OCR Parser")]
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                txt = f.read()
            for s in split_sentences(txt):
                if s:
                    sentences.append((s, "Text File"))
        else:
            return [(f"Error: Unsupported file type: {ext}", "File Handler")]
        return sentences if sentences else [("Info: No text could be extracted from the document.", "System")]
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


# ... existing code ...
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
                        wobblers
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

        # --- Simple schema migration for compliance_score ---
        cur.execute("PRAGMA table_info(analysis_runs)")
        columns = [row[1] for row in cur.fetchall()]
        if "compliance_score" not in columns:
            cur.execute("ALTER TABLE analysis_runs ADD COLUMN compliance_score REAL")
            logger.info("Upgraded analysis_runs table to include 'compliance_score' column.")

        conn.commit()
    except Exception as e:
        logger.warning(f"Ensure analytics schema failed: {e}")


def persist_analysis_run(file_path: str, run_time: str, metrics: dict, issues_scored: list[dict],
                         compliance: dict, mode: str) -> Optional[int]:
    try:
        with _get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                        INSERT INTO analysis_runs (file_name, run_time, pages_est, flags, wobblers, suggestions, notes,
                                                   sentences_final, dedup_removed, compliance_score, mode)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            os.path.basename(file_path), run_time,
                            int(metrics.get("pages", 0)), int(metrics.get("flags", 0)), int(metrics.get("wobblers", 0)),
                            int(metrics.get("suggestions", 0)), int(metrics.get("notes", 0)),
                            int(metrics.get("sentences_final", 0)), int(metrics.get("dedup_removed", 0)),
                            float(compliance.get("score", 0.0)), mode
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
        "avg_wobblers": 0.0,
        "avg_suggestions": 0.0,
    }
    try:
        with _get_db_connection() as conn:
            runs = pd.read_sql_query(
                "SELECT compliance_score, flags, wobblers, suggestions FROM analysis_runs ORDER BY run_time ASC", conn
            )
        if runs.empty:
            return out
        sub = runs.tail(max_runs).copy()
        scores = [float(x) for x in sub["compliance_score"].tolist()]
        out["recent_scores"] = scores
        out["avg_score"] = round(float(sum(scores) / len(scores)), 1) if scores else 0.0
        out["score_delta"] = round((scores[-1] - scores[0]) if len(scores) >= 2 else 0.0, 1)
        out["avg_flags"] = round(float(sub["flags"].mean()), 2)
        out["avg_wobblers"] = round(float(sub["wobblers"].mean()), 2)
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


def _audit_from_rubric(text: str, strict: bool | None = None) -> list[dict]:
    t = (text or "").lower()
    issues: list[dict] = []

    def add(sev: str, title: str, detail: str, cat: str) -> None:
        issues.append({"severity": sev, "title": title, "detail": detail, "category": cat})

    s = bool(strict)
    if not any(k in t for k in ("signature", "signed", "dated")):
        add("flag" if s else "wobbler", "Provider signature/date possibly missing",
            "No explicit evidence of dated/signature entries found.", "Signatures/Dates")
    if "goal" in t and not any(k in t for k in ("measurable", "time", "timed")):
        add("flag" if s else "wobbler", "Goals may not be measurable/time-bound",
            "Consider restating goals with measurable, time-bound targets and baselines.", "Goals")
    if not any(k in t for k in ("medical necessity", "reasonable and necessary", "necessity")):
        add("flag" if s else "wobbler", "Medical necessity not explicitly supported",
            "Ensure documentation ties interventions to functional limitations and outcomes aligned with Medicare Part B.",
            "Medical Necessity")
    if "assistant" in t and "supervis" not in t:
        add("wobbler" if s else "suggestion", "Assistant supervision context unclear",
            "When assistants are involved, document supervision/oversight per Medicare/state requirements.",
            "Assistant Supervision")
    if not any(k in t for k in ("plan of care", "poc", "certification", "recert")):
        add("flag" if s else "wobbler", "Plan/Certification not clearly referenced",
            "Explicitly reference plan of care/certification dates and responsible signatures.", "Plan/Certification")
    issues.append({
        "severity": "auditor_note",
        "title": "General auditor checks",
        "detail": "Review compliance with Medicare Part B (qualified personnel, plan establishment/recert, timings/units, documentation integrity).",
        "category": "General"
    })
    return issues


def _attach_issue_citations(issues_in: list[dict], records: list[tuple[str, str]], cap: int = 3) -> list[dict]:
    out: list[dict] = []
    for it in issues_in:
        q = (it.get("title", "") + " " + it.get("detail", "")).lower()
        tok = [w for w in re.findall(r"[a-z]{4,}", q)]
        cites: list[tuple[str, str]] = []
        for (text, src) in records:
            tl = text.lower()
            score = sum(1 for w in tok if w in tl)
            if score >= max(1, len(tok) // 4):
                cites.append((text.strip(), src))
            if len(cites) >= cap:
                break
        out.append({**it, "citations": cites})
    return out


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
                        cats = ["Flags", "Wobblers", "Suggestions", "Notes"]
                        vals = [sev_counts.get("flag", 0), sev_counts.get("wobbler", 0),
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
                            cats = ["Flags", "Wobblers", "Suggestions", "Notes"]
                            vals = [sev_counts.get("flag", 0), sev_counts.get("wobbler", 0),
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


# ... existing code ...
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
    wobblers = sev_counts.get("wobbler", 0)

    if score >= 90 and flags == 0:
        risk = "Low"
        summary = "Good compliance posture."
    elif score >= 70 and flags <= 1:
        risk = "Medium"
        summary = "Some areas need review."
    else:
        risk = "High"
        summary = "Critical issues require attention."

    lines.append(f"Overall Risk: {risk}")
    lines.append(f"Compliance Score: {score:.1f}/100")
    lines.append(f"Summary: {summary}")
    lines.append(f"Critical Findings (Flags): {flags}")
    lines.append(f"Areas of Concern (Wobblers): {wobblers}")
    lines.append("")
    return lines

def _generate_compliance_checklist(strengths: list[str], weaknesses: list[str]) -> list[str]:
    lines = ["--- Compliance Checklist ---"]

    checklist_items = {
        "Provider Authentication": "Provider authentication (signature/date)",
        "Measurable Goals": "Goals appear to be measurable",
        "Medical Necessity": "Medical necessity is explicitly discussed",
        "Assistant Supervision": "Assistant involvement includes supervision context",
        "Plan/Certification": "Plan/certification is referenced"
    }

    for key, text in checklist_items.items():
        if any(text in s for s in strengths):
            lines.append(f"[✔] {key}")
        elif any(text in w for w in weaknesses):
            lines.append(f"[❌] {key}")
        else:
            simplified_weakness_text = text.split('(')[0].strip()
            if any(simplified_weakness_text in w for w in weaknesses):
                 lines.append(f"[❌] {key}")
            else:
                 lines.append(f"[○] {key} (Not mentioned)")

    lines.append("")
    return lines


def run_analyzer(file_path: str,
                 scrub_override: Optional[bool] = None,
                 review_mode_override: Optional[str] = None,
                 dedup_method_override: Optional[str] = None,
                 progress_cb: Optional[Callable[[int, str], None]] = None,
                 cancel_cb: Optional[Callable[[], bool]] = None) -> dict:
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

        check_cancel()
        report(60, "Computing summary")
        summary = build_rich_summary(processed, collapsed)

        report(70, "Analyzing compliance")
        full_text = "\n".join(t for t, _ in collapsed)
        strict_flag = (CURRENT_REVIEW_MODE == "Strict")
        issues_base = _audit_from_rubric(full_text, strict=strict_flag)
        issues_scored = _score_issue_confidence(_attach_issue_citations(issues_base, collapsed), collapsed)

        # Add location data to each issue based on its first citation
        full_text_for_loc = "\n".join(t for t, _ in collapsed)
        for issue in issues_scored:
            if issue.get("citations"):
                # Use the text of the first citation to find its location
                cite_text = issue["citations"][0][0]
                try:
                    start_index = full_text_for_loc.index(cite_text)
                    end_index = start_index + len(cite_text)
                    issue['location'] = {'start': start_index, 'end': end_index}
                except ValueError:
                    # Citation might not be an exact substring, ignore for now.
                    issue['location'] = None

        sev_order = {"flag": 0, "wobbler": 1, "suggestion": 2, "auditor_note": 3}
        issues_scored.sort(key=lambda x: (sev_order.get(str(x.get("severity")), 9),
                                          str(x.get("category", "")),
                                          str(x.get("title", ""))))

        # I'll inject the details into the issue object itself for easier rendering later.
        # This is not in the original code, but it's a good refactoring.
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


        pages_est = len({s for _, s in collapsed if s.startswith("Page ")}) or 1

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
            weaknesses.append("Medical necessity not explicitly supported throughout the documentation.")
            missing.append("Medical Necessity")

        if "assistant" in tl and "supervis" in tl:
            strengths.append("Assistant involvement includes supervision context.")
        elif "assistant" in tl:
            weaknesses.append("Assistant activity present; supervision/oversight context is not clearly documented.")
            missing.append("Assistant Supervision Context")

        if any(k in tl for k in ("plan of care", "poc", "certification", "recert")):
            strengths.append("Plan/certification is referenced in the record.")
        else:
            weaknesses.append("Plan/certification not clearly referenced with dates and signatures.")
            missing.append("Plan/Certification Reference")

        sev_counts = {
            "flag": sum(1 for i in issues_scored if i.get("severity") == "flag"),
            "wobbler": sum(1 for i in issues_scored if i.get("severity") == "wobbler"),
            "suggestion": sum(1 for i in issues_scored if i.get("severity") == "suggestion"),
            "auditor_note": sum(1 for i in issues_scored if i.get("severity") == "auditor_note"),
        }
        cat_counts = count_categories(issues_scored)

        def compute_compliance_score(issues: list[dict], strengths_in: list[str], missing_in: list[str],
                                     mode: ReviewMode) -> dict:
            flags = sum(1 for i in issues if i.get("severity") == "flag")
            wob = sum(1 for i in issues if i.get("severity") == "wobbler")
            sug = sum(1 for i in issues if i.get("severity") == "suggestion")
            base = 100.0
            if mode == "Strict":
                base -= flags * 6.0
                base -= wob * 3.0
                base -= sug * 1.5
                base -= len(missing_in) * 4.0
            else:
                base -= flags * 4.0
                base -= wob * 2.0
                base -= sug * 1.0
                base -= len(missing_in) * 2.5
            base += min(5.0, len(strengths_in) * 0.5)
            score = max(0.0, min(100.0, base))
            breakdown = f"Flags={flags}, Wobblers={wob}, Suggestions={sug}, Missing={len(missing_in)}, Strengths={len(strengths_in)}; Mode={mode}"
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
            tips.append("Resolve flags first (signatures/dates, plan/certification), then clarify grey areas.")
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
                "wobblers_delta": sev_counts["wobbler"] - int(prev.get("wobblers", 0)),
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
                    "good_example": "A note that clearly links interventions to functional goals and documents the patient's progress over time.",
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
                    narrative_lines.append(f"  - Recommended Action: {details['action']}")
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
        narrative_lines.append(" • Consistency is key. Ensure all notes follow a standard format.")
        narrative_lines.append(" • Be specific and objective. Use numbers and standardized tests to measure progress.")
        narrative_lines.append(" • Always link treatment to function. Explain how the therapy helps the patient achieve their functional goals.")
        narrative_lines.append(" • Tell a story. The documentation should paint a clear picture of the patient's journey from evaluation to discharge.")
        narrative_lines.append("")

        narrative_lines.append("--- Trends & Analytics (Last 10 Runs) ---")
        if trends.get("recent_scores"):
            sc = trends["recent_scores"]
            narrative_lines.append(f" • Recent scores (oldest→newest): {', '.join(str(round(s, 1)) for s in sc)}")
            narrative_lines.append(
                f" • Score delta: {trends['score_delta']:+.1f} | Average score: {trends['avg_score']:.1f}")
            narrative_lines.append(
                f" • Avg Flags: {trends['avg_flags']:.2f} | Avg Wobblers: {trends['avg_wobblers']:.2f} | Avg Suggestions: {trends['avg_suggestions']:.2f}")
        else:
            narrative_lines.append(" • Not enough history to compute trends yet.")
        narrative_lines.append("")

        metrics = {
            "pages": pages_est,
            "findings_total": len(issues_scored),
            "flags": sev_counts["flag"],
            "wobblers": sev_counts["wobbler"],
            "suggestions": sev_counts["suggestion"],
            "notes": sev_counts["auditor_note"],
            "sentences_raw": summary["total_sentences_raw"],
            "sentences_final": summary["total_sentences_final"],
            "dedup_removed": summary["dedup_removed"],
        }

        try:
            persist_analysis_run(file_path, _now_iso(), metrics, issues_scored, compliance, CURRENT_REVIEW_MODE)
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
                "clinical_ner_enabled": False,
                "source_sentences": collapsed,
                "sev_counts": sev_counts,
                "cat_counts": cat_counts,
                "trends": trends,
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
                "wobblers": sev_counts["wobbler"],
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
        return result_info
    except KeyboardInterrupt:
        logger.info("Analysis cancelled by user.")
        return result_info
    except Exception:
        logger.exception("Analyzer failed")
        return result_info


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

    row_flags = QHBoxLayout()
    chk_cache = QCheckBox("Enable analysis cache")
    chk_cache.setChecked(get_bool_setting("allow_cache", True))
    row_flags.addWidget(chk_cache)
    vbox.addLayout(row_flags)

    row_theme = QHBoxLayout()
    row_theme.addWidget(QLabel("UI Theme:"))
    cmb_theme = QComboBox()
    cmb_theme.addItems(["dark", "light"])
    cmb_theme.setCurrentText(get_str_setting("ui_theme", "dark"))
    row_theme.addWidget(cmb_theme)
    vbox.addLayout(row_theme)

    row_dedup = QHBoxLayout()
    row_dedup.addWidget(QLabel("Default Dedup Method:"))
    cmb_dedup = QComboBox()
    cmb_dedup.addItems(["tfidf", "simple"])
    cmb_dedup.setCurrentText(get_str_setting("dedup_method", "tfidf"))
    row_dedup.addWidget(cmb_dedup)
    vbox.addLayout(row_dedup)

    row_rep = QHBoxLayout()
    row_rep.addWidget(QLabel("Reports size cap (MB):"))
    sp_rep_size = QSpinBox()
    sp_rep_size.setRange(0, 100000)
    sp_rep_size.setValue(get_int_setting("reports_max_size_mb", 512))
    row_rep.addWidget(sp_rep_size)
    row_rep.addWidget(QLabel("Reports max age (days):"))
    sp_rep_age = QSpinBox()
    sp_rep_age.setRange(0, 10000)
    sp_rep_age.setValue(get_int_setting("reports_max_age_days", 90))
    row_rep.addWidget(sp_rep_age)
    vbox.addLayout(row_rep)

    row_recent = QHBoxLayout()
    row_recent.addWidget(QLabel("Recent files max:"))
    sp_recent = QSpinBox()
    sp_recent.setRange(1, 200)
    sp_recent.setValue(get_int_setting("recent_max", 20))
    row_recent.addWidget(sp_recent)
    vbox.addLayout(row_recent)

    row_trends = QHBoxLayout()
    row_trends.addWidget(QLabel("Trends window (N recent runs):"))
    sp_trends = QSpinBox()
    sp_trends.setRange(3, 100)
    sp_trends.setValue(get_int_setting("trends_window", 10))
    row_trends.addWidget(sp_trends)
    vbox.addLayout(row_trends)

    row_pdf = QHBoxLayout()
    chk_pdf_chart = QCheckBox("Show mini chart in PDF")
    chk_pdf_chart.setChecked(get_bool_setting("pdf_chart_enabled", True))
    row_pdf.addWidget(chk_pdf_chart)
    row_pdf.addWidget(QLabel("Chart position:"))
    cmb_chart_pos = QComboBox()
    cmb_chart_pos.addItems(["bottom", "top", "none"])
    cmb_chart_pos.setCurrentText(get_str_setting("pdf_chart_position", "bottom"))
    row_pdf.addWidget(cmb_chart_pos)
    row_pdf.addWidget(QLabel("Chart theme:"))
    cmb_chart_theme = QComboBox()
    cmb_chart_theme.addItems(["dark", "light"])
    cmb_chart_theme.setCurrentText(get_str_setting("pdf_chart_theme", "dark"))
    row_pdf.addWidget(cmb_chart_theme)
    vbox.addLayout(row_pdf)

    row_btn = QHBoxLayout()
    btn_ok = QPushButton("Save")
    btn_cancel = QPushButton("Cancel")
    for b in (btn_ok, btn_cancel):
        f = QFont()
        f.setPointSize(12)
        f.setBold(True)
        b.setFont(f)
        b.setMinimumHeight(36)
        b.setStyleSheet("text-align:center; padding:8px 14px;")
        b.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
    row_btn.addStretch(1)
    row_btn.addWidget(btn_ok)
    row_btn.addWidget(btn_cancel)
    vbox.addLayout(row_btn)

    def on_save():
        set_bool_setting("allow_cache", chk_cache.isChecked())
        set_str_setting("ui_theme", cmb_theme.currentText().strip().lower())
        set_str_setting("dedup_method", cmb_dedup.currentText().strip())
        set_str_setting("reports_max_size_mb", str(sp_rep_size.value()))
        set_str_setting("reports_max_age_days", str(sp_rep_age.value()))
        set_bool_setting("pdf_chart_enabled", chk_pdf_chart.isChecked())
        set_str_setting("pdf_chart_position", cmb_chart_pos.currentText().strip().lower())
        set_str_setting("pdf_chart_theme", cmb_chart_theme.currentText().strip().lower())
        set_str_setting("recent_max", str(sp_recent.value()))
        set_str_setting("trends_window", str(sp_trends.value()))
        dlg.accept()

    try:
        btn_ok.clicked.connect(on_save)  # type: ignore[attr-defined]
        btn_cancel.clicked.connect(dlg.reject)  # type: ignore[attr-defined]
    except Exception:
        ...
    dlg.show()
    try:
        dlg.raise_()
        dlg.activateWindow()
    except Exception:
        ...
    dlg.exec()


# ... existing code ...
def _run_gui() -> Optional[int]:
    try:
        _ = QApplication  # noqa
    except Exception as e:
        logger.warning(f"PyQt6 not available for GUI: {e}")
        print("PyQt6 is not installed. Please install PyQt6 to run the GUI.")
        return 0

    # --- Trial Period Check ---
    from datetime import datetime, date, timedelta

    # We need a QApplication instance to show a message box, so create it early.
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
                # Handle case where date is malformed or not a string
                first_run_date = date.today()
                set_setting("first_run_date", first_run_date.isoformat())

        expiration_date = first_run_date + timedelta(days=trial_duration_days)

        if date.today() > expiration_date:
            QMessageBox.critical(None, "Trial Expired",
                                 f"Your trial period of {trial_duration_days} days has expired.\n"
                                 "Please contact the administrator to continue using the application.")
            return 0 # Exit cleanly

    def apply_theme(app: QApplication):
        theme = (get_str_setting("ui_theme", "dark") or "dark").lower()
        if theme == "light":
            app.setStyleSheet("""
                QMainWindow { background: #f3f4f6; color: #111827; border: 2px solid #3b82f6; }
                QWidget { background: #f3f4f6; color: #111827; }
                QTextEdit, QLineEdit { background: #ffffff; color: #111827; border: 2px solid #93c5fd; border-radius: 10px; }
                QPushButton { background: #2563eb; color: #ffffff; border: none; padding: 10px 14px; border-radius: 12px; font-size: 14px; font-weight: 700; }
                QPushButton:hover { background: #1d4ed8; }
                QToolBar { background: #e5e7eb; spacing: 10px; border: 2px solid #3b82f6; padding: 6px; }
                QStatusBar { background: #e5e7eb; color: #111827; }
                QGroupBox { border: 2px solid #3b82f6; margin-top: 20px; border-radius: 10px; }
                QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 10px; padding: 6px 8px; font-weight: 700; font-size: 18px; color: #111827; }
            """)
        else:
            app.setStyleSheet("""
                QMainWindow { background: #1f2937; color: #e5e7eb; border: 2px solid #1f4fd1; }
                QWidget { background: #1f2937; color: #e5e7eb; }
                QTextEdit, QLineEdit { background: #111827; color: #e5e7eb; border: 2px solid #1f4fd1; border-radius: 10px; }
                QPushButton { background: #1f4fd1; color: #ffffff; border: none; padding: 10px 14px; border-radius: 12px; font-size: 14px; font-weight: 700; }
                QPushButton:hover { background: #163dc0; }
                QToolBar { background: #111827; spacing: 10px; border: 2px solid #1f4fd1; padding: 6px; }
                QStatusBar { background: #111827; color: #e5e7eb; }
                QGroupBox { border: 2px solid #1f4fd1; margin-top: 20px; border-radius: 10px; }
                QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 10px; padding: 6px 8px; font-weight: 700; font-size: 18px; color: #e5e7eb; }
            """)
        f = QFont()
        f.setPointSize(14)
        app.setFont(f)

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

            central = QWidget()
            self.setCentralWidget(central)
            vmain = QVBoxLayout(central)
            vmain.setContentsMargins(12, 12, 12, 12)
            vmain.setSpacing(14)

            top_split = QSplitter(Qt.Orientation.Horizontal)
            try:
                top_split.setChildrenCollapsible(False)
            except Exception:
                ...

            # Left: Rubric panel
            rubric_panel = QWidget()
            rubric_layout = QVBoxLayout(rubric_panel)
            rubric_layout.setContentsMargins(12, 12, 12, 12)
            rubric_layout.setSpacing(8)

            row_rubric_btns = QHBoxLayout()
            self.btn_upload_rubric = QPushButton("Upload Rubric")
            self.btn_preview_rubric = QPushButton("Preview Rubric")
            self.btn_manage_rubrics = QPushButton("Manage Rubrics")
            self.btn_save_rubric = QPushButton("Save (App Only)")
            self.btn_remove_rubric = QPushButton("Remove Rubric")
            for b in (self.btn_upload_rubric, self.btn_preview_rubric, self.btn_manage_rubrics, self.btn_save_rubric, self.btn_remove_rubric):
                self._style_action_button(b, font_size=13, bold=True, height=40, padding="8px 12px")
                row_rubric_btns.addWidget(b)
            row_rubric_btns.addStretch(1)
            try:
                self.btn_upload_rubric.clicked.connect(self.action_upload_rubric)  # type: ignore[attr-defined]
                self.btn_preview_rubric.clicked.connect(self.action_toggle_rubric_preview)  # type: ignore[attr-defined]
                self.btn_manage_rubrics.clicked.connect(self.action_manage_rubrics)  # type: ignore[attr-defined]
                self.btn_save_rubric.clicked.connect(self.action_save_rubric_app_only)  # type: ignore[attr-defined]
                self.btn_remove_rubric.clicked.connect(self.action_remove_rubric)  # type: ignore[attr-defined]
            except Exception:
                ...
            rubric_layout.addLayout(row_rubric_btns)

            self.lbl_rubric_title = QLabel("Medicare B Guidelines")
            self.lbl_rubric_file = QLabel("(No rubric selected)")
            self.lbl_rubric_file.setWordWrap(True)
            rubric_layout.addWidget(self.lbl_rubric_title)
            rubric_layout.addWidget(self.lbl_rubric_file)

            self.txt_rubric = QTextEdit()
            self.txt_rubric.setPlaceholderText("Rubric (hidden for compact view).")
            self.txt_rubric.setVisible(False)
            try:
                current_txt = get_setting("rubric_current_text")
                self.txt_rubric.setPlainText(current_txt if current_txt else _RUBRIC_DEFAULT)
                self.lbl_rubric_file.setText(
                    "Rubric Loaded" if self.txt_rubric.toPlainText().strip() else "(No rubric selected)")
                if self.txt_rubric.toPlainText().strip():
                    self.lbl_rubric_file.setStyleSheet("color:#60a5fa; font-weight:700;")
            except Exception:
                self.txt_rubric.setPlainText(_RUBRIC_DEFAULT)
            rubric_layout.addWidget(self.txt_rubric)

            # Right: Report panel
            report_panel = QWidget()
            report_layout = QVBoxLayout(report_panel)
            report_layout.setContentsMargins(12, 12, 12, 12)
            report_layout.setSpacing(8)

            row_report_btns = QHBoxLayout()
            self.btn_upload_report = QPushButton("Open File")
            self.btn_analyze_all = QPushButton("Analyze")
            self.btn_cancel_batch = QPushButton("Cancel Batch")
            self.btn_clear_all = QPushButton("Clear All")
            for b in (self.btn_upload_report, self.btn_analyze_all,
                      self.btn_cancel_batch, self.btn_clear_all):
                self._style_action_button(b, font_size=13, bold=True, height=40, padding="8px 12px")
                row_report_btns.addWidget(b)
            row_report_btns.addStretch(1)
            try:
                self.btn_upload_report.clicked.connect(self.action_open_report)  # type: ignore[attr-defined]
                self.btn_analyze_all.clicked.connect(self.action_analyze_combined)  # type: ignore[attr-defined]
                self.btn_cancel_batch.clicked.connect(self.action_cancel_batch)  # type: ignore[attr-defined]
                self.btn_cancel_batch.setDisabled(True)
                self.btn_clear_all.clicked.connect(self.action_clear_all)  # type: ignore[attr-defined]
            except Exception:
                ...
            report_layout.addLayout(row_report_btns)

            self.lbl_report_name = QLabel("(No report selected)")
            self.lbl_report_name.setWordWrap(True)
            report_layout.addWidget(self.lbl_report_name)

            self.list_folder_files = QListWidget()
            try:
                self.list_folder_files.setMinimumHeight(60)
                self.list_folder_files.setMaximumHeight(100)
                self.list_folder_files.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            except Exception:
                ...
            # report_layout.addWidget(self.list_folder_files) # Removed from here

            top_split.addWidget(rubric_panel)
            top_split.addWidget(report_panel)
            top_split.setStretchFactor(0, 1)
            top_split.setStretchFactor(1, 1)

            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Ready")
            self.progress_bar.setMinimumHeight(20)
            self.progress_bar.setVisible(False)
            self.progress_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

            # --- Combined File Queue and Logs Tab ---
            self.grp_queue_logs = QGroupBox("File Queue & Application Logs")
            queue_logs_layout = QVBoxLayout(self.grp_queue_logs)

            self.queue_log_tabs = QTabWidget()

            # File Queue Tab - reuse the existing list widget
            self.queue_log_tabs.addTab(self.list_folder_files, "File Queue")

            # Logs Tab
            log_widget_container = QWidget()
            logs_vbox = QVBoxLayout(log_widget_container)
            logs_vbox.setContentsMargins(4, 4, 4, 4)

            log_actions_layout = QHBoxLayout()
            self.btn_clear_recent_files = QPushButton("Clear Recent Files")
            log_actions_layout.addStretch(1)
            log_actions_layout.addWidget(self.btn_clear_recent_files)
            self._style_action_button(self.btn_clear_recent_files, font_size=11, bold=True, height=28, padding="4px 10px")
            try:
                self.btn_clear_recent_files.clicked.connect(self.action_clear_recent_files)
            except Exception:
                ...
            logs_vbox.addLayout(log_actions_layout)

            self.txt_logs = QTextEdit()
            self.txt_logs.setReadOnly(True)
            flog = QFont();
            flog.setPointSize(11)
            self.txt_logs.setFont(flog)
            logs_vbox.addWidget(self.txt_logs)

            self.queue_log_tabs.addTab(log_widget_container, "Logs")
            queue_logs_layout.addWidget(self.queue_log_tabs)

            self.grp_results = QGroupBox("Analysis Window")
            res_layout = QVBoxLayout(self.grp_results)
            res_layout.setContentsMargins(12, 12, 12, 12)
            res_layout.setSpacing(8)

            row_results_actions = QHBoxLayout()
            self.btn_results_analytics = QPushButton("Export Analytics CSV")
            try:
                self._style_action_button(self.btn_results_analytics, font_size=11, bold=True, height=28, padding="4px 10px")
                self.btn_results_analytics.clicked.connect(
                    lambda: self._export_analytics_csv())  # type: ignore[attr-defined]
            except Exception:
                ...
            row_results_actions.addStretch(1)
            row_results_actions.addWidget(self.btn_results_analytics)
            res_layout.addLayout(row_results_actions)

            self.txt_chat = QTextEdit()
            self.txt_chat.setPlaceholderText("Analysis summary will appear here.")
            try:
                self.txt_chat.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                fstable = QFont();
                fstable.setPointSize(12)
                self.txt_chat.setFont(fstable)
                self.txt_chat.anchorClicked.connect(self.handle_anchor_clicked)
            except Exception:
                ...
            res_layout.addWidget(self.txt_chat, 1)
            self.grp_results.setLayout(res_layout)

            # Layout order
            main_splitter = QSplitter(Qt.Orientation.Vertical)
            main_splitter.addWidget(top_split)
            main_splitter.addWidget(self.grp_queue_logs)
            main_splitter.addWidget(self.grp_results)
            main_splitter.setStretchFactor(0, 0)  # Do not stretch top panel
            main_splitter.setStretchFactor(1, 1)  # Stretch logs/queue
            main_splitter.setStretchFactor(2, 2)  # Stretch analysis window more

            vmain.addWidget(main_splitter)
            vmain.addWidget(self.progress_bar, 0)

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
            vmain.addLayout(input_row_bottom)

            try:
                self.grp_queue_logs.setStyleSheet(self.grp_queue_logs.styleSheet() + " QGroupBox::title { padding-top: 6px; }")
                self.grp_queue_logs.raise_()
                self.grp_results.raise_()
            except Exception:
                ...

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
                self.lbl_lm1 = QLabel(" LM A: n/a ")
                self.lbl_lm1.setStyleSheet("background:#6b7280; color:#fff; padding:3px 8px; border-radius:12px;")
                self.lbl_lm2 = QLabel(" LM B: disabled ")
                self.lbl_lm2.setStyleSheet("background:#6b7280; color:#fff; padding:3px 8px; border-radius:12px;")
                sb.addPermanentWidget(self.lbl_brand)
                sb.addPermanentWidget(self.lbl_lm1)
                sb.addPermanentWidget(self.lbl_lm2)
                sb.addPermanentWidget(self.lbl_err)
            except Exception:
                ...

            # Init
            try:
                self._current_report_path = None
                self.lbl_report_name.setText("(No report selected)")
                self.refresh_llm_indicator()
                self.refresh_recent_files()
            except Exception:
                ...

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

            chk_llm_a = QCheckBox("Enable Primary LLM (Model A)")
            chk_llm_a.setChecked(get_bool_setting("llm_a_enabled", False))
            vbox.addWidget(chk_llm_a)

            chk_llm_b = QCheckBox("Enable Secondary LLM (Model B)")
            chk_llm_b.setChecked(get_bool_setting("llm_b_enabled", False))
            vbox.addWidget(chk_llm_b)

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
                set_bool_setting("llm_a_enabled", chk_llm_a.isChecked())
                set_bool_setting("llm_b_enabled", chk_llm_b.isChecked())
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
                QMessageBox.information(self, "Analyze", "Please upload/select a report first.")
                return
            try:
                self.btn_analyze_all.setDisabled(True)
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                self.statusBar().showMessage("Analyzing...")

                self._progress_start("Analyzing...")

                def _cb(p, m):
                    self._progress_update(p, m)

                def _cancel():
                    return self._progress_was_canceled()

                res = run_analyzer(self._current_report_path, progress_cb=_cb, cancel_cb=_cancel)

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

        def action_analyze_batch(self):
            try:
                n = self.list_folder_files.count()
                if n == 0:
                    QMessageBox.information(self, "Analyze Batch", "Please upload a folder with documents first.")
                    return
                reply = QMessageBox.question(self, "Analyze Batch",
                                             f"Process {n} file(s) sequentially?")  # type: ignore
                if not str(reply).lower().endswith("yes"):
                    return
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

                        res = run_analyzer(path, progress_cb=_cb, cancel_cb=_cancel)
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

        def render_analysis_to_results(self, data: dict, highlight_range: Optional[Tuple[int, int]] = None) -> None:
            try:
                self.current_report_data = data

                file_name = os.path.basename(data.get("file", "Unknown File"))
                report_html = f"<h1>Analysis for: {file_name}</h1>"

                # Re-generate the narrative from structured data to ensure consistency
                narrative_lines = []
                narrative_lines.extend(_generate_risk_dashboard(data['compliance']['score'], data['sev_counts']))
                narrative_lines.extend(_generate_compliance_checklist(data['strengths'], data['weaknesses']))

                narrative_lines.append("--- Detailed Findings ---")
                issues = data.get("issues", [])
                if issues:
                    for issue in issues:
                        loc = issue.get('location')
                        link = f"<a href='highlight:{loc['start']}:{loc['end']}'>Show in text</a>" if loc else "(location not found)"

                        sev = str(issue.get("severity", "")).title()
                        cat = issue.get("category", "") or "General"
                        title = issue.get("title", "") or "Finding"
                        narrative_lines.append(f"<b>[{sev}][{cat}] {title}</b>")

                        details = issue.get("details", {}) # Assuming details are now nested
                        if 'action' in details: narrative_lines.append(f"  - Recommended Action: {details['action']}")
                        if 'why' in details: narrative_lines.append(f"  - Why it matters: {details['why']}")
                        if 'good_example' in details: narrative_lines.append(f"  - Good Example: {details['good_example']}")
                        if 'bad_example' in details: narrative_lines.append(f"  - Bad Example: {details['bad_example']}")

                        narrative_lines.append(f"  - {link}")
                        narrative_lines.append("") # Spacer
                else:
                    narrative_lines.append("No specific audit findings were identified.")

                report_html += "<br>".join(narrative_lines)

                # Full Text
                report_html += "<hr><h2>Full Note Text</h2>"
                full_text = "\n".join(s[0] for s in data.get('source_sentences', []))

                if highlight_range:
                    start, end = highlight_range
                    pre_text = html.escape(full_text[:start])
                    highlighted_text = html.escape(full_text[start:end])
                    post_text = html.escape(full_text[end:])

                    full_text_html = (f"{pre_text.replace('\n', '<br>')}"
                                      f"<span style='background-color: yellow;'>{highlighted_text.replace('\n', '<br>')}</span>"
                                      f"{post_text.replace('\n', '<br>')}")
                else:
                    full_text_html = html.escape(full_text).replace('\n', '<br>')

                report_html += f"<div style='font-family: monospace; white-space: pre-wrap; background: #eee; padding: 10px; border-radius: 5px;'>{full_text_html}</div>"

                self.txt_chat.setHtml(report_html)

                if highlight_range:
                    cursor = self.txt_chat.textCursor()
                    doc = self.txt_chat.document()
                    # A trick to find the position of the span
                    cursor = doc.find("<span", cursor)
                    self.txt_chat.setTextCursor(cursor)
                    self.txt_chat.ensureCursorVisible()

            except Exception as e:
                self.log(f"Failed to render analysis results: {e}")
                logger.exception("Render analysis failed")

        def handle_anchor_clicked(self, url):
            url_str = url.toString()
            if url_str.startswith("highlight:"):
                parts = url_str.split(':')
                if len(parts) == 3:
                    try:
                        start = int(parts[1])
                        end = int(parts[2])
                        if hasattr(self, 'current_report_data') and self.current_report_data:
                             self.render_analysis_to_results(self.current_report_data, highlight_range=(start, end))
                    except (ValueError, IndexError) as e:
                        self.log(f"Invalid highlight URL: {url_str} - {e}")

        def refresh_llm_indicator(self):
            try:
                llm_a_enabled = get_bool_setting("llm_a_enabled", False)
                llm_b_enabled = get_bool_setting("llm_b_enabled", False)

                self.lbl_lm1.setText(" LM A: On " if llm_a_enabled else " LM A: Off ")
                self.lbl_lm1.setStyleSheet(("background:#10b981; color:#111; padding:3px 8px; border-radius:12px;")
                                           if llm_a_enabled else "background:#6b7280; color:#fff; padding:3px 8px; border-radius:12px;")

                self.lbl_lm2.setText(" LM B: On " if llm_b_enabled else " LM B: Off ")
                self.lbl_lm2.setStyleSheet(("background:#10b981; color:#111; padding:3px 8px; border-radius:12px;")
                                           if llm_b_enabled else "background:#6b7280; color:#fff; padding:3px 8px; border-radius:12px;")
            except Exception:
                ...

        def action_export_fhir(self):
            last_json = get_setting("last_report_json")
            if not last_json or not os.path.isfile(last_json):
                QMessageBox.warning(self, "FHIR Export", "Please run an analysis first.")
                return

            base_name = os.path.basename(last_json).replace('.json', '')
            default_fhir_path = os.path.join(os.path.dirname(last_json), f"{base_name}-fhir.json")

            fhir_path, _ = QFileDialog.getSaveFileName(self, "Save FHIR Report", default_fhir_path, "JSON Files (*.json)")
            if not fhir_path:
                return

            try:
                import json
                with open(last_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # The export function is outside the class
                if export_report_fhir_json(data, fhir_path):
                    self.log(f"FHIR report exported successfully to: {fhir_path}")
                    QMessageBox.information(self, "FHIR Export", f"Successfully exported to:\n{fhir_path}")
                else:
                    raise ReportExportError("FHIR export function returned False.")
            except Exception as e:
                logger.error(f"FHIR export failed: {e}")
                self.set_error(str(e))
                QMessageBox.critical(self, "Error", f"Failed to export FHIR report:\n{e}")

        def action_send(self):
            q = self.input_query_te.toPlainText().strip() if hasattr(self, "input_query_te") else ""
            if not q:
                return
            try:
                last_json = get_setting("last_report_json")
                if not last_json or not os.path.isfile(last_json):
                    self.txt_chat.append("No analysis context available. Analyze a file first.\n")
                    return
                import json
                with open(last_json, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Search the original document sentences, not the narrative summary
                sentences = data.get("source_sentences", [])
                if not sentences:
                    self.txt_chat.append("No document text available to search. Please analyze a file first.\n")
                    return

                # The sentences are stored as [text, source] pairs. We search the text.
                lines = [item[0] for item in sentences if isinstance(item, list) and len(item) > 0]

                ql = q.lower()
                search_terms = set(re.findall(r"[a-z0-9]{3,}", ql))

                hits = []
                if search_terms:
                    for line in lines:
                        line_lower = line.lower()
                        if any(term in line_lower for term in search_terms):
                            hits.append(line.strip())

                ans = "\n".join(hits[:5]) if hits else "(No specific passages found. Try rephrasing.)"
                self.txt_chat.append(f"User:\n{q}\n\nAnswer:\n{ans}\n")
                self.input_query_te.setPlainText("")
            except Exception as e:
                self.set_error(str(e))

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
