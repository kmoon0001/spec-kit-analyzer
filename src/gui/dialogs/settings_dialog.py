
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QFormLayout, 
    QCheckBox, QSlider, QSpinBox, QPushButton, QMessageBox, QDialogButtonBox,
    QHBoxLayout, QLineEdit, QFileDialog
)
from PySide6.QtCore import Qt, QSettings

from src.core.cache_service import cache_service

class SettingsDialog(QDialog):
    """A dialog for configuring application-wide settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Settings")
        self.setMinimumWidth(500)

        self.settings = QSettings("TherapyCo", "ComplianceAnalyzer")

        # --- Main Layout and Tabs ---
        self.main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        # --- Analysis Tab ---
        self.analysis_tab = QWidget()
        self.analysis_layout = QFormLayout(self.analysis_tab)
        self.strict_mode_checkbox = QCheckBox("Enable strict compliance checks")
        self.sensitivity_slider = QSlider(Qt.Horizontal)
        self.sensitivity_slider.setRange(1, 10)
        self.analysis_layout.addRow("Strict Mode:", self.strict_mode_checkbox)
        self.analysis_layout.addRow("Analysis Sensitivity:", self.sensitivity_slider)
        self.tab_widget.addTab(self.analysis_tab, "Analysis")

        # --- Performance Tab ---
        self.performance_tab = QWidget()
        self.performance_layout = QFormLayout(self.performance_tab)
        self.use_gpu_checkbox = QCheckBox("Utilize GPU for processing (if available)")
        self.model_quantization_checkbox = QCheckBox("Use quantized models for lower memory usage")
        self.max_workers_spinbox = QSpinBox()
        self.max_workers_spinbox.setRange(1, 16)
        self.cache_size_spinbox = QSpinBox()
        self.cache_size_spinbox.setRange(64, 8192)
        self.cache_size_spinbox.setSuffix(" MB")
        self.clear_cache_button = QPushButton("Clear Document & Analysis Cache")
        self.performance_layout.addRow(self.use_gpu_checkbox)
        self.performance_layout.addRow(self.model_quantization_checkbox)
        self.performance_layout.addRow("Max Parallel Workers:", self.max_workers_spinbox)
        self.performance_layout.addRow("Max Disk Cache Size:", self.cache_size_spinbox)
        self.performance_layout.addRow(self.clear_cache_button)
        self.tab_widget.addTab(self.performance_tab, "Performance")

        # --- Automation Tab ---
        self.automation_tab = QWidget()
        self.automation_layout = QFormLayout(self.automation_tab)
        self.watch_folder_enabled_checkbox = QCheckBox("Enable Watch Folder for automated analysis")
        self.watch_folder_path_edit = QLineEdit()
        self.watch_folder_path_edit.setReadOnly(True)
        self.watch_folder_browse_button = QPushButton("Browse…")
        watch_folder_layout = QHBoxLayout()
        watch_folder_layout.addWidget(self.watch_folder_path_edit)
        watch_folder_layout.addWidget(self.watch_folder_browse_button)
        self.scan_interval_spinbox = QSpinBox()
        self.scan_interval_spinbox.setRange(5, 300) # 5 seconds to 5 minutes
        self.scan_interval_spinbox.setSuffix(" seconds")
        self.automation_layout.addRow(self.watch_folder_enabled_checkbox)
        self.automation_layout.addRow("Folder to Watch:", watch_folder_layout)
        self.automation_layout.addRow("Scan Interval:", self.scan_interval_spinbox)
        self.tab_widget.addTab(self.automation_tab, "Automation")

        # --- Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Apply)
        self.main_layout.addWidget(self.button_box)

        # --- Connections ---
        self.button_box.accepted.connect(self.save_settings)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_settings)
        self.clear_cache_button.clicked.connect(self.clear_cache)
        self.watch_folder_browse_button.clicked.connect(self._select_watch_folder)

        self.load_settings()

    def load_settings(self):
        """Load settings from QSettings and populate the UI."""
        # Analysis
        self.strict_mode_checkbox.setChecked(self.settings.value("analysis/strict_mode", False, type=bool))
        self.sensitivity_slider.setValue(self.settings.value("analysis/sensitivity", 5, type=int))

        # Performance
        self.use_gpu_checkbox.setChecked(self.settings.value("performance/use_gpu", False, type=bool))
        self.model_quantization_checkbox.setChecked(self.settings.value("performance/model_quantization", True, type=bool))
        self.max_workers_spinbox.setValue(self.settings.value("performance/max_workers", 2, type=int))
        self.cache_size_spinbox.setValue(self.settings.value("performance/max_cache_memory_mb", 2048, type=int))

        # Automation
        self.watch_folder_enabled_checkbox.setChecked(self.settings.value("automation/watch_folder_enabled", False, type=bool))
        self.watch_folder_path_edit.setText(self.settings.value("automation/watch_folder_path", "", type=str))
        self.scan_interval_spinbox.setValue(self.settings.value("automation/scan_interval", 10, type=int))

    def apply_settings(self):
        """Save the current settings."""
        # Analysis
        self.settings.setValue("analysis/strict_mode", self.strict_mode_checkbox.isChecked())
        self.settings.setValue("analysis/sensitivity", self.sensitivity_slider.value())

        # Performance
        self.settings.setValue("performance/use_gpu", self.use_gpu_checkbox.isChecked())
        self.settings.setValue("performance/model_quantization", self.model_quantization_checkbox.isChecked())
        self.settings.setValue("performance/max_workers", self.max_workers_spinbox.value())
        self.settings.setValue("performance/max_cache_memory_mb", self.cache_size_spinbox.value())

        # Automation
        self.settings.setValue("automation/watch_folder_enabled", self.watch_folder_enabled_checkbox.isChecked())
        self.settings.setValue("automation/watch_folder_path", self.watch_folder_path_edit.text())
        self.settings.setValue("automation/scan_interval", self.scan_interval_spinbox.value())
        
        QMessageBox.information(self, "Settings Applied", "Your settings have been saved. Some changes may require an application restart to take full effect.")

    def save_settings(self):
        """Apply settings and close the dialog."""
        self.apply_settings()
        self.accept()

    def clear_cache(self):
        """Clear the on-disk application cache."""
        reply = QMessageBox.question(self, "Confirm Cache Deletion", 
                                     "Are you sure you want to delete all cached document and analysis data? This cannot be undone.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                cache_service.clear_disk_cache()
                QMessageBox.information(self, "Cache Cleared", "The application cache has been successfully cleared.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear cache: {e}")

    def _select_watch_folder(self):
        """Opens a dialog to select the watch folder."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Watch Folder", self.watch_folder_path_edit.text())
        if folder_path:
            self.watch_folder_path_edit.setText(folder_path)
