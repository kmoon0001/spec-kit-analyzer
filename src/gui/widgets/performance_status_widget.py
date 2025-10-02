"""
Performance Status Widget - Shows real-time performance metrics in the main window.
Provides quick access to performance settings and system monitoring.
"""

import logging
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QProgressBar
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class PerformanceStatusWidget(QWidget):
    """
    Compact performance status widget for the main window status bar.
    Shows key metrics and provides quick access to performance settings.
    """

    settings_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.performance_manager = None
        self.setup_ui()
        self.setup_performance_manager()

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(5000)  # Update every 5 seconds

    def setup_ui(self):
        """Setup the performance status UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        # Performance profile indicator
        self.profile_label = QLabel("Balanced")
        self.profile_label.setStyleSheet(
            """
            QLabel {
                background-color: #e8f4fd;
                border: 1px solid #bee5eb;
                border-radius: 3px;
                padding: 2px 6px;
                font-size: 10px;
                font-weight: bold;
            }
        """
        )

        # Memory usage indicator
        self.memory_bar = QProgressBar()
        self.memory_bar.setRange(0, 100)
        self.memory_bar.setFixedSize(60, 12)
        self.memory_bar.setTextVisible(False)
        self.memory_bar.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 2px;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 1px;
            }
        """
        )

        # Status text
        self.status_label = QLabel("Optimal")
        font = QFont()
        font.setPointSize(9)
        self.status_label.setFont(font)

        # Settings button
        self.settings_button = QPushButton("⚙")
        self.settings_button.setFixedSize(20, 20)
        self.settings_button.setToolTip("Open Performance Settings")
        self.settings_button.clicked.connect(self.settings_requested.emit)
        self.settings_button.setStyleSheet(
            """
            QPushButton {
                border: 1px solid #ccc;
                border-radius: 10px;
                background-color: #f8f9fa;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """
        )

        # Add widgets to layout
        layout.addWidget(QLabel("Performance:"))
        layout.addWidget(self.profile_label)
        layout.addWidget(QLabel("Memory:"))
        layout.addWidget(self.memory_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.settings_button)

    def setup_performance_manager(self):
        """Initialize performance manager connection."""
        try:
            from ...core.performance_manager import performance_manager

            self.performance_manager = performance_manager
            logger.info("Performance manager connected to status widget")
        except ImportError:
            logger.warning("Performance manager not available")

    def update_status(self):
        """Update performance status display with error handling."""
        if not self.performance_manager:
            return

        try:
            # Get current performance data with timeout protection
            memory_stats = self.performance_manager.get_memory_usage()
            current_profile = self.performance_manager.current_profile

            # Update profile display
            profile_name = (
                current_profile.value.title() if current_profile else "Unknown"
            )
            self.profile_label.setText(profile_name)

            # Update memory bar
            memory_percent = memory_stats.get("system_used_percent", 0)
            self.memory_bar.setValue(int(memory_percent))

            # Update memory bar color based on usage
            if memory_percent > 85:
                color = "#f44336"  # Red
                status = "High Load"
            elif memory_percent > 70:
                color = "#ff9800"  # Orange
                status = "Moderate"
            else:
                color = "#4CAF50"  # Green
                status = "Optimal"

            self.memory_bar.setStyleSheet(
                f"""
                QProgressBar {{
                    border: 1px solid #ccc;
                    border-radius: 2px;
                    background-color: #f0f0f0;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 1px;
                }}
            """
            )

            # Update status text
            self.status_label.setText(status)

            # Update tooltips with detailed info
            process_memory = memory_stats.get("process_memory_mb", 0)
            tooltip = (
                f"System Memory: {memory_percent:.1f}%\n"
                f"Process Memory: {process_memory:.1f} MB\n"
                f"Profile: {profile_name}\n"
                f"Status: {status}"
            )
            self.setToolTip(tooltip)

        except Exception as e:
            logger.error(f"Error updating performance status: {e}")
            self.status_label.setText("Error")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get current performance summary for external use."""
        if not self.performance_manager:
            return {}

        try:
            memory_stats = self.performance_manager.get_memory_usage()
            return {
                "profile": self.performance_manager.current_profile.value,
                "memory_percent": memory_stats.get("system_used_percent", 0),
                "process_memory_mb": memory_stats.get("process_memory_mb", 0),
                "status": self.status_label.text(),
            }
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {}

    def cleanup(self):
        """Clean up resources."""
        if self.update_timer:
            self.update_timer.stop()
