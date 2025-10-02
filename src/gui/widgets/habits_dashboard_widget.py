"""
7 Habits Dashboard Widget for Growth Journey tracking.

Provides visualization and tracking of habit progression, mastery levels,
weekly focus, and personalized coaching recommendations.
"""

import logging
from typing import Dict, Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush, QColor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QTextEdit,
    QTabWidget,
    QGroupBox,
    QSplitter,
)

from ...config import get_settings
from ...core.enhanced_habit_mapper import SevenHabitsFramework

logger = logging.getLogger(__name__)


class HabitProgressBar(QWidget):
    """Custom progress bar for habit mastery visualization."""

    def __init__(self, habit_name: str, percentage: float, mastery_level: str):
        super().__init__()
        self.habit_name = habit_name
        self.percentage = percentage
        self.mastery_level = mastery_level
        self.setFixedHeight(40)
        self.setMinimumWidth(300)

    def paintEvent(self, event):
        """Custom paint event for habit progress bar."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.setBrush(QBrush(QColor("#ecf0f1")))
        painter.setPen(QPen(QColor("#bdc3c7"), 1))
        painter.drawRoundedRect(0, 20, self.width(), 16, 8, 8)

        # Progress bar color based on mastery level
        if self.mastery_level == "Mastered":
            color = QColor("#27ae60")
        elif self.mastery_level == "Proficient":
            color = QColor("#3498db")
        elif self.mastery_level == "Developing":
            color = QColor("#f39c12")
        else:  # Needs Focus
            color = QColor("#e74c3c")

        # Progress fill
        fill_width = int((self.percentage / 100) * self.width())
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color, 1))
        painter.drawRoundedRect(0, 20, fill_width, 16, 8, 8)

        # Text labels
        painter.setPen(QPen(QColor("#2c3e50"), 1))
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(5, 15, f"Habit {self.habit_name}")

        # Percentage and mastery level
        font = QFont("Segoe UI", 8)
        painter.setFont(font)
        painter.drawText(
            self.width() - 120, 15, f"{self.percentage:.1f}% - {self.mastery_level}"
        )


class WeeklyFocusWidget(QFrame):
    """Widget showing this week's habit focus."""

    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 12px;
                color: white;
                padding: 15px;
            }
            QLabel {
                color: white;
                background: transparent;
            }
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        """)

        self.setup_ui()

    def setup_ui(self):
        """Setup the weekly focus widget UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("🌟 This Week's Focus")
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Habit name
        self.habit_label = QLabel("Habit 5: Seek First to Understand")
        self.habit_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.habit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.habit_label.setWordWrap(True)
        layout.addWidget(self.habit_label)

        # Description
        self.description_label = QLabel("40% of your findings relate to this habit")
        self.description_label.setFont(QFont("Segoe UI", 10))
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)

        # Action button
        self.action_button = QPushButton("View Strategies")
        self.action_button.clicked.connect(self.show_strategies)
        layout.addWidget(self.action_button)

    def update_focus(self, habit_name: str, description: str):
        """Update the weekly focus display."""
        self.habit_label.setText(habit_name)
        self.description_label.setText(description)

    def show_strategies(self):
        """Show detailed strategies for the focus habit."""
        # This would open a detailed view or dialog
        logger.info("Show strategies clicked")


class HabitDetailsWidget(QWidget):
    """Widget showing detailed information about a specific habit."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Setup the habit details widget UI."""
        layout = QVBoxLayout(self)

        # Habit title
        self.title_label = QLabel()
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(self.title_label)

        # Principle
        self.principle_label = QLabel()
        self.principle_label.setFont(QFont("Segoe UI", 12))
        self.principle_label.setStyleSheet(
            "color: #7f8c8d; font-style: italic; margin-bottom: 15px;"
        )
        layout.addWidget(self.principle_label)

        # Description
        self.description_text = QTextEdit()
        self.description_text.setMaximumHeight(100)
        self.description_text.setReadOnly(True)
        self.description_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 10px;
                background: #f8f9fa;
            }
        """)
        layout.addWidget(self.description_text)

        # Clinical examples
        examples_group = QGroupBox("Clinical Examples")
        examples_layout = QVBoxLayout(examples_group)
        self.examples_text = QTextEdit()
        self.examples_text.setMaximumHeight(80)
        self.examples_text.setReadOnly(True)
        examples_layout.addWidget(self.examples_text)
        layout.addWidget(examples_group)

        # Improvement strategies
        strategies_group = QGroupBox("Improvement Strategies")
        strategies_layout = QVBoxLayout(strategies_group)
        self.strategies_text = QTextEdit()
        self.strategies_text.setMaximumHeight(80)
        self.strategies_text.setReadOnly(True)
        strategies_layout.addWidget(self.strategies_text)
        layout.addWidget(strategies_group)

    def update_habit(self, habit_info: Dict):
        """Update the widget with habit information."""
        self.title_label.setText(f"Habit {habit_info['number']}: {habit_info['name']}")
        self.principle_label.setText(f"Principle: {habit_info['principle']}")
        self.description_text.setPlainText(habit_info["description"].strip())

        # Clinical examples
        examples_text = "\n".join(
            [f"• {example}" for example in habit_info["clinical_examples"]]
        )
        self.examples_text.setPlainText(examples_text)

        # Improvement strategies
        strategies_text = "\n".join(
            [f"• {strategy}" for strategy in habit_info["improvement_strategies"]]
        )
        self.strategies_text.setPlainText(strategies_text)


class HabitsDashboardWidget(QWidget):
    """
    Main dashboard widget for 7 Habits Growth Journey.

    Provides comprehensive habit tracking, progression visualization,
    and personalized coaching recommendations.
    """

    habit_selected = pyqtSignal(str)  # Emitted when a habit is selected

    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.habits_framework = SevenHabitsFramework()
        self.current_metrics = None

        # Check if habits are enabled
        if not self.settings.habits_framework.enabled:
            self.setup_disabled_ui()
            return

        self.setup_ui()
        self.setup_timer()

    def setup_disabled_ui(self):
        """Setup UI when habits framework is disabled."""
        layout = QVBoxLayout(self)

        message = QLabel("7 Habits Personal Development Framework is disabled")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setStyleSheet("color: #7f8c8d; font-size: 14px;")
        layout.addWidget(message)

        enable_info = QLabel(
            "Enable it in config.yaml: habits_framework.enabled = true"
        )
        enable_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        enable_info.setStyleSheet("color: #95a5a6; font-size: 12px;")
        layout.addWidget(enable_info)

    def setup_ui(self):
        """Setup the main dashboard UI."""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("📈 Growth Journey - 7 Habits Framework")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left panel - Overview and Progress
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # Right panel - Habit Details
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions
        splitter.setSizes([400, 300])

    def create_left_panel(self) -> QWidget:
        """Create the left panel with overview and progress."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Weekly focus widget (if enabled)
        if self.settings.habits_framework.dashboard_integration.show_weekly_focus_widget:
            self.weekly_focus = WeeklyFocusWidget()
            layout.addWidget(self.weekly_focus)

        # Habit progression section
        if self.settings.habits_framework.dashboard_integration.show_habit_progression_charts:
            progress_group = QGroupBox("📊 Habit Mastery Levels")
            progress_layout = QVBoxLayout(progress_group)

            # Scroll area for habit progress bars
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setMaximumHeight(300)

            self.progress_widget = QWidget()
            self.progress_layout = QVBoxLayout(self.progress_widget)
            scroll.setWidget(self.progress_widget)

            progress_layout.addWidget(scroll)
            layout.addWidget(progress_group)

        # Achievement section (if gamification enabled)
        if self.settings.habits_framework.gamification.enabled:
            achievements_group = QGroupBox("🏆 Recent Achievements")
            achievements_layout = QVBoxLayout(achievements_group)

            self.achievements_label = QLabel("No recent achievements")
            self.achievements_label.setStyleSheet("color: #7f8c8d; padding: 10px;")
            achievements_layout.addWidget(self.achievements_label)

            layout.addWidget(achievements_group)

        layout.addStretch()
        return panel

    def create_right_panel(self) -> QWidget:
        """Create the right panel with habit details."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Habit selection tabs
        self.habit_tabs = QTabWidget()

        # Add tab for each habit
        for habit_id in sorted(
            self.habits_framework.HABITS.keys(), key=lambda x: int(x.split("_")[1])
        ):
            habit = self.habits_framework.get_habit_details(habit_id)

            details_widget = HabitDetailsWidget()
            details_widget.update_habit(habit)

            tab_name = f"Habit {habit['number']}"
            self.habit_tabs.addTab(details_widget, tab_name)

        layout.addWidget(self.habit_tabs)
        return panel

    def setup_timer(self):
        """Setup timer for periodic data refresh."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(300000)  # Refresh every 5 minutes

        # Initial data load
        self.refresh_data()

    def refresh_data(self):
        """Refresh habit progression data."""
        try:
            # In a real implementation, this would fetch data from the database
            # For now, we'll simulate some data
            sample_findings = (
                [{"habit_id": "habit_1"} for _ in range(5)]
                + [{"habit_id": "habit_5"} for _ in range(15)]
                + [{"habit_id": "habit_3"} for _ in range(8)]
            )

            self.current_metrics = self.habits_framework.get_habit_progression_metrics(
                sample_findings
            )
            self.update_progress_display()
            self.update_weekly_focus()

        except Exception as e:
            logger.exception(f"Failed to refresh habit data: {e}")

    def update_progress_display(self):
        """Update the habit progress bars."""
        if not self.current_metrics or not hasattr(self, "progress_layout"):
            return

        # Clear existing progress bars
        for i in reversed(range(self.progress_layout.count())):
            child = self.progress_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # Add progress bars for each habit
        for habit_id in sorted(
            self.current_metrics["habit_breakdown"].keys(),
            key=lambda x: int(x.split("_")[1]),
        ):
            habit_data = self.current_metrics["habit_breakdown"][habit_id]

            progress_bar = HabitProgressBar(
                f"{habit_data['habit_number']}: {habit_data['habit_name']}",
                habit_data["percentage"],
                habit_data["mastery_level"],
            )

            self.progress_layout.addWidget(progress_bar)

    def update_weekly_focus(self):
        """Update the weekly focus widget."""
        if not hasattr(self, "weekly_focus") or not self.current_metrics:
            return

        # Get the top focus area
        if self.current_metrics["top_focus_areas"]:
            habit_id, metrics = self.current_metrics["top_focus_areas"][0]
            habit_info = self.habits_framework.get_habit_details(habit_id)

            habit_name = f"Habit {habit_info['number']}: {habit_info['name']}"
            description = (
                f"{metrics['percentage']:.1f}% of your findings relate to this habit"
            )

            self.weekly_focus.update_focus(habit_name, description)
        else:
            self.weekly_focus.update_focus(
                "Great job! No major focus areas",
                "Your documentation is well-balanced across all habits",
            )

    def get_habit_metrics(self) -> Optional[Dict]:
        """Get current habit metrics."""
        return self.current_metrics

    def set_habit_focus(self, habit_id: str):
        """Set focus to a specific habit tab."""
        try:
            habit_number = int(habit_id.split("_")[1])
            self.habit_tabs.setCurrentIndex(habit_number - 1)
        except (ValueError, IndexError):
            logger.warning(f"Invalid habit_id for focus: {habit_id}")
