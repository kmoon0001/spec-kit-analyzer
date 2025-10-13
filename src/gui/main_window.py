"""Primary GUI window for the Therapy Compliance Analyzer - Refactored Version."""

from __future__ import annotations

import logging
import random
from pathlib import Path
from typing import Any

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDockWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QStatusBar,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.config import get_settings
from src.core.report_generator import ReportGenerator
from src.database import models

# Import beautiful medical-themed components
from src.gui.components.header_component import HeaderComponent
from src.gui.components.menu_builder import MenuBuilder
from src.gui.components.status_component import StatusComponent
from src.gui.components.tab_builder import TabBuilder

# Import dialogs for test compatibility
from src.gui.handlers.analysis_handlers import AnalysisHandlers
from src.gui.handlers.file_handlers import FileHandlers
from src.gui.handlers.ui_handlers import UIHandlers

# Import refactored components
from src.gui.view_models.main_view_model import MainViewModel
from src.gui.widgets.medical_theme import medical_theme

# Import minimal micro-interactions (subtle animations only)
from src.gui.widgets.micro_interactions import AnimatedButton
from src.gui.widgets.mission_control_widget import LogViewerWidget, MissionControlWidget, SettingsEditorWidget

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


class MainApplicationWindow(QMainWindow):
    """The main application window (View) - Refactored for better maintainability."""

    def __init__(self, user: models.User, token: str) -> None:
        super().__init__()
        self.setWindowTitle("Therapy Compliance Analyzer")
        # Set larger minimum size to prevent UI cramping
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)

        self.current_user = user
        self.auth_token = token
        self.settings = QSettings("TherapyCo", "ComplianceAnalyzer")
        self.report_generator = ReportGenerator()
        self._current_payload: dict[str, Any] = {}
        self._selected_file: Path | None = None
        self._cached_preview_content: str = ""

        # Initialize handlers and builders
        self.view_model = MainViewModel(token)
        self.menu_builder = MenuBuilder(self)
        self.tab_builder = TabBuilder(self)
        self.analysis_handlers = AnalysisHandlers(self)
        self.file_handlers = FileHandlers(self)
        self.ui_handlers = UIHandlers(self)

        # Initialize UI attributes to prevent "defined outside __init__" warnings
        self._initialize_ui_attributes()

        self._build_ui()
        self._connect_view_model()
        self._load_initial_state()
        self._load_gui_settings()

    def _initialize_ui_attributes(self) -> None:
        """Initialize all UI attributes to prevent warnings."""
        # Core UI components
        self.header: HeaderComponent | None = None
        self.status_component: StatusComponent | None = None
        self.tab_widget: QTabWidget | None = None

        # Tab widgets
        self.analysis_tab: QWidget | None = None
        self.dashboard_tab: QWidget | None = None
        self.mission_control_tab: QWidget | None = None
        self.settings_tab: QWidget | None = None

        # Analysis components
        self.rubric_selector: QComboBox | None = None
        self.strictness_buttons: list[Any] = []
        self.strictness_levels: list[Any] = []
        self.strictness_description: QWidget | None = None
        self.section_checkboxes: dict[str, Any] = {}
        self.analysis_summary_browser: QTextBrowser | None = None
        self.detailed_results_browser: QTextBrowser | None = None
        self.file_display: QTextEdit | None = None

        # Action buttons
        self.open_file_button: AnimatedButton | None = None
        self.open_folder_button: AnimatedButton | None = None
        self.run_analysis_button: AnimatedButton | None = None
        self.repeat_analysis_button: AnimatedButton | None = None
        self.stop_analysis_button: AnimatedButton | None = None
        self.view_report_button: AnimatedButton | None = None

        # Dashboard and mission control
        self.dashboard_widget: Any | None = None
        self.mission_control_widget: MissionControlWidget | None = None
        self.settings_editor: SettingsEditorWidget | None = None

        # Status bar components
        self.resource_label: QWidget | None = None
        self.connection_label: QWidget | None = None
        self.connection_indicator: QWidget | None = None
        self.connection_status_widget: QWidget | None = None

        self.progress_bar: QProgressBar | None = None

        # Dock widgets
        self.meta_analytics_dock: QDockWidget | None = None
        self.meta_widget: Any | None = None
        self.performance_dock: QDockWidget | None = None
        self.performance_widget: Any | None = None
        self.log_viewer: LogViewerWidget | None = None

        # Menu actions
        self.meta_analytics_action: QAction | None = None
        self.performance_action: QAction | None = None

        # System monitoring
        self.has_psutil: bool = False
        self.resource_timer: QTimer | None = None

        # Easter egg attributes
        self.konami_sequence: list[Qt.Key] = []
        self.konami_code = [
            Qt.Key.Key_Up,
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
            Qt.Key.Key_Down,
            Qt.Key.Key_Left,
            Qt.Key.Key_Right,
            Qt.Key.Key_Left,
            Qt.Key.Key_Right,
            Qt.Key.Key_B,
            Qt.Key.Key_A,
        ]
        self.developer_mode = False
        self.is_testing = False
        self.model_status_timer = QTimer(self)  # Initialize the timer here

    def _check_ai_models_status(self) -> None:
        """Periodically check the status of AI models."""
        if not self.status_component:
            return

        all_ready = True
        for model_name, status in self.status_component.models.items():
            if not status:
                # In a real implementation, this would be a call to a service
                # that checks the model's status. For now, we'll simulate it.
                if random.random() < 0.3:  # 30% chance of a model becoming ready
                    self.status_component.update_model_status(model_name, True)
                all_ready = False

        if all_ready:
            self.model_status_timer.stop()
            self.analysis_handlers.on_ai_models_ready()
        else:
            status_summary = self.status_component.get_overall_status()
            self.statusBar().showMessage(
                f"⌛ Loading AI Models: {status_summary['ready_count']}/{status_summary['total_count']}"
            )

    def _build_ui(self) -> None:
        """Build the complete UI using modular builders."""
        self._setup_responsive_scaling()
        self._build_header()
        self._build_docks()
        self.menu_builder.build_all_menus()
        self._build_central_layout()
        self._build_status_bar()
        self._setup_keyboard_shortcuts()
        self._apply_medical_theme()

    def _setup_responsive_scaling(self) -> None:
        """Setup responsive scaling for better UI adaptation to different screen sizes."""
        screen = QApplication.primaryScreen()
        if screen:
            screen_size = screen.size()
            screen_width = screen_size.width()

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
        self.header = HeaderComponent(self)
        self.header.theme_toggle_requested.connect(self.ui_handlers.toggle_theme)
        self.header.logo_clicked.connect(self.ui_handlers.on_logo_clicked)

        self.status_component = StatusComponent(self)
        self.status_component.status_clicked.connect(self.ui_handlers.on_model_status_clicked)

        self.header.setStyleSheet(self.header.get_default_stylesheet())
        self.ui_handlers.check_license_status()

    def _build_central_layout(self) -> None:
        """Build the main central widget with 4-tab structure."""
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        # Add header at the top
        root_layout.addWidget(self.header)

        # Create main tab widget
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setDocumentMode(False)
        self.tab_widget.setStyleSheet(self._get_tab_stylesheet())
        root_layout.addWidget(self.tab_widget, stretch=1)

        # Create tabs using tab builder with error handling
        try:
            self.analysis_tab = self.tab_builder.create_analysis_tab()
            self.tab_widget.addTab(self.analysis_tab, "Analysis")
            logging.info("Analysis tab created successfully")
        except Exception as e:
            logging.error(f"Failed to create Analysis tab: {e}")
            # Create fallback tab
            self.analysis_tab = QWidget()
            self.tab_widget.addTab(self.analysis_tab, "Analysis")

        try:
            self.dashboard_tab = self.tab_builder.create_dashboard_tab()
            self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
            logging.info("Dashboard tab created successfully")
        except Exception as e:
            logging.error(f"Failed to create Dashboard tab: {e}")
            # Create fallback tab
            self.dashboard_tab = QWidget()
            self.tab_widget.addTab(self.dashboard_tab, "Dashboard")

        try:
            self.mission_control_tab = self.tab_builder.create_mission_control_tab()
            self.tab_widget.addTab(self.mission_control_tab, "Mission Control")
            logging.info("Mission Control tab created successfully")
        except Exception as e:
            logging.error(f"Failed to create Mission Control tab: {e}")
            # Create fallback tab
            self.mission_control_tab = QWidget()
            self.tab_widget.addTab(self.mission_control_tab, "Mission Control")

        try:
            self.settings_tab = self.tab_builder.create_settings_tab()
            self.tab_widget.addTab(self.settings_tab, "Settings")
            logging.info("Settings tab created successfully")
        except Exception as e:
            logging.error(f"Failed to create Settings tab: {e}")
            # Create fallback tab
            self.settings_tab = QWidget()
            self.tab_widget.addTab(self.settings_tab, "Settings")

        # Set Analysis as default tab
        self.tab_widget.setCurrentWidget(self.analysis_tab)

        # Log tab count for debugging
        tab_count = self.tab_widget.count()
        logging.info(f"MainApplicationWindow initialized with {tab_count} tabs")
        for i in range(tab_count):
            tab_text = self.tab_widget.tabText(i)
            logging.info(f"Tab {i}: {tab_text}")

    def _get_tab_stylesheet(self) -> str:
        """Get the stylesheet for the tab widget."""
        return f"""
            QTabWidget::pane {{
                border: 2px solid {medical_theme.get_color("border_light")};
                border-radius: 10px;
                background: {medical_theme.get_color("bg_primary")};
                top: -2px;
            }}
            QTabBar::tab {{
                background: {medical_theme.get_color("bg_secondary")};
                border: 2px solid {medical_theme.get_color("border_light")};
                border-bottom: none;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                padding: 12px 24px;
                margin-right: 6px;
                color: {medical_theme.get_color("text_secondary")};
                font-weight: 700;
                font-size: 12px;
                min-width: 120px;
            }}
            QTabBar::tab:selected {{
                background: white;
                color: {medical_theme.get_color("primary_blue")};
                border-bottom: 2px solid white;
                margin-bottom: -2px;
            }}
            QTabBar::tab:hover:!selected {{
                background: {medical_theme.get_color("hover_bg")};
                color: {medical_theme.get_color("primary_blue")};
            }}
        """

    def _build_docks(self) -> None:
        """Build optional dock widgets (Meta Analytics and Performance - hidden by default)."""
        # Meta Analytics Dock
        if MetaAnalyticsWidget:
            self.meta_analytics_dock = QDockWidget("Meta Analytics", self)
            self.meta_analytics_dock.setObjectName("MetaAnalyticsDock")
            self.meta_analytics_dock.setAllowedAreas(
                Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
            )
            self.meta_widget = MetaAnalyticsWidget()
            self.meta_widget.refresh_requested.connect(self.view_model.load_meta_analytics)
            self.meta_analytics_dock.setWidget(self.meta_widget)
            self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.meta_analytics_dock)
            self.meta_analytics_dock.hide()

        # Performance Status Dock
        if PerformanceStatusWidget:
            self.performance_dock = QDockWidget("Performance Status", self)
            self.performance_dock.setObjectName("PerformanceStatusDock")
            self.performance_dock.setAllowedAreas(
                Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.BottomDockWidgetArea
            )
            self.performance_widget = PerformanceStatusWidget()
            self.performance_dock.setWidget(self.performance_widget)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.performance_dock)
            self.performance_dock.hide()

        # Log Viewer
        self.log_viewer = LogViewerWidget(self)

    def _build_status_bar(self) -> None:
        """Build status bar with AI indicators, progress, and branding."""
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

        # Add status components
        status.addPermanentWidget(self.status_component)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximumWidth(220)
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

        # Connect progress bar to analysis status
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

    def _setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts for tab navigation."""
        shortcuts = [
            ("Ctrl+1", lambda: self.tab_widget.setCurrentIndex(0)),
            ("Ctrl+2", lambda: self.tab_widget.setCurrentIndex(1)),
            ("Ctrl+3", lambda: self.tab_widget.setCurrentIndex(2)),
            ("Ctrl+4", lambda: self.tab_widget.setCurrentIndex(3)),
        ]

        for shortcut_key, callback in shortcuts:
            shortcut = QAction(self)
            shortcut.setShortcut(shortcut_key)
            shortcut.triggered.connect(callback)
            self.addAction(shortcut)

    def _apply_medical_theme(self) -> None:
        """Apply the comprehensive medical theme styling."""
        main_style = f"""
            QMainWindow {{
                background-color: {medical_theme.get_color("bg_primary")};
                color: {medical_theme.get_color("text_primary")};
            }}
            QWidget {{
                font-family: "Segoe UI", "Inter", Arial, sans-serif;
                color: {medical_theme.get_color("text_primary")};
            }}
            QLabel {{
                color: {medical_theme.get_color("text_primary")};
            }}
            QTextBrowser, QTextEdit {{
                background-color: {medical_theme.get_color("bg_primary")};
                color: {medical_theme.get_color("text_primary")};
                border: 1px solid {medical_theme.get_color("border_light")};
            }}
        """

        combined_style = (
            main_style
            + medical_theme.get_main_window_stylesheet()
            + medical_theme.get_form_stylesheet()
            + medical_theme.get_card_stylesheet()
        )

        self.setStyleSheet(combined_style)

        # Update header theme
        is_dark = medical_theme.current_theme == "dark"
        if self.header:
            self.header.update_theme_button(is_dark)
            if is_dark:
                self.header.setStyleSheet(self.header.get_dark_theme_stylesheet())
            else:
                self.header.setStyleSheet(self.header.get_default_stylesheet())

    def _connect_view_model(self) -> None:
        """Connect view model signals to UI handlers."""
        self.view_model.status_message_changed.connect(self.statusBar().showMessage)
        self.view_model.api_status_changed.connect(self.mission_control_widget.update_api_status)
        self.view_model.task_list_changed.connect(self.mission_control_widget.update_task_list)
        if self.log_viewer:
            self.view_model.log_message_received.connect(self.log_viewer.add_log_message)
        if self.settings_editor:
            self.view_model.settings_loaded.connect(self.settings_editor.set_settings)
        self.view_model.analysis_result_received.connect(self.analysis_handlers.handle_analysis_success)
        self.view_model.rubrics_loaded.connect(self._on_rubrics_loaded)
        if hasattr(self, "dashboard_widget") and self.dashboard_widget:
            self.view_model.dashboard_data_loaded.connect(self.dashboard_widget.load_data)
        if MetaAnalyticsWidget and self.meta_widget:
            self.view_model.meta_analytics_loaded.connect(self.meta_widget.update_data)
        self.view_model.show_message_box_signal.connect(self._show_message_box)

    def _show_message_box(
        self, title: str, text: str, icon_str: str, buttons: list[str], technical_details: str = ""
    ) -> None:
        """Show a message box with the given parameters."""
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

        msg.exec()

        if technical_button and msg.clickedButton() == technical_button:
            QMessageBox.information(self, "🔧 Technical Details", technical_details)

        if "Error" in title:
            self.analysis_handlers.handle_analysis_error(text)

    def _load_initial_state(self) -> None:
        """Load initial application state."""
        self._load_default_rubrics()
        self.view_model.start_workers()
        if self.current_user.is_admin:
            self.view_model.load_settings()

        if self.status_component:
            self.status_component.set_all_loading()

        # Start a recurring timer to check model statuses
        self.model_status_timer = QTimer(self)
        self.model_status_timer.timeout.connect(self._check_ai_models_status)
        self.model_status_timer.start(1000)  # Check every second

        self._start_resource_monitoring()

    def _load_default_rubrics(self) -> None:
        """Load default rubrics immediately as fallback."""
        if hasattr(self, "rubric_selector") and self.rubric_selector:
            self.rubric_selector.clear()

            # Add comprehensive default Medicare rubrics
            default_rubrics = [
                (
                    "📋 Medicare Benefits Policy Manual - Chapter 15 (Covered Medical Services)",
                    "medicare_benefits_policy_manual_ch15",
                ),
                ("📋 Medicare Part B Outpatient Therapy Guidelines", "medicare_part_b_therapy_guidelines"),
                ("📋 CMS-1500 Documentation Requirements", "cms_1500_documentation_requirements"),
                ("📋 Medicare Therapy Cap & Exception Guidelines", "medicare_therapy_cap_guidelines"),
                ("📋 Skilled Therapy Documentation Standards", "skilled_therapy_documentation_standards"),
                ("🏃 Physical Therapy - APTA Guidelines", "apta_pt_guidelines"),
                ("🖐️ Occupational Therapy - AOTA Standards", "aota_ot_standards"),
                ("🗣️ Speech-Language Pathology - ASHA Guidelines", "asha_slp_guidelines"),
            ]

            for name, value in default_rubrics:
                self.rubric_selector.addItem(name, value)

            self.rubric_selector.setCurrentIndex(0)

    def _on_rubrics_loaded(self, rubrics: list[dict]) -> None:
        """Load rubrics into dropdown with comprehensive Medicare defaults."""
        if not self.rubric_selector:
            return

        self.rubric_selector.clear()
        self._load_default_rubrics()

        # Add separator if there are custom rubrics
        if rubrics:
            self.rubric_selector.insertSeparator(self.rubric_selector.count())
            self.rubric_selector.addItem("--- Custom Rubrics ---", "")
            self.rubric_selector.model().item(self.rubric_selector.count() - 1).setEnabled(False)

        # Add custom rubrics from API
        for rubric in rubrics:
            self.rubric_selector.addItem(f"📝 {rubric.get('name', 'Unnamed rubric')}", rubric.get("value"))

        self._load_gui_settings()

    def _start_resource_monitoring(self) -> None:
        """Start system resource monitoring timer."""
        try:
            import importlib.util

            if importlib.util.find_spec("psutil") is not None:
                self.has_psutil = True
                self.resource_timer = QTimer()
                self.resource_timer.timeout.connect(self._update_resource_info)
                self.resource_timer.start(2000)
            else:
                self.has_psutil = False
        except ImportError:
            self.has_psutil = False

    def _update_resource_info(self) -> None:
        """Update system resource information in status bar."""
        if not self.has_psutil or not self.resource_label:
            return

        try:
            import psutil  # type: ignore[import-untyped]

            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            memory_mb = memory.used // (1024 * 1024)
            memory_percent = memory.percent

            resource_text = f"💻 CPU: {cpu_percent}% | RAM: {memory_mb}MB ({memory_percent}%)"
            self.resource_label.setText(resource_text)

            # Change color based on usage
            if cpu_percent > 80 or memory_percent > 80:
                color = "#dc2626"
            elif cpu_percent > 60 or memory_percent > 60:
                color = "#d97706"
            else:
                color = "#059669"

            self.resource_label.setStyleSheet(f"color: {color}; font-size: 10px; font-family: monospace;")

        except (ImportError, ModuleNotFoundError, AttributeError) as e:
            if self.resource_label:
                self.resource_label.setText("💻 Resource info unavailable")
                self.resource_label.setToolTip(f"Error getting resource info: {e!s}")

    def _save_gui_settings(self) -> None:
        """Save GUI settings including window geometry, theme, and preferences."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("ui/last_active_tab", self.tab_widget.currentIndex())
        self.settings.setValue("theme", medical_theme.current_theme)
        if self.rubric_selector:
            self.settings.setValue("analysis/rubric", self.rubric_selector.currentData())
        if self._selected_file:
            self.settings.setValue("analysis/last_file", str(self._selected_file))

    def _load_gui_settings(self) -> None:
        """Load GUI settings including window geometry, theme, and preferences."""
        if geometry := self.settings.value("geometry"):
            self.restoreGeometry(geometry)
        if window_state := self.settings.value("windowState"):
            self.restoreState(window_state)

        last_tab = self.settings.value("ui/last_active_tab", 0, type=int)
        if 0 <= last_tab < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(last_tab)

        saved_theme = self.settings.value("theme", "light", type=str)
        self.ui_handlers.apply_theme(saved_theme)

        if self.rubric_selector and (saved_rubric_data := self.settings.value("analysis/rubric")):
            index = self.rubric_selector.findData(saved_rubric_data)
            if index >= 0:
                self.rubric_selector.setCurrentIndex(index)

        if last_file_str := self.settings.value("analysis/last_file", type=str):
            last_file = Path(last_file_str)
            if last_file.exists():
                self.file_handlers.set_selected_file(last_file)

    # Delegate methods to handlers
    def _prompt_for_document(self) -> None:
        self.file_handlers.prompt_for_document()

    def _prompt_for_folder(self) -> None:
        self.file_handlers.prompt_for_folder()

    def _set_selected_file(self, file_path: Path) -> None:
        """Set the selected file (delegation to file_handlers)."""
        self.file_handlers.set_selected_file(file_path)

    def _export_report(self) -> None:
        self.file_handlers.export_report()

    def _export_report_pdf(self) -> None:
        self.file_handlers.export_report_pdf()

    def _export_report_html(self) -> None:
        self.file_handlers.export_report_html()

    def _start_analysis(self) -> None:
        self.analysis_handlers.start_analysis()

    def _repeat_analysis(self) -> None:
        self.analysis_handlers.repeat_analysis()

    def _stop_analysis(self) -> None:
        self.analysis_handlers.stop_analysis()

    def _toggle_theme(self) -> None:
        self.ui_handlers.toggle_theme()

    def _apply_theme(self, theme_name: str) -> None:
        self.ui_handlers.apply_theme(theme_name)

    def _open_report_popup(self) -> None:
        self.ui_handlers.open_report_popup()

    def _toggle_all_sections(self, checked: bool) -> None:
        self.ui_handlers.toggle_all_sections(checked)

    def _open_rubric_manager(self) -> None:
        self.ui_handlers.open_rubric_manager()

    def _open_settings_dialog(self) -> None:
        self.ui_handlers.open_settings_dialog()

    def show_change_password_dialog(self) -> None:
        self.ui_handlers.show_change_password_dialog()

    def _open_chat_dialog(self, initial_message: str | None = None) -> None:
        self.ui_handlers.open_chat_dialog(initial_message)

    def _toggle_meta_analytics_dock(self) -> None:
        self.ui_handlers.toggle_meta_analytics_dock()

    def _toggle_performance_dock(self) -> None:
        self.ui_handlers.toggle_performance_dock()

    def _clear_all_caches(self) -> None:
        self.ui_handlers.clear_all_caches()

    def _run_diagnostics(self) -> None:
        self.ui_handlers.run_diagnostics()

    def _start_api_server(self) -> None:
        self.ui_handlers.start_api_server()

    def _show_about_dialog(self) -> None:
        self.ui_handlers.show_about_dialog()

    def _show_system_info(self) -> None:
        self.ui_handlers.show_system_info()

    def _show_user_management(self) -> None:
        self.ui_handlers.show_user_management()

    def _handle_link_clicked(self, url) -> None:
        self.ui_handlers.handle_link_clicked(url)

    def _handle_report_link(self, url) -> None:
        self.ui_handlers.handle_link_clicked(url)

    def _on_strictness_selected_with_description(self, index: int) -> None:
        self.analysis_handlers.on_strictness_selected_with_description(index)

    def _update_strictness_description(self, index: int) -> None:
        self.analysis_handlers.update_strictness_description(index)

    def _handle_mission_control_start(self) -> None:
        """Handle start analysis request from Mission Control."""
        self.tab_widget.setCurrentWidget(self.analysis_tab)
        self.file_handlers.prompt_for_document()

    def _handle_mission_control_review(self, doc_info: dict) -> None:
        """Handle review document request from Mission Control."""
        doc_name = doc_info.get("title") or doc_info.get("name") or doc_info.get("document_name") or "Document"
        self.statusBar().showMessage(f"Detailed replay for '{doc_name}' will be available in a future update.")

    def show_progress(self, value: int = 0, text: str = "") -> None:
        """Show and update the progress bar."""
        if self.progress_bar:
            self.progress_bar.setValue(value)
            if text:
                self.progress_bar.setFormat(f"{text} ({value}%)")
            else:
                self.progress_bar.setFormat(f"{value}%")
            self.progress_bar.show()

    def hide_progress(self) -> None:
        """Hide the progress bar."""
        if self.progress_bar:
            self.progress_bar.hide()
            self.progress_bar.setValue(0)

    def closeEvent(self, event) -> None:
        """Handle application close - exit gracefully with proper cleanup."""
        logger.debug("Application closing - cleaning up resources")

        try:
            self._save_gui_settings()
        except (RuntimeError, AttributeError):
            pass

        try:
            # Stop workers with a longer timeout to prevent hanging
            self.view_model.stop_all_workers()
        except Exception as e:
            logger.warning("Error stopping workers during shutdown: %s", e)

        # Accept the close event first, then quit
        event.accept()

        # Use QTimer to delay quit slightly to allow cleanup
        from PySide6.QtCore import QTimer

        QTimer.singleShot(200, QApplication.quit)  # Increased delay for cleanup

    def keyPressEvent(self, event) -> None:
        """Handle key press events for Konami code and other shortcuts."""
        super().keyPressEvent(event)

        # Initialize konami sequence if not exists
        if not hasattr(self, "konami_sequence"):
            self.konami_sequence = []

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
            "For all the amazing therapists out there!",
        )

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
            "- Kevin 🫶",
        )

    def _show_developer_console(self) -> None:
        """Show developer console dialog."""
        if not hasattr(self, "developer_mode") or not self.developer_mode:
            QMessageBox.warning(self, "Access Denied", "Developer console requires Konami code activation!")
            return

        console_text = f"""
🔧 DEVELOPER CONSOLE 🔧
🔧 DEVELOPER CONSOLE 🔧
🔧 DEVELOPER CONSOLE 🔧

System Information:
- User: {self.current_user.username}
- Theme: {medical_theme.current_theme}
- Active Threads: {len(self.view_model._active_threads)}
- Selected File: {self._selected_file.name if self._selected_file else "None"}
- Current Payload: {"Available" if self._current_payload else "None"}

Memory Usage:
- Python Objects: {len(__import__("gc").get_objects())} objects
- Cache Status: Active

Debug Commands Available:
- Clear all caches
- Reset UI state
- Force garbage collection
- Export debug logs

This console is only available in developer mode! 🎮
        """

        QMessageBox.information(self, "🔧 Developer Console", console_text)

    def resizeEvent(self, event) -> None:
        """Handle window resize events with responsive scaling."""
        super().resizeEvent(event)

        if hasattr(self, "tab_widget") and self.tab_widget:
            self.tab_widget.updateGeometry()


__all__ = ["MainApplicationWindow"]
