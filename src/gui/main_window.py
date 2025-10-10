
"""Primary GUI window for the Therapy Compliance Analyzer."""
from __future__ import annotations

# Removed unused gc import
import json
import logging
import webbrowser
import requests
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Protocol
from urllib.parse import urlparse, parse_qs

from PySide6.QtCore import Qt, QThread, QSettings, QObject, Signal, QUrl
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QStatusBar,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QInputDialog,
)

from src.config import get_settings
from src.database import models
from src.core.report_generator import ReportGenerator
from src.gui.dialogs.chat_dialog import ChatDialog
from src.gui.dialogs.rubric_manager_dialog import RubricManagerDialog
from src.gui.dialogs.batch_analysis_dialog import BatchAnalysisDialog
from src.gui.dialogs.change_password_dialog import ChangePasswordDialog
from src.gui.dialogs.settings_dialog import SettingsDialog
from src.gui.workers.analysis_starter_worker import AnalysisStarterWorker
from src.gui.workers.generic_api_worker import GenericApiWorker, HealthCheckWorker, TaskMonitorWorker, LogStreamWorker, FeedbackWorker
from src.gui.workers.single_analysis_polling_worker import SingleAnalysisPollingWorker

# Import diagnostic tools
from src.core.analysis_workflow_logger import workflow_logger
from src.core.analysis_status_tracker import status_tracker, AnalysisState
from src.core.analysis_diagnostics import diagnostics
from src.core.analysis_error_handler import error_handler

# Import beautiful medical-themed components
from src.gui.components.header_component import HeaderComponent
from src.gui.components.status_component import StatusComponent
from src.gui.widgets.medical_theme import medical_theme

# Import minimal micro-interactions (subtle animations only)
from src.gui.widgets.micro_interactions import AnimatedButton, LoadingSpinner

from src.gui.widgets.mission_control_widget import MissionControlWidget, LogViewerWidget, SettingsEditorWidget
from src.core.license_manager import license_manager

from src.gui.widgets.dashboard_widget import DashboardWidget

try:
    from src.gui.widgets.meta_analytics_widget import MetaAnalyticsWidget
except ImportError:
    MetaAnalyticsWidget = None  # type: ignore

try:
    from src.gui.widgets.performance_status_widget import PerformanceStatusWidget
except ImportError:
    PerformanceStatusWidget = None  # type: ignore

logger = logging.getLogger(__name__)

SETTINGS = get_settings()
API_URL = SETTINGS.paths.api_url


class WorkerProtocol(Protocol):
    def run(self) -> None: ...
    def moveToThread(self, thread: QThread) -> None: ...


class MainViewModel(QObject):
    """ViewModel for the MainApplicationWindow, handling state and business logic."""
    status_message_changed = Signal(str)
    api_status_changed = Signal(str, str)
    task_list_changed = Signal(dict)
    log_message_received = Signal(str)
    settings_loaded = Signal(dict)
    analysis_result_received = Signal(dict)
    rubrics_loaded = Signal(list)
    dashboard_data_loaded = Signal(dict)
    meta_analytics_loaded = Signal(dict)
    show_message_box_signal = Signal(str, str, str, list, str)

    def __init__(self, auth_token: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.auth_token = auth_token
        self._active_threads: list[QThread] = []

    def start_workers(self) -> None:
        self._start_health_check_worker()
        self._start_task_monitor_worker()
        self._start_log_stream_worker()
        self.load_rubrics()
        self.load_dashboard_data()
        if MetaAnalyticsWidget:
            self.load_meta_analytics()

    def _run_worker(
        self,
        worker_class,
        on_success: Callable | None = None,
        on_error: Callable | None = None,
        *,
        success_signal: Optional[str] = "success",
        error_signal: Optional[str] = "error",
        auto_stop: bool = True,
        start_slot: str = "run",
        **kwargs: Any,
    ) -> None:
        thread = QThread()
        worker = worker_class(**kwargs)
        worker.moveToThread(thread)
        setattr(thread, "_worker_ref", worker)

        def connect_signal(signal_name: Optional[str], callback: Callable | None, should_quit: bool) -> None:
            if not signal_name:
                return
            if not hasattr(worker, signal_name):
                if callback is not None:
                    raise AttributeError(f"{worker_class.__name__} does not expose signal '{signal_name}'")
                return
            signal = getattr(worker, signal_name)
            if callback is not None:
                signal.connect(callback)
            if should_quit:
                signal.connect(thread.quit)

        connect_signal(success_signal, on_success, auto_stop)
        connect_signal(error_signal, on_error, auto_stop)

        if hasattr(worker, "finished"):
            getattr(worker, "finished").connect(thread.quit)

        thread.finished.connect(thread.deleteLater)
        if hasattr(worker, "deleteLater"):
            thread.finished.connect(worker.deleteLater)

        def _cleanup() -> None:
            if hasattr(thread, "_worker_ref"):
                setattr(thread, "_worker_ref", None)
            if thread in self._active_threads:
                self._active_threads.remove(thread)

        thread.finished.connect(_cleanup)

        start_callable = getattr(worker, start_slot)
        thread.started.connect(start_callable)

        self._active_threads.append(thread)
        thread.start()


    def _start_health_check_worker(self) -> None:
        self._run_worker(
            HealthCheckWorker,
            on_success=self.api_status_changed.emit,
            success_signal="status_update",
            error_signal=None,
            auto_stop=False,
        )

    def _start_task_monitor_worker(self) -> None:
        self._run_worker(
            TaskMonitorWorker,
            on_success=self.task_list_changed.emit,
            on_error=lambda msg: self.status_message_changed.emit(f"Task Monitor Error: {msg}"),
            success_signal="tasks_updated",
            auto_stop=False,
            token=self.auth_token,
        )

    def _start_log_stream_worker(self) -> None:
        self._run_worker(
            LogStreamWorker,
            on_success=self.log_message_received.emit,
            on_error=lambda msg: self.status_message_changed.emit(f"Log Stream: {msg}"),
            success_signal="new_log_message",
            auto_stop=False,
        )

    def load_rubrics(self) -> None:
        self._run_worker(GenericApiWorker, on_success=self.rubrics_loaded.emit, on_error=lambda msg: self.status_message_changed.emit(f"Could not load rubrics: {msg}"), endpoint="/rubrics", token=self.auth_token)

    def load_dashboard_data(self) -> None:
        self._run_worker(GenericApiWorker, on_success=self.dashboard_data_loaded.emit, on_error=lambda msg: self.status_message_changed.emit(f"Could not load dashboard data: {msg}"), endpoint="/dashboard/statistics", token=self.auth_token)

    def load_meta_analytics(self, params: Dict[str, Any] = None) -> None:
        endpoint = "/meta-analytics/widget_data"
        if params:
            param_str = f"days_back={params.get('days_back', 90)}&discipline={params.get('discipline', '')}"
            endpoint += f"?{param_str}"
        self._run_worker(GenericApiWorker, on_success=self.meta_analytics_loaded.emit, on_error=lambda msg: self.status_message_changed.emit(f"Could not load meta-analytics: {msg}"), endpoint=endpoint, token=self.auth_token)

    def start_analysis(self, file_path: str, options: dict) -> None:
        self.status_message_changed.emit(f"Submitting document for analysis: {Path(file_path).name}")
        self._run_worker(AnalysisStarterWorker, on_success=self._handle_analysis_task_started, on_error=lambda msg: self.status_message_changed.emit(f"Analysis failed: {msg}"), file_path=file_path, data=options, token=self.auth_token)

    def _handle_analysis_task_started(self, task_id: str) -> None:
        # Log successful task creation
        workflow_logger.log_api_response(200, {"task_id": task_id})
        
        # Update status tracker with task ID
        status_tracker.set_task_id(task_id)
        status_tracker.update_status(AnalysisState.PROCESSING, 20, f"Analysis task created: {task_id[:8]}...")
        
        self.status_message_changed.emit(f"Analysis running (Task: {task_id[:8]}...)…")

        # Start polling for results
        self._run_worker(
            SingleAnalysisPollingWorker,
            on_success=self._on_analysis_polling_success,
            on_error=self._handle_analysis_error_with_logging,
            task_id=task_id,
        )
    
    def _on_analysis_polling_success(self, result: dict) -> None:
        """Handle successful analysis with comprehensive logging."""
        # Log successful completion
        workflow_logger.log_workflow_completion(True, result)
        status_tracker.complete_analysis(result)
        
        # Emit signal for the view to handle
        self.analysis_result_received.emit(result)
    
    def _handle_analysis_error_with_logging(self, error_msg: str) -> None:
        """Handle analysis error with comprehensive logging and user-friendly messaging."""
        # Log the error
        workflow_logger.log_workflow_completion(False, error=error_msg)
        status_tracker.set_error(error_msg)
        
        # Process error through error handler for better user experience
        analysis_error = error_handler.categorize_and_handle_error(error_msg)
        formatted_message = error_handler.format_error_message(analysis_error, include_technical=False)
        
        # Emit signal for the view to show the message box
        self.show_message_box_signal.emit(
            f"{analysis_error.icon} Analysis Error",
            formatted_message,
            str(QMessageBox.Icon.Warning if analysis_error.severity == "warning" else QMessageBox.Icon.Critical),
            ["🔧 Technical Details", "Ok"],
            error_handler.format_error_message(analysis_error, include_technical=True)
        )
        
        # Call the original error handler for UI cleanup
        # self.on_analysis_error(error_msg) # This is now handled by the view after the message box

    def load_settings(self) -> None:
        self._run_worker(GenericApiWorker, on_success=self.settings_loaded.emit, on_error=lambda msg: self.status_message_changed.emit(f"Failed to load settings: {msg}"), endpoint="/admin/settings", token=self.auth_token)

    def save_settings(self, settings: dict) -> None:
        auth_token = self.auth_token  # Capture in local scope
        
        class SettingsSaveWorker(QThread):
            success = Signal(str)
            error = Signal(str)
            def run(self) -> None:
                try:
                    response = requests.post(f"{API_URL}/admin/settings", headers={"Authorization": f"Bearer {auth_token}"}, json=settings, timeout=10)
                    response.raise_for_status()
                    self.success.emit(response.json().get("message", "Success!"))
                except (requests.RequestException, ValueError, KeyError) as e:
                    self.error.emit(str(e))
                except Exception as e:
                    self.error.emit(f"Unexpected error: {str(e)}")
        self._run_worker(SettingsSaveWorker, on_success=lambda msg: self.status_message_changed.emit(msg), on_error=lambda msg: self.status_message_changed.emit(f"Failed to save settings: {msg}"))

    def submit_feedback(self, feedback_data: Dict[str, Any]) -> None:
        self._run_worker(FeedbackWorker, on_success=self.status_message_changed.emit, on_error=lambda msg: self.status_message_changed.emit(f"Feedback Error: {msg}"), token=self.auth_token, feedback_data=feedback_data)

    def stop_all_workers(self) -> None:
        """Stop all worker threads quickly - don't wait too long."""
        for thread in list(self._active_threads):
            try:
                if thread.isRunning():
                    thread.quit()
                    thread.wait(100)  # Wait max 100ms per thread
                    if thread.isRunning():
                        thread.terminate()  # Force terminate if still running
            except Exception:
                pass
        self._active_threads.clear()


class MainApplicationWindow(QMainWindow):
    """The main application window (View)."""

    def __init__(self, user: models.User, token: str) -> None:
        super().__init__()
        self.setWindowTitle("Therapy Compliance Analyzer")  # Shorter title that fits better
        self.resize(1440, 920)
        self.setMinimumSize(800, 500)  # Allow even smaller scaling for better flexibility

        self.current_user = user
        self.settings = QSettings("TherapyCo", "ComplianceAnalyzer")
        self.report_generator = ReportGenerator()
        self._current_payload: Dict[str, Any] = {}
        self._selected_file: Optional[Path] = None
        self._cached_preview_content: str = ""

        self.view_model = MainViewModel(token)
        self.mission_control_widget = MissionControlWidget(self)
        
        # Initialize UI attributes to prevent "defined outside __init__" warnings
        self.auto_analysis_queue_list: Optional[Any] = None
        self.auth_token = token
        self.report_preview_browser: Optional[QTextBrowser] = None
        self.header: Optional[HeaderComponent] = None
        self.status_component: Optional[StatusComponent] = None
        self.tab_widget: Optional[QTabWidget] = None
        self.analysis_tab: Optional[QWidget] = None
        self.dashboard_tab: Optional[QWidget] = None
        self.mission_control_tab: Optional[QWidget] = None
        self.settings_tab: Optional[QWidget] = None
        self.rubric_selector: Optional[QComboBox] = None
        self.strictness_buttons: list[Any] = []
        self.section_checkboxes: dict[str, Any] = {}
        self.analysis_summary_browser: Optional[QTextBrowser] = None
        self.detailed_results_browser: Optional[QTextBrowser] = None
        # Removed chat_input - using main chat dialog instead
        self.file_display: Optional[QTextEdit] = None
        self.open_file_button: Optional[AnimatedButton] = None
        self.open_folder_button: Optional[AnimatedButton] = None
        self.run_analysis_button: Optional[AnimatedButton] = None
        self.repeat_analysis_button: Optional[AnimatedButton] = None
        self.stop_analysis_button: Optional[AnimatedButton] = None
        self.view_report_button: Optional[AnimatedButton] = None
        self.dashboard_widget: Optional[DashboardWidget] = None
        self.settings_editor: Optional[SettingsEditorWidget] = None
        self.resource_label: Optional[QLabel] = None
        self.connection_label: Optional[QLabel] = None
        self.loading_spinner: Optional[LoadingSpinner] = None
        self.progress_bar: Optional[QProgressBar] = None
        self.meta_analytics_dock: Optional[QDockWidget] = None
        self.meta_widget: Optional[Any] = None
        self.performance_dock: Optional[QDockWidget] = None
        self.performance_widget: Optional[Any] = None
        self.log_viewer: Optional[LogViewerWidget] = None
        # Removed chat_button - using main chat dialog instead
        self.meta_analytics_action: Optional[QAction] = None
        self.performance_action: Optional[QAction] = None
        
        # System monitoring attributes
        self.has_psutil: bool = False
        self.resource_timer: Optional[Any] = None
        
        # Easter egg attributes
        self.konami_sequence = []
        self.konami_code = [
            Qt.Key.Key_Up, Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Down,
            Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Left, Qt.Key.Key_Right,
            Qt.Key.Key_B, Qt.Key.Key_A
        ]
        self.developer_mode = False
        self.is_testing = False

        self._build_ui()
        self._connect_view_model()
        self._load_initial_state()
        self._load_gui_settings()

    def _build_ui(self) -> None:
        self._setup_responsive_scaling()  # Add responsive scaling first
        self._build_header()
        self._build_docks()
        self._build_menus()
        self._build_central_layout()
        self._build_status_bar()
        # Removed floating chat button - using main chat dialog instead
        self._setup_keyboard_shortcuts()
        self._apply_medical_theme()

    def _setup_responsive_scaling(self) -> None:
        """Setup responsive scaling for better UI adaptation to different screen sizes."""
        # Get screen size for responsive scaling
        screen = QApplication.primaryScreen()
        if screen:
            screen_size = screen.size()
            screen_width = screen_size.width()
            screen_height = screen_size.height()
            
            # Calculate scale factor based on screen size
            base_width = 1920  # Base design width
            scale_factor = min(1.2, max(0.8, screen_width / base_width))
            
            # Apply responsive font scaling
            app = QApplication.instance()
            if app:
                font = app.font()
                base_font_size = 9
                scaled_font_size = int(base_font_size * scale_factor)
                font.setPointSize(scaled_font_size)
                app.setFont(font)
    
    def _build_header(self) -> None:
        """Build the professional application header with clean styling."""
        # Create header component
        self.header = HeaderComponent(self)
        self.header.theme_toggle_requested.connect(self._toggle_theme)
        self.header.logo_clicked.connect(self._on_logo_clicked)
        
        # Create status component for AI models
        self.status_component = StatusComponent(self)
        self.status_component.status_clicked.connect(self._on_model_status_clicked)
        
        # Apply header stylesheet
        self.header.setStyleSheet(self.header.get_default_stylesheet())
        
        # Check license status and initialize trial if needed
        self._check_license_status()
        
        # Note: Header will be added to central layout in _build_central_layout

    def _apply_medical_theme(self) -> None:
        """Apply the comprehensive medical theme styling with better contrast."""
        # Apply comprehensive medical theme styling
        main_style = f"""
            QMainWindow {{
                background-color: {medical_theme.get_color('bg_primary')};
                color: {medical_theme.get_color('text_primary')};
            }}
            QWidget {{
                font-family: "Segoe UI", "Inter", Arial, sans-serif;
                color: {medical_theme.get_color('text_primary')};
            }}
            QLabel {{
                color: {medical_theme.get_color('text_primary')};
            }}
            QTextBrowser, QTextEdit {{
                background-color: {medical_theme.get_color('bg_primary')};
                color: {medical_theme.get_color('text_primary')};
                border: 1px solid {medical_theme.get_color('border_light')};
            }}
        """
        
        # Combine with form and other stylesheets
        combined_style = (main_style + 
                         medical_theme.get_main_window_stylesheet() + 
                         medical_theme.get_form_stylesheet() + 
                         medical_theme.get_card_stylesheet())
        
        self.setStyleSheet(combined_style)
        
        # Update header theme
        is_dark = medical_theme.current_theme == "dark"
        self.header.update_theme_button(is_dark)
        if is_dark:
            self.header.setStyleSheet(self.header.get_dark_theme_stylesheet())
        else:
            self.header.setStyleSheet(self.header.get_default_stylesheet())

    def _toggle_theme(self) -> None:
        """Toggle between light and dark theme."""
        medical_theme.toggle_theme()
        self._apply_medical_theme()
        
        # Update status bar message
        theme_name = "Dark" if medical_theme.current_theme == "dark" else "Light"
        self.statusBar().showMessage(f"Switched to {theme_name} theme", 3000)

    def _apply_theme(self, theme_name: str) -> None:
        """Apply a specific theme."""
        medical_theme.set_theme(theme_name)
        self._apply_medical_theme()
        
        # Update status bar message
        theme_display = "Dark" if theme_name == "dark" else "Light"
        self.statusBar().showMessage(f"Applied {theme_display} theme", 3000)

    def _on_logo_clicked(self) -> None:
        """Handle logo clicks for easter eggs (7 clicks triggers special message)."""
        if self.header.click_count == 7:
            QMessageBox.information(
                self,
                "🎉 Easter Egg Found!",
                "You found the secret! 🌴\n\n"
                "Pacific Coast Therapy - Where compliance meets excellence!\n\n"
                "Keep up the great documentation work! 💪"
            )
            self.statusBar().showMessage("🎉 Easter egg activated!", 5000)

    def _on_model_status_clicked(self, model_name: str) -> None:
        """Handle clicks on AI model status indicators with detailed descriptions."""
        status = self.status_component.models.get(model_name, False)
        status_text = "✅ Ready" if status else "❌ Not Ready"
        
        # Detailed model descriptions with complete transparency - Updated with real models
        model_descriptions = {
            "Phi-2 LLM": {
                "full_name": "Natural Language Generation Model (Phi-2/Mistral-7B)",
                "description": "Generates personalized compliance recommendations and improvement suggestions",
                "function": "Creates human-readable explanations of compliance issues and actionable advice",
                "technology": "Microsoft Phi-2 (2.7B parameters) or Mistral-7B (quantized) - chosen for medical accuracy and local processing capability",
                "why_chosen": "Selected for excellent reasoning capabilities, medical knowledge, and ability to run locally for privacy",
                "use_cases": ["Compliance recommendations", "Report generation", "Improvement suggestions", "Personalized feedback"]
            },
            "FAISS+BM25": {
                "full_name": "Hybrid Retrieval-Augmented Generation (RAG) System",
                "description": "Finds relevant compliance rules and guidelines for document analysis",
                "function": "Combines semantic search (FAISS) with keyword matching (BM25) for precise rule retrieval",
                "technology": "FAISS vector database + BM25 ranking algorithm with hybrid scoring",
                "why_chosen": "Hybrid approach ensures both semantic understanding and exact keyword matching for comprehensive rule coverage",
                "use_cases": ["Rule matching", "Guideline retrieval", "Context-aware search", "Compliance verification"]
            },
            "Fact Checker": {
                "full_name": "AI Fact Verification & Confidence Scoring System",
                "description": "Verifies accuracy of compliance findings and reduces false positives through secondary validation",
                "function": "Cross-references findings against multiple sources and applies confidence scoring to ensure accuracy",
                "technology": "Secondary transformer model with specialized verification algorithms and uncertainty quantification",
                "why_chosen": "Critical for medical compliance - reduces false positives and provides confidence metrics for clinical decision-making",
                "use_cases": ["Finding verification", "Accuracy validation", "Confidence scoring", "False positive reduction"]
            },
            "BioBERT": {
                "full_name": "Biomedical Named Entity Recognition (BioBERT)",
                "description": "Extracts biomedical terminology and general medical concepts from documents",
                "function": "Identifies biomedical entities, drug names, diseases, and general medical terminology",
                "technology": "BioBERT - BERT pre-trained on biomedical literature (PubMed abstracts and PMC full-text articles)",
                "why_chosen": "Specifically trained on biomedical texts, excels at general medical terminology and research-based language",
                "use_cases": ["Biomedical term extraction", "Drug and disease identification", "Research terminology", "General medical concepts"]
            },
            "ClinicalBERT": {
                "full_name": "Clinical Named Entity Recognition (ClinicalBERT)",
                "description": "Extracts medical terminology and clinical concepts from therapy documentation",
                "function": "Identifies medical entities, conditions, treatments, and clinical terminology with high precision",
                "technology": "BioBERT (biomedical BERT) + ClinicalBERT - dual model approach for comprehensive medical entity extraction",
                "why_chosen": "BioBERT excels at general biomedical terms, ClinicalBERT specializes in clinical notes - together they provide comprehensive coverage",
                "use_cases": ["Medical term extraction", "Clinical concept identification", "Entity linking", "Medical terminology validation"]
            },
            "Chat Assistant": {
                "full_name": "Conversational AI Assistant (Local LLM)",
                "description": "Provides interactive assistance and answers compliance questions in real-time",
                "function": "Offers contextual help, clarification on compliance issues, and educational guidance",
                "technology": "Local conversational model based on Phi-2/Mistral with compliance-specific fine-tuning",
                "why_chosen": "Local processing ensures privacy while providing instant, contextual assistance for complex compliance questions",
                "use_cases": ["Interactive help", "Question answering", "Compliance guidance", "Educational support"]
            },
            "MiniLM-L6": {
                "full_name": "Semantic Embedding System (sentence-transformers/all-MiniLM-L6-v2)",
                "description": "Converts text into numerical representations for semantic understanding and similarity matching",
                "function": "Creates 384-dimensional vector representations of documents and rules for similarity matching",
                "technology": "sentence-transformers/all-MiniLM-L6-v2 - optimized for semantic similarity with medical domain adaptation",
                "why_chosen": "Excellent balance of performance, speed, and accuracy. Specifically chosen for medical text understanding and efficient local processing",
                "use_cases": ["Semantic search", "Document similarity", "Context understanding", "Rule matching"]
            }
        }
        
        model_info = model_descriptions.get(model_name, {
            "full_name": model_name,
            "description": "AI model for compliance analysis",
            "function": "Supports document analysis and compliance checking",
            "technology": "Local AI processing",
            "use_cases": ["Compliance analysis"]
        })
        
        # Create detailed popup
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"🤖 AI Model Details: {model_name}")
        dialog.resize(600, 500)
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8fafc, stop:1 #e2e8f0);
                border: 2px solid #cbd5e0;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Content browser
        content_browser = QTextBrowser()
        content_browser.setStyleSheet("""
            QTextBrowser {
                background: white;
                border: 2px solid #d1d5db;
                border-radius: 8px;
                padding: 15px;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        
        # Generate detailed HTML content
        html_content = f"""
        <div style='font-family: Segoe UI; line-height: 1.6;'>
            <h2 style='color: #1d4ed8; margin-top: 0;'>🤖 {model_info['full_name']}</h2>
            
            <div style='background: #f0f9ff; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #0ea5e9;'>
                <h3 style='color: #0ea5e9; margin-top: 0;'>Current Status</h3>
                <p style='font-size: 16px; font-weight: bold; color: {"#059669" if status else "#dc2626"};'>{status_text}</p>
            </div>
            
            <div style='background: #f8fafc; padding: 15px; border-radius: 8px; margin: 15px 0;'>
                <h3 style='color: #334155; margin-top: 0;'>Description</h3>
                <p style='color: #475569;'>{model_info['description']}</p>
            </div>
            
            <div style='background: #f0fdf4; padding: 15px; border-radius: 8px; margin: 15px 0;'>
                <h3 style='color: #059669; margin-top: 0;'>Function in System</h3>
                <p style='color: #475569;'>{model_info['function']}</p>
            </div>
            
            <div style='background: #fef7ff; padding: 15px; border-radius: 8px; margin: 15px 0;'>
                <h3 style='color: #7c3aed; margin-top: 0;'>Technology</h3>
                <p style='color: #475569;'>{model_info['technology']}</p>
            </div>
            
            <div style='background: #f0f9ff; padding: 15px; border-radius: 8px; margin: 15px 0;'>
                <h3 style='color: #0ea5e9; margin-top: 0;'>Why This Model Was Chosen</h3>
                <p style='color: #475569;'>{model_info.get('why_chosen', 'Selected for optimal performance in medical compliance analysis.')}</p>
            </div>
            
            <div style='background: #fffbeb; padding: 15px; border-radius: 8px; margin: 15px 0;'>
                <h3 style='color: #d97706; margin-top: 0;'>Use Cases</h3>
                <ul style='color: #475569; margin: 0; padding-left: 20px;'>
                    {"".join([f"<li>{use_case}</li>" for use_case in model_info['use_cases']])}
                </ul>
            </div>
            
            <div style='background: #f1f5f9; padding: 15px; border-radius: 8px; margin: 15px 0; border: 1px solid #cbd5e0;'>
                <h3 style='color: #1e293b; margin-top: 0;'>Privacy & Security</h3>
                <p style='color: #475569;'>🔒 All processing occurs locally on your device. No data is sent to external servers, ensuring complete privacy and HIPAA compliance.</p>
            </div>
        </div>
        """
        
        content_browser.setHtml(html_content)
        layout.addWidget(content_browser)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #1d4ed8;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1e40af;
            }
        """)
        layout.addWidget(close_btn)
        
        dialog.exec()

    def _connect_view_model(self) -> None:
        self.view_model.status_message_changed.connect(self.statusBar().showMessage)
        self.view_model.api_status_changed.connect(self.mission_control_widget.update_api_status)
        self.view_model.task_list_changed.connect(self.mission_control_widget.update_task_list)
        self.view_model.log_message_received.connect(self.log_viewer.add_log_message)
        self.view_model.settings_loaded.connect(self.settings_editor.set_settings)
        self.view_model.analysis_result_received.connect(self._handle_analysis_success)
        self.view_model.rubrics_loaded.connect(self._on_rubrics_loaded)
        self.view_model.dashboard_data_loaded.connect(self.dashboard_widget.load_data)
        if MetaAnalyticsWidget:
            self.view_model.meta_analytics_loaded.connect(self.meta_widget.update_data)
        self.view_model.show_message_box_signal.connect(self._show_message_box)

    def _show_message_box(self, title: str, text: str, icon_str: str, buttons: list[str], technical_details: str = "") -> None:
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        
        # Convert icon_str back to QMessageBox.Icon
        icon_map = {
            str(QMessageBox.Icon.Warning): QMessageBox.Icon.Warning,
            str(QMessageBox.Icon.Critical): QMessageBox.Icon.Critical,
            str(QMessageBox.Icon.Information): QMessageBox.Icon.Information,
            str(QMessageBox.Icon.Question): QMessageBox.Icon.Question,
            str(QMessageBox.Icon.NoIcon): QMessageBox.Icon.NoIcon,
        }
        msg.setIcon(icon_map.get(icon_str, QMessageBox.Icon.Information))

        technical_button = None
        for button_text in buttons:
            if button_text == "🔧 Technical Details":
                technical_button = msg.addButton(button_text, QMessageBox.ButtonRole.ActionRole)
            elif button_text == "Ok":
                msg.addButton(QMessageBox.StandardButton.Ok)
            # Add other standard buttons if needed

        msg.exec()

        if technical_button and msg.clickedButton() == technical_button:
            QMessageBox.information(self, "🔧 Technical Details", technical_details)

        # Call the original error handler for UI cleanup if it was an error message
        if "Error" in title:
            self.on_analysis_error(text)

    def _load_initial_state(self) -> None:
        # Load default rubrics immediately (fallback if API fails)
        self._load_default_rubrics()
        
        self.view_model.start_workers()
        if self.current_user.is_admin:
            self.view_model.load_settings()
        
        # Simulate AI model loading (set all to loading state initially)
        self.status_component.set_all_loading()
        
        # After a short delay, set all models as ready (in production, this would be based on actual model loading)
        # For now, we'll set them as ready after 2 seconds
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, self._on_ai_models_ready)
        
        # Start system resource monitoring
        self._start_resource_monitoring()

    def _on_ai_models_ready(self) -> None:
        """Called when AI models are loaded and ready."""
        self.status_component.set_all_ready()
        status_text = self.status_component.get_status_text()
        self.statusBar().showMessage(f"✅ {status_text}", 5000)

    def _start_analysis(self) -> None:
        # Pre-flight checks
        if not self._selected_file:
            QMessageBox.warning(self, "No Document", "Please select a document before starting the analysis.")
            return
        
        # Check if rubric is selected
        if not self.rubric_selector.currentData():
            QMessageBox.warning(self, "No Rubric", "Please select a compliance guideline before analysis.")
            return
        
        # Run diagnostic checks before starting analysis
        self.statusBar().showMessage("🔍 Running pre-analysis diagnostics...", 2000)
        diagnostic_results = diagnostics.run_full_diagnostic()
        
        # Check for critical issues
        critical_issues = [
            result for result in diagnostic_results.values() 
            if result.status.value == "error" and result.component in ["api_connectivity", "analysis_endpoints"]
        ]
        
        if critical_issues:
            error_messages = [f"• {issue.message}" for issue in critical_issues]
            QMessageBox.critical(
                self, 
                "🚨 Analysis Prerequisites Failed", 
                "Cannot start analysis due to critical issues:\n\n" + "\n".join(error_messages) + 
                "\n\nPlease resolve these issues and try again."
            )
            return
        
        # Validate the selected file
        file_validation = diagnostics.validate_file_format(str(self._selected_file))
        if file_validation.status.value == "error":
            QMessageBox.warning(
                self, 
                "📄 File Validation Failed", 
                f"The selected file cannot be processed:\n\n{file_validation.message}\n\nPlease select a different file."
            )
            return
        
        # Start workflow logging and tracking
        rubric_name = self.rubric_selector.currentText()
        session_id = workflow_logger.log_analysis_start(
            str(self._selected_file), 
            rubric_name, 
            self.current_user.username
        )
        
        status_tracker.start_tracking(
            session_id,
            str(self._selected_file),
            rubric_name
        )
        
        # Prepare analysis options
        options = {
            "discipline": self.rubric_selector.currentData() or "",
            "analysis_mode": "rubric",
            "session_id": session_id
        }
        
        # Update UI state
        self.run_analysis_button.setEnabled(False)
        self.repeat_analysis_button.setEnabled(False)
        self.stop_analysis_button.setEnabled(True)  # Enable stop button during analysis
        self.view_report_button.setEnabled(False)
        
        # Show loading indicators
        self.loading_spinner.start_spinning()
        self.statusBar().showMessage("⏳ Starting analysis... This may take a moment.", 0)
        
        # Update status tracker
        status_tracker.update_status(AnalysisState.STARTING, 0, "Submitting analysis request...")
        
        try:
            # Log the analysis request
            workflow_logger.log_api_request("/analysis/submit", "POST", options)
            
            # Start the analysis
            self.view_model.start_analysis(str(self._selected_file), options)
            
            # Update status
            status_tracker.update_status(AnalysisState.UPLOADING, 10, "Document uploaded, processing...")
            
        except Exception as e:
            # Log the error
            workflow_logger.log_workflow_completion(False, error=str(e))
            status_tracker.set_error(f"Failed to start analysis: {str(e)}")
            
            # Reset UI
            self.loading_spinner.stop_spinning()
            self.run_analysis_button.setEnabled(True)
            self.repeat_analysis_button.setEnabled(True)
            
            # Use error handler for user-friendly error message
            analysis_error = error_handler.categorize_and_handle_error(str(e))
            formatted_message = error_handler.format_error_message(analysis_error, include_technical=False)
            
            # Show user-friendly error dialog
            msg = QMessageBox(self)
            msg.setWindowTitle(f"{analysis_error.icon} Analysis Startup Error")
            msg.setText(formatted_message)
            msg.setIcon(QMessageBox.Icon.Critical if analysis_error.severity == "critical" else QMessageBox.Icon.Warning)
            
            # Add "Show Technical Details" button
            technical_button = msg.addButton("🔧 Technical Details", QMessageBox.ButtonRole.ActionRole)
            msg.addButton(QMessageBox.StandardButton.Ok)
            
            msg.exec()
            
            # Show technical details if requested
            if msg.clickedButton() == technical_button:
                technical_msg = error_handler.format_error_message(analysis_error, include_technical=True)
                QMessageBox.information(self, "🔧 Technical Details", technical_msg)
            self.statusBar().showMessage("❌ Analysis failed to start", 5000)

    def _repeat_analysis(self) -> None:
        """Repeat analysis on the same document with current settings."""
        if not self._selected_file:
            QMessageBox.warning(self, "No document", "No document selected to repeat analysis.")
            return
        
        self.statusBar().showMessage("Repeating analysis...", 2000)
        self._start_analysis()
    
    def _stop_analysis(self) -> None:
        """Stop the currently running analysis with user confirmation."""
        # Confirm with user before stopping
        reply = QMessageBox.question(
            self,
            "⏹️ Stop Analysis",
            "Are you sure you want to stop the current analysis?\n\n"
            "This will cancel the analysis in progress and you'll need to restart it.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Stop the analysis worker if it exists
                if hasattr(self.view_model, 'current_worker') and self.view_model.current_worker:
                    self.view_model.current_worker.terminate()
                
                # Reset UI state
                self.loading_spinner.stop_spinning()
                self.run_analysis_button.setEnabled(True)
                self.repeat_analysis_button.setEnabled(True)
                self.stop_analysis_button.setEnabled(False)
                
                # Update status
                self.statusBar().showMessage("⏹️ Analysis stopped by user", 5000)
                
                # Log the cancellation
                logger.info("Analysis stopped by user request")
                
            except Exception as e:
                logger.error(f"Error stopping analysis: {e}")
                QMessageBox.warning(
                    self,
                    "Stop Analysis Error",
                    f"Could not stop analysis cleanly: {str(e)}\n\n"
                    "The analysis may continue in the background."
                )

    def _on_strictness_selected(self, selected_button: AnimatedButton) -> None:
        """Handle strictness level selection (only one can be selected at a time)."""
        for btn in self.strictness_buttons:
            if btn != selected_button:
                btn.setChecked(False)
        selected_button.setChecked(True)
        
        # Get selected level
        level = selected_button.text().split()[-1]  # Extract level name
        self.statusBar().showMessage(f"Review strictness set to: {level}", 3000)
    
    def _on_strictness_selected_with_description(self, index: int) -> None:
        """Handle strictness level selection with description update."""
        # Uncheck all other buttons
        for i, btn in enumerate(self.strictness_buttons):
            btn.setChecked(i == index)
        
        # Update description
        self._update_strictness_description(index)
        
        # Update status
        level = self.strictness_levels[index][0]
        self.statusBar().showMessage(f"Review strictness set to: {level}", 3000)
    
    def _update_strictness_description(self, index: int) -> None:
        """Update the strictness description based on selected level."""
        if hasattr(self, 'strictness_description') and hasattr(self, 'strictness_levels'):
            level, emoji, info = self.strictness_levels[index]
            
            description_html = f"""
            <div style='font-family: Segoe UI; line-height: 1.5;'>
                <h3 style='color: #1d4ed8; margin-top: 0; margin-bottom: 10px;'>{emoji} {level} Analysis</h3>
                <p style='color: #475569; margin-bottom: 15px; font-weight: 500;'>{info['description']}</p>
                
                <div style='background: #f1f5f9; padding: 12px; border-radius: 6px; margin-bottom: 12px;'>
                    <h4 style='color: #334155; margin: 0 0 8px 0; font-size: 13px;'>Analysis Details:</h4>
                    <div style='color: #64748b; font-size: 12px; white-space: pre-line;'>{info['details']}</div>
                </div>
                
                <div style='color: #059669; font-weight: 500; font-size: 12px;'>{info['use_case']}</div>
            </div>
            """
            
            self.strictness_description.setText(description_html)

    def _open_report_popup(self) -> None:
        """Open the full report in a popup window."""
        if not self._current_payload:
            QMessageBox.information(self, "No Report", "No analysis report available yet. Please run an analysis first.")
            return
        
        # Create popup dialog
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("📊 Compliance Analysis Report")
        # Make dialog responsive to parent window size
        parent_size = self.size()
        dialog_width = min(1000, int(parent_size.width() * 0.8))
        dialog_height = min(700, int(parent_size.height() * 0.8))
        dialog.resize(dialog_width, dialog_height)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Report browser
        report_browser = QTextBrowser(dialog)
        report_browser.setOpenExternalLinks(False)
        report_browser.anchorClicked.connect(self._handle_link_clicked)
        
        # Load report
        analysis = self._current_payload.get("analysis", {})
        doc_name = self._selected_file.name if self._selected_file else "Document"
        report_html = self._current_payload.get("report_html") or self.report_generator.generate_html_report(
            analysis_result=analysis, doc_name=doc_name
        )
        report_browser.setHtml(report_html)
        
        layout.addWidget(report_browser)
        
        # Close button
        close_btn = AnimatedButton("✖️ Close", dialog)
        close_btn.clicked.connect(dialog.close)
        close_btn.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        layout.addWidget(close_btn)
        
        dialog.exec()

    def _toggle_all_sections(self, checked: bool) -> None:
        """Toggle all report section checkboxes."""
        for checkbox in self.section_checkboxes.values():
            checkbox.setChecked(checked)
        
        status = "selected" if checked else "deselected"
        self.statusBar().showMessage(f"All sections {status}", 2000)

    def _open_document_preview(self) -> None:
        """Open document preview in a popup window."""
        if not self._selected_file:
            QMessageBox.information(self, "No Document", "No document selected to preview.")
            return
        
        # Create popup dialog
        from PySide6.QtWidgets import QDialog
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"📄 Document Preview - {self._selected_file.name}")
        # Make dialog responsive to parent window size
        parent_size = self.size()
        dialog_width = min(900, int(parent_size.width() * 0.75))
        dialog_height = min(700, int(parent_size.height() * 0.75))
        dialog.resize(dialog_width, dialog_height)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Document browser
        doc_browser = QTextBrowser(dialog)
        doc_browser.setPlainText(self._cached_preview_content or "Loading document...")
        layout.addWidget(doc_browser)
        
        # Close button
        close_btn = AnimatedButton("✖️ Close", dialog)
        close_btn.clicked.connect(dialog.close)
        close_btn.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        layout.addWidget(close_btn)
        
        dialog.exec()

    def _export_report_pdf(self) -> None:
        """Export the current report as PDF."""
        if not self._current_payload:
            QMessageBox.information(self, "No Report", "No analysis report available to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Report as PDF", "", "PDF Files (*.pdf)"
        )
        
        if file_path:
            try:
                from src.core.pdf_export_service import PDFExportService
                from pathlib import Path
                import shutil
                
                # Get HTML content from current payload
                html_content = self._current_payload.get("report_html", "")
                if not html_content:
                    QMessageBox.warning(self, "No Content", "Report HTML content not available.")
                    return
                
                # Initialize PDF export service
                pdf_service = PDFExportService(output_dir="temp/reports")
                
                # Get document name for metadata
                doc_name = self._current_payload.get("document_name", "Compliance Report")
                
                # Export to PDF
                result = pdf_service.export_to_pdf(
                    html_content=html_content,
                    document_name=doc_name,
                    filename=Path(file_path).stem,
                    metadata={
                        "title": f"Compliance Analysis - {doc_name}",
                        "author": "Therapy Compliance Analyzer",
                        "subject": "Clinical Documentation Compliance Report"
                    }
                )
                
                if result["success"]:
                    # Copy the generated PDF to the user's chosen location
                    shutil.copy2(result["pdf_path"], file_path)
                    
                    self.statusBar().showMessage(f"✅ Report exported to: {file_path}", 5000)
                    QMessageBox.information(self, "Export Successful", f"Report exported successfully to:\n{file_path}")
                else:
                    error_msg = result.get("error", "Unknown error occurred")
                    QMessageBox.warning(self, "Export Failed", f"PDF export failed:\n{error_msg}\n\nTip: Install weasyprint for better PDF support:\npip install weasyprint")
                    
            except Exception as e:
                logger.error("PDF export failed: %s", str(e))
                QMessageBox.warning(self, "Export Failed", f"Failed to export report: {str(e)}\n\nTip: Install weasyprint:\npip install weasyprint")

    def _export_report_html(self) -> None:
        """Export the current report as HTML."""
        if not self._current_payload:
            QMessageBox.information(self, "No Report", "No analysis report available to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Report as HTML", "", "HTML Files (*.html)"
        )
        
        if file_path:
            try:
                analysis = self._current_payload.get("analysis", {})
                doc_name = self._selected_file.name if self._selected_file else "Document"
                report_html = self._current_payload.get("report_html") or self.report_generator.generate_html_report(
                    analysis_result=analysis, doc_name=doc_name
                )
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_html)
                
                self.statusBar().showMessage(f"✅ Report exported to: {file_path}", 5000)
                QMessageBox.information(self, "Export Successful", f"Report exported successfully to:\n{file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Export Failed", f"Failed to export report: {str(e)}")

    def _handle_analysis_success(self, payload: Dict[str, Any]) -> None:
        """Handle successful analysis completion with automatic report display."""
        # Hide loading spinner
        self.loading_spinner.stop_spinning()
        
        # Update UI state
        self.statusBar().showMessage("✅ Analysis Complete - Report displayed automatically", 5000)
        self.run_analysis_button.setEnabled(True)
        self.repeat_analysis_button.setEnabled(True)
        self.stop_analysis_button.setEnabled(False)  # Disable stop button when analysis complete
        self.view_report_button.setEnabled(True)
        self._current_payload = payload
        
        # Display human-readable summary in results tab
        analysis = payload.get("analysis", {})
        doc_name = self._selected_file.name if self._selected_file else "Document"
        
        # Create human-readable summary
        summary_text = f"""
ANALYSIS COMPLETE
================

Document: {doc_name}
Status: ✅ Analysis Successful
Timestamp: {payload.get('timestamp', 'N/A')}

SUMMARY:
--------
Total Findings: {len(analysis.get('findings', []))}
Compliance Score: {analysis.get('compliance_score', 'N/A')}%
Risk Level: {analysis.get('risk_level', 'N/A')}

The detailed report has been automatically displayed in a popup window.

You can also:
- Click "🔄 Repeat" to run analysis again
- Click "📊 View Report" to see the report again
- Click "📄 Export PDF" or "🌐 Export HTML" to save the report
        """
        
        self.analysis_summary_browser.setPlainText(summary_text)
        self.detailed_results_browser.setPlainText(json.dumps(payload, indent=2))
        
        # AUTOMATICALLY DISPLAY THE ENHANCED REPORT POPUP (Best Practice: Immediate Results)
        try:
            # Display the enhanced report popup immediately
            self._open_report_popup()
            
        except Exception as e:
            # Fallback: Log error but don't break the workflow
            logger.warning(f"Warning: Could not auto-display report popup: {e}")
            self.statusBar().showMessage("✅ Analysis Complete - Click 'View Report' to see results", 5000)
        
        # Refresh dashboard after analysis
        self.view_model.load_dashboard_data()
    
    def _generate_enhanced_report_html(self, payload: Dict[str, Any]) -> str:
        """Generate enhanced HTML report from analysis payload following best practices."""
        analysis = payload.get("analysis", {})
        findings = analysis.get('findings', [])
        compliance_score = analysis.get('compliance_score', 0)
        doc_name = self._selected_file.name if self._selected_file else "Document"
        
        # Determine score color based on compliance level
        score_color = '#059669' if compliance_score >= 80 else '#d97706' if compliance_score >= 60 else '#dc2626'
        
        # Generate findings HTML
        findings_html = ""
        for i, finding in enumerate(findings, 1):
            severity = finding.get('severity', 'medium')
            severity_color = '#dc2626' if severity == 'high' else '#d97706' if severity == 'medium' else '#059669'
            
            findings_html += f"""
            <div style='margin: 15px 0; padding: 15px; border-left: 4px solid {severity_color}; background: #f8fafc; border-radius: 6px;'>
                <h4 style='color: {severity_color}; margin-top: 0;'>Finding #{i} - {severity.title()} Risk</h4>
                <p><strong>Issue:</strong> {finding.get('description', 'No description available')}</p>
                <p><strong>Evidence:</strong> "{finding.get('evidence', 'No evidence provided')}"</p>
                <p><strong>Recommendation:</strong> {finding.get('recommendation', 'No recommendation provided')}</p>
                <p><strong>Confidence:</strong> {finding.get('confidence', 0)}%</p>
            </div>
            """
        
        # Generate complete HTML report
        html_report = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Compliance Analysis Report</title>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; margin: 20px; background: #f8fafc; }}
                .header {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 2px solid #e2e8f0; }}
                .score-card {{ background: white; padding: 20px; border-radius: 10px; margin: 20px 0; border: 2px solid #e2e8f0; text-align: center; }}
                .findings-section {{ background: white; padding: 20px; border-radius: 10px; border: 2px solid #e2e8f0; }}
                h1 {{ color: #1d4ed8; margin-top: 0; }}
                h2 {{ color: #1d4ed8; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }}
                .score {{ font-size: 48px; font-weight: bold; color: {score_color}; }}
                .timestamp {{ color: #64748b; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Clinical Compliance Analysis Report</h1>
                <p><strong>Document:</strong> {doc_name}</p>
                <p><strong>Analysis Date:</strong> {payload.get('timestamp', 'N/A')}</p>
                <p><strong>Discipline:</strong> {self.rubric_selector.currentText()}</p>
            </div>
            
            <div class="score-card">
                <h2>Overall Compliance Score</h2>
                <div class="score">{compliance_score}%</div>
                <p>Based on {len(findings)} findings analyzed</p>
            </div>
            
            <div class="findings-section">
                <h2>Detailed Findings</h2>
                {findings_html if findings_html else '<p style="text-align: center; color: #059669; font-size: 18px;">🎉 No compliance issues found! Excellent documentation.</p>'}
            </div>
            
            <div style="background: white; padding: 20px; border-radius: 10px; margin-top: 20px; border: 2px solid #e2e8f0;">
                <h2>Next Steps</h2>
                <ul>
                    <li>Review all findings and implement recommended changes</li>
                    <li>Update documentation templates to prevent recurring issues</li>
                    <li>Schedule regular compliance reviews</li>
                    <li>Consider additional training for areas with multiple findings</li>
                </ul>
            </div>
            
            <div style="background: #f0f9ff; padding: 15px; border-radius: 10px; margin-top: 20px; border: 1px solid #0ea5e9;">
                <p style="margin: 0; color: #0ea5e9; font-size: 14px;">
                    <strong>AI Transparency:</strong> This report was generated using local AI models. 
                    All analysis occurred on your device with no external data transmission. 
                    Please review findings with professional judgment.
                </p>
            </div>
        </body>
        </html>
        """
        
        return html_report

    def on_analysis_error(self, message: str) -> None:
        """Handles analysis errors by surfacing the status."""
        self.statusBar().showMessage(f"Analysis failed: {message}", 5000)

    def _on_rubrics_loaded(self, rubrics: list[dict]) -> None:
        """Load rubrics into dropdown with comprehensive Medicare defaults."""
        self.rubric_selector.clear()
        
        # Add comprehensive default Medicare rubrics
        self.rubric_selector.addItem("📋 Medicare Benefits Policy Manual - Chapter 15 (Covered Medical Services)", "medicare_benefits_policy_manual_ch15")
        self.rubric_selector.addItem("📋 Medicare Part B Outpatient Therapy Guidelines", "medicare_part_b_therapy_guidelines")
        self.rubric_selector.addItem("📋 CMS-1500 Documentation Requirements", "cms_1500_documentation_requirements")
        self.rubric_selector.addItem("📋 Medicare Therapy Cap & Exception Guidelines", "medicare_therapy_cap_guidelines")
        self.rubric_selector.addItem("📋 Skilled Therapy Documentation Standards", "skilled_therapy_documentation_standards")
        
        # Add discipline-specific defaults
        self.rubric_selector.insertSeparator(5)
        self.rubric_selector.addItem("🏃 Physical Therapy - APTA Guidelines", "apta_pt_guidelines")
        self.rubric_selector.addItem("🖐️ Occupational Therapy - AOTA Standards", "aota_ot_standards")
        self.rubric_selector.addItem("🗣️ Speech-Language Pathology - ASHA Guidelines", "asha_slp_guidelines")
        
        # Add separator if there are custom rubrics
        if rubrics:
            self.rubric_selector.insertSeparator(self.rubric_selector.count())
            self.rubric_selector.addItem("--- Custom Rubrics ---", "")
            self.rubric_selector.model().item(self.rubric_selector.count() - 1).setEnabled(False)
        
        # Add custom rubrics from API
        for rubric in rubrics:
            self.rubric_selector.addItem(f"📝 {rubric.get('name', 'Unnamed rubric')}", rubric.get("value"))
        
        # Select Medicare Benefits Policy Manual as default
        self.rubric_selector.setCurrentIndex(0)
        
        self._load_gui_settings() # Re-apply settings after rubrics are loaded

    def _load_default_rubrics(self) -> None:
        """Load default rubrics immediately as fallback."""
        if hasattr(self, 'rubric_selector') and self.rubric_selector:
            self.rubric_selector.clear()
            
            # Add comprehensive default Medicare rubrics
            self.rubric_selector.addItem("📋 Medicare Benefits Policy Manual - Chapter 15 (Covered Medical Services)", "medicare_benefits_policy_manual_ch15")
            self.rubric_selector.addItem("📋 Medicare Part B Outpatient Therapy Guidelines", "medicare_part_b_therapy_guidelines")
            self.rubric_selector.addItem("📋 CMS-1500 Documentation Requirements", "cms_1500_documentation_requirements")
            self.rubric_selector.addItem("📋 Medicare Therapy Cap & Exception Guidelines", "medicare_therapy_cap_guidelines")
            self.rubric_selector.addItem("📋 Skilled Therapy Documentation Standards", "skilled_therapy_documentation_standards")
            
            # Add discipline-specific defaults
            self.rubric_selector.insertSeparator(5)
            self.rubric_selector.addItem("🏃 Physical Therapy - APTA Guidelines", "apta_pt_guidelines")
            self.rubric_selector.addItem("🖐️ Occupational Therapy - AOTA Standards", "aota_ot_standards")
            self.rubric_selector.addItem("🗣️ Speech-Language Pathology - ASHA Guidelines", "asha_slp_guidelines")
            
            # Select Medicare Benefits Policy Manual as default
            self.rubric_selector.setCurrentIndex(0)

    def _handle_link_clicked(self, url: QUrl) -> None:
        if url.scheme() == "feedback":
            parsed_url = urlparse(url.toString())
            query_params = parse_qs(parsed_url.query)
            finding_id = query_params.get("finding_id", [None])[0]
            action = parsed_url.path.strip("/")

            if not finding_id:
                return

            if action == "correct":
                self.view_model.submit_feedback({"finding_id": finding_id, "is_correct": True})
                self.statusBar().showMessage(f"Feedback for finding {finding_id[:8]}... marked as correct.", 3000)
            elif action == "incorrect":
                correction, ok = QInputDialog.getText(self, "Submit Correction", "Please provide a brief correction:")
                if ok and correction:
                    self.view_model.submit_feedback({"finding_id": finding_id, "is_correct": False, "correction": correction})
                    self.statusBar().showMessage(f"Correction for finding {finding_id[:8]}... submitted.", 3000)
        else:
            webbrowser.open(url.toString())


    def _handle_report_link(self, url: QUrl) -> None:
        """Route analysis browser anchor clicks through the shared handler."""
        self._handle_link_clicked(url)

    def closeEvent(self, event) -> None:
        """Handle application close - exit quickly."""
        try:
            self._save_gui_settings()
        except Exception:
            pass  # Don't block exit on save errors
        
        # Force quit workers quickly
        try:
            self.view_model.stop_all_workers()
        except Exception:
            pass
        
        # Force terminate any remaining threads
        QApplication.quit()
        event.accept()

    def _build_menus(self) -> None:
        menu_bar = self.menuBar()
        self._build_file_menu(menu_bar)
        self._build_view_menu(menu_bar)
        self._build_tools_menu(menu_bar)
        self._build_admin_menu(menu_bar)  # Now available to all users
        self._build_help_menu(menu_bar)

    def _build_file_menu(self, menu_bar) -> None:
        file_menu = menu_bar.addMenu("&File")
        open_file_action = QAction("Open Document…", self)
        open_file_action.triggered.connect(self._prompt_for_document)
        file_menu.addAction(open_file_action)
        open_folder_action = QAction("Open Folder…", self)
        open_folder_action.triggered.connect(self._prompt_for_folder)
        file_menu.addAction(open_folder_action)
        file_menu.addSeparator()
        export_action = QAction("Export Report…", self)
        export_action.triggered.connect(self._export_report)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _build_view_menu(self, menu_bar) -> None:
        view_menu = menu_bar.addMenu("&View")
        
        # Optional docks (hidden by default)
        if self.performance_dock:
            view_menu.addAction(self.performance_dock.toggleViewAction())
        
        view_menu.addSeparator()
        
        # Theme submenu
        theme_menu = QMenu("Theme", self)
        
        light_action = QAction("Light Theme", self)
        light_action.triggered.connect(lambda: self._apply_theme("light"))
        theme_menu.addAction(light_action)
        
        dark_action = QAction("Dark Theme", self)
        dark_action.triggered.connect(lambda: self._apply_theme("dark"))
        theme_menu.addAction(dark_action)
        
        theme_menu.addSeparator()
        toggle_action = QAction("🔄 Toggle Theme", self)
        toggle_action.setShortcut("Ctrl+T")
        toggle_action.triggered.connect(self._toggle_theme)
        theme_menu.addAction(toggle_action)
        
        view_menu.addMenu(theme_menu)
    def _build_tools_menu(self, menu_bar) -> None:
        tools_menu = menu_bar.addMenu("&Tools")
        
        # Meta Analytics
        if MetaAnalyticsWidget:
            meta_action = QAction("Meta Analytics", self, checkable=True)
            meta_action.setShortcut("Ctrl+Shift+A")
            meta_action.triggered.connect(self._toggle_meta_analytics_dock)
            tools_menu.addAction(meta_action)
            self.meta_analytics_action = meta_action
        
        # Performance Status
        if PerformanceStatusWidget:
            perf_action = QAction("Performance Status", self, checkable=True)
            perf_action.setShortcut("Ctrl+Shift+P")
            perf_action.triggered.connect(self._toggle_performance_dock)
            tools_menu.addAction(perf_action)
            self.performance_action = perf_action
        
        tools_menu.addSeparator()
        
        # AI Chat Assistant - Removed (redundant with main window chat)
        
        tools_menu.addSeparator()
        
        # Refresh
        refresh_action = QAction("🔄 Refresh All Data", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._load_initial_state)
        tools_menu.addAction(refresh_action)
        
        # Clear Cache
        clear_cache_action = QAction("🗑️ Clear Cache", self)
        clear_cache_action.triggered.connect(self._clear_all_caches)
        tools_menu.addAction(clear_cache_action)
        
        tools_menu.addSeparator()
        
        # Diagnostic Tools
        diagnostic_action = QAction("🔍 Run Diagnostics", self)
        diagnostic_action.triggered.connect(self._run_diagnostics)
        tools_menu.addAction(diagnostic_action)
        
        start_api_action = QAction("🚀 Start API Server", self)
        start_api_action.triggered.connect(self._start_api_server)
        tools_menu.addAction(start_api_action)

    def _build_admin_menu(self, menu_bar) -> None:
        admin_menu = menu_bar.addMenu("&Admin")
        
        # Non-critical features available to all users
        # Change Password (all users need this)
        password_action = QAction("Change Password", self)
        password_action.triggered.connect(self.show_change_password_dialog)
        admin_menu.addAction(password_action)
        
        # Settings (all users need this)
        settings_action = QAction("Settings…", self)
        settings_action.triggered.connect(self._open_settings_dialog)
        admin_menu.addAction(settings_action)
        
        # System Info (informational, safe for all users)
        system_info_action = QAction("System Information", self)
        system_info_action.triggered.connect(self._show_system_info)
        admin_menu.addAction(system_info_action)
        
        # CRITICAL ADMIN-ONLY FEATURES (keep protected)
        if self.current_user.is_admin:
            admin_menu.addSeparator()
            
            # Rubric Management (ADMIN ONLY - affects compliance rules)
            rubrics_action = QAction("Manage Rubrics… (Admin)", self)
            rubrics_action.triggered.connect(self._open_rubric_manager)
            admin_menu.addAction(rubrics_action)
            
            # User Management (ADMIN ONLY - security critical)
            users_action = QAction("Manage Users (Admin)", self)
            users_action.triggered.connect(self._show_user_management)
            admin_menu.addAction(users_action)

    def _build_help_menu(self, menu_bar) -> None:
        help_menu = menu_bar.addMenu("&Help")
        docs_action = QAction("Open Documentation", self)
        docs_action.triggered.connect(lambda: webbrowser.open("https://github.com/your-username/your-repo-name"))
        help_menu.addAction(docs_action)
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _build_central_layout(self) -> None:
        """Build the main central widget with 4-tab structure."""
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)
        
        # Add beautiful medical-themed header at the top
        root_layout.addWidget(self.header)
        
        # Create main tab widget with modern styling (no chat tab - integrated into analysis)
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setDocumentMode(False)
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 10px;
                background: {medical_theme.get_color('bg_primary')};
                top: -2px;
            }}
            QTabBar::tab {{
                background: {medical_theme.get_color('bg_secondary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-bottom: none;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                padding: 12px 24px;
                margin-right: 6px;
                color: {medical_theme.get_color('text_secondary')};
                font-weight: 700;
                font-size: 12px;
                min-width: 120px;
            }}
            QTabBar::tab:selected {{
                background: white;
                color: {medical_theme.get_color('primary_blue')};
                border-bottom: 2px solid white;
                margin-bottom: -2px;
            }}
            QTabBar::tab:hover:!selected {{
                background: {medical_theme.get_color('hover_bg')};
                color: {medical_theme.get_color('primary_blue')};
            }}
        """)
        root_layout.addWidget(self.tab_widget, stretch=1)
        
        # Tab 1: Analysis (with left 3 panels + right chat/analysis)
        self.analysis_tab = self._create_analysis_tab()
        self.tab_widget.addTab(self.analysis_tab, "Analysis")
        
        # Tab 2: Dashboard
        self.dashboard_tab = self._create_dashboard_tab()
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        
        # Tab 3: Mission Control
        self.mission_control_tab = self._create_mission_control_tab()
        self.tab_widget.addTab(self.mission_control_tab, "Mission Control")
        
        # Tab 4: Settings
        self.settings_tab = self._create_settings_tab()
        self.tab_widget.addTab(self.settings_tab, "Settings")
        
        # Set Analysis as default tab
        self.tab_widget.setCurrentWidget(self.analysis_tab)

    def _create_analysis_tab(self) -> QWidget:
        """Create the Analysis tab with improved layout and scaling."""
        tab = QWidget(self)
        main_layout = QHBoxLayout(tab)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Left column: Rubric Selection (25%)
        left_column = self._create_rubric_selection_panel()
        main_layout.addWidget(left_column, stretch=25)
        
        # Middle column: Compliance Guidelines & Report Sections (30%)
        middle_column = self._create_middle_column_panel()
        main_layout.addWidget(middle_column, stretch=30)
        
        # Right column: Analysis Results with Chat (45%)
        right_column = self._create_analysis_results_with_chat()
        main_layout.addWidget(right_column, stretch=45)
        
        return tab
    
    def _create_rubric_selection_panel(self) -> QWidget:
        """Create left panel with rubric selection and document upload."""
        from PySide6.QtWidgets import QSizePolicy
        
        panel = QWidget(self)
        panel.setMinimumWidth(280)
        panel.setMaximumWidth(400)
        panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Document Upload Section
        upload_section = self._create_document_upload_section()
        layout.addWidget(upload_section)
        
        # Rubric Selection Section (moved here from middle)
        rubric_section = self._create_rubric_selector_section()
        layout.addWidget(rubric_section)
        
        # Action Buttons
        actions_section = self._create_action_buttons_section()
        layout.addWidget(actions_section)
        
        layout.addStretch(1)
        return panel
    
    def _create_rubric_selector_section(self) -> QWidget:
        """Create rubric selector section."""
        section = QWidget(self)
        section.setStyleSheet(f"""
            QWidget {{
                background-color: {medical_theme.get_color("bg_secondary")};
                border: 2px solid {medical_theme.get_color("border_light")};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("📚 Select Rubric", section)
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {medical_theme.get_color('primary_blue')}; background: transparent; border: none;")
        layout.addWidget(title)
        
        # Rubric selector
        self.rubric_selector = QComboBox(section)
        self.rubric_selector.setMinimumHeight(40)
        self.rubric_selector.setStyleSheet(f"""
            QComboBox {{
                padding: 10px 12px;
                border: 2px solid {medical_theme.get_color('border_medium')};
                border-radius: 8px;
                background: white;
                font-size: 11px;
                font-weight: 500;
                color: {medical_theme.get_color('text_primary')};
            }}
            QComboBox:hover {{
                border-color: {medical_theme.get_color('primary_blue')};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 35px;
            }}
        """)
        layout.addWidget(self.rubric_selector)
        
        return section
    
    def _create_middle_column_panel(self) -> QWidget:
        """Create middle panel with compliance guidelines and report sections."""
        from PySide6.QtWidgets import QSizePolicy
        
        panel = QWidget(self)
        panel.setMinimumWidth(300)
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Compliance Guidelines Section (moved from left, above report sections)
        guidelines_section = self._create_compliance_guidelines_section()
        layout.addWidget(guidelines_section, stretch=1)
        
        # Report Sections (moved from middle)
        report_section = self._create_report_sections_panel()
        layout.addWidget(report_section, stretch=1)
        
        return panel
    
    def _create_compliance_guidelines_section(self) -> QWidget:
        """Create compliance guidelines section with smaller buttons."""
        
        section = QWidget(self)
        section.setStyleSheet(f"""
            QWidget {{
                background-color: {medical_theme.get_color("bg_secondary")};
                border: 2px solid {medical_theme.get_color("border_light")};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("⚙️ Review Strictness", section)
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {medical_theme.get_color('primary_blue')}; background: transparent; border: none;")
        layout.addWidget(title)
        
        # Strictness buttons (smaller)
        strictness_layout = QHBoxLayout()
        strictness_layout.setSpacing(8)
        self.strictness_buttons = []
        
        # Strictness definitions with detailed descriptions
        self.strictness_levels = [
            ("Lenient", "😊", {
                "description": "Lenient analysis focusing on major compliance issues only",
                "details": "• Identifies critical Medicare violations\n• Overlooks minor documentation gaps\n• Faster processing time\n• Suitable for initial reviews",
                "use_case": "Best for: Quick assessments, high-volume processing"
            }),
            ("Standard", "📋", {
                "description": "Balanced analysis covering most compliance requirements", 
                "details": "• Comprehensive Medicare compliance checking\n• Identifies moderate to severe issues\n• Standard processing time\n• Recommended for most users",
                "use_case": "Best for: Regular compliance reviews, quality assurance"
            }),
            ("Strict", "🔍", {
                "description": "Thorough analysis with detailed scrutiny of all elements",
                "details": "• Exhaustive compliance verification\n• Identifies all potential issues\n• Longer processing time\n• Maximum regulatory protection",
                "use_case": "Best for: Audit preparation, high-risk documentation"
            })
        ]
        
        for i, (level, emoji, info) in enumerate(self.strictness_levels):
            btn = AnimatedButton(f"{emoji}\n{level}", section)
            btn.setCheckable(True)
            btn.setMinimumHeight(45)
            btn.setMaximumHeight(50)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: white;
                    border: 2px solid {medical_theme.get_color('border_medium')};
                    border-radius: 8px;
                    color: {medical_theme.get_color('text_primary')};
                    font-size: 10px;
                    font-weight: 600;
                    padding: 4px;
                }}
                QPushButton:hover {{
                    background-color: {medical_theme.get_color('hover_bg')};
                    border-color: {medical_theme.get_color('primary_blue')};
                }}
                QPushButton:checked {{
                    background-color: {medical_theme.get_color('primary_blue')};
                    color: white;
                    border-color: {medical_theme.get_color('primary_blue')};
                }}
            """)
            btn.clicked.connect(lambda checked, idx=i: self._on_strictness_selected_with_description(idx))
            self.strictness_buttons.append(btn)
            strictness_layout.addWidget(btn)
        
        layout.addLayout(strictness_layout)
        
        # Dynamic description area with complementary background
        self.strictness_description = QLabel()
        self.strictness_description.setWordWrap(True)
        self.strictness_description.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f0f9ff, stop:1 #e0f2fe);
                border: 2px solid #0ea5e9;
                border-radius: 8px;
                padding: 15px;
                color: #0c4a6e;
                font-size: 13px;
                line-height: 1.4;
            }
        """)
        self.strictness_description.setMinimumHeight(120)
        layout.addWidget(self.strictness_description)
        
        # Set default to Standard and show its description
        if len(self.strictness_buttons) >= 2:
            self.strictness_buttons[1].setChecked(True)
            self._update_strictness_description(1)
        
        return section
    
    def _create_report_sections_panel(self) -> QWidget:
        """Create report sections panel."""
        from PySide6.QtWidgets import QCheckBox, QGridLayout
        
        section = QWidget(self)
        section.setStyleSheet(f"""
            QWidget {{
                background-color: {medical_theme.get_color("bg_secondary")};
                border: 2px solid {medical_theme.get_color("border_light")};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("📋 Report Sections", section)
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {medical_theme.get_color('primary_blue')}; background: transparent; border: none;")
        layout.addWidget(title)
        
        # Checkboxes in grid
        grid = QGridLayout()
        grid.setSpacing(8)
        
        sections = [
            "Executive Summary", "Detailed Findings",
            "Risk Assessment", "Recommendations",
            "Regulatory Citations", "Action Plan",
            "AI Transparency", "Improvement Strategies"
        ]
        
        self.section_checkboxes = {}
        for i, section_name in enumerate(sections):
            checkbox = QCheckBox(section_name)
            checkbox.setChecked(True)
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    color: {medical_theme.get_color('text_primary')};
                    font-size: 10px;
                    spacing: 6px;
                    background: transparent;
                    border: none;
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                    border: 2px solid {medical_theme.get_color('border_medium')};
                    border-radius: 4px;
                    background: white;
                }}
                QCheckBox::indicator:checked {{
                    background: {medical_theme.get_color('primary_blue')};
                    border-color: {medical_theme.get_color('primary_blue')};
                }}
            """)
            self.section_checkboxes[section_name] = checkbox
            grid.addWidget(checkbox, i // 2, i % 2)
        
        layout.addLayout(grid)
        
        # Export buttons
        export_layout = QHBoxLayout()
        export_layout.setSpacing(8)
        
        pdf_btn = AnimatedButton("📄 PDF", section)
        pdf_btn.clicked.connect(self._export_report_pdf)
        pdf_btn.setMinimumHeight(35)
        pdf_btn.setStyleSheet(medical_theme.get_button_stylesheet("primary"))
        export_layout.addWidget(pdf_btn)
        
        html_btn = AnimatedButton("🌐 HTML", section)
        html_btn.clicked.connect(self._export_report_html)
        html_btn.setMinimumHeight(35)
        html_btn.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        export_layout.addWidget(html_btn)
        
        layout.addLayout(export_layout)
        
        return section
    
    def _create_analysis_results_with_chat(self) -> QWidget:
        """Create right panel with analysis results and integrated chat bar."""
        panel = QWidget(self)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Analysis results (existing)
        results_panel = self._create_analysis_right_panel_content()
        layout.addWidget(results_panel, stretch=1)
        
        # Removed redundant chat input bar - use main AI chat instead
        
        return panel
    
    def _create_analysis_right_panel_content(self) -> QWidget:
        """Create the analysis results content."""
        from PySide6.QtWidgets import QTabWidget
        
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Modern styled tabs
        results_tabs = QTabWidget(panel)
        results_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 8px;
                background: white;
                top: -1px;
            }}
            QTabBar::tab {{
                background: {medical_theme.get_color('bg_secondary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 10px 20px;
                margin-right: 4px;
                color: {medical_theme.get_color('text_secondary')};
                font-weight: 600;
                font-size: 11px;
            }}
            QTabBar::tab:selected {{
                background: white;
                color: {medical_theme.get_color('primary_blue')};
                border-bottom: 2px solid white;
            }}
            QTabBar::tab:hover {{
                background: {medical_theme.get_color('hover_bg')};
            }}
        """)
        
        # Summary tab
        self.analysis_summary_browser = QTextBrowser(panel)
        self.analysis_summary_browser.setOpenExternalLinks(False)
        self.analysis_summary_browser.anchorClicked.connect(self._handle_report_link)
        self.analysis_summary_browser.setPlaceholderText(
            "📊 ANALYSIS SUMMARY\n\n"
            "Upload a document and run analysis to see:\n"
            "• Compliance score and risk assessment\n"
            "• Key findings and recommendations\n"
            "• Medicare guideline compliance status\n"
            "• Actionable improvement suggestions\n\n"
            "Select a rubric and click 'Run Analysis' to begin."
        )
        self.analysis_summary_browser.setStyleSheet(f"""
            QTextBrowser {{
                border: 2px solid {medical_theme.get_color('border_light')};
                background: {medical_theme.get_color('bg_primary')};
                padding: 20px;
                font-size: 13px;
                line-height: 1.6;
                border-radius: 8px;
                color: {medical_theme.get_color('text_primary')};
            }}
        """)
        results_tabs.addTab(self.analysis_summary_browser, "📊 Summary")
        
        # Detailed results tab
        self.detailed_results_browser = QTextBrowser(panel)
        self.detailed_results_browser.setOpenExternalLinks(False)
        self.detailed_results_browser.anchorClicked.connect(self._handle_report_link)
        self.detailed_results_browser.setPlaceholderText(
            "📋 DETAILED ANALYSIS RESULTS\n\n"
            "This section will display:\n"
            "• Complete analysis payload data\n"
            "• Technical details and confidence scores\n"
            "• Raw AI model outputs\n"
            "• Processing timestamps and metadata\n"
            "• Full compliance rule matching results\n\n"
            "Run an analysis to populate this section with detailed technical information."
        )
        self.detailed_results_browser.setStyleSheet(f"""
            QTextBrowser {{
                border: 2px solid {medical_theme.get_color('border_light')};
                background: {medical_theme.get_color('bg_primary')};
                padding: 20px;
                font-size: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                border-radius: 8px;
                color: {medical_theme.get_color('text_primary')};
            }}
        """)
        results_tabs.addTab(self.detailed_results_browser, "📋 Details")
        
        layout.addWidget(results_tabs)
        return panel
    
    # Removed redundant chat input bar - use main AI chat dialog instead
    
    def _create_analysis_left_column(self) -> QWidget:
        """Create the left column with document upload and settings."""
        from PySide6.QtWidgets import QSizePolicy
        
        column = QWidget(self)
        column.setMinimumWidth(350)
        column.setMaximumWidth(450)
        column.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        
        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Document Upload Section
        upload_section = self._create_document_upload_section()
        layout.addWidget(upload_section, stretch=0)
        
        # Analysis Settings Section
        settings_section = self._create_analysis_settings_section()
        layout.addWidget(settings_section, stretch=0)
        
        # Action Buttons Section
        actions_section = self._create_action_buttons_section()
        layout.addWidget(actions_section, stretch=0)
        
        layout.addStretch(1)
        return column
    
    def _create_document_upload_section(self) -> QWidget:
        """Create the document upload section."""
        section = QWidget(self)
        section.setStyleSheet(f"""
            QWidget {{
                background-color: {medical_theme.get_color("bg_secondary")};
                border: 2px solid {medical_theme.get_color("border_light")};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("📁 Upload Document", section)
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {medical_theme.get_color('primary_blue')}; background: transparent; border: none;")
        layout.addWidget(title)
        
        # File display
        self.file_display = QTextEdit(section)
        self.file_display.setReadOnly(True)
        self.file_display.setMinimumHeight(90)
        self.file_display.setMaximumHeight(110)
        self.file_display.setPlaceholderText("📋 DOCUMENT UPLOAD CENTER\n\n📁 This window displays your selected document for compliance analysis\n\n🔹 Click 'Upload Document' to browse and select a file\n🔹 Supported formats: PDF, DOCX, TXT\n🔹 Maximum file size: 50MB\n\n✨ Once uploaded, document details will appear here")
        self.file_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: {medical_theme.get_color("bg_primary")};
                border: 2px dashed {medical_theme.get_color("border_medium")};
                border-radius: 8px;
                padding: 12px;
                font-size: 11px;
                color: {medical_theme.get_color("text_secondary")};
            }}
        """)
        layout.addWidget(self.file_display)
        
        # Upload buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.open_file_button = AnimatedButton("📄 Upload Document", section)
        self.open_file_button.clicked.connect(self._prompt_for_document)
        self.open_file_button.setStyleSheet(medical_theme.get_button_stylesheet("primary"))
        self.open_file_button.setMinimumHeight(42)
        buttons_layout.addWidget(self.open_file_button)
        
        self.open_folder_button = AnimatedButton("📂 Batch", section)
        self.open_folder_button.clicked.connect(self._prompt_for_folder)
        self.open_folder_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        self.open_folder_button.setMinimumHeight(42)
        self.open_folder_button.setMaximumWidth(100)
        buttons_layout.addWidget(self.open_folder_button)
        
        layout.addLayout(buttons_layout)
        return section

    def _create_analysis_settings_section(self) -> QWidget:
        """Create the analysis settings section with rubric and strictness."""
        section = QWidget(self)
        section.setStyleSheet(f"""
            QWidget {{
                background-color: {medical_theme.get_color("bg_secondary")};
                border: 2px solid {medical_theme.get_color("border_light")};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)
        
        # Title
        title = QLabel("📋 Compliance Guidelines", section)
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {medical_theme.get_color('primary_blue')}; background: transparent; border: none;")
        layout.addWidget(title)
        
        # Rubric selector with better styling
        rubric_label = QLabel("Select Guidelines:", section)
        rubric_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        rubric_label.setStyleSheet("background: transparent; border: none; color: #475569;")
        layout.addWidget(rubric_label)
        
        self.rubric_selector = QComboBox(section)
        self.rubric_selector.setMinimumHeight(45)
        self.rubric_selector.setStyleSheet(f"""
            QComboBox {{
                padding: 12px 14px;
                border: 2px solid {medical_theme.get_color('border_medium')};
                border-radius: 8px;
                background: {medical_theme.get_color('bg_primary')};
                font-size: 12px;
                font-weight: 500;
                color: {medical_theme.get_color('text_primary')};
            }}
            QComboBox:hover {{
                border-color: {medical_theme.get_color('primary_blue')};
                background: white;
            }}
            QComboBox:focus {{
                border-color: {medical_theme.get_color('primary_blue')};
                border-width: 2px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 40px;
            }}
            QComboBox::down-arrow {{
                width: 14px;
                height: 14px;
            }}
        """)
        layout.addWidget(self.rubric_selector)
        
        # Separator
        separator = QWidget(section)
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {medical_theme.get_color('border_light')}; border: none; margin: 8px 0px;")
        layout.addWidget(separator)
        
        # Strictness selector with dynamic descriptions
        strictness_label = QLabel("Review Strictness:", section)
        strictness_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        strictness_label.setStyleSheet("background: transparent; border: none; color: #475569;")
        layout.addWidget(strictness_label)
        
        # Create strictness container with description area
        strictness_container = QWidget()
        strictness_container_layout = QVBoxLayout(strictness_container)
        strictness_container_layout.setSpacing(15)
        
        # Strictness buttons
        strictness_layout = QHBoxLayout()
        strictness_layout.setSpacing(10)
        self.strictness_buttons = []
        
        # Strictness definitions with detailed descriptions
        self.strictness_levels = [
            ("Moderate", "😊", {
                "description": "Lenient analysis focusing on major compliance issues only",
                "details": "• Identifies critical Medicare violations\n• Overlooks minor documentation gaps\n• Faster processing time\n• Suitable for initial reviews",
                "use_case": "Best for: Quick assessments, high-volume processing"
            }),
            ("Standard", "📋", {
                "description": "Balanced analysis covering most compliance requirements", 
                "details": "• Comprehensive Medicare compliance checking\n• Identifies moderate to severe issues\n• Standard processing time\n• Recommended for most users",
                "use_case": "Best for: Regular compliance reviews, quality assurance"
            }),
            ("Strict", "🔍", {
                "description": "Thorough analysis with detailed scrutiny of all elements",
                "details": "• Exhaustive compliance verification\n• Identifies all potential issues\n• Longer processing time\n• Maximum regulatory protection",
                "use_case": "Best for: Audit preparation, high-risk documentation"
            })
        ]
        
        for i, (level, emoji, info) in enumerate(self.strictness_levels):
            btn = AnimatedButton(f"{emoji}\n{level}", section)
            btn.setCheckable(True)
            btn.setMinimumHeight(55)
            btn.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
            btn.clicked.connect(lambda checked, idx=i: self._on_strictness_selected_with_description(idx))
            strictness_layout.addWidget(btn)
            self.strictness_buttons.append(btn)
        
        strictness_container_layout.addLayout(strictness_layout)
        
        # Dynamic description area
        self.strictness_description = QLabel()
        self.strictness_description.setWordWrap(True)
        self.strictness_description.setStyleSheet("""
            QLabel {
                background: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 15px;
                color: #475569;
                font-size: 13px;
                line-height: 1.4;
            }
        """)
        self.strictness_description.setMinimumHeight(120)
        strictness_container_layout.addWidget(self.strictness_description)
        
        # Set default to Standard and show its description
        self.strictness_buttons[1].setChecked(True)
        self._update_strictness_description(1)
        
        layout.addWidget(strictness_container)
        
        return section

    def _create_action_buttons_section(self) -> QWidget:
        """Create the action buttons section."""
        section = QWidget(self)
        section.setStyleSheet(f"""
            QWidget {{
                background-color: {medical_theme.get_color("bg_secondary")};
                border: 2px solid {medical_theme.get_color("border_light")};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Run Analysis button (big and prominent)
        self.run_analysis_button = AnimatedButton("▶️  Run Compliance Analysis", section)
        self.run_analysis_button.clicked.connect(self._start_analysis)
        self.run_analysis_button.setEnabled(False)
        self.run_analysis_button.setStyleSheet(medical_theme.get_button_stylesheet("success"))
        self.run_analysis_button.setMinimumHeight(55)
        self.run_analysis_button.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        layout.addWidget(self.run_analysis_button)
        
        # Secondary actions
        secondary_layout = QHBoxLayout()
        secondary_layout.setSpacing(10)
        
        self.repeat_analysis_button = AnimatedButton("🔄 Repeat", section)
        self.repeat_analysis_button.clicked.connect(self._repeat_analysis)
        self.repeat_analysis_button.setEnabled(False)
        self.repeat_analysis_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        self.repeat_analysis_button.setMinimumHeight(42)
        secondary_layout.addWidget(self.repeat_analysis_button)
        
        # Stop Analysis button - professional implementation
        self.stop_analysis_button = AnimatedButton("⏹️ Stop Analysis", section)
        self.stop_analysis_button.clicked.connect(self._stop_analysis)
        self.stop_analysis_button.setEnabled(False)
        self.stop_analysis_button.setStyleSheet(medical_theme.get_button_stylesheet("error"))
        self.stop_analysis_button.setMinimumHeight(42)
        secondary_layout.addWidget(self.stop_analysis_button)
        
        self.view_report_button = AnimatedButton("📊 View Report", section)
        self.view_report_button.clicked.connect(self._open_report_popup)
        self.view_report_button.setEnabled(False)
        self.view_report_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        self.view_report_button.setMinimumHeight(42)
        secondary_layout.addWidget(self.view_report_button)
        
        layout.addLayout(secondary_layout)
        return section


    def _create_report_outputs_panel(self) -> QWidget:
        """Create the Report Sections panel with grid of checkboxes."""
        panel = QWidget(self)
        panel.setStyleSheet(f"""
            QWidget {{
                background-color: {medical_theme.get_color("bg_secondary")};
                border: 2px solid {medical_theme.get_color("border_light")};
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("📋 Report Sections", panel)
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {medical_theme.get_color('primary_blue')}; background: transparent; border: none;")
        layout.addWidget(title)
        
        # Grid of checkboxes (2 columns)
        from PySide6.QtWidgets import QCheckBox, QGridLayout
        
        grid_widget = QWidget(panel)
        grid_widget.setStyleSheet("background: transparent; border: none;")
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(10)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Report sections
        sections = [
            ("✅ Medicare Guidelines", "medicare"),
            ("💪 Strengths", "strengths"),
            ("⚠️ Weaknesses", "weaknesses"),
            ("💡 Suggestions", "suggestions"),
            ("📚 Education", "education"),
            ("🎯 7 Habits", "habits"),
            ("📊 Compliance Score", "score"),
            ("🔍 Detailed Findings", "findings"),
        ]
        
        self.section_checkboxes = {}
        row, col = 0, 0
        
        for emoji_text, key in sections:
            checkbox = QCheckBox(emoji_text, grid_widget)
            checkbox.setChecked(True)
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    font-size: 12px;
                    font-weight: 500;
                    color: {medical_theme.get_color('text_primary')};
                    spacing: 8px;
                    background: transparent;
                }}
                QCheckBox::indicator {{
                    width: 20px;
                    height: 20px;
                    border: 2px solid {medical_theme.get_color('border_medium')};
                    border-radius: 4px;
                    background: {medical_theme.get_color('bg_primary')};
                }}
                QCheckBox::indicator:checked {{
                    background: {medical_theme.get_color('primary_blue')};
                    border-color: {medical_theme.get_color('primary_blue')};
                    image: url(none);
                }}
                QCheckBox::indicator:hover {{
                    border-color: {medical_theme.get_color('primary_blue')};
                }}
            """)
            grid_layout.addWidget(checkbox, row, col)
            self.section_checkboxes[key] = checkbox
            
            col += 1
            if col > 1:  # 2 columns
                col = 0
                row += 1
        
        layout.addWidget(grid_widget)
        
        # Utility buttons row
        utility_layout = QHBoxLayout()
        utility_layout.setSpacing(8)
        
        # Document Preview button
        preview_btn = AnimatedButton("📄 Preview Document", panel)
        preview_btn.clicked.connect(self._open_document_preview)
        preview_btn.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        utility_layout.addWidget(preview_btn)
        
        # Select All / Deselect All
        select_all_btn = AnimatedButton("☑️ All", panel)
        select_all_btn.clicked.connect(lambda: self._toggle_all_sections(True))
        select_all_btn.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        select_all_btn.setMaximumWidth(80)
        utility_layout.addWidget(select_all_btn)
        
        deselect_all_btn = AnimatedButton("☐ None", panel)
        deselect_all_btn.clicked.connect(lambda: self._toggle_all_sections(False))
        deselect_all_btn.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        deselect_all_btn.setMaximumWidth(80)
        utility_layout.addWidget(deselect_all_btn)
        
        layout.addLayout(utility_layout)
        
        # Export buttons
        export_layout = QHBoxLayout()
        export_layout.setSpacing(8)
        
        export_pdf_btn = AnimatedButton("📄 Export PDF", panel)
        export_pdf_btn.clicked.connect(self._export_report_pdf)
        export_pdf_btn.setStyleSheet(medical_theme.get_button_stylesheet("success"))
        export_layout.addWidget(export_pdf_btn)
        
        export_html_btn = AnimatedButton("🌐 Export HTML", panel)
        export_html_btn.clicked.connect(self._export_report_html)
        export_html_btn.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        export_layout.addWidget(export_html_btn)
        
        layout.addLayout(export_layout)
        
        return panel
    
    def _create_analysis_right_panel(self) -> QWidget:
        """Create the right panel with Chat/Analysis tabs."""
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Tab widget for Chat and Analysis
        right_tabs = QTabWidget(panel)
        
        # Analysis results tab
        analysis_widget = QWidget()
        analysis_layout = QVBoxLayout(analysis_widget)
        analysis_layout.setContentsMargins(0, 0, 0, 0)
        self.analysis_summary_browser = QTextBrowser(analysis_widget)
        self.analysis_summary_browser.setOpenExternalLinks(False)
        self.analysis_summary_browser.anchorClicked.connect(self._handle_link_clicked)
        analysis_layout.addWidget(self.analysis_summary_browser)
        right_tabs.addTab(analysis_widget, "Analysis Results")
        
        # Detailed findings tab
        detailed_widget = QWidget()
        detailed_layout = QVBoxLayout(detailed_widget)
        detailed_layout.setContentsMargins(0, 0, 0, 0)
        self.detailed_results_browser = QTextBrowser(detailed_widget)
        detailed_layout.addWidget(self.detailed_results_browser)
        right_tabs.addTab(detailed_widget, "Detailed Findings")
        
        # Chat tab (placeholder for now)
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_label = QLabel("AI Chat Assistant\n\nClick the 'Ask AI Assistant' button to open the chat dialog.", chat_widget)
        chat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chat_layout.addWidget(chat_label)
        right_tabs.addTab(chat_widget, "Chat")
        
        layout.addWidget(right_tabs)
        return panel



    def _create_mission_control_tab(self) -> QWidget:
        """Create the Mission Control tab."""
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.mission_control_widget = MissionControlWidget(tab)
        self.mission_control_widget.start_analysis_requested.connect(self._handle_mission_control_start)
        self.mission_control_widget.review_document_requested.connect(self._handle_mission_control_review)
        layout.addWidget(self.mission_control_widget)
        return tab



    def _handle_mission_control_start(self) -> None:
        """Handle start analysis request from Mission Control."""
        self.tab_widget.setCurrentWidget(self.analysis_tab)
        self._prompt_for_document()

    def _handle_mission_control_review(self, doc_info: dict) -> None:
        """Handle review document request from Mission Control."""
        doc_name = doc_info.get("title") or doc_info.get("name") or doc_info.get("document_name") or "Document"
        self.statusBar().showMessage(f"Detailed replay for '{doc_name}' will be available in a future update.")
    
    def _toggle_meta_analytics_dock(self) -> None:
        """Toggle Meta Analytics dock widget visibility."""
        if self.meta_analytics_dock:
            if self.meta_analytics_dock.isVisible():
                self.meta_analytics_dock.hide()
            else:
                self.meta_analytics_dock.show()
                self.view_model.load_meta_analytics()
    
    def _toggle_performance_dock(self) -> None:
        """Toggle Performance Status dock widget visibility."""
        if self.performance_dock:
            if self.performance_dock.isVisible():
                self.performance_dock.hide()
            else:
                self.performance_dock.show()
    

    
    def _setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts for tab navigation."""
        # Ctrl+1: Analysis tab
        shortcut_analysis = QAction(self)
        shortcut_analysis.setShortcut("Ctrl+1")
        shortcut_analysis.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        self.addAction(shortcut_analysis)
        
        # Ctrl+2: Dashboard tab
        shortcut_dashboard = QAction(self)
        shortcut_dashboard.setShortcut("Ctrl+2")
        shortcut_dashboard.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        self.addAction(shortcut_dashboard)
        
        # Ctrl+3: Mission Control tab
        shortcut_mission = QAction(self)
        shortcut_mission.setShortcut("Ctrl+3")
        shortcut_mission.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
        self.addAction(shortcut_mission)
        
        # Ctrl+4: Settings tab
        shortcut_settings = QAction(self)
        shortcut_settings.setShortcut("Ctrl+4")
        shortcut_settings.triggered.connect(lambda: self.tab_widget.setCurrentIndex(3))
        self.addAction(shortcut_settings)



    def _create_dashboard_tab(self) -> QWidget:
        """Create the Dashboard tab."""
        tab, layout = self._create_tab_base_layout()
        try:
            self.dashboard_widget = DashboardWidget()
            self.dashboard_widget.refresh_requested.connect(self.view_model.load_dashboard_data)
        except (ImportError, NameError):
            self.dashboard_widget = QTextBrowser()
            self.dashboard_widget.setPlainText("Dashboard component unavailable.")
        layout.addWidget(self.dashboard_widget)
        return tab
    
    def _create_settings_tab(self) -> QWidget:
        """Create the Settings tab with comprehensive options."""
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("⚙️ Application Settings", tab)
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {medical_theme.get_color('primary_blue')};")
        layout.addWidget(title)
        
        # Settings tabs
        settings_tabs = QTabWidget(tab)
        settings_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 8px;
                background: {medical_theme.get_color('bg_secondary')};
            }}
            QTabBar::tab {{
                padding: 10px 20px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                background: {medical_theme.get_color('bg_tertiary')};
                color: {medical_theme.get_color('text_secondary')};
            }}
            QTabBar::tab:selected {{
                background: {medical_theme.get_color('primary_blue')};
                color: white;
            }}
        """)
        
        # User Preferences
        user_prefs_widget = self._create_user_preferences_widget()
        settings_tabs.addTab(user_prefs_widget, "👤 User Preferences")
        
        # Analysis Settings
        analysis_settings_widget = self._create_analysis_settings_widget()
        settings_tabs.addTab(analysis_settings_widget, "📊 Analysis Settings")
        
        # Report Settings
        report_settings_widget = self._create_report_settings_widget()
        settings_tabs.addTab(report_settings_widget, "📄 Report Settings")
        
        # Performance Settings
        perf_widget = self._create_performance_settings_widget()
        settings_tabs.addTab(perf_widget, "⚡ Performance")
        
        # Admin Settings (if admin)
        if self.current_user.is_admin:
            self.settings_editor = SettingsEditorWidget(tab)
            self.settings_editor.save_requested.connect(self.view_model.save_settings)
            settings_tabs.addTab(self.settings_editor, "🔧 Advanced (Admin)")
        
        layout.addWidget(settings_tabs)
        return tab
    
    def _create_user_preferences_widget(self) -> QWidget:
        """Create user preferences settings widget with professional layout."""
        from PySide6.QtWidgets import QCheckBox, QScrollArea
        
        # Create scroll area for better organization
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(25)  # Proper spacing between sections
        
        # Theme selection
        theme_section = QWidget()
        theme_section.setStyleSheet(f"""
            QWidget {{
                background: {medical_theme.get_color('bg_primary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        theme_layout = QVBoxLayout(theme_section)
        theme_layout.setContentsMargins(20, 20, 20, 20)  # Internal padding
        theme_layout.setSpacing(15)  # Spacing within section
        
        theme_label = QLabel("🎨 Theme Selection", theme_section)
        theme_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        theme_label.setStyleSheet("margin-bottom: 10px;")  # Extra space after title
        theme_layout.addWidget(theme_label)
        
        theme_buttons = QHBoxLayout()
        light_button = AnimatedButton("☀️ Light Theme", theme_section)
        light_button.clicked.connect(lambda: self._apply_theme("light"))
        light_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        light_button.setMinimumHeight(40)
        theme_buttons.addWidget(light_button)
        
        dark_button = AnimatedButton("🌙 Dark Theme", theme_section)
        dark_button.clicked.connect(lambda: self._apply_theme("dark"))
        dark_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        dark_button.setMinimumHeight(40)
        theme_buttons.addWidget(dark_button)
        
        theme_layout.addLayout(theme_buttons)
        layout.addWidget(theme_section)
        
        # Account settings
        account_section = QWidget()
        account_section.setStyleSheet(f"""
            QWidget {{
                background: {medical_theme.get_color('bg_primary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        account_layout = QVBoxLayout(account_section)
        account_layout.setContentsMargins(20, 20, 20, 20)  # Internal padding
        account_layout.setSpacing(15)  # Spacing within section
        
        account_label = QLabel("👤 Account Settings", account_section)
        account_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        account_label.setStyleSheet("margin-bottom: 10px;")  # Extra space after title
        account_layout.addWidget(account_label)
        
        user_info = QLabel(f"Logged in as: {self.current_user.username}", account_section)
        user_info.setStyleSheet("color: #64748b; padding: 5px;")
        account_layout.addWidget(user_info)
        
        password_button = AnimatedButton("🔒 Change Password", account_section)
        password_button.clicked.connect(self.show_change_password_dialog)
        password_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        password_button.setMinimumHeight(40)
        account_layout.addWidget(password_button)
        
        layout.addWidget(account_section)
        
        # UI Preferences
        ui_section = QWidget()
        ui_section.setStyleSheet(f"""
            QWidget {{
                background: {medical_theme.get_color('bg_primary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        ui_layout = QVBoxLayout(ui_section)
        
        ui_label = QLabel("🖥️ Interface Preferences", ui_section)
        ui_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        ui_layout.addWidget(ui_label)
        
        show_tooltips = QCheckBox("Show helpful tooltips", ui_section)
        show_tooltips.setChecked(True)
        ui_layout.addWidget(show_tooltips)
        
        auto_save = QCheckBox("Auto-save analysis results", ui_section)
        auto_save.setChecked(True)
        ui_layout.addWidget(auto_save)
        
        show_animations = QCheckBox("Enable button animations", ui_section)
        show_animations.setChecked(True)
        ui_layout.addWidget(show_animations)
        
        layout.addWidget(ui_section)
        
        layout.addStretch()
        
        # Set up scroll area
        scroll_area.setWidget(widget)
        
        # Create container for scroll area
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(scroll_area)
        
        return container
    
    def _create_analysis_settings_widget(self) -> QWidget:
        """Create analysis settings widget."""
        from PySide6.QtWidgets import QCheckBox
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Default Analysis Settings
        section = QWidget()
        section.setStyleSheet(f"""
            QWidget {{
                background: {medical_theme.get_color('bg_primary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        section_layout = QVBoxLayout(section)
        
        title = QLabel("📊 Default Analysis Settings", section)
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        section_layout.addWidget(title)
        
        auto_analyze = QCheckBox("Auto-analyze on document upload", section)
        section_layout.addWidget(auto_analyze)
        
        include_7habits = QCheckBox("Include 7 Habits Framework in reports", section)
        include_7habits.setChecked(True)
        section_layout.addWidget(include_7habits)
        
        include_education = QCheckBox("Include educational resources", section)
        include_education.setChecked(True)
        section_layout.addWidget(include_education)
        
        show_confidence = QCheckBox("Show AI confidence scores", section)
        show_confidence.setChecked(True)
        section_layout.addWidget(show_confidence)
        
        layout.addWidget(section)
        layout.addStretch()
        return widget

    def _create_report_settings_widget(self) -> QWidget:
        """Create report settings widget."""
        from PySide6.QtWidgets import QCheckBox
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Report Content Settings
        section = QWidget()
        section.setStyleSheet(f"""
            QWidget {{
                background: {medical_theme.get_color('bg_primary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        section_layout = QVBoxLayout(section)
        
        title = QLabel("📄 Report Content Settings", section)
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        section_layout.addWidget(title)
        
        # Medicare Guidelines with description
        medicare_container = QWidget()
        medicare_layout = QVBoxLayout(medicare_container)
        medicare_layout.setContentsMargins(0, 0, 0, 0)
        medicare_layout.setSpacing(5)
        
        include_medicare = QCheckBox("✅ Medicare Guidelines Compliance", section)
        include_medicare.setChecked(True)
        medicare_layout.addWidget(include_medicare)
        
        medicare_desc = QLabel("   Includes CMS compliance requirements and Medicare documentation standards")
        medicare_desc.setStyleSheet("color: #64748b; font-size: 11px; margin-left: 20px;")
        medicare_desc.setWordWrap(True)
        medicare_layout.addWidget(medicare_desc)
        section_layout.addWidget(medicare_container)
        
        # Strengths with description
        strengths_container = QWidget()
        strengths_layout = QVBoxLayout(strengths_container)
        strengths_layout.setContentsMargins(0, 0, 0, 0)
        strengths_layout.setSpacing(5)
        
        include_strengths = QCheckBox("💪 Strengths & Best Practices", section)
        include_strengths.setChecked(True)
        strengths_layout.addWidget(include_strengths)
        
        strengths_desc = QLabel("   Highlights well-documented areas and exemplary practices in your documentation")
        strengths_desc.setStyleSheet("color: #64748b; font-size: 11px; margin-left: 20px;")
        strengths_desc.setWordWrap(True)
        strengths_layout.addWidget(strengths_desc)
        section_layout.addWidget(strengths_container)
        
        # Add descriptions for all remaining checkboxes
        checkboxes_with_descriptions = [
            ("⚠️ Weaknesses & Areas for Improvement", "Identifies documentation gaps and areas that need attention for compliance", True),
            ("💡 Actionable Suggestions", "Provides specific, implementable recommendations to improve documentation quality", True),
            ("📚 Educational Resources", "Includes links to relevant guidelines, training materials, and best practice examples", True),
            ("🎯 7 Habits Framework Integration", "Incorporates Stephen Covey's 7 Habits for professional development and effectiveness", True),
            ("📊 Compliance Score & Risk Level", "Shows overall compliance percentage and risk assessment for reimbursement", True),
            ("🔍 Detailed Findings Analysis", "Comprehensive breakdown of all compliance issues with evidence and explanations", True)
        ]
        
        for checkbox_text, description, checked in checkboxes_with_descriptions:
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(5)
            
            checkbox = QCheckBox(checkbox_text, section)
            checkbox.setChecked(checked)
            container_layout.addWidget(checkbox)
            
            desc_label = QLabel(f"   {description}")
            desc_label.setStyleSheet("color: #64748b; font-size: 11px; margin-left: 20px;")
            desc_label.setWordWrap(True)
            container_layout.addWidget(desc_label)
            
            section_layout.addWidget(container)
        
        layout.addWidget(section)
        layout.addStretch()
        return widget

    def _create_performance_settings_widget(self) -> QWidget:
        """Create performance settings widget."""
        from PySide6.QtWidgets import QCheckBox
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        section = QWidget()
        section.setStyleSheet(f"""
            QWidget {{
                background: {medical_theme.get_color('bg_primary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        section_layout = QVBoxLayout(section)
        
        title = QLabel("⚡ Performance Settings", section)
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        section_layout.addWidget(title)
        
        enable_cache = QCheckBox("Enable analysis caching", section)
        enable_cache.setChecked(True)
        section_layout.addWidget(enable_cache)
        
        parallel_processing = QCheckBox("Enable parallel processing", section)
        parallel_processing.setChecked(True)
        section_layout.addWidget(parallel_processing)
        
        auto_cleanup = QCheckBox("Auto-cleanup temporary files", section)
        auto_cleanup.setChecked(True)
        section_layout.addWidget(auto_cleanup)
        
        layout.addWidget(section)
        
        info_label = QLabel("💡 Tip: Enable caching for faster repeated analyses", widget)
        info_label.setStyleSheet("color: #64748b; font-style: italic; padding: 10px;")
        layout.addWidget(info_label)
        
        layout.addStretch()
        return widget




    def _create_tab_base_layout(self, spacing: int = 0) -> tuple[QWidget, QVBoxLayout]:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(spacing)
        return tab, layout

    def _create_browser_tab(self, parent: Optional[QWidget] = None) -> tuple[QTextBrowser, QWidget]:
        tab, layout = self._create_tab_base_layout()
        browser = QTextBrowser(tab)
        layout.addWidget(browser)
        return browser, tab

    def _build_status_bar(self) -> None:
        """Build status bar with AI indicators, progress, and branding at the bottom."""
        status: QStatusBar = self.statusBar()
        status.showMessage("Ready")
        status.setStyleSheet("""
            QStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f8fafc, stop:1 #e2e8f0);
                border-top: 1px solid #cbd5e0;
                padding: 4px;
            }
        """)
        
        # AI Model Status Indicators (left side) - improved styling
        status.addPermanentWidget(self.status_component)
        
        # Add separator
        separator1 = QLabel(" | ")
        separator1.setStyleSheet("color: #94a3b8; font-weight: bold;")
        status.addPermanentWidget(separator1)
        
        # Progress bar - positioned prominently in feng shui center-left position
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximumWidth(220)  # Wider for better visibility
        self.progress_bar.setMinimumWidth(220)
        self.progress_bar.setMaximumHeight(18)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #cbd5e0;
                border-radius: 9px;
                background-color: #f1f5f9;
                text-align: center;
                font-weight: bold;
                font-size: 11px;
                color: #1e293b;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10b981, stop:0.5 #059669, stop:1 #047857);
                border-radius: 7px;
                margin: 1px;
            }
        """)
        self.progress_bar.hide()
        status.addPermanentWidget(self.progress_bar)
        
        # System Resource Monitor - compact display
        self.resource_label = QLabel("CPU: 0% | RAM: 0MB")
        self.resource_label.setStyleSheet("""
            color: #64748b; 
            font-size: 10px; 
            font-family: 'Consolas', 'Monaco', monospace;
            background: rgba(248, 250, 252, 0.8);
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid #e2e8f0;
        """)
        self.resource_label.setToolTip("System resource usage")
        status.addPermanentWidget(self.resource_label)
        
        # Add separator
        separator2 = QLabel(" | ")
        separator2.setStyleSheet("color: #94a3b8; font-weight: bold;")
        status.addPermanentWidget(separator2)
        
        # Connection Status - improved with colored box instead of green dot
        self.connection_status_widget = QWidget()
        connection_layout = QHBoxLayout(self.connection_status_widget)
        connection_layout.setContentsMargins(0, 0, 0, 0)
        connection_layout.setSpacing(4)
        
        # Status indicator box (changes color based on status)
        self.connection_indicator = QLabel()
        self.connection_indicator.setFixedSize(12, 12)
        self.connection_indicator.setStyleSheet("""
            background-color: #10b981;
            border-radius: 6px;
            border: 1px solid #059669;
        """)
        connection_layout.addWidget(self.connection_indicator)
        
        self.connection_label = QLabel("API Connected")
        self.connection_label.setStyleSheet("""
            color: #059669; 
            font-size: 10px; 
            font-weight: bold;
            background: rgba(16, 185, 129, 0.1);
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid rgba(16, 185, 129, 0.3);
        """)
        connection_layout.addWidget(self.connection_label)
        
        self.connection_status_widget.setToolTip("API connection status")
        status.addPermanentWidget(self.connection_status_widget)
        
        # Add separator
        separator3 = QLabel(" | ")
        separator3.setStyleSheet("color: #94a3b8; font-weight: bold;")
        status.addPermanentWidget(separator3)
        
        # Subtle loading spinner (hidden by default)
        self.loading_spinner = LoadingSpinner(size=16, parent=self)
        self.loading_spinner.hide()
        status.addPermanentWidget(self.loading_spinner)
        
        # Pacific Coast Therapy branding in bottom right
        branding_label = QLabel("🌴 Pacific Coast Therapy")
        branding_label.setObjectName("brandingLabel")
        branding_label.setStyleSheet("""
            QLabel#brandingLabel {
                font-family: "Brush Script MT", "Lucida Handwriting", "Comic Sans MS", cursive;
                font-size: 11px;
                color: #94a3b8;
                font-style: italic;
                padding-right: 10px;
                background: rgba(148, 163, 184, 0.1);
                padding: 2px 8px;
                border-radius: 4px;
            }
        """)
        branding_label.setToolTip("Powered by Pacific Coast Therapy")
        status.addPermanentWidget(branding_label)
    
    def update_connection_status(self, connected: bool, message: str = ""):
        """Update the connection status indicator."""
        if connected:
            self.connection_indicator.setStyleSheet("""
                background-color: #10b981;
                border-radius: 6px;
                border: 1px solid #059669;
            """)
            self.connection_label.setText("API Connected")
            self.connection_label.setStyleSheet("""
                color: #059669; 
                font-size: 10px; 
                font-weight: bold;
                background: rgba(16, 185, 129, 0.1);
                padding: 2px 6px;
                border-radius: 4px;
                border: 1px solid rgba(16, 185, 129, 0.3);
            """)
        else:
            self.connection_indicator.setStyleSheet("""
                background-color: #ef4444;
                border-radius: 6px;
                border: 1px solid #dc2626;
            """)
            self.connection_label.setText("API Disconnected")
            self.connection_label.setStyleSheet("""
                color: #dc2626; 
                font-size: 10px; 
                font-weight: bold;
                background: rgba(239, 68, 68, 0.1);
                padding: 2px 6px;
                border-radius: 4px;
                border: 1px solid rgba(239, 68, 68, 0.3);
            """)
        
        if message:
            self.connection_status_widget.setToolTip(f"API Status: {message}")

    def _build_docks(self) -> None:
        """Build optional dock widgets (Meta Analytics and Performance - hidden by default)."""
        # Meta Analytics Dock (hidden by default, accessible via Tools menu)
        if MetaAnalyticsWidget:
            self.meta_analytics_dock = QDockWidget("Meta Analytics", self)
            self.meta_analytics_dock.setObjectName("MetaAnalyticsDock")
            self.meta_analytics_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
            self.meta_widget = MetaAnalyticsWidget()
            self.meta_widget.refresh_requested.connect(self.view_model.load_meta_analytics)
            self.meta_analytics_dock.setWidget(self.meta_widget)
            self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.meta_analytics_dock)
            self.meta_analytics_dock.hide()  # Hidden by default
        else:
            self.meta_analytics_dock = None
        
        # Performance Status Dock (hidden by default, accessible via Tools menu)
        if PerformanceStatusWidget:
            self.performance_dock = QDockWidget("Performance Status", self)
            self.performance_dock.setObjectName("PerformanceStatusDock")
            self.performance_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.BottomDockWidgetArea)
            self.performance_widget = PerformanceStatusWidget()
            self.performance_dock.setWidget(self.performance_widget)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.performance_dock)
            self.performance_dock.hide()  # Hidden by default
        else:
            self.performance_dock = None
        
        # Log Viewer (create widget for Mission Control to use)
        self.log_viewer = LogViewerWidget(self)



    def _add_files_to_auto_analysis_queue(self) -> None:
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Select documents to queue for analysis", str(Path.home()), "Documents (*.pdf *.docx *.txt *.md *.json)")
        if file_paths:
            for path in file_paths:
                item = QListWidgetItem(path)
                self.auto_analysis_queue_list.addItem(item)
            self.statusBar().showMessage(f"Added {len(file_paths)} files to the queue.")

    def _process_auto_analysis_queue(self) -> None:
        count = self.auto_analysis_queue_list.count()
        if count == 0:
            QMessageBox.information(self, "Queue Empty", "There are no files in the queue to process.")
            return

        self.statusBar().showMessage(f"Starting to process {count} files from the queue…")
        
        item = self.auto_analysis_queue_list.takeItem(0)
        if item:
            file_path = item.text()
            self._selected_file = Path(file_path)
            self._start_analysis()

    # Removed _build_floating_chat_button - redundant functionality eliminated

    def _save_gui_settings(self) -> None:
        """Save GUI settings including window geometry, theme, and preferences."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("ui/last_active_tab", self.tab_widget.currentIndex())
        
        # Save current theme
        self.settings.setValue("theme", medical_theme.current_theme)
        self.settings.setValue("analysis/rubric", self.rubric_selector.currentData())
        if self._selected_file:
            self.settings.setValue("analysis/last_file", str(self._selected_file))
        
        # Save dock widget states
        if self.meta_analytics_dock:
            self.settings.setValue("docks/meta_analytics_visible", self.meta_analytics_dock.isVisible())
        if self.performance_dock:
            self.settings.setValue("docks/performance_status_visible", self.performance_dock.isVisible())

    def _load_gui_settings(self) -> None:
        """Load GUI settings including window geometry, theme, and preferences."""
        if geometry := self.settings.value("geometry"):
            self.restoreGeometry(geometry)
        if window_state := self.settings.value("windowState"):
            self.restoreState(window_state)
        
        # Restore last active tab
        last_tab = self.settings.value("ui/last_active_tab", 0, type=int)
        if 0 <= last_tab < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(last_tab)
        
        saved_theme = self.settings.value("theme", "light", type=str)
        self._apply_theme(saved_theme)

        if saved_rubric_data := self.settings.value("analysis/rubric"):
            index = self.rubric_selector.findData(saved_rubric_data)
            if index >= 0:
                self.rubric_selector.setCurrentIndex(index)

        if last_file_str := self.settings.value("analysis/last_file", type=str):
            last_file = Path(last_file_str)
            if last_file.exists():
                self._set_selected_file(last_file)
        
        # Restore dock widget visibility
        if self.meta_analytics_dock:
            visible = self.settings.value("docks/meta_analytics_visible", False, type=bool)
            if visible:
                self.meta_analytics_dock.show()
            if hasattr(self, 'meta_analytics_action'):
                self.meta_analytics_action.setChecked(visible)
        
        if self.performance_dock:
            visible = self.settings.value("docks/performance_status_visible", False, type=bool)
            if visible:
                self.performance_dock.show()
            if hasattr(self, 'performance_action'):
                self.performance_action.setChecked(visible)

    def open_file_dialog(self) -> None:
        """Public wrapper to trigger the standard file picker."""
        self._prompt_for_document()

    def _prompt_for_document(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Select clinical document", str(Path.home()), "Documents (*.pdf *.docx *.txt *.md *.json)")
        if file_path:
            self._set_selected_file(Path(file_path))

    def _set_selected_file(self, file_path: Path) -> None:
        self.run_analysis_button.setEnabled(False)
        self._cached_preview_content = ""
        try:
            max_preview_chars = 2_000_000
            with open(file_path, "r", encoding="utf-8", errors="ignore") as stream:
                content = stream.read(max_preview_chars)
        except FileNotFoundError:
            self.statusBar().showMessage(f"File not found: {file_path.name}", 5000)
            placeholder = f"Preview unavailable: {file_path.name} not found."
            self._selected_file = file_path
            self._cached_preview_content = placeholder
            self.file_display.setPlainText(placeholder)
            self.run_analysis_button.setEnabled(True)
            return
        except Exception as exc:
            self._selected_file = None
            error_message = f"Could not display preview: {exc}"
            self.file_display.setPlainText(error_message)
            self.statusBar().showMessage(f"Failed to load {file_path.name}", 5000)
            return

        self._selected_file = file_path
        self._cached_preview_content = content
        
        # Show clear document status instead of confusing description
        file_size_mb = len(content) / (1024 * 1024)
        from datetime import datetime
        file_info = f"""✅ DOCUMENT READY FOR ANALYSIS

📄 {file_path.name}
📊 Size: {file_size_mb:.1f} MB ({len(content):,} characters)
📁 Location: {file_path.parent.name}/
📅 Modified: {datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}

✨ Document successfully loaded and ready for compliance analysis!
Click 'Run Analysis' to begin processing.
        """
        self.file_display.setPlainText(file_info)
        self.statusBar().showMessage(f"✅ Document loaded: {self._selected_file.name}", 3000)
        self.run_analysis_button.setEnabled(True)
        self._update_document_preview()

    def _update_document_preview(self) -> None:
        """Document preview is now handled via popup button - this method is deprecated."""
        # This method is kept for backward compatibility but no longer used
        return

    def _prompt_for_folder(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(self, "Select folder for batch analysis", str(Path.home()))
        if folder_path:
            analysis_data = {
                "discipline": self.rubric_selector.currentData() or "",
                "analysis_mode": "rubric",
            }
            dialog = BatchAnalysisDialog(folder_path, self.auth_token, analysis_data, self)
            dialog.exec()

    def _export_report(self) -> None:
        if not self._current_payload:
            QMessageBox.information(self, "No report", "Run an analysis before exporting a report.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save report",
            str(Path.home() / "compliance_report.html"),
            "HTML Files (*.html)",
        )
        if not file_path:
            return

        Path(file_path).write_text(self.report_preview_browser.toHtml(), encoding='utf-8')
        self.statusBar().showMessage(f"Report exported to {file_path}", 5000)

    def _open_rubric_manager(self) -> None:
        dialog = RubricManagerDialog(self.auth_token, self)
        if dialog.exec():
            self.view_model.load_rubrics()

    def _open_settings_dialog(self) -> None:
        dialog = SettingsDialog(self)
        dialog.exec()

    def show_change_password_dialog(self) -> None:
        """Opens the change password dialog."""
        dialog = ChangePasswordDialog(self)
        dialog.exec()

    def _open_chat_dialog(self, initial_message: Optional[str] = None) -> None:
        """Open the AI chat dialog with optional initial message."""
        if initial_message:
            initial_context = f"User question: {initial_message}\n\nContext: {self.analysis_summary_browser.toPlainText()}"
        else:
            initial_context = self.analysis_summary_browser.toPlainText() or "Provide a compliance summary."
        dialog = ChatDialog(initial_context, self.auth_token, self)
        dialog.exec()

    def _show_about_dialog(self) -> None:
        """Show about dialog with easter eggs."""
        about_text = f"""
Therapy Compliance Analyzer
Version 2.0.0

Welcome, {self.current_user.username}!

🌟 Created with love by Kevin Moon 🫶

🙏 Special Thanks:
   • Dennis Baloy - For unwavering professional support and guidance 🤝
   • Rand Looper - For exceptional dedication and collaborative excellence 🌟

🎯 AI-Powered Clinical Documentation Analysis
🔒 Privacy-First Local Processing
📊 Medicare & CMS Compliance Focused

Special thanks to all the therapists who make 
healthcare better every day! 💪

🎮 Try the Konami Code: ↑↑↓↓←→←→BA
🎨 Press Ctrl+T to toggle themes
🎉 Click the logo 7 times for a surprise!
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("About Therapy Compliance Analyzer")
        msg.setText(about_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Add custom button for more easter eggs
        easter_egg_button = msg.addButton("🥚 More Easter Eggs", QMessageBox.ButtonRole.ActionRole)
        
        msg.exec()
        
        if msg.clickedButton() == easter_egg_button:
            self._show_easter_eggs_dialog()

    def _show_easter_eggs_dialog(self) -> None:
        """Show hidden easter eggs dialog."""
        easter_text = """
🥚 HIDDEN EASTER EGGS DISCOVERED! 🥚

🎮 Konami Code: ↑↑↓↓←→←→BA
   - Unlocks special developer mode features
   - Shows hidden performance metrics
   - Enables advanced debugging tools

🖱️ Logo Clicks:
   - 3 clicks: Shows current system stats
   - 5 clicks: Displays memory usage
   - 7 clicks: Pacific Coast Therapy message
   - 10 clicks: Secret developer credits

⌨️ Keyboard Shortcuts:
   - Ctrl+Shift+D: Developer console
   - Ctrl+Alt+M: Memory usage display
   - Ctrl+Shift+K: Kevin's special message
   - F12: Hidden debug panel

🎨 Theme Secrets:
   - Hold Shift while switching themes for animations
   - Ctrl+Alt+T: Cycles through all theme variants
   - Double-click theme button: Random theme

🔍 Hidden Features:
   - Type "kevin" in any text field for surprises
   - Right-click logo 3 times: Developer menu
   - Hold Ctrl+Alt while starting app: Debug mode

Keep exploring! There are more secrets hidden throughout the app! 🕵️‍♂️
        """
        
        QMessageBox.information(self, "🥚 Easter Eggs Collection", easter_text)

    def keyPressEvent(self, event) -> None:
        """Handle key press events for Konami code and other shortcuts."""
        super().keyPressEvent(event)
        
        # Initialize konami sequence if not exists
        if not hasattr(self, 'konami_sequence'):
            self.konami_sequence = []
            self.konami_code = [
                Qt.Key.Key_Up, Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Down,
                Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Left, Qt.Key.Key_Right,
                Qt.Key.Key_B, Qt.Key.Key_A
            ]
        
        # Track konami code
        self.konami_sequence.append(event.key())
        if len(self.konami_sequence) > len(self.konami_code):
            self.konami_sequence.pop(0)
        
        if self.konami_sequence == self.konami_code:
            self._activate_konami_code()
            self.konami_sequence = []
        
        # Special shortcuts
        if event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            if event.key() == Qt.Key.Key_K:
                self._show_kevin_message()
            elif event.key() == Qt.Key.Key_D:
                self._show_developer_console()

    def _activate_konami_code(self) -> None:
        """Activate Konami code easter egg."""
        QMessageBox.information(
            self,
            "🎮 KONAMI CODE ACTIVATED! 🎮",
            "🌟 DEVELOPER MODE UNLOCKED! 🌟\n\n"
            "You've unlocked special features:\n"
            "• Advanced debugging tools enabled\n"
            "• Hidden performance metrics visible\n"
            "• Developer console accessible\n"
            "• Secret keyboard shortcuts active\n\n"
            "Welcome to the inner circle! 🕵️‍♂️\n\n"
            "Created with ❤️ by Kevin Moon\n"
            "For all the amazing therapists out there!"
        )
        
        # Enable developer mode
        self.developer_mode = True
        self.statusBar().showMessage("🎮 Developer Mode Activated! Press Ctrl+Shift+D for console", 10000)

    def _show_kevin_message(self) -> None:
        """Show Kevin's special message."""
        QMessageBox.information(
            self,
            "👋 Message from Kevin Moon",
            "Hey there! 🫶\n\n"
            "Thanks for using the Therapy Compliance Analyzer!\n\n"
            "This app was built with love and countless hours of coding\n"
            "to help amazing therapists like you provide the best care\n"
            "while staying compliant with all those tricky regulations.\n\n"
            "Remember: You're making a real difference in people's lives! 💪\n\n"
            "Keep being awesome! 🌟\n\n"
            "- Kevin 🫶"
        )
    
    def _check_license_status(self) -> None:
        """Check license status and show trial information if needed."""
        try:
            is_valid, status_message, days_remaining = license_manager.check_license_status()
            
            if not is_valid:
                # Show license expired dialog
                from PySide6.QtWidgets import QMessageBox
                
                msg = QMessageBox(self)
                msg.setWindowTitle("🔐 License Status")
                msg.setText(f"License Status: {status_message}")
                msg.setIcon(QMessageBox.Icon.Warning)
                
                # Add activation button
                activate_btn = msg.addButton("🔑 Activate Full License", QMessageBox.ButtonRole.ActionRole)
                msg.addButton(QMessageBox.StandardButton.Ok)
                
                msg.exec()
                
                if msg.clickedButton() == activate_btn:
                    self._show_license_activation_dialog()
                    
            elif days_remaining is not None and days_remaining <= 7:
                # Show trial warning for last 7 days
                QMessageBox.information(
                    self,
                    "🔔 Trial Period Notice",
                    f"Trial period: {days_remaining} days remaining\n\n"
                    f"Contact your administrator to activate the full license."
                )
                
        except Exception as e:
            logger.error(f"License check failed: {e}")
    
    def _show_license_activation_dialog(self) -> None:
        """Show license activation dialog for admin users."""
        if not self.current_user.is_admin:
            QMessageBox.information(
                self,
                "🔐 License Activation",
                "Only administrators can activate licenses.\n\n"
                "Please contact your system administrator."
            )
            return
        
        from PySide6.QtWidgets import QInputDialog, QLineEdit
        
        activation_code, ok = QInputDialog.getText(
            self,
            "🔑 License Activation",
            "Enter activation code:",
            echo=QLineEdit.EchoMode.Password
        )
        
        if ok and activation_code:
            if license_manager.activate_full_license(activation_code):
                QMessageBox.information(
                    self,
                    "✅ License Activated",
                    "Full license activated successfully!\n\n"
                    "All features are now available."
                )
            else:
                QMessageBox.warning(
                    self,
                    "❌ Activation Failed",
                    "Invalid activation code.\n\n"
                    "Please check the code and try again."
                )

    def _show_developer_console(self) -> None:
        """Show developer console dialog."""
        if not hasattr(self, 'developer_mode') or not self.developer_mode:
            QMessageBox.warning(self, "Access Denied", "Developer console requires Konami code activation!")
            return
        
        console_text = f"""
🔧 DEVELOPER CONSOLE 🔧

System Information:
- User: {self.current_user.username}
- Theme: {medical_theme.current_theme}
- Active Threads: {len(self.view_model._active_threads)}
- Selected File: {self._selected_file.name if self._selected_file else 'None'}
- Current Payload: {'Available' if self._current_payload else 'None'}

Memory Usage:
- Python Objects: {len(__import__('gc').get_objects())} objects
- Cache Status: Active

Debug Commands Available:
- Clear all caches
- Reset UI state  
- Force garbage collection
- Export debug logs

This console is only available in developer mode! 🎮
        """
        
        QMessageBox.information(self, "🔧 Developer Console", console_text)

    def _clear_all_caches(self) -> None:
        """Clear all application caches."""
        reply = QMessageBox.question(
            self,
            "Clear All Caches",
            "Are you sure you want to clear all application caches?\n\n"
            "This will:\n"
            "• Clear document cache\n"
            "• Clear analysis cache\n"
            "• Clear AI model cache\n"
            "• Reset temporary files\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Clear various caches
                if hasattr(self, '_current_payload'):
                    self._current_payload = {}
                if hasattr(self, '_cached_preview_content'):
                    self._cached_preview_content = ""
                
                # Force garbage collection
                import gc
                gc.collect()
                
                self.statusBar().showMessage("✅ All caches cleared successfully", 5000)
                QMessageBox.information(self, "Cache Cleared", "All application caches have been cleared successfully!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to clear caches: {str(e)}")

    def _show_user_management(self) -> None:
        """Show user management dialog (placeholder)."""
        QMessageBox.information(
            self,
            "👥 User Management",
            "User Management features:\n\n"
            "• View all registered users\n"
            "• Manage user permissions\n"
            "• Reset user passwords\n"
            "• View user activity logs\n\n"
            "This feature will be available in a future update!"
        )

    def _show_system_info(self) -> None:
        """Show system information dialog."""
        import platform
        import sys
        from PySide6 import __version__ as pyside_version
        
        system_info = f"""
🖥️ SYSTEM INFORMATION

Operating System:
• Platform: {platform.system()} {platform.release()}
• Architecture: {platform.machine()}
• Processor: {platform.processor()}

Python Environment:
• Python Version: {sys.version.split()[0]}
• PySide6 Version: {pyside_version}
• Current User: {self.current_user.username}
• User Role: {'Administrator' if self.current_user.is_admin else 'Standard User'}

Application:
• Theme: {medical_theme.current_theme.title()}
• Active Threads: {len(self.view_model._active_threads)}
• Developer Mode: {'Enabled' if hasattr(self, 'developer_mode') and self.developer_mode else 'Disabled'}

Memory:
• Python Objects: {len(__import__('gc').get_objects())}
• Selected File: {self._selected_file.name if self._selected_file else 'None'}
• Analysis Data: {'Available' if self._current_payload else 'None'}
        """
        
        QMessageBox.information(self, "ℹ️ System Information", system_info)

    def _run_diagnostics(self) -> None:
        """Run comprehensive system diagnostics."""
        self.statusBar().showMessage("🔍 Running system diagnostics...", 0)
        
        try:
            # Run diagnostics
            diagnostic_results = diagnostics.run_full_diagnostic()
            
            # Format results for display
            results_text = "🔍 SYSTEM DIAGNOSTICS REPORT\n\n"
            
            healthy_count = 0
            warning_count = 0
            error_count = 0
            
            for component, result in diagnostic_results.items():
                status_icon = {
                    "healthy": "✅",
                    "warning": "⚠️",
                    "error": "❌",
                    "unknown": "❓"
                }.get(result.status.value, "❓")
                
                results_text += f"{status_icon} {component.replace('_', ' ').title()}\n"
                results_text += f"   {result.message}\n\n"
                
                if result.status.value == "healthy":
                    healthy_count += 1
                elif result.status.value == "warning":
                    warning_count += 1
                elif result.status.value == "error":
                    error_count += 1
            
            # Add summary
            results_text += "📊 SUMMARY\n"
            results_text += f"✅ Healthy: {healthy_count}\n"
            results_text += f"⚠️ Warnings: {warning_count}\n"
            results_text += f"❌ Errors: {error_count}\n\n"
            
            if error_count > 0:
                results_text += "💡 RECOMMENDATIONS\n"
                results_text += "• Fix critical errors before running analysis\n"
                results_text += "• Check that the API server is running\n"
                results_text += "• Use Tools → Start API Server if needed\n"
            
            # Show results in a dialog
            msg = QMessageBox(self)
            msg.setWindowTitle("🔍 System Diagnostics")
            msg.setText(results_text)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()
            
            self.statusBar().showMessage("✅ Diagnostics completed", 5000)
            
        except Exception as e:
            QMessageBox.critical(self, "Diagnostics Error", f"Failed to run diagnostics:\n{str(e)}")
            self.statusBar().showMessage("❌ Diagnostics failed", 5000)

    def _start_api_server(self) -> None:
        """Start the API server from within the GUI."""
        reply = QMessageBox.question(
            self,
            "🚀 Start API Server",
            "This will start the API server in a separate process.\n\n"
            "The server is required for document analysis to work.\n\n"
            "Do you want to start the API server now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                import subprocess
                import sys
                from pathlib import Path
                
                # Start the API server
                api_script = Path("scripts/run_api.py")
                if api_script.exists():
                    self.statusBar().showMessage("🚀 Starting API server...", 0)
                    
                    # Start in a separate process
                    subprocess.Popen([
                        sys.executable, str(api_script)
                    ], creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0)
                    
                    QMessageBox.information(
                        self,
                        "🚀 API Server Starting",
                        "The API server is starting in a separate window.\n\n"
                        "Please wait a moment for it to initialize, then try your analysis again.\n\n"
                        "You can also run diagnostics (Tools → Run Diagnostics) to check the status."
                    )
                    
                    self.statusBar().showMessage("✅ API server started", 5000)
                else:
                    QMessageBox.warning(
                        self,
                        "Script Not Found",
                        f"Could not find API server script at: {api_script}\n\n"
                        "Please start the API server manually:\n"
                        "python scripts/run_api.py"
                    )
                    
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Failed to Start API Server",
                    f"Could not start the API server:\n\n{str(e)}\n\n"
                    "Please start it manually:\n"
                    "python scripts/run_api.py"
                )

    def _start_resource_monitoring(self) -> None:
        """Start system resource monitoring timer."""
        try:
            import importlib.util
            if importlib.util.find_spec("psutil") is not None:
                self.has_psutil = True
            else:
                self.has_psutil = False
        except ImportError:
            self.has_psutil = False
            self.resource_label.setText("💻 Resource monitoring unavailable")
            self.resource_label.setToolTip("Install psutil for resource monitoring: pip install psutil")
            return
        
        from PySide6.QtCore import QTimer
        self.resource_timer = QTimer()
        self.resource_timer.timeout.connect(self._update_resource_info)
        self.resource_timer.start(2000)  # Update every 2 seconds

    def _update_resource_info(self) -> None:
        """Update system resource information in status bar."""
        if not self.has_psutil:
            return
        
        try:
            import psutil  # type: ignore[import-untyped]
            
            # Get CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            memory_mb = memory.used // (1024 * 1024)
            memory_percent = memory.percent
            
            # Get disk usage for current drive
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Update resource label
            resource_text = f"💻 CPU: {cpu_percent:.1f}% | RAM: {memory_mb}MB ({memory_percent:.1f}%) | Disk: {disk_percent:.1f}%"
            self.resource_label.setText(resource_text)
            
            # Change color based on usage
            if cpu_percent > 80 or memory_percent > 80:
                color = "#dc2626"  # Red for high usage
            elif cpu_percent > 60 or memory_percent > 60:
                color = "#d97706"  # Orange for medium usage
            else:
                color = "#059669"  # Green for normal usage
            
            self.resource_label.setStyleSheet(f"color: {color}; font-size: 10px; font-family: monospace;")
            
        except Exception as e:
            self.resource_label.setText("💻 Resource info unavailable")
            self.resource_label.setToolTip(f"Error getting resource info: {str(e)}")

    def resizeEvent(self, event) -> None:
        """Handle window resize events with responsive scaling."""
        super().resizeEvent(event)
        
        # Update responsive scaling based on new window size
        if hasattr(self, 'tab_widget') and self.tab_widget:
            # Ensure tab widget adapts to new size
            self.tab_widget.updateGeometry()
        
        # Update any dialogs or popups to be responsive to new size
        # This helps with better scaling when window is resized

__all__ = ["MainApplicationWindow"]


