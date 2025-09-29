import logging
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QMessageBox,
)
from PyQt6.QtCore import pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import requests

from ...config import get_settings
from ...database.schemas import DirectorDashboardData

logger = logging.getLogger(__name__)
settings = get_settings()


class DirectorDashboardWidget(QWidget):
    """
    A widget to display director-level analytics, including team performance
    and clinician-specific breakdowns.
    """

    refresh_requested = pyqtSignal()

    def __init__(self, access_token: str, parent=None):
        super().__init__(parent)
        self.access_token = access_token
        self.dashboard_data = None
        self._init_ui()

    def _init_ui(self):
        """Initializes the user interface of the widget."""
        layout = QVBoxLayout(self)

        # Top-level stats
        stats_group = QGroupBox("High-Level Summary")
        stats_layout = QGridLayout()
        stats_group.setLayout(stats_layout)
        self.total_findings_label = QLabel("Total Findings: N/A")
        stats_layout.addWidget(self.total_findings_label, 0, 0)
        layout.addWidget(stats_group)

        # Team Habit Summary Chart
        chart_group = QGroupBox("Team Habit Summary")
        self.chart_layout = QVBoxLayout()
        chart_group.setLayout(self.chart_layout)
        self.habit_chart_canvas = self._create_chart_canvas()
        self.chart_layout.addWidget(self.habit_chart_canvas)
        layout.addWidget(chart_group)

        # Clinician Breakdown
        tree_group = QGroupBox("Clinician Habit Breakdown")
        tree_layout = QVBoxLayout()
        tree_group.setLayout(tree_layout)
        self.clinician_tree = QTreeWidget()
        self.clinician_tree.setHeaderLabels(["Clinician", "Habit", "Findings"])
        self.clinician_tree.setColumnWidth(0, 200)
        tree_layout.addWidget(self.clinician_tree)
        layout.addWidget(tree_group)

        # AI Coaching Focus
        coaching_group = QGroupBox("AI-Generated Coaching Focus")
        coaching_layout = QVBoxLayout()
        coaching_group.setLayout(coaching_layout)
        self.coaching_focus_label = QLabel("Click 'Generate Focus' to get AI-powered coaching recommendations.")
        self.coaching_focus_label.setWordWrap(True)
        self.generate_focus_button = QPushButton("Generate Coaching Focus")
        self.generate_focus_button.clicked.connect(self.generate_coaching_focus)
        coaching_layout.addWidget(self.coaching_focus_label)
        coaching_layout.addWidget(self.generate_focus_button)
        layout.addWidget(coaching_group)

        self.refresh_button = QPushButton("Refresh Data")
        self.refresh_button.clicked.connect(self.load_data)
        layout.addWidget(self.refresh_button)

    def _create_chart_canvas(self):
        """Creates a canvas for the Matplotlib chart."""
        fig = Figure(figsize=(10, 5), dpi=100)
        canvas = FigureCanvas(fig)
        return canvas

    def load_data(self):
        """Loads data from the API and updates the dashboard."""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{settings.api_url}/dashboard/director-dashboard", headers=headers
            )
            response.raise_for_status()
            self.dashboard_data = DirectorDashboardData(**response.json())
            self.update_dashboard()
        except requests.RequestException as e:
            logger.error(f"Failed to load director dashboard data: {e}")
            QMessageBox.warning(
                self, "Error", f"Failed to load dashboard data: {e}"
            )

    def update_dashboard(self):
        """Updates the UI elements with the loaded data."""
        if not self.dashboard_data:
            return

        # Update summary stats
        self.total_findings_label.setText(f"Total Findings: {self.dashboard_data.total_findings}")

        # Update team habit chart
        self._update_habit_chart()

        # Update clinician breakdown tree
        self._update_clinician_tree()

    def _update_habit_chart(self):
        """Updates the team habit summary bar chart."""
        if not self.dashboard_data or not self.dashboard_data.team_habit_summary:
            return

        summary = self.dashboard_data.team_habit_summary
        habits = [item.habit_name for item in summary]
        counts = [item.count for item in summary]

        fig = self.habit_chart_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.bar(habits, counts, color="#4a5bdc")
        ax.set_ylabel("Number of Findings")
        ax.set_title("Team Findings by Habit")
        fig.tight_layout()
        self.habit_chart_canvas.draw()

    def _update_clinician_tree(self):
        """Updates the clinician breakdown tree view."""
        if not self.dashboard_data or not self.dashboard_data.clinician_habit_breakdown:
            return

        self.clinician_tree.clear()
        breakdown = self.dashboard_data.clinician_habit_breakdown

        # Group by clinician
        clinician_data = {}
        for item in breakdown:
            if item.clinician_name not in clinician_data:
                clinician_data[item.clinician_name] = []
            clinician_data[item.clinician_name].append(item)

        for clinician, habits in clinician_data.items():
            parent_item = QTreeWidgetItem(self.clinician_tree, [clinician])
            for habit in habits:
                child_item = QTreeWidgetItem(parent_item, ["", habit.habit_name, str(habit.count)])
            self.clinician_tree.expandItem(parent_item)

    def generate_coaching_focus(self):
        """Generates and displays the AI coaching focus."""
        if not self.dashboard_data:
            QMessageBox.warning(self, "No Data", "Please load dashboard data first.")
            return

        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.post(
                f"{settings.api_url}/dashboard/coaching-focus",
                json=self.dashboard_data.model_dump(),
                headers=headers,
            )
            response.raise_for_status()
            coaching_focus = response.json()

            focus_text = f"**{coaching_focus['focus_title']}**\n\n"
            focus_text += f"{coaching_focus['summary']}\n\n"
            focus_text += "**Action Steps:**\n"
            for step in coaching_focus['action_steps']:
                focus_text += f"- {step}\n"

            self.coaching_focus_label.setText(focus_text)

        except requests.RequestException as e:
            logger.error(f"Failed to generate coaching focus: {e}")
            QMessageBox.warning(
                self, "Error", f"Failed to generate coaching focus: {e}"
            )