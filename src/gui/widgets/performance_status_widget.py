"""Performance Status Widget - Shows real-time performance metrics.

This widget provides a live view of the application's CPU and memory usage,
helping to monitor and diagnose performance issues.
"""

import logging

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QWidget

from ...core.performance_manager import get_performance_manager

logger = logging.getLogger(__name__)

class PerformanceStatusWidget(QWidget):
    """A widget that displays real-time CPU and memory usage.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.performance_manager = get_performance_manager()
        self._setup_ui()

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start(2000)  # Update every 2 seconds

    def _setup_ui(self):
        """Sets up the user interface for the widget."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)

        # CPU Display
        self.cpu_label = QLabel("CPU: --%")
        layout.addWidget(self.cpu_label)

        # Memory Display
        layout.addWidget(QLabel("Mem:"))
        self.memory_bar = QProgressBar()
        self.memory_bar.setRange(0, 100)
        self.memory_bar.setFixedSize(80, 14)
        self.memory_bar.setTextVisible(False)
        layout.addWidget(self.memory_bar)
        self.memory_label = QLabel("-- MB")
        layout.addWidget(self.memory_label)

    def update_metrics(self):
        """Fetches and displays the latest performance metrics."""
        try:
            cpu_usage = self.performance_manager.get_cpu_usage()
            memory_usage = self.performance_manager.get_memory_usage()

            # Update CPU Label
            self.cpu_label.setText(f"CPU: {cpu_usage}%")

            # Update Memory Bar and Label
            if memory_usage:
                mem_percent = memory_usage.get("system_used_percent", 0)
                process_mem_mb = memory_usage.get("process_rss_mb", 0)

                self.memory_bar.setValue(int(mem_percent))
                self.memory_label.setText(f"{process_mem_mb} MB")

                # Set tooltip with detailed info
                tooltip = (
                    f"System Memory Usage: {mem_percent}%\n"
                    f"Application Memory: {process_mem_mb} MB"
                )
                self.setToolTip(tooltip)

                # Update memory bar color based on usage
                if mem_percent > 85:
                    color = "#dc3545"  # Red
                elif mem_percent > 70:
                    color = "#ffc107"  # Orange
                else:
                    color = "#28a745"  # Green
                self.memory_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")

        except Exception as e:
            logger.exception("Error updating performance metrics: %s", e)
            self.cpu_label.setText("CPU: Err")
            self.memory_label.setText("Mem: Err")
