import logging
import datetime
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
    QComboBox,
    QDateEdit,
    QHBoxLayout,
)
from PyQt6.QtCore import pyqtSignal, QDate
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import requests
import pandas as pd

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
        self.trend_data = None
        self.selected_habit_filter = None
        self._init_ui()

    def _init_ui(self):
        """Initializes the user interface of the widget."""
        layout = QVBoxLayout(self)

        # Filter controls
        filter_group = QGroupBox("Filters")
        filter_layout = QHBoxLayout()
        filter_group.setLayout(filter_layout)

        # Discipline filter
        filter_layout.addWidget(QLabel("Discipline:"))
        self.discipline_combo = QComboBox()
        self.discipline_combo.addItems(["All", "PT", "OT", "SLP"])
        filter_layout.addWidget(self.discipline_combo)

        filter_layout.addSpacing(20)

        # Date range filter
        filter_layout.addWidget(QLabel("Date Range:"))
        self.date_range_combo = QComboBox()
        self.date_range_combo.addItems(["All Time", "Last 7 Days", "Last 30 Days", "This Quarter", "Custom"])
        self.date_range_combo.currentTextChanged.connect(self._on_date_range_changed)
        filter_layout.addWidget(self.date_range_combo)
        self.start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setVisible(False)
        filter_layout.addWidget(self.start_date_edit)
        self.end_date_edit = QDateEdit(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setVisible(False)
        filter_layout.addWidget(self.end_date_edit)

        filter_layout.addStretch()

        self.refresh_button = QPushButton("Refresh Data")
        self.refresh_button.clicked.connect(self.load_data)
        filter_layout.addWidget(self.refresh_button)

        layout.addWidget(filter_group)

        # Top-level stats
        stats_group = QGroupBox("High-Level Summary")
        stats_layout = QGridLayout()
        stats_group.setLayout(stats_layout)
        self.total_findings_label = QLabel("Total Findings: N/A")
        stats_layout.addWidget(self.total_findings_label, 0, 0)
        layout.addWidget(stats_group)

        # Team Habit Summary Chart
        chart_group = QGroupBox("Team Habit Summary (Click a bar to filter clinicians)")
        self.chart_layout = QVBoxLayout()
        chart_group.setLayout(self.chart_layout)
        self.habit_chart_canvas = self._create_chart_canvas()
        self.habit_chart_canvas.mpl_connect("button_press_event", self._on_habit_chart_click)
        self.chart_layout.addWidget(self.habit_chart_canvas)
        layout.addWidget(chart_group)

        # Habit Trend Chart
        trend_chart_group = QGroupBox("Habit Trends Over Time")
        self.trend_chart_layout = QVBoxLayout()
        trend_chart_group.setLayout(self.trend_chart_layout)
        self.trend_chart_canvas = self._create_chart_canvas()
        self.trend_chart_layout.addWidget(self.trend_chart_canvas)
        layout.addWidget(trend_chart_group)

        # Clinician Breakdown
        tree_group_layout = QHBoxLayout()
        self.tree_group = QGroupBox("Clinician Habit Breakdown")
        tree_layout = QVBoxLayout()
        self.tree_group.setLayout(tree_layout)
        self.reset_filter_button = QPushButton("Reset Filter")
        self.reset_filter_button.clicked.connect(self._reset_clinician_filter)
        self.reset_filter_button.setVisible(False)
        tree_group_layout.addWidget(self.tree_group)
        tree_group_layout.addWidget(self.reset_filter_button, 0, pyqtSignal.AlignmentFlag.AlignTop)

        self.clinician_tree = QTreeWidget()
        self.clinician_tree.setHeaderLabels(["Clinician", "Habit", "Findings"])
        self.clinician_tree.setColumnWidth(0, 200)
        tree_layout.addWidget(self.clinician_tree)
        layout.addLayout(tree_group_layout)

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

    def _on_date_range_changed(self, text: str):
        is_custom = text == "Custom"
        self.start_date_edit.setVisible(is_custom)
        self.end_date_edit.setVisible(is_custom)

    def _create_chart_canvas(self):
        fig = Figure(figsize=(10, 5), dpi=100)
        return FigureCanvas(fig)

    def load_data(self):
        params = {}
        # Date range filter
        date_range = self.date_range_combo.currentText()
        today = datetime.date.today()
        if date_range == "Last 7 Days":
            params["start_date"] = (today - datetime.timedelta(days=7)).isoformat()
        elif date_range == "Last 30 Days":
            params["start_date"] = (today - datetime.timedelta(days=30)).isoformat()
        elif date_range == "This Quarter":
            start_date = datetime.date(today.year, 3 * ((today.month - 1) // 3) + 1, 1)
            params["start_date"] = start_date.isoformat()
        if date_range != "All Time":
            params["end_date"] = today.isoformat()
        if date_range == "Custom":
            params["start_date"] = self.start_date_edit.date().toString("yyyy-MM-dd")
            params["end_date"] = self.end_date_edit.date().toString("yyyy-MM-dd")

        # Discipline filter
        discipline = self.discipline_combo.currentText()
        if discipline != "All":
            params["discipline"] = discipline

        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{settings.api_url}/dashboard/director-dashboard", headers=headers, params=params)
            response.raise_for_status()
            self.dashboard_data = DirectorDashboardData(**response.json())
            trend_response = requests.get(f"{settings.api_url}/dashboard/habit-trends", headers=headers, params=params)
            trend_response.raise_for_status()
            self.trend_data = trend_response.json()
            self.update_dashboard()
        except requests.RequestException as e:
            logger.error(f"Failed to load director dashboard data: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load dashboard data: {e}")

    def update_dashboard(self):
        if not self.dashboard_data:
            return
        self.total_findings_label.setText(f"Total Findings: {self.dashboard_data.total_findings}")
        self._update_habit_chart()
        self._update_clinician_tree()
        self._update_trend_chart()

    def _on_habit_chart_click(self, event):
        if event.inaxes and self.dashboard_data:
            summary = self.dashboard_data.team_habit_summary
            for i, bar in enumerate(self.habit_chart_canvas.figure.axes[0].patches):
                if bar.contains(event)[0]:
                    self.selected_habit_filter = summary[i].habit_name
                    self.tree_group.setTitle(f"Clinician Breakdown (Filtered by: {self.selected_habit_filter})")
                    self.reset_filter_button.setVisible(True)
                    self._update_clinician_tree()
                    break

    def _reset_clinician_filter(self):
        self.selected_habit_filter = None
        self.tree_group.setTitle("Clinician Habit Breakdown")
        self.reset_filter_button.setVisible(False)
        self._update_clinician_tree()

    def _update_habit_chart(self):
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

    def _update_trend_chart(self):
        if not self.trend_data:
            return
        df = pd.DataFrame(self.trend_data)
        df['date'] = pd.to_datetime(df['date'])
        pivot_df = df.pivot(index='date', columns='habit_name', values='count').fillna(0)
        fig = self.trend_chart_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        if not pivot_df.empty:
            pivot_df.plot(kind='line', ax=ax, marker='o')
            ax.set_ylabel("Number of Findings")
            ax.set_title("Habit Findings Trend")
            ax.legend(title="Habits")
            ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        else:
            ax.text(0.5, 0.5, "No trend data available for the selected period.", ha='center', va='center')
        fig.tight_layout()
        self.trend_chart_canvas.draw()

    def _update_clinician_tree(self):
        if not self.dashboard_data or not self.dashboard_data.clinician_habit_breakdown:
            return
        self.clinician_tree.clear()
        breakdown = self.dashboard_data.clinician_habit_breakdown
        if self.selected_habit_filter:
            breakdown = [item for item in breakdown if item.habit_name == self.selected_habit_filter]

        clinician_data = {}
        for item in breakdown:
            if item.clinician_name not in clinician_data:
                clinician_data[item.clinician_name] = []
            clinician_data[item.clinician_name].append(item)

        for clinician, habits in clinician_data.items():
            parent_item = QTreeWidgetItem(self.clinician_tree, [clinician])
            for habit in habits:
                QTreeWidgetItem(parent_item, ["", habit.habit_name, str(habit.count)])
            self.clinician_tree.expandItem(parent_item)

    def generate_coaching_focus(self):
        if not self.dashboard_data:
            QMessageBox.warning(self, "No Data", "Please load dashboard data first.")
            return
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.post(f"{settings.api_url}/dashboard/coaching-focus", json=self.dashboard_data.model_dump(), headers=headers)
            response.raise_for_status()
            coaching_focus = response.json()
            focus_text = f"**{coaching_focus['focus_title']}**\n\n{coaching_focus['summary']}\n\n**Action Steps:**\n"
            for step in coaching_focus['action_steps']:
                focus_text += f"- {step}\n"
            self.coaching_focus_label.setText(focus_text)
        except requests.RequestException as e:
            logger.error(f"Failed to generate coaching focus: {e}")
            QMessageBox.warning(self, "Error", f"Failed to generate coaching focus: {e}")
