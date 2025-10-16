from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.cache_service import cache_service
from src.gui.widgets.medical_theme import medical_theme


class SettingsDialog(QDialog):
    """A dialog for configuring application-wide settings."""

    def __init__(self, parent=None, *, settings: QSettings | None = None, cache_service_override=None):
        super().__init__(parent)
        self.setWindowTitle("🔧 Application Settings")
        self.setMinimumSize(700, 600)  # Larger minimum size
        self.resize(800, 700)  # Default size

        self.settings = settings or QSettings("TherapyCo", "ComplianceAnalyzer")
        self._cache_service = cache_service_override or cache_service

        # Apply medical theme
        self.setStyleSheet(
            medical_theme.get_main_window_stylesheet()
            + medical_theme.get_form_stylesheet()
            + medical_theme.get_tab_stylesheet()
            + medical_theme.get_card_stylesheet()
        )

        # --- Main Layout and Tabs ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(16)
        self.main_layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header_label = QLabel("Application Settings")
        header_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header_label.setStyleSheet(f"color: {medical_theme.get_color('primary_blue')}; margin-bottom: 16px;")
        self.main_layout.addWidget(header_label)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.main_layout.addWidget(self.tab_widget)

        # --- Analysis Tab ---
        self.analysis_tab = self._create_analysis_tab()
        self.tab_widget.addTab(self.analysis_tab, "📊 Analysis")

        # --- Performance Tab ---
        self.performance_tab = self._create_performance_tab()
        self.tab_widget.addTab(self.performance_tab, "⚡ Performance")

        # --- Automation Tab ---
        self.automation_tab = self._create_automation_tab()
        self.tab_widget.addTab(self.automation_tab, "🤖 Automation")

        # --- Privacy & Security Tab ---
        self.privacy_tab = self._create_privacy_tab()
        self.tab_widget.addTab(self.privacy_tab, "🔒 Privacy & Security")

        # --- Interface Tab ---
        self.interface_tab = self._create_interface_tab()
        self.tab_widget.addTab(self.interface_tab, "🎨 Interface")

        # --- Buttons ---
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply
        )
        self.main_layout.addWidget(self.button_box)

        # --- Connections ---
        self.button_box.accepted.connect(self.save_settings)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_settings)
        self.clear_cache_button.clicked.connect(self.clear_cache)
        self.watch_folder_browse_button.clicked.connect(self._select_watch_folder)

        self.load_settings()

    def _create_analysis_tab(self) -> QWidget:
        """Create the analysis settings tab with proper spacing."""
        tab = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(16, 16, 16, 16)

        # Compliance Analysis Group
        compliance_group = QGroupBox("📋 Compliance Analysis Settings")
        compliance_layout = QGridLayout(compliance_group)
        compliance_layout.setSpacing(12)

        self.strict_mode_checkbox = QCheckBox("Enable strict compliance checks")
        self.strict_mode_checkbox.setToolTip("Apply stricter compliance rules for higher accuracy")
        compliance_layout.addWidget(self.strict_mode_checkbox, 0, 0, 1, 2)

        sensitivity_label = QLabel("Analysis Sensitivity:")
        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(1, 10)
        self.sensitivity_slider.setValue(5)
        self.sensitivity_value_label = QLabel("5")
        self.sensitivity_slider.valueChanged.connect(lambda v: self.sensitivity_value_label.setText(str(v)))

        compliance_layout.addWidget(sensitivity_label, 1, 0)
        compliance_layout.addWidget(self.sensitivity_slider, 1, 1)
        compliance_layout.addWidget(self.sensitivity_value_label, 1, 2)

        layout.addWidget(compliance_group)

        # AI Model Settings Group
        ai_group = QGroupBox("🤖 AI Model Configuration")
        ai_layout = QGridLayout(ai_group)
        ai_layout.setSpacing(12)

        self.confidence_threshold_spinbox = QSpinBox()
        self.confidence_threshold_spinbox.setRange(50, 95)
        self.confidence_threshold_spinbox.setValue(75)
        self.confidence_threshold_spinbox.setSuffix("%")
        ai_layout.addWidget(QLabel("Minimum Confidence Threshold:"), 0, 0)
        ai_layout.addWidget(self.confidence_threshold_spinbox, 0, 1)

        self.enable_fact_checking_checkbox = QCheckBox("Enable AI fact-checking verification")
        self.enable_fact_checking_checkbox.setChecked(True)
        ai_layout.addWidget(self.enable_fact_checking_checkbox, 1, 0, 1, 2)

        layout.addWidget(ai_group)
        layout.addStretch()

        scroll_area.setWidget(content_widget)
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll_area)

        return tab

    def _create_performance_tab(self) -> QWidget:
        """Create the performance settings tab with proper spacing."""
        tab = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(16, 16, 16, 16)

        # Processing Group
        processing_group = QGroupBox("⚡ Processing Configuration")
        processing_layout = QGridLayout(processing_group)
        processing_layout.setSpacing(12)

        self.use_gpu_checkbox = QCheckBox("Utilize GPU for processing (if available)")
        self.model_quantization_checkbox = QCheckBox("Use quantized models for lower memory usage")
        self.model_quantization_checkbox.setChecked(True)

        processing_layout.addWidget(self.use_gpu_checkbox, 0, 0, 1, 2)
        processing_layout.addWidget(self.model_quantization_checkbox, 1, 0, 1, 2)

        self.max_workers_spinbox = QSpinBox()
        self.max_workers_spinbox.setRange(1, 16)
        self.max_workers_spinbox.setValue(2)
        processing_layout.addWidget(QLabel("Max Parallel Workers:"), 2, 0)
        processing_layout.addWidget(self.max_workers_spinbox, 2, 1)

        layout.addWidget(processing_group)

        # Cache Management Group
        cache_group = QGroupBox("💾 Cache Management")
        cache_layout = QGridLayout(cache_group)
        cache_layout.setSpacing(12)

        self.cache_size_spinbox = QSpinBox()
        self.cache_size_spinbox.setRange(64, 8192)
        self.cache_size_spinbox.setValue(2048)
        self.cache_size_spinbox.setSuffix(" MB")
        cache_layout.addWidget(QLabel("Max Disk Cache Size:"), 0, 0)
        cache_layout.addWidget(self.cache_size_spinbox, 0, 1)

        self.clear_cache_button = QPushButton("🗑️ Clear Document & Analysis Cache")
        self.clear_cache_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        cache_layout.addWidget(self.clear_cache_button, 1, 0, 1, 2)

        layout.addWidget(cache_group)
        layout.addStretch()

        scroll_area.setWidget(content_widget)
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll_area)

        return tab

    def _create_automation_tab(self) -> QWidget:
        """Create the automation settings tab with proper spacing."""
        tab = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(16, 16, 16, 16)

        # Watch Folder Group
        watch_group = QGroupBox("📁 Watch Folder Automation")
        watch_layout = QGridLayout(watch_group)
        watch_layout.setSpacing(12)

        self.watch_folder_enabled_checkbox = QCheckBox("Enable Watch Folder for automated analysis")
        watch_layout.addWidget(self.watch_folder_enabled_checkbox, 0, 0, 1, 3)

        watch_layout.addWidget(QLabel("Folder to Watch:"), 1, 0)
        self.watch_folder_path_edit = QLineEdit()
        self.watch_folder_path_edit.setReadOnly(True)
        self.watch_folder_path_edit.setPlaceholderText("Select a folder to monitor...")
        self.watch_folder_browse_button = QPushButton("📂 Browse...")
        self.watch_folder_browse_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))

        watch_layout.addWidget(self.watch_folder_path_edit, 1, 1)
        watch_layout.addWidget(self.watch_folder_browse_button, 1, 2)

        self.scan_interval_spinbox = QSpinBox()
        self.scan_interval_spinbox.setRange(5, 300)
        self.scan_interval_spinbox.setValue(10)
        self.scan_interval_spinbox.setSuffix(" seconds")
        watch_layout.addWidget(QLabel("Scan Interval:"), 2, 0)
        watch_layout.addWidget(self.scan_interval_spinbox, 2, 1)

        layout.addWidget(watch_group)

        # Batch Processing Group
        batch_group = QGroupBox("📊 Batch Processing")
        batch_layout = QGridLayout(batch_group)
        batch_layout.setSpacing(12)

        self.auto_export_checkbox = QCheckBox("Automatically export reports after analysis")
        self.auto_export_format_combo = QComboBox()
        self.auto_export_format_combo.addItems(["HTML", "PDF", "Both"])

        batch_layout.addWidget(self.auto_export_checkbox, 0, 0, 1, 2)
        batch_layout.addWidget(QLabel("Export Format:"), 1, 0)
        batch_layout.addWidget(self.auto_export_format_combo, 1, 1)

        layout.addWidget(batch_group)
        layout.addStretch()

        scroll_area.setWidget(content_widget)
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll_area)

        return tab

    def _create_privacy_tab(self) -> QWidget:
        """Create the privacy and security settings tab."""
        tab = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(16, 16, 16, 16)

        # PHI Protection Group
        phi_group = QGroupBox("🔒 PHI Protection")
        phi_layout = QGridLayout(phi_group)
        phi_layout.setSpacing(12)

        self.enable_phi_scrubbing_checkbox = QCheckBox("Enable automatic PHI scrubbing")
        self.enable_phi_scrubbing_checkbox.setChecked(True)
        self.enable_phi_scrubbing_checkbox.setToolTip("Automatically detect and redact Protected Health Information")
        phi_layout.addWidget(self.enable_phi_scrubbing_checkbox, 0, 0, 1, 2)

        self.phi_confidence_spinbox = QSpinBox()
        self.phi_confidence_spinbox.setRange(50, 95)
        self.phi_confidence_spinbox.setValue(80)
        self.phi_confidence_spinbox.setSuffix("%")
        phi_layout.addWidget(QLabel("PHI Detection Confidence:"), 1, 0)
        phi_layout.addWidget(self.phi_confidence_spinbox, 1, 1)

        layout.addWidget(phi_group)

        # Data Retention Group
        retention_group = QGroupBox("📅 Data Retention")
        retention_layout = QGridLayout(retention_group)
        retention_layout.setSpacing(12)

        self.auto_delete_reports_checkbox = QCheckBox("Automatically delete old reports")
        self.retention_days_spinbox = QSpinBox()
        self.retention_days_spinbox.setRange(1, 365)
        self.retention_days_spinbox.setValue(30)
        self.retention_days_spinbox.setSuffix(" days")

        retention_layout.addWidget(self.auto_delete_reports_checkbox, 0, 0, 1, 2)
        retention_layout.addWidget(QLabel("Retention Period:"), 1, 0)
        retention_layout.addWidget(self.retention_days_spinbox, 1, 1)

        layout.addWidget(retention_group)
        layout.addStretch()

        scroll_area.setWidget(content_widget)
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll_area)

        return tab

    def _create_interface_tab(self) -> QWidget:
        """Create the interface settings tab."""
        tab = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(16, 16, 16, 16)

        # Theme Group
        theme_group = QGroupBox("🎨 Appearance")
        theme_layout = QGridLayout(theme_group)
        theme_layout.setSpacing(12)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Auto (System)"])
        theme_layout.addWidget(QLabel("Theme:"), 0, 0)
        theme_layout.addWidget(self.theme_combo, 0, 1)

        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 24)
        self.font_size_spinbox.setValue(14)
        self.font_size_spinbox.setSuffix(" pt")
        theme_layout.addWidget(QLabel("Font Size:"), 1, 0)
        theme_layout.addWidget(self.font_size_spinbox, 1, 1)

        layout.addWidget(theme_group)

        # Notifications Group
        notifications_group = QGroupBox("🔔 Notifications")
        notifications_layout = QGridLayout(notifications_group)
        notifications_layout.setSpacing(12)

        self.show_completion_notifications_checkbox = QCheckBox("Show analysis completion notifications")
        self.show_completion_notifications_checkbox.setChecked(True)
        self.play_sound_checkbox = QCheckBox("Play sound on completion")

        notifications_layout.addWidget(self.show_completion_notifications_checkbox, 0, 0, 1, 2)
        notifications_layout.addWidget(self.play_sound_checkbox, 1, 0, 1, 2)

        layout.addWidget(notifications_group)
        layout.addStretch()

        scroll_area.setWidget(content_widget)
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll_area)

        return tab

    def load_settings(self):
        """Load settings from QSettings and populate the UI."""
        # Analysis
        self.strict_mode_checkbox.setChecked(self.settings.value("analysis/strict_mode", False, type=bool))
        self.sensitivity_slider.setValue(self.settings.value("analysis/sensitivity", 5, type=int))
        self.confidence_threshold_spinbox.setValue(self.settings.value("analysis/confidence_threshold", 75, type=int))
        self.enable_fact_checking_checkbox.setChecked(
            self.settings.value("analysis/enable_fact_checking", True, type=bool)
        )

        # Performance
        self.use_gpu_checkbox.setChecked(self.settings.value("performance/use_gpu", False, type=bool))
        self.model_quantization_checkbox.setChecked(
            self.settings.value("performance/model_quantization", True, type=bool)
        )
        self.max_workers_spinbox.setValue(self.settings.value("performance/max_workers", 2, type=int))
        self.cache_size_spinbox.setValue(self.settings.value("performance/max_cache_memory_mb", 2048, type=int))

        # Automation
        self.watch_folder_enabled_checkbox.setChecked(
            self.settings.value("automation/watch_folder_enabled", False, type=bool)
        )
        self.watch_folder_path_edit.setText(self.settings.value("automation/watch_folder_path", "", type=str))
        self.scan_interval_spinbox.setValue(self.settings.value("automation/scan_interval", 10, type=int))
        self.auto_export_checkbox.setChecked(self.settings.value("automation/auto_export", False, type=bool))
        self.auto_export_format_combo.setCurrentText(self.settings.value("automation/export_format", "HTML", type=str))

        # Privacy & Security
        self.enable_phi_scrubbing_checkbox.setChecked(
            self.settings.value("privacy/enable_phi_scrubbing", True, type=bool)
        )
        self.phi_confidence_spinbox.setValue(self.settings.value("privacy/phi_confidence", 80, type=int))
        self.auto_delete_reports_checkbox.setChecked(
            self.settings.value("privacy/auto_delete_reports", False, type=bool)
        )
        self.retention_days_spinbox.setValue(self.settings.value("privacy/retention_days", 30, type=int))

        # Interface
        self.theme_combo.setCurrentText(self.settings.value("interface/theme", "Light", type=str))
        self.font_size_spinbox.setValue(self.settings.value("interface/font_size", 14, type=int))
        self.show_completion_notifications_checkbox.setChecked(
            self.settings.value("interface/show_notifications", True, type=bool)
        )
        self.play_sound_checkbox.setChecked(self.settings.value("interface/play_sound", False, type=bool))

    def apply_settings(self):
        """Save the current settings."""
        # Analysis
        self.settings.setValue("analysis/strict_mode", self.strict_mode_checkbox.isChecked())
        self.settings.setValue("analysis/sensitivity", self.sensitivity_slider.value())
        self.settings.setValue("analysis/confidence_threshold", self.confidence_threshold_spinbox.value())
        self.settings.setValue("analysis/enable_fact_checking", self.enable_fact_checking_checkbox.isChecked())

        # Performance
        self.settings.setValue("performance/use_gpu", self.use_gpu_checkbox.isChecked())
        self.settings.setValue("performance/model_quantization", self.model_quantization_checkbox.isChecked())
        self.settings.setValue("performance/max_workers", self.max_workers_spinbox.value())
        self.settings.setValue("performance/max_cache_memory_mb", self.cache_size_spinbox.value())

        # Automation
        self.settings.setValue("automation/watch_folder_enabled", self.watch_folder_enabled_checkbox.isChecked())
        self.settings.setValue("automation/watch_folder_path", self.watch_folder_path_edit.text())
        self.settings.setValue("automation/scan_interval", self.scan_interval_spinbox.value())
        self.settings.setValue("automation/auto_export", self.auto_export_checkbox.isChecked())
        self.settings.setValue("automation/export_format", self.auto_export_format_combo.currentText())

        # Privacy & Security
        self.settings.setValue("privacy/enable_phi_scrubbing", self.enable_phi_scrubbing_checkbox.isChecked())
        self.settings.setValue("privacy/phi_confidence", self.phi_confidence_spinbox.value())
        self.settings.setValue("privacy/auto_delete_reports", self.auto_delete_reports_checkbox.isChecked())
        self.settings.setValue("privacy/retention_days", self.retention_days_spinbox.value())

        # Interface
        self.settings.setValue("interface/theme", self.theme_combo.currentText())
        self.settings.setValue("interface/font_size", self.font_size_spinbox.value())
        self.settings.setValue("interface/show_notifications", self.show_completion_notifications_checkbox.isChecked())
        self.settings.setValue("interface/play_sound", self.play_sound_checkbox.isChecked())

        QMessageBox.information(
            self,
            "✅ Settings Applied",
            "Your settings have been saved successfully!\n\nSome changes may require an application restart to take full effect.",
        )

    def save_settings(self):
        """Apply settings and close the dialog."""
        self.apply_settings()
        self.accept()

    def clear_cache(self):
        """Clear the on-disk application cache."""
        reply = QMessageBox.question(
            self,
            "Confirm Cache Deletion",
            "Are you sure you want to delete all cached document and analysis data? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._cache_service.clear_disk_cache()
                QMessageBox.information(self, "Cache Cleared", "The application cache has been successfully cleared.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear cache: {e}")

    def _select_watch_folder(self):
        """Opens a dialog to select the watch folder."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Watch Folder", self.watch_folder_path_edit.text())
        if folder_path:
            self.watch_folder_path_edit.setText(folder_path)
