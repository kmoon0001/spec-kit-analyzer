# Python
from __future__ import annotations

# Standard library
import logging
import os
import sys
from typing import Optional, Tuple
from urllib.parse import quote, unquote
import json

# Third-party
from PyQt6.QtWidgets import (
    QMainWindow, QToolBar, QLabel, QFileDialog, QMessageBox, QApplication,
    QVBoxLayout, QHBoxLayout, QLineEdit, QWidget,
    QStatusBar, QTabWidget, QGridLayout, QInputDialog, QPushButton
)
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal as Signal, QObject
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
import numpy as np


# Local imports
from .database import (
    get_int_setting, get_str_setting, add_recent_file,
    get_setting, set_setting, ensure_reports_dir_configured
)
from .utils import (
    _open_path
)
from .reporting import (
    export_analytics_csv
)
from .analyzer import run_analyzer
from .ui.settings_dialog import show_settings_dialog
from .local_llm import LocalRAG
from .guideline_service import GuidelineService
from .rubric_service import ComplianceRule


logger = logging.getLogger(__name__)

class LLMWorker(QObject):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, model_repo_id: str, model_filename: str):
        super().__init__()
        self.model_repo_id = model_repo_id
        self.model_filename = model_filename

    def run(self):
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
            logger.exception(f"LLMWorker failed to load model: {e}")
            self.error.emit(f"Failed to load AI model: {e}")

class GuidelineWorker(QObject):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, rag_instance: LocalRAG):
        super().__init__()
        self.rag_instance = rag_instance

    def run(self):
        try:
            guideline_service = GuidelineService(self.rag_instance)
            sources = [
                "https://www.cms.gov/files/document/r12532bp.pdf",
                "test_data/static_guidelines.txt"
            ]
            guideline_service.load_and_index_guidelines(sources)
            if guideline_service.is_index_ready():
                self.finished.emit(guideline_service)
            else:
                self.error.emit("Guideline index failed to build.")
        except Exception as e:
            logger.exception(f"GuidelineWorker failed: {e}")
            self.error.emit(f"Failed to load guidelines: {e}")

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spec Kit Analyzer")
        self.setMinimumSize(1100, 780)
        self._current_report_path: Optional[str] = None
        self._last_error: Optional[str] = None
        self._batch_cancel = False
        self.current_report_data: Optional[dict] = None
        self.local_rag: Optional[LocalRAG] = None
        self.guideline_service: Optional[GuidelineService] = None
        self.chat_history: list[tuple[str, str]] = []
        self.compliance_rules: list[ComplianceRule] = []

        self._setup_ui()
        self._init_llm_thread()

    def _setup_ui(self):
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_status_bar()

    def _setup_toolbar(self):
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)
        actions = {"Open File...": self.action_open_report, "Analyze": self.action_analyze_combined, "Open Logs Folder": self.action_open_logs,
                   "Export Analytics CSV": self._export_analytics_csv, "Settings": lambda: (show_settings_dialog(self), self.reapply_theme()),
                   "Admin Settings...": self._show_admin_settings_dialog, "Exit": self.close}
        for name, func in actions.items():
            act = QAction(name, self)
            act.triggered.connect(func)
            tb.addAction(act)

    def _setup_central_widget(self):
        central = QWidget()
        self.setCentralWidget(central)
        vmain = QVBoxLayout(central)
        vmain.setContentsMargins(12, 12, 12, 12)
        vmain.setSpacing(14)
        self.tabs = QTabWidget()
        vmain.addWidget(self.tabs)
        setup_tab = QWidget()
        results_tab = QWidget()
        logs_tab = QWidget()
        analytics_tab = QWidget()
        self.tabs.addTab(setup_tab, "Setup & File Queue")
        self.tabs.addTab(results_tab, "Analysis Results")
        self.tabs.addTab(logs_tab, "Application Logs")
        self.tabs.addTab(analytics_tab, "Analytics Dashboard")
        self._setup_analytics_tab(analytics_tab)
        self._setup_setup_tab(setup_tab)
        self._setup_results_tab(results_tab)
        self._setup_logs_tab(logs_tab)
        vmain.addWidget(self.tabs)

    def _setup_analytics_tab(self, tab):
        layout = QVBoxLayout(tab)
        controls = QHBoxLayout()
        btn_refresh = QPushButton("Refresh Analytics")
        btn_refresh.clicked.connect(self._update_analytics_tab)
        controls.addWidget(btn_refresh)
        controls.addStretch(1)
        layout.addLayout(controls)
        self.analytics_figure = Figure(figsize=(5, 3))
        self.analytics_canvas = FigureCanvas(self.analytics_figure)
        layout.addWidget(self.analytics_canvas)
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
        layout.addWidget(stats_group)

    def _setup_setup_tab(self, tab):
        layout = QVBoxLayout(tab)
        top_layout = QHBoxLayout()
        layout.addLayout(top_layout)
        rubric_panel = QGroupBox("Rubric")
        rubric_layout = QVBoxLayout(rubric_panel)
        top_layout.addWidget(rubric_panel)
        report_panel = QGroupBox("File Selection")
        report_layout = QVBoxLayout(report_panel)
        top_layout.addWidget(report_panel)
        queue_group = QGroupBox("File Queue (for batch analysis)")
        queue_layout = QVBoxLayout(queue_group)
        layout.addWidget(queue_group)

    def _setup_results_tab(self, tab):
        layout = QVBoxLayout(tab)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.txt_chat = QTextEdit()
        self.txt_chat.setReadOnly(True)
        splitter.addWidget(self.txt_chat)
        self.txt_full_note = QTextEdit()
        self.txt_full_note.setReadOnly(True)
        splitter.addWidget(self.txt_full_note)
        layout.addWidget(splitter)

    def _setup_logs_tab(self, tab):
        layout = QVBoxLayout(tab)
        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        layout.addWidget(self.txt_logs)

    def _setup_status_bar(self):
        sb: QStatusBar = self.statusBar()
        sb.clearMessage()
        self.lbl_brand = QLabel("Pacific Coast Therapy 🏝️")
        brand_font = QFont("cursive")
        brand_font.setPointSize(12)
        self.lbl_brand.setFont(brand_font)
        self.lbl_brand.setStyleSheet("color:#93c5fd; padding-left:8px; font-weight:700;")
        self.lbl_brand.setToolTip("Kevin Moon")
        self.lbl_err = QLabel(" Status: OK ")
        self.lbl_err.setStyleSheet("background:#10b981; color:#111; padding:3px 8px; border-radius:12px;")
        self.lbl_lm1 = QLabel(" LM A: n/a ")
        self.lbl_lm1.setStyleSheet("background:#6b7280; color:#fff; padding:3px 8px; border-radius:12px;")
        self.lbl_lm2 = QLabel(" LM B: disabled ")
        self.lbl_lm2.setStyleSheet("background:#6b7280; color:#fff; padding:3px 8px; border-radius:12px;")
        self.lbl_rag_status = QLabel(" AI: Loading... ")
        self.lbl_rag_status.setStyleSheet("background:#6b7280; color:#fff; padding:3px 8px; border-radius:12px;")
        sb.addPermanentWidget(self.lbl_brand)
        sb.addPermanentWidget(self.lbl_rag_status)
        sb.addPermanentWidget(self.lbl_lm1)
        sb.addPermanentWidget(self.lbl_lm2)
        sb.addPermanentWidget(self.lbl_err)

    def _init_llm_thread(self):
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
        self.local_rag = rag_instance
        self.lbl_rag_status.setText(" AI: Ready ")
        self.lbl_rag_status.setStyleSheet("background:#10b981; color:#111; padding:3px 8px; border-radius:12px;")
        self.log("Local RAG AI is ready.")
        self.llm_thread.quit()

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
        self.guideline_service = guideline_service
        self.log("Compliance guidelines loaded and indexed successfully.")
        self.guideline_thread.quit()

    def _on_guideline_load_error(self, error_message: str):
        self.guideline_service = None
        self.log(f"Error loading guidelines: {error_message}")
        self.guideline_thread.quit()

    def _on_rag_load_error(self, error_message: str):
        self.local_rag = None
        self.lbl_rag_status.setText(" AI: Error ")
        self.lbl_rag_status.setStyleSheet("background:#ef4444; color:#fff; padding:3px 8px; border-radius:12px;")
        self.log(f"Error loading RAG AI: {error_message}")
        self.llm_thread.quit()

    def log(self, msg: str):
        try:
            self.txt_logs.append(msg)
        except AttributeError:
            pass

    def reapply_theme(self):
        try:
            app = QApplication.instance()
            # apply_theme(app)
            self.update()
        except Exception:
            pass

    def action_open_report(self):
        try:
            path, _ = QFileDialog.getOpenFileName(self, "Select a document to analyze", "", "All Files (*);;PDF (*.pdf);;Word (*.docx);;CSV (*.csv);;Excel (*.xlsx *.xls);;Images (*.png *.jpg *.jpeg *.bmp *.tiff)")
            if not path:
                return
            self._current_report_path = path
            add_recent_file(path)
        except Exception as e:
            self.log(f"Error opening file: {e}")

    def action_analyze_combined(self):
        if self._current_report_path:
            self.action_analyze()
        else:
            QMessageBox.information(self, "Analyze", "Please select a file or folder first.")

    def action_analyze(self):
        if not self._current_report_path:
            QMessageBox.information(self, "Analyze", "Please select a report first.")
            return

        try:
            selected_disciplines = [] # logic to get from checkboxes
            res = run_analyzer(
                self._current_report_path,
                selected_disciplines=selected_disciplines,
                guideline_service=self.guideline_service
            )
            # ... process results
        except Exception as e:
            self.log(f"Error during analysis: {e}")
            QMessageBox.critical(self, "Analysis Error", f"An unexpected error occurred during analysis:\n{e}")


    def _export_analytics_csv(self):
        try:
            dest = os.path.join(ensure_reports_dir_configured(), "SpecKit-Analytics.csv")
            if export_analytics_csv(dest):
                _open_path(dest)
                self.log(f"Exported analytics CSV: {dest}")
            else:
                QMessageBox.information(self, "Analytics", "No analytics available yet.")
        except Exception as e:
            self.log(f"Error exporting analytics: {e}")

    def _show_admin_settings_dialog(self):
        try:
            password, ok = QInputDialog.getText(self, "Admin Access", "Enter Admin Password:", QLineEdit.EchoMode.Password)
            if not ok or password != get_str_setting("admin_password", "admin123"):
                QMessageBox.warning(self, "Admin Access", "Incorrect password.")
                return
            # ... show admin dialog
        except Exception as e:
            self.log(f"Error showing admin settings: {e}")

    def _update_analytics_tab(self):
        pass

    def action_open_logs(self):
        try:
            LOGS_DIR = os.path.join(os.path.expanduser("~"), "Documents", "SpecKitData", "logs")
            _open_path(LOGS_DIR)
        except Exception as e:
            self.log(f"Error opening logs: {e}")

def _run_gui() -> Optional[int]:
    try:
        app = QApplication.instance() or QApplication(sys.argv)
        from datetime import date, timedelta
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
            if date.today() > first_run_date + timedelta(days=trial_duration_days):
                QMessageBox.critical(None, "Trial Expired", f"Your trial period of {trial_duration_days} days has expired.\nPlease contact the administrator to continue using the application.")
                return 0

        win = MainWindow()
        win.show()
        return app.exec()
    except SystemExit:
        pass
    except Exception as e:
        logger.exception("GUI failed to run")
        QMessageBox.critical(None, "Application Error", f"A critical error occurred:\n{e}")
        return 1

if __name__ == "__main__":
    try:
        code = _run_gui()
        sys.exit(code if code is not None else 0)
    except Exception as e:
        logger.exception("GUI failed")
        sys.exit(1)
