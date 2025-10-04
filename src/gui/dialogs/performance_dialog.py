"""
Performance Settings Dialog - Simplified version for system configuration.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QGroupBox,
    QProgressBar,
    QFormLayout,
    QSpinBox,
    QCheckBox,
)
from PySide6.QtCore import QTimer, Signal
import logging

logger = logging.getLogger(__name__)


class PerformanceDialog(QDialog):
    """Simplified performance settings dialog."""

    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Performance Settings")
        self.setModal(True)
        self.resize(500, 400)

        try:
            from ...core.performance_manager import (
                performance_manager,
                PerformanceProfile,
            )

            self.performance_manager = performance_manager
            self.PerformanceProfile = PerformanceProfile
        except ImportError as e:
            logger.error(f"Could not import performance manager: {e}")
            self.performance_manager = None
            return

        self.setup_ui()
        self.load_settings()

        # Monitor timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_memory_display)
        self.timer.start(2000)

    def setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout(self)

        # Profile selection
        profile_group = QGroupBox("Performance Profile")
        profile_layout = QFormLayout(profile_group)

        self.profile_combo = QComboBox()
        for profile in self.PerformanceProfile:
            self.profile_combo.addItem(profile.value.title(), profile)

        profile_layout.addRow("Profile:", self.profile_combo)
        layout.addWidget(profile_group)

        # System info
        system_group = QGroupBox("System Information")
        system_layout = QFormLayout(system_group)

        self.memory_label = QLabel()
        self.cpu_label = QLabel()
        self.gpu_label = QLabel()

        system_layout.addRow("Memory:", self.memory_label)
        system_layout.addRow("CPU Cores:", self.cpu_label)
        system_layout.addRow("GPU:", self.gpu_label)

        # Memory usage bar
        self.memory_bar = QProgressBar()
        self.memory_bar.setRange(0, 100)
        system_layout.addRow("Memory Usage:", self.memory_bar)

        layout.addWidget(system_group)

        # Settings
        settings_group = QGroupBox("Settings")
        settings_layout = QFormLayout(settings_group)

        self.cache_spin = QSpinBox()
        self.cache_spin.setRange(256, 8192)
        self.cache_spin.setSuffix(" MB")
        settings_layout.addRow("Cache Memory:", self.cache_spin)

        self.gpu_check = QCheckBox()
        settings_layout.addRow("Use GPU:", self.gpu_check)

        self.quantization_check = QCheckBox()
        settings_layout.addRow("Model Quantization:", self.quantization_check)

        layout.addWidget(settings_group)

        # Buttons
        button_layout = QHBoxLayout()

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_settings)

        reset_btn = QPushButton("Auto Detect")
        reset_btn.clicked.connect(self.auto_detect)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        button_layout.addWidget(apply_btn)
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def load_settings(self):
        """Load current settings."""
        if not self.performance_manager:
            return

        config = self.performance_manager.config
        system_info = self.performance_manager.system_info

        # System info
        self.memory_label.setText(f"{system_info['total_memory_gb']} GB")
        self.cpu_label.setText(str(system_info["cpu_count"]))

        gpu_text = "Available" if system_info["cuda_available"] else "Not Available"
        self.gpu_label.setText(gpu_text)

        # Settings
        self.cache_spin.setValue(config.max_cache_memory_mb)
        self.gpu_check.setChecked(config.use_gpu)
        self.quantization_check.setChecked(config.model_quantization)

        # Profile
        current_profile = self.performance_manager.current_profile
        index = self.profile_combo.findData(current_profile)
        if index >= 0:
            self.profile_combo.setCurrentIndex(index)

    def update_memory_display(self):
        """Update memory usage display."""
        if not self.performance_manager:
            return

        try:
            memory_usage = self.performance_manager.get_memory_usage()
            percent = int(memory_usage["system_used_percent"])
            self.memory_bar.setValue(percent)

            # Color coding
            if percent > 85:
                self.memory_bar.setStyleSheet(
                    "QProgressBar::chunk { background-color: red; }"
                )
            elif percent > 70:
                self.memory_bar.setStyleSheet(
                    "QProgressBar::chunk { background-color: orange; }"
                )
            else:
                self.memory_bar.setStyleSheet(
                    "QProgressBar::chunk { background-color: green; }"
                )
        except Exception as e:
            logger.error(f"Error updating memory display: {e}")

    def apply_settings(self):
        """Apply current settings."""
        if not self.performance_manager:
            return

        try:
            profile = self.profile_combo.currentData()
            self.performance_manager.set_profile(profile)

            # Update specific settings if custom
            if profile == self.PerformanceProfile.CUSTOM:
                config = self.performance_manager.config
                config.max_cache_memory_mb = self.cache_spin.value()
                config.use_gpu = self.gpu_check.isChecked()
                config.model_quantization = self.quantization_check.isChecked()
                self.performance_manager.save_config()

            self.settings_changed.emit()
            logger.info("Performance settings applied")

        except Exception as e:
            logger.error(f"Error applying settings: {e}")

    def auto_detect(self):
        """Auto-detect optimal settings."""
        if not self.performance_manager:
            return

        try:
            from ...core.performance_manager import SystemProfiler

            recommended = SystemProfiler.recommend_profile(
                self.performance_manager.system_info
            )

            index = self.profile_combo.findData(recommended)
            if index >= 0:
                self.profile_combo.setCurrentIndex(index)

            self.apply_settings()

        except Exception as e:
            logger.error(f"Error in auto-detect: {e}")

    def closeEvent(self, event):
        """Handle close event."""
        if hasattr(self, "timer"):
            self.timer.stop()
        super().closeEvent(event)
