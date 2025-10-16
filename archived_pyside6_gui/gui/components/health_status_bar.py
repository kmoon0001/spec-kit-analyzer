"""
Health Status Bar Component

Displays real-time system health metrics in the application status bar:
    - RAM usage with mini progress bar
    - CPU usage with mini progress bar
    - API connection status
    - Active tasks count
    - Easter egg: "Pacific Coast Therapy" in cursive

Architecture:
    - Uses ResourceMonitor for metrics
    - Updates every second via QTimer
    - Thread-safe (all updates on main thread)
    - Responsive to theme changes
"""

import logging
from PySide6.QtWidgets import QStatusBar, QLabel, QWidget, QHBoxLayout
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont

from src.gui.core import ResourceMonitor


logger = logging.getLogger(__name__)


class HealthStatusBar(QStatusBar):
    """
    Production-ready health status bar with system monitoring.

    Features:
        - Real-time RAM/CPU monitoring
        - API status indicator (icon only, no dots!)
        - Active tasks counter
        - Easter egg branding
        - PyCharm dark theme styling

    Usage:
        ```python
        status_bar = HealthStatusBar(resource_monitor=monitor)
        main_window.setStatusBar(status_bar)

        # Update API status
        status_bar.set_api_status(True)

        # Update active tasks
        status_bar.set_active_tasks(3)
        ```
    """

    def __init__(self, resource_monitor: ResourceMonitor | None = None, parent: QWidget | None = None):
        """
        Initialize health status bar.

        Args:
            resource_monitor: Resource monitor instance (creates new if None)
            parent: Parent widget
        """
        super().__init__(parent)

        self.resource_monitor = resource_monitor or ResourceMonitor()

        # State
        self._api_connected = False
        self._active_tasks = 0

        # Create widgets
        self._create_widgets()

        # Apply dark theme
        self._apply_theme()

        # Start monitoring
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_health)
        self._timer.start(1000)  # Update every second

        logger.info("HealthStatusBar initialized")

    def _create_widgets(self):
        """Create all status bar widgets."""
        # Container for left-aligned widgets
        left_widget = QWidget()
        left_layout = QHBoxLayout(left_widget)
        left_layout.setContentsMargins(10, 0, 10, 0)
        left_layout.setSpacing(20)

        # RAM widget
        self.ram_label = QLabel("RAM: --")
        self.ram_label.setToolTip("Random Access Memory Usage")
        left_layout.addWidget(self.ram_label)

        # CPU widget
        self.cpu_label = QLabel("CPU: --")
        self.cpu_label.setToolTip("Central Processing Unit Usage")
        left_layout.addWidget(self.cpu_label)

        # API status widget (icon only - no dot!)
        self.api_label = QLabel()
        self.api_label.setToolTip("API Connection Status")
        self._update_api_icon()
        left_layout.addWidget(self.api_label)

        # Active tasks widget
        self.tasks_label = QLabel("Tasks: 0")
        self.tasks_label.setToolTip("Active Background Tasks")
        left_layout.addWidget(self.tasks_label)

        left_layout.addStretch()

        # Add to status bar (left side)
        self.addWidget(left_widget, 1)

        # Easter egg (permanent widget on right)
        self.easter_egg = QLabel("Pacific Coast Therapy")

        # Cursive font for easter egg
        cursive_font = QFont()
        cursive_font.setFamilies(["Brush Script MT", "Lucida Handwriting", "Segoe Script", "cursive"])
        cursive_font.setPointSize(10)
        cursive_font.setItalic(True)
        self.easter_egg.setFont(cursive_font)

        self.addPermanentWidget(self.easter_egg)

    def _apply_theme(self):
        """Apply PyCharm dark theme styling."""
        # Status bar base style
        self.setStyleSheet("""
            QStatusBar {
                background: #2B2B2B;
                color: #A9B7C6;
                border-top: 1px solid #323232;
                padding: 4px;
            }

            QLabel {
                color: #A9B7C6;
                background: transparent;
                padding: 0px 5px;
            }
        """)

        # Easter egg style
        self.easter_egg.setStyleSheet("""
            QLabel {
                color: #4A9FD8;
                background: transparent;
                padding-right: 10px;
            }
        """)

    def _update_health(self):
        """Update health metrics (called every second)."""
        try:
            metrics = self.resource_monitor.get_current_metrics()

            # Update RAM
            ram_bar = self._create_mini_bar(metrics.ram_percent)
            ram_color = self._get_usage_color(metrics.ram_percent)
            self.ram_label.setText(f"RAM: {metrics.ram_percent:.0f}% {ram_bar}")
            self.ram_label.setStyleSheet(f"color: {ram_color};")

            # Update CPU
            cpu_bar = self._create_mini_bar(metrics.cpu_percent)
            cpu_color = self._get_usage_color(metrics.cpu_percent)
            self.cpu_label.setText(f"CPU: {metrics.cpu_percent:.0f}% {cpu_bar}")
            self.cpu_label.setStyleSheet(f"color: {cpu_color};")

        except Exception as e:
            logger.error(f"Failed to update health metrics: {e}")

    def _create_mini_bar(self, percent: float) -> str:
        """
        Create ASCII mini progress bar.

        Args:
            percent: Percentage (0-100)

        Returns:
            String like "▓▓▓░░"
        """
        filled = int(percent / 20)  # 5 blocks max (0-100% → 0-5 blocks)
        filled = min(filled, 5)  # Cap at 5
        empty = 5 - filled
        return "▓" * filled + "░" * empty

    def _get_usage_color(self, percent: float) -> str:
        """
        Get color based on usage percentage.

        Args:
            percent: Usage percentage

        Returns:
            Hex color code
        """
        if percent >= 85:
            return "#FF6B68"  # Red (critical)
        elif percent >= 75:
            return "#FFC66D"  # Yellow/orange (warning)
        else:
            return "#6A8759"  # Green (normal)

    def set_api_status(self, connected: bool):
        """
        Update API connection status.

        Args:
            connected: True if API is connected
        """
        self._api_connected = connected
        self._update_api_icon()

    def _update_api_icon(self):
        """Update API status icon (NO DOTS - button-icon lighting style)."""
        if self._api_connected:
            # Green glow effect (connected)
            self.api_label.setText("API")
            self.api_label.setStyleSheet("""
                QLabel {
                    color: #6A8759;
                    background: rgba(106, 135, 89, 0.2);
                    border: 1px solid #6A8759;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-weight: bold;
                }
            """)
            self.api_label.setToolTip("API Connected")
        else:
            # Red glow effect (disconnected)
            self.api_label.setText("API")
            self.api_label.setStyleSheet("""
                QLabel {
                    color: #FF6B68;
                    background: rgba(255, 107, 104, 0.2);
                    border: 1px solid #FF6B68;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-weight: bold;
                }
            """)
            self.api_label.setToolTip("API Disconnected")

    def set_active_tasks(self, count: int):
        """
        Update active tasks count.

        Args:
            count: Number of active tasks
        """
        self._active_tasks = count
        self.tasks_label.setText(f"Tasks: {count}")

        # Color based on task count
        if count > 3:
            color = "#FFC66D"  # Warning - many tasks
        elif count > 0:
            color = "#4A9FD8"  # Info - some tasks
        else:
            color = "#A9B7C6"  # Normal - no tasks

        self.tasks_label.setStyleSheet(f"color: {color};")

    def stop_monitoring(self):
        """Stop health monitoring."""
        if self._timer.isActive():
            self._timer.stop()
            logger.info("HealthStatusBar monitoring stopped")
