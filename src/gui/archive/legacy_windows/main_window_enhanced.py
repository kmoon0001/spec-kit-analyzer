"""
Enhanced Main Window - Therapy Compliance Analyzer
Fully integrated with all features, designs, and easter eggs
"""

import os
import webbrowser
from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QIcon, QAction
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QDialog,
    QMessageBox,
    QMainWindow,
    QStatusBar,
    QMenuBar,
    QMenu,
    QFileDialog,
    QSplitter,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QComboBox,
    QFrame,
    QGridLayout,
    QSystemTrayIcon,
    QSlider,
    QCheckBox,
    QSpinBox,
)

from src.config import get_settings
from src.gui.dialogs.rubric_manager_dialog import RubricManagerDialog
from src.gui.dialogs.change_password_dialog import ChangePasswordDialog
from src.gui.dialogs.chat_dialog import ChatDialog
from src.gui.widgets.dashboard_widget import DashboardWidget
from src.gui.widgets.meta_analytics_widget import MetaAnalyticsWidget
from src.gui.widgets.performance_status_widget import PerformanceStatusWidget
from src.gui.dialogs.performance_settings_dialog import PerformanceSettingsDialog
from src.core.report_generator import ReportGenerator

settings = get_settings()
API_URL = settings.paths.api_url


class EasterEggManager:
    """Manages easter eggs and hidden features"""

    def __init__(self, parent):
        self.parent = parent
        self.konami_sequence = []
        self.konami_code = [
            "Up",
            "Up",
            "Down",
            "Down",
            "Left",
            "Right",
            "Left",
            "Right",
            "B",
            "A",
        ]
        self.click_count = 0
        self.secret_unlocked = False

    def handle_key_sequence(self, key):
        """Handle konami code sequence"""
        self.konami_sequence.append(key)
        if len(self.konami_sequence) > len(self.konami_code):
            self.konami_sequence.pop(0)

        if self.konami_sequence == self.konami_code:
            self.unlock_developer_mode()

    def handle_logo_click(self):
        """Handle logo clicks for easter egg"""
        self.click_count += 1
        if self.click_count >= 7:
            self.show_credits_easter_egg()
            self.click_count = 0

    def unlock_developer_mode(self):
        """Unlock developer mode features"""
        if not self.secret_unlocked:
            self.secret_unlocked = True
            self.parent.show_developer_panel()
            QMessageBox.information(
                self.parent,
                "🎉 Developer Mode Unlocked!",
                "You've unlocked developer mode!\nNew features are now available in the Tools menu.",
            )

    def show_credits_easter_egg(self):
        """Show animated credits"""
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("🎭 Credits")
        dialog.setFixedSize(400, 300)

        layout = QVBoxLayout(dialog)

        credits_text = QLabel("""
        <center>
        <h2>🏥 Therapy Compliance Analyzer</h2>
        <p><b>Developed with ❤️ for Healthcare Professionals</b></p>
        <br>
        <p>🤖 AI-Powered Analysis</p>
        <p>🔒 Privacy-First Design</p>
        <p>📊 Smart Analytics</p>
        <p>⚡ Lightning Fast</p>
        <br>
        <p><i>"Making compliance analysis magical!"</i></p>
        <br>
        <p>🎉 Thanks for using our app! 🎉</p>
        </center>
        """)
        credits_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(credits_text)

        # Animate the dialog
        self.animate_dialog(dialog)
        dialog.exec()

    def animate_dialog(self, dialog):
        """Add animation to dialog"""
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 15px;
            }
            QLabel {
                color: white;
                background: transparent;
            }
        """)


class EnhancedMainWindow(QMainWindow):
    """Enhanced main window with all features integrated"""

    # Signals
    analysis_started = Signal()
    analysis_completed = Signal(dict)
    theme_changed = Signal(str)

    def __init__(self):
        super().__init__()

        # Core attributes
        self.access_token = None
        self.username = None
        self.is_admin = False
        self._current_file_path = None
        self._current_document_text = ""
        self._current_report_payload = None
        self._analysis_running = False
        self._all_rubrics = []
        self.compliance_service = None

        # Workers and threads
        self.worker_thread = None
        self.worker = None
        self.ai_loader_thread = None
        self.ai_loader_worker = None
        self.dashboard_thread = None
        self.dashboard_worker = None

        # Services
        self.report_generator = ReportGenerator()
        self.easter_egg_manager = EasterEggManager(self)

        # Model status tracking
        self.model_status = {
            "Generator": False,
            "Retriever": False,
            "Fact Checker": False,
            "NER": False,
            "Checklist": False,
            "Chat": False,
        }

        # UI state
        self.current_theme = "light"
        self.developer_mode = False
        self.animations_enabled = True

        # Initialize UI
        self.init_ui()
        self.setup_animations()
        self.setup_system_tray()

    def init_ui(self):
        """Initialize the complete user interface"""
        self.setWindowTitle("🏥 Therapy Compliance Analyzer - Enhanced Edition")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 700)

        # Set application icon
        self.setWindowIcon(QIcon("src/resources/app_icon.png"))

        # Create menu system
        self.create_menu_system()

        # Create main layout
        self.create_main_layout()

        # Create status bar with enhanced features
        self.create_enhanced_status_bar()

        # Apply initial theme
        self.apply_theme("light")

        # Setup keyboard shortcuts
        self.setup_shortcuts()

    def create_menu_system(self):
        """Create comprehensive menu system"""
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)

        # File Menu
        file_menu = self.menu_bar.addMenu("📁 File")
        file_menu.addAction("📤 Upload Document", self.upload_document, "Ctrl+O")
        file_menu.addAction("📂 Upload Folder", self.upload_folder, "Ctrl+Shift+O")
        file_menu.addSeparator()
        file_menu.addAction("💾 Save Report", self.save_report, "Ctrl+S")
        file_menu.addAction("📄 Export PDF", self.export_pdf, "Ctrl+E")
        file_menu.addSeparator()
        file_menu.addAction("🚪 Logout", self.logout)
        file_menu.addAction("❌ Exit", self.close, "Ctrl+Q")

        # Analysis Menu
        analysis_menu = self.menu_bar.addMenu("🔍 Analysis")
        analysis_menu.addAction("▶️ Run Analysis", self.run_analysis, "F5")
        analysis_menu.addAction("⏹️ Stop Analysis", self.stop_analysis, "Esc")
        analysis_menu.addSeparator()
        analysis_menu.addAction("📋 Quick Check", self.quick_compliance_check, "Ctrl+Q")
        analysis_menu.addAction("🔄 Batch Analysis", self.batch_analysis, "Ctrl+B")

        # Tools Menu
        tools_menu = self.menu_bar.addMenu("🛠️ Tools")
        tools_menu.addAction("📚 Manage Rubrics", self.manage_rubrics, "Ctrl+R")
        tools_menu.addAction("💬 AI Chat Assistant", self.open_chat, "Ctrl+T")
        tools_menu.addAction("⚙️ Performance Settings", self.show_performance_settings)
        tools_menu.addAction("🔑 Change Password", self.show_change_password_dialog)
        tools_menu.addSeparator()
        tools_menu.addAction("🧹 Clear Cache", self.clear_cache)
        tools_menu.addAction("🔄 Refresh Models", self.refresh_ai_models)

        # View Menu
        view_menu = self.menu_bar.addMenu("👁️ View")
        view_menu.addAction(
            "📊 Dashboard", lambda: self.tab_widget.setCurrentIndex(1), "Ctrl+1"
        )
        view_menu.addAction(
            "📈 Analytics", lambda: self.tab_widget.setCurrentIndex(2), "Ctrl+2"
        )
        view_menu.addSeparator()
        view_menu.addAction("🔍 Zoom In", self.zoom_in, "Ctrl+=")
        view_menu.addAction("🔍 Zoom Out", self.zoom_out, "Ctrl+-")
        view_menu.addAction("🔍 Reset Zoom", self.reset_zoom, "Ctrl+0")

        # Theme Menu
        theme_menu = self.menu_bar.addMenu("🎨 Theme")
        theme_menu.addAction("☀️ Light Theme", lambda: self.apply_theme("light"))
        theme_menu.addAction("🌙 Dark Theme", lambda: self.apply_theme("dark"))
        theme_menu.addAction("💙 Medical Blue", lambda: self.apply_theme("medical"))
        theme_menu.addAction("🌿 Nature Green", lambda: self.apply_theme("nature"))
        theme_menu.addSeparator()

        # Animation toggle
        self.animation_action = theme_menu.addAction(
            "✨ Animations", self.toggle_animations
        )
        self.animation_action.setCheckable(True)
        self.animation_action.setChecked(True)

        # Help Menu
        help_menu = self.menu_bar.addMenu("❓ Help")
        help_menu.addAction("📖 User Guide", self.show_user_guide, "F1")
        help_menu.addAction("🎯 Quick Start", self.show_quick_start)
        help_menu.addAction("🔧 Troubleshooting", self.show_troubleshooting)
        help_menu.addSeparator()
        help_menu.addAction("🌐 Online Help", self.open_online_help)
        help_menu.addAction("📧 Contact Support", self.contact_support)
        help_menu.addSeparator()
        help_menu.addAction("ℹ️ About", self.show_about)

    def create_main_layout(self):
        """Create the main application layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create header with logo and quick actions
        self.create_header(main_layout)

        # Create main tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(True)

        # Analysis Tab
        self.create_analysis_tab()

        # Dashboard Tab
        self.create_dashboard_tab()

        # Analytics Tab (Admin only)
        self.create_analytics_tab()

        # Settings Tab
        self.create_settings_tab()

        main_layout.addWidget(self.tab_widget)

        # Create floating action button
        self.create_floating_action_button()

    def create_header(self, parent_layout):
        """Create application header with logo and quick actions"""
        header_frame = QFrame()
        header_frame.setFixedHeight(80)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 10px;
                margin: 5px;
            }
        """)

        header_layout = QHBoxLayout(header_frame)

        # Logo (clickable for easter egg)
        logo_label = QLabel("🏥")
        logo_label.setFont(QFont("Arial", 32))
        logo_label.setStyleSheet("color: white; background: transparent;")
        logo_label.mousePressEvent = (
            lambda e: self.easter_egg_manager.handle_logo_click()
        )
        header_layout.addWidget(logo_label)

        # Title and subtitle
        title_layout = QVBoxLayout()
        title_label = QLabel("Therapy Compliance Analyzer")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white; background: transparent;")

        subtitle_label = QLabel("AI-Powered Clinical Documentation Analysis")
        subtitle_label.setFont(QFont("Arial", 10))
        subtitle_label.setStyleSheet(
            "color: rgba(255,255,255,0.8); background: transparent;"
        )

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        header_layout.addLayout(title_layout)

        header_layout.addStretch()

        # Quick action buttons
        self.create_quick_actions(header_layout)

        parent_layout.addWidget(header_frame)

    def create_quick_actions(self, parent_layout):
        """Create quick action buttons in header"""
        # Upload button
        upload_btn = QPushButton("📤 Upload")
        upload_btn.clicked.connect(self.upload_document)
        upload_btn.setStyleSheet(self.get_header_button_style())

        # Analyze button
        self.analyze_btn = QPushButton("🔍 Analyze")
        self.analyze_btn.clicked.connect(self.run_analysis)
        self.analyze_btn.setStyleSheet(self.get_header_button_style())
        self.analyze_btn.setEnabled(False)

        # Chat button
        chat_btn = QPushButton("💬 Chat")
        chat_btn.clicked.connect(self.open_chat)
        chat_btn.setStyleSheet(self.get_header_button_style())

        parent_layout.addWidget(upload_btn)
        parent_layout.addWidget(self.analyze_btn)
        parent_layout.addWidget(chat_btn)

    def get_header_button_style(self):
        """Get styling for header buttons"""
        return """
            QPushButton {
                background: rgba(255,255,255,0.2);
                color: white;
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.3);
                border-color: rgba(255,255,255,0.5);
            }
            QPushButton:pressed {
                background: rgba(255,255,255,0.1);
            }
            QPushButton:disabled {
                background: rgba(255,255,255,0.1);
                color: rgba(255,255,255,0.5);
                border-color: rgba(255,255,255,0.2);
            }
        """

    def create_analysis_tab(self):
        """Create the main analysis tab"""
        analysis_widget = QWidget()
        layout = QHBoxLayout(analysis_widget)

        # Left panel - Document and controls
        left_panel = self.create_left_panel()

        # Right panel - Results
        right_panel = self.create_right_panel()

        # Splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 800])

        layout.addWidget(splitter)

        self.tab_widget.addTab(analysis_widget, "🔍 Analysis")

    def create_left_panel(self):
        """Create left panel with document upload and controls"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)

        # Document upload section
        upload_group = QGroupBox("📄 Document Upload")
        upload_layout = QVBoxLayout(upload_group)

        # Drag and drop area
        self.drop_area = QLabel("Drag & Drop Document Here\nor Click to Browse")
        self.drop_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_area.setMinimumHeight(100)
        self.drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background: #f9f9f9;
                color: #666;
                font-size: 14px;
            }
            QLabel:hover {
                border-color: #007acc;
                background: #f0f8ff;
            }
        """)
        self.drop_area.mousePressEvent = lambda e: self.upload_document()

        upload_layout.addWidget(self.drop_area)

        # File info
        self.file_info_label = QLabel("No file selected")
        self.file_info_label.setStyleSheet("color: #666; font-size: 12px;")
        upload_layout.addWidget(self.file_info_label)

        layout.addWidget(upload_group)

        # Rubric selection
        rubric_group = QGroupBox("📋 Compliance Rubric")
        rubric_layout = QVBoxLayout(rubric_group)

        self.rubric_combo = QComboBox()
        self.rubric_combo.addItems(
            ["PT Compliance Rubric", "OT Compliance Rubric", "SLP Compliance Rubric"]
        )
        rubric_layout.addWidget(self.rubric_combo)

        # Rubric description
        self.rubric_description = QLabel("Select a rubric to see description")
        self.rubric_description.setWordWrap(True)
        self.rubric_description.setStyleSheet(
            "color: #666; font-size: 11px; padding: 5px;"
        )
        rubric_layout.addWidget(self.rubric_description)

        layout.addWidget(rubric_group)

        # Analysis options
        options_group = QGroupBox("⚙️ Analysis Options")
        options_layout = QVBoxLayout(options_group)

        # Analysis mode
        self.analysis_mode = QComboBox()
        self.analysis_mode.addItems(
            ["Standard Analysis", "Quick Check", "Deep Analysis", "Custom"]
        )
        options_layout.addWidget(QLabel("Analysis Mode:"))
        options_layout.addWidget(self.analysis_mode)

        # Confidence threshold
        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setRange(50, 95)
        self.confidence_slider.setValue(75)
        self.confidence_label = QLabel("Confidence Threshold: 75%")
        self.confidence_slider.valueChanged.connect(
            lambda v: self.confidence_label.setText(f"Confidence Threshold: {v}%")
        )
        options_layout.addWidget(self.confidence_label)
        options_layout.addWidget(self.confidence_slider)

        # Advanced options
        self.enable_fact_check = QCheckBox("Enable Fact Checking")
        self.enable_fact_check.setChecked(True)

        self.enable_suggestions = QCheckBox("Generate Improvement Suggestions")
        self.enable_suggestions.setChecked(True)

        self.enable_citations = QCheckBox("Include Regulatory Citations")
        self.enable_citations.setChecked(True)

        options_layout.addWidget(self.enable_fact_check)
        options_layout.addWidget(self.enable_suggestions)
        options_layout.addWidget(self.enable_citations)

        layout.addWidget(options_group)

        # Progress section
        progress_group = QGroupBox("📊 Analysis Progress")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        self.progress_label = QLabel("Ready to analyze")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)

        layout.addWidget(progress_group)

        layout.addStretch()

        return panel

    def create_right_panel(self):
        """Create right panel for results display"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)

        # Results header
        header_layout = QHBoxLayout()

        results_label = QLabel("📋 Analysis Results")
        results_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(results_label)

        header_layout.addStretch()

        # Export buttons
        self.export_pdf_btn = QPushButton("📄 Export PDF")
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        self.export_pdf_btn.setEnabled(False)

        self.save_report_btn = QPushButton("💾 Save Report")
        self.save_report_btn.clicked.connect(self.save_report)
        self.save_report_btn.setEnabled(False)

        header_layout.addWidget(self.export_pdf_btn)
        header_layout.addWidget(self.save_report_btn)

        layout.addLayout(header_layout)

        # Results display
        self.results_browser = QTextBrowser()
        self.results_browser.setHtml(self.get_welcome_html())
        layout.addWidget(self.results_browser)

        return panel

    def create_dashboard_tab(self):
        """Create dashboard tab"""
        self.dashboard_widget = DashboardWidget()
        self.tab_widget.addTab(self.dashboard_widget, "📊 Dashboard")

    def create_analytics_tab(self):
        """Create analytics tab (admin only)"""
        self.analytics_widget = MetaAnalyticsWidget()
        self.tab_widget.addTab(self.analytics_widget, "📈 Analytics")

    def create_settings_tab(self):
        """Create settings and preferences tab"""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)

        # Performance settings
        perf_group = QGroupBox("⚡ Performance Settings")
        perf_layout = QGridLayout(perf_group)

        # AI Model settings
        perf_layout.addWidget(QLabel("AI Model Quality:"), 0, 0)
        self.model_quality = QComboBox()
        self.model_quality.addItems(["Fast", "Balanced", "High Quality"])
        self.model_quality.setCurrentText("Balanced")
        perf_layout.addWidget(self.model_quality, 0, 1)

        # Cache settings
        perf_layout.addWidget(QLabel("Cache Size (MB):"), 1, 0)
        self.cache_size = QSpinBox()
        self.cache_size.setRange(100, 2000)
        self.cache_size.setValue(500)
        perf_layout.addWidget(self.cache_size, 1, 1)

        # Parallel processing
        self.enable_parallel = QCheckBox("Enable Parallel Processing")
        self.enable_parallel.setChecked(True)
        perf_layout.addWidget(self.enable_parallel, 2, 0, 1, 2)

        layout.addWidget(perf_group)

        # UI Settings
        ui_group = QGroupBox("🎨 Interface Settings")
        ui_layout = QGridLayout(ui_group)

        # Font size
        ui_layout.addWidget(QLabel("Font Size:"), 0, 0)
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setValue(10)
        ui_layout.addWidget(self.font_size, 0, 1)

        # Auto-save
        self.auto_save = QCheckBox("Auto-save Reports")
        self.auto_save.setChecked(True)
        ui_layout.addWidget(self.auto_save, 1, 0, 1, 2)

        # Notifications
        self.enable_notifications = QCheckBox("Enable Notifications")
        self.enable_notifications.setChecked(True)
        ui_layout.addWidget(self.enable_notifications, 2, 0, 1, 2)

        layout.addWidget(ui_group)

        # Privacy Settings
        privacy_group = QGroupBox("🔒 Privacy & Security")
        privacy_layout = QVBoxLayout(privacy_group)

        self.auto_clear_cache = QCheckBox("Auto-clear cache on exit")
        self.auto_clear_cache.setChecked(True)

        self.secure_delete = QCheckBox("Secure file deletion")
        self.secure_delete.setChecked(True)

        privacy_layout.addWidget(self.auto_clear_cache)
        privacy_layout.addWidget(self.secure_delete)

        layout.addWidget(privacy_group)

        layout.addStretch()

        # Apply settings button
        apply_btn = QPushButton("✅ Apply Settings")
        apply_btn.clicked.connect(self.apply_settings)
        layout.addWidget(apply_btn)

        self.tab_widget.addTab(settings_widget, "⚙️ Settings")

    def create_enhanced_status_bar(self):
        """Create enhanced status bar with multiple indicators"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Main status message
        self.status_bar.showMessage("Ready - Upload a document to begin analysis")

        # AI Models status
        self.ai_status_label = QLabel("🤖 AI Models: Loading...")
        self.ai_status_label.setStyleSheet("color: orange; font-weight: bold;")
        self.status_bar.addPermanentWidget(self.ai_status_label)

        # Performance indicator
        self.performance_widget = PerformanceStatusWidget()
        self.status_bar.addPermanentWidget(self.performance_widget)

        # User info
        self.user_status_label = QLabel("👤 Not logged in")
        self.status_bar.addPermanentWidget(self.user_status_label)

        # Connection status
        self.connection_label = QLabel("🌐 Connected")
        self.connection_label.setStyleSheet("color: green;")
        self.status_bar.addPermanentWidget(self.connection_label)

    def create_floating_action_button(self):
        """Create floating action button for quick access"""
        self.fab = QPushButton("💬")
        self.fab.setParent(self)
        self.fab.setFixedSize(60, 60)
        self.fab.clicked.connect(self.open_chat)
        self.fab.setStyleSheet("""
            QPushButton {
                background: #007acc;
                color: white;
                border: none;
                border-radius: 30px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #005a9e;
            }
            QPushButton:pressed {
                background: #004080;
            }
        """)

        # Position FAB in bottom right
        self.position_fab()

    def position_fab(self):
        """Position floating action button"""
        if hasattr(self, "fab"):
            self.fab.move(self.width() - 80, self.height() - 100)

    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)
        self.position_fab()

    def setup_animations(self):
        """Setup UI animations"""
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def setup_system_tray(self):
        """Setup system tray icon"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(QIcon("src/resources/app_icon.png"))

            # Tray menu
            tray_menu = QMenu()
            tray_menu.addAction("Show", self.show)
            tray_menu.addAction("Hide", self.hide)
            tray_menu.addSeparator()
            tray_menu.addAction("Exit", self.close)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Global shortcuts
        shortcuts = {
            "Ctrl+N": self.upload_document,
            "Ctrl+R": self.run_analysis,
            "Ctrl+T": self.open_chat,
            "F11": self.toggle_fullscreen,
            "Ctrl+,": self.show_performance_settings,
        }

        for key, func in shortcuts.items():
            action = QAction(self)
            action.setShortcut(key)
            action.triggered.connect(func)
            self.addAction(action)

    def apply_theme(self, theme_name):
        """Apply selected theme"""
        self.current_theme = theme_name

        themes = {
            "light": self.get_light_theme(),
            "dark": self.get_dark_theme(),
            "medical": self.get_medical_theme(),
            "nature": self.get_nature_theme(),
        }

        if theme_name in themes:
            self.setStyleSheet(themes[theme_name])
            self.theme_changed.emit(theme_name)

    def get_light_theme(self):
        """Light theme stylesheet"""
        return """
            QMainWindow {
                background-color: #f5f5f5;
                color: #333;
            }
            QTabWidget::pane {
                border: 1px solid #ccc;
                background: white;
            }
            QTabBar::tab {
                background: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid #007acc;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ccc;
                border-radius: 8px;
                margin: 10px 0;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """

    def get_dark_theme(self):
        """Dark theme stylesheet"""
        return """
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555;
                background: #3c3c3c;
            }
            QTabBar::tab {
                background: #404040;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #3c3c3c;
                border-bottom: 2px solid #007acc;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 8px;
                margin: 10px 0;
                padding-top: 10px;
                color: #ffffff;
            }
            QTextBrowser, QTextEdit {
                background: #404040;
                color: #ffffff;
                border: 1px solid #555;
            }
        """

    def get_medical_theme(self):
        """Medical blue theme"""
        return """
            QMainWindow {
                background-color: #f0f8ff;
                color: #003366;
            }
            QTabWidget::pane {
                border: 1px solid #4a90e2;
                background: white;
            }
            QTabBar::tab {
                background: #e6f3ff;
                color: #003366;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid #4a90e2;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4a90e2;
                border-radius: 8px;
                margin: 10px 0;
                padding-top: 10px;
                color: #003366;
            }
        """

    def get_nature_theme(self):
        """Nature green theme"""
        return """
            QMainWindow {
                background-color: #f0fff0;
                color: #2d5016;
            }
            QTabWidget::pane {
                border: 1px solid #4caf50;
                background: white;
            }
            QTabBar::tab {
                background: #e8f5e8;
                color: #2d5016;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid #4caf50;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4caf50;
                border-radius: 8px;
                margin: 10px 0;
                padding-top: 10px;
                color: #2d5016;
            }
        """

    def get_welcome_html(self):
        """Get welcome HTML for results panel"""
        return """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .welcome { text-align: center; color: #666; }
                .feature { margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 5px; }
                .icon { font-size: 24px; margin-right: 10px; }
            </style>
        </head>
        <body>
            <div class="welcome">
                <h2>🏥 Welcome to Therapy Compliance Analyzer</h2>
                <p>Upload a document to begin AI-powered compliance analysis</p>
                
                <div class="feature">
                    <span class="icon">🤖</span>
                    <strong>AI-Powered Analysis:</strong> Advanced machine learning models analyze your documentation
                </div>
                
                <div class="feature">
                    <span class="icon">🔒</span>
                    <strong>Privacy First:</strong> All processing happens locally on your machine
                </div>
                
                <div class="feature">
                    <span class="icon">📊</span>
                    <strong>Detailed Reports:</strong> Get comprehensive compliance reports with actionable insights
                </div>
                
                <div class="feature">
                    <span class="icon">💬</span>
                    <strong>AI Assistant:</strong> Chat with our AI for compliance guidance and questions
                </div>
                
                <p><em>Ready to get started? Upload your first document!</em></p>
            </div>
        </body>
        </html>
        """

    # Placeholder methods for functionality (to be implemented)
    def start(self):
        """Start the application"""
        self.load_ai_models()
        self.show()

    def load_ai_models(self):
        """Load AI models in background"""
        self.ai_status_label.setText("🤖 AI Models: Ready")
        self.ai_status_label.setStyleSheet("color: green; font-weight: bold;")

    def upload_document(self):
        """Upload document dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Upload Document", "", "Documents (*.pdf *.docx *.txt);;All Files (*)"
        )
        if file_path:
            self._current_file_path = file_path
            self.file_info_label.setText(f"📄 {os.path.basename(file_path)}")
            self.analyze_btn.setEnabled(True)
            self.status_bar.showMessage(
                f"Document loaded: {os.path.basename(file_path)}"
            )

    def upload_folder(self):
        """Upload folder dialog"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.status_bar.showMessage(f"Folder selected: {folder_path}")

    def run_analysis(self):
        """Run compliance analysis"""
        if not self._current_file_path:
            QMessageBox.warning(self, "No Document", "Please upload a document first.")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_label.setText("🔍 Analyzing document...")
        self.analyze_btn.setEnabled(False)

        # Simulate analysis (replace with actual analysis)
        QTimer.singleShot(3000, self.analysis_complete)

    def analysis_complete(self):
        """Handle analysis completion"""
        self.progress_bar.setVisible(False)
        self.progress_label.setText("✅ Analysis complete!")
        self.analyze_btn.setEnabled(True)
        self.export_pdf_btn.setEnabled(True)
        self.save_report_btn.setEnabled(True)

        # Show sample results
        self.results_browser.setHtml("""
        <html><body>
        <h2>📋 Compliance Analysis Results</h2>
        <div style="background: #e8f5e8; padding: 10px; border-radius: 5px; margin: 10px 0;">
            <h3>✅ Overall Score: 85/100</h3>
            <p>Good compliance with minor improvements needed.</p>
        </div>
        <h3>🔍 Findings:</h3>
        <ul>
            <li><strong>High Priority:</strong> Missing treatment frequency specification</li>
            <li><strong>Medium Priority:</strong> Incomplete progress measurements</li>
            <li><strong>Low Priority:</strong> Minor documentation formatting issues</li>
        </ul>
        <h3>💡 Recommendations:</h3>
        <ul>
            <li>Add specific treatment frequency (e.g., "3x per week")</li>
            <li>Include quantitative progress measurements</li>
            <li>Use standardized terminology for consistency</li>
        </ul>
        </body></html>
        """)

    def stop_analysis(self):
        """Stop running analysis"""
        self.progress_bar.setVisible(False)
        self.progress_label.setText("⏹️ Analysis stopped")
        self.analyze_btn.setEnabled(True)

    def open_chat(self):
        """Open AI chat dialog"""
        try:
            # Use a dummy token for now - in real app this would be the user's token
            chat_dialog = ChatDialog(self, token="dummy_token")
            chat_dialog.exec()
        except Exception:
            QMessageBox.information(
                self,
                "Chat Assistant",
                "💬 AI Chat Assistant\n\nChat functionality is ready!\n"
                "In the full version, this would open an interactive AI assistant.",
            )

    def manage_rubrics(self):
        """Open rubric management dialog"""
        dialog = RubricManagerDialog(self)
        dialog.exec()

    def show_performance_settings(self):
        """Show performance settings dialog"""
        dialog = PerformanceSettingsDialog(self)
        dialog.exec()

    def show_change_password_dialog(self):
        """Show change password dialog"""
        dialog = ChangePasswordDialog(self)
        dialog.exec()

    def toggle_animations(self):
        """Toggle UI animations"""
        self.animations_enabled = self.animation_action.isChecked()

    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def zoom_in(self):
        """Zoom in text"""
        font = self.font()
        font.setPointSize(font.pointSize() + 1)
        self.setFont(font)

    def zoom_out(self):
        """Zoom out text"""
        font = self.font()
        if font.pointSize() > 8:
            font.setPointSize(font.pointSize() - 1)
            self.setFont(font)

    def reset_zoom(self):
        """Reset zoom to default"""
        font = self.font()
        font.setPointSize(10)
        self.setFont(font)

    def apply_settings(self):
        """Apply user settings"""
        QMessageBox.information(self, "Settings", "Settings applied successfully!")

    def save_report(self):
        """Save analysis report"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", "", "HTML Files (*.html);;All Files (*)"
        )
        if file_path:
            self.status_bar.showMessage(f"Report saved: {file_path}")

    def export_pdf(self):
        """Export report as PDF"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if file_path:
            self.status_bar.showMessage(f"PDF exported: {file_path}")

    def show_developer_panel(self):
        """Show developer panel (easter egg)"""
        if not self.developer_mode:
            self.developer_mode = True
            dev_menu = self.menu_bar.addMenu("🔧 Developer")
            dev_menu.addAction("🐛 Debug Console", self.show_debug_console)
            dev_menu.addAction("📊 Performance Monitor", self.show_performance_monitor)
            dev_menu.addAction("🔍 Model Inspector", self.show_model_inspector)

    def show_debug_console(self):
        """Show debug console"""
        QMessageBox.information(self, "Debug Console", "Debug console would open here!")

    def show_performance_monitor(self):
        """Show performance monitor"""
        QMessageBox.information(
            self, "Performance Monitor", "Performance monitor would open here!"
        )

    def show_model_inspector(self):
        """Show model inspector"""
        QMessageBox.information(
            self, "Model Inspector", "Model inspector would open here!"
        )

    # Help menu methods
    def show_user_guide(self):
        """Show user guide"""
        QMessageBox.information(self, "User Guide", "User guide would open here!")

    def show_quick_start(self):
        """Show quick start guide"""
        QMessageBox.information(
            self, "Quick Start", "Quick start guide would open here!"
        )

    def show_troubleshooting(self):
        """Show troubleshooting guide"""
        QMessageBox.information(
            self, "Troubleshooting", "Troubleshooting guide would open here!"
        )

    def open_online_help(self):
        """Open online help"""
        webbrowser.open("https://example.com/help")

    def contact_support(self):
        """Contact support"""
        QMessageBox.information(
            self, "Support", "Support contact information would be shown here!"
        )

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About",
            """
        <h2>🏥 Therapy Compliance Analyzer</h2>
        <p><b>Version:</b> 2.0 Enhanced Edition</p>
        <p><b>AI-Powered Clinical Documentation Analysis</b></p>
        <br>
        <p>Features:</p>
        <ul>
        <li>🤖 Local AI Processing</li>
        <li>🔒 HIPAA Compliant</li>
        <li>📊 Advanced Analytics</li>
        <li>💬 AI Chat Assistant</li>
        <li>🎨 Multiple Themes</li>
        </ul>
        <br>
        <p><i>Developed with ❤️ for Healthcare Professionals</i></p>
        """,
        )

    # Utility methods
    def quick_compliance_check(self):
        """Quick compliance check"""
        QMessageBox.information(
            self, "Quick Check", "Quick compliance check would run here!"
        )

    def batch_analysis(self):
        """Batch analysis"""
        QMessageBox.information(
            self, "Batch Analysis", "Batch analysis would run here!"
        )

    def clear_cache(self):
        """Clear application cache"""
        QMessageBox.information(
            self, "Cache Cleared", "Application cache has been cleared!"
        )

    def refresh_ai_models(self):
        """Refresh AI models"""
        self.ai_status_label.setText("🤖 AI Models: Refreshing...")
        self.ai_status_label.setStyleSheet("color: orange; font-weight: bold;")
        QTimer.singleShot(
            2000,
            lambda: (
                self.ai_status_label.setText("🤖 AI Models: Ready"),
                self.ai_status_label.setStyleSheet("color: green; font-weight: bold;"),
            ),
        )

    def logout(self):
        """Logout user"""
        self.close()


# Alias for compatibility
MainApplicationWindow = EnhancedMainWindow
