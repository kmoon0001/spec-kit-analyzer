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
REPORT_TEMPLATE_VERSION = "v2.1"

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
    pdfplumber = None
    logger.warning(f"pdfplumber unavailable: {e}")

try:
    import pytesseract
except Exception as e:
    pytesseract = None
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
    Image = None
    class UnidentifiedImageError(Exception): ...
    logger.warning(f"PIL unavailable: {e}")

try:
    import numpy as np
except ImportError:
    np = None
    logger.warning("Numpy unavailable. Some analytics features will be disabled.")

try:
    import shap
except ImportError:
    shap = None
    logger.warning("SHAP library not found. Explanation features will be disabled.")

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
        QProgressDialog, QSizePolicy, QStatusBar, QProgressBar, QMenu, QTabWidget, QGridLayout
    )
    from PyQt6.QtGui import QAction, QFont, QTextDocument, QPdfWriter, QColor, QTextCharFormat
    from PyQt6.QtCore import Qt, QThread, pyqtSignal as Signal, QObject

    # Matplotlib for analytics chart
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure

    # Local imports
    from .local_llm import LocalRAG
    from .rubric_service import RubricService, ComplianceRule
    from .guideline_service import GuidelineService

except Exception:
    # Dummy classes for headless operation
    class QObject: ...
    class QMainWindow: ...
    class QDialog: ...
    class QWidget: ...
    # Add other dummy classes as needed to avoid crashing on import
    class QApplication:
        def __init__(self, *args, **kwargs): ...
        @staticmethod
        def instance(): return None
    class Signal:
        def emit(self, *args, **kwargs): ...

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

    # Prioritize flags, then wobblers
    sorted_issues = sorted(issues, key=lambda x: ({"flag": 0, "wobbler": 1}.get(x.get('severity'), 2)))

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

# ... (All helper functions like _ensure_directories, _get_db_connection, etc. are assumed to be here)
# --- PDF Charting Helpers ---

def _create_gauge_chart(score: float, theme: str):
    """Creates a matplotlib gauge chart for the compliance score."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Wedge, Circle
    import io

    fig, ax = plt.subplots(figsize=(2.5, 1.25), dpi=150, subplot_kw={'aspect': 'equal'})

    if theme == 'light':
        fig.patch.set_facecolor('#ffffff')
        text_color = '#111827'
    else:
        fig.patch.set_facecolor('#2b2b2b')
        text_color = '#e5e7eb'

    # Draw the gauge background
    wedge_red = Wedge(center=(0.5, 0.3), r=0.4, theta1=180, theta2=180 * (1 - 0.6), facecolor='#ef4444', width=0.1)
    ax.add_patch(wedge_red)
    wedge_yellow = Wedge(center=(0.5, 0.3), r=0.4, theta1=180 * (1 - 0.85), theta2=180 * (1 - 0.6), facecolor='#f59e0b', width=0.1)
    ax.add_patch(wedge_yellow)
    wedge_green = Wedge(center=(0.5, 0.3), r=0.4, theta1=0, theta2=180 * (1 - 0.85), facecolor='#10b981', width=0.1)
    ax.add_patch(wedge_green)

    angle = 180 * (1 - score / 100)
    needle_len = 0.3
    x_end = 0.5 - needle_len * np.cos(np.radians(angle))
    y_end = 0.3 + needle_len * np.sin(np.radians(angle))
    ax.arrow(0.5, 0.3, x_end - 0.5, y_end - 0.3, width=0.01, head_width=0.03, head_length=0.03, fc=text_color, ec=text_color)

    ax.text(0.5, 0.4, f'{score:.1f}', horizontalalignment='center', verticalalignment='center', fontsize=16, fontweight='bold', color=text_color)
    ax.text(0.5, 0.15, 'Compliance Score', horizontalalignment='center', verticalalignment='center', fontsize=6, color=text_color)

    center_circle = Circle((0.5, 0.3), 0.02, facecolor=text_color)
    ax.add_patch(center_circle)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 0.7)
    ax.axis('off')

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.05, transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf

def _create_trendline_chart(trends: dict, theme: str):
    """Creates a matplotlib trendline chart for recent scores."""
    import matplotlib.pyplot as plt
    import io

    scores = trends.get("recent_scores", [])
    if len(scores) < 2:
        return None

    fig, ax = plt.subplots(figsize=(2.5, 1.25), dpi=150)

    if theme == 'light':
        fig.patch.set_facecolor('#ffffff')
        ax.set_facecolor('#f9fafb')
        text_color, grid_color, line_color, trend_color = '#111827', '#d1d5db', '#3b82f6', '#ef4444'
    else:
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#374151')
        text_color, grid_color, line_color, trend_color = '#e5e7eb', '#4b5563', '#60a5fa', '#f87171'

    ax.plot(scores, marker='o', linestyle='-', color=line_color, label='Score', markersize=4)

    if np:
        x = np.arange(len(scores))
        try:
            z = np.polyfit(x, scores, 1)
            p = np.poly1d(z)
            ax.plot(x, p(x), "--", color=trend_color, label='Trend')
        except Exception: pass

    ax.set_title("Recent Score Trend", color=text_color, fontsize=8)
    ax.tick_params(axis='x', colors=text_color, labelsize=6)
    ax.tick_params(axis='y', colors=text_color, labelsize=6)
    for spine in ax.spines.values(): spine.set_color(grid_color)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, color=grid_color)
    ax.legend(fontsize=6)
    fig.tight_layout(pad=0.5)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf

# --- Exports ---
def export_report_pdf(lines: list[str], pdf_path: str, meta: Optional[dict] = None,
                      sev_counts: Optional[dict] = None, cat_counts: Optional[dict] = None,
                      trends: Optional[dict] = None) -> bool:
    try:
        doc = QTextDocument()
        doc.setDocumentMargin(36) # 0.5 inch

        theme = (get_str_setting("pdf_chart_theme", "dark") or "dark").lower()

        # Build HTML content
        html_parts = [f"<html><head><style>{REPORT_STYLESHEET}</style></head><body>"]

        # Header
        html_parts.append(f"<h1>Compliance Analysis Report</h1>")
        html_parts.append(f"<p><b>File:</b> {meta.get('file_name', 'N/A')}<br/>")
        html_parts.append(f"<b>Analyzed On:</b> {meta.get('run_time', 'N/A')}</p><hr/>")

        # --- Visual Dashboard Section ---
        html_parts.append("<table width='100%'><tr>")

        # Gauge Chart
        if meta.get('compliance_score') is not None:
            gauge_img_buf = _create_gauge_chart(meta['compliance_score'], theme)
            gauge_img_b64 = base64.b64encode(gauge_img_buf.read()).decode('utf-8')
            html_parts.append(f"<td width='33%' style='vertical-align: top;'><img src='data:image/png;base64,{gauge_img_b64}'/></td>")

        # Trendline Chart
        if trends:
            trend_img_buf = _create_trendline_chart(trends, theme)
            if trend_img_buf:
                trend_img_b64 = base64.b64encode(trend_img_buf.read()).decode('utf-8')
                html_parts.append(f"<td width='33%' style='vertical-align: top;'><img src='data:image/png;base64,{trend_img_b64}'/></td>")

        # Findings Summary (Bar chart)
        if sev_counts:
            # Simple HTML bar chart as an alternative to matplotlib for this one
            html_parts.append("<td width='33%' style='vertical-align: top;'><h3>Findings by Severity</h3>")
            total_findings = sum(sev_counts.values())
            for sev, count in sev_counts.items():
                if count > 0:
                    perc = (count / total_findings) * 100 if total_findings > 0 else 0
                    color = {"flag": "#ef4444", "wobbler": "#f59e0b", "suggestion": "#10b981"}.get(sev, "#6b7280")
                    html_parts.append(f"<div style='font-size: 8pt;'>{sev.title()} ({count})</div>")
                    html_parts.append(f"<div style='background: #e5e7eb; border-radius: 3px;'><div style='width: {perc}%; background: {color}; height: 12px; border-radius: 3px;'></div></div>")
            html_parts.append("</td>")

        html_parts.append("</tr></table><hr/>")

        # Add text content
        # This is a bit of a hack to get the HTML from the narrative lines
        narrative_html = "\n".join(lines).replace("\n", "<br>")
        html_parts.append(narrative_html)

        html_parts.append("</body></html>")
        doc.setHtml("".join(html_parts))

        writer = QPdfWriter(pdf_path)
        writer.setPageSize(QPdfWriter.PageSize.A4)
        doc.print_(writer)
        return True
    except Exception as e:
        logger.error(f"Failed to export PDF: {e}")
        return False
# ... (The rest of the file, including run_analyzer and the MainWindow class, is assumed to be here, correctly merged)
# ...
if __name__ == "__main__":
    try:
        code = _run_gui()
        sys.exit(code if code is not None else 0)
    except Exception:
        logger.exception("GUI failed")
        sys.exit(1)
