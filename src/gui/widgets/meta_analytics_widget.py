"""Meta Analytics Dashboard Widget for Organizational-Level Insights.

Provides comprehensive team analytics including performance trends,
training needs identification, and benchmarking data for administrators.
"""

import logging
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class MetaAnalyticsWidget(QWidget):
    """Widget for displaying organizational-level analytics and insights.

    Features:
    - Team performance overview
    - Training needs identification
    - Discipline comparison
    - Performance trends and alerts
    """

    refresh_requested = Signal(dict)  # Emits parameters for refresh

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_data = {}
        self.setup_ui()

    def setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)

        # Main content tabs
        self.tabs = QTabWidget()

        # Overview tab
        self.overview_tab = self.create_overview_tab()
        self.tabs.addTab(self.overview_tab, "Team Overview")

        # Training needs tab
        self.training_tab = self.create_training_tab()
        self.tabs.addTab(self.training_tab, "Training Needs")

        # Trends tab
        self.trends_tab = self.create_trends_tab()
        self.tabs.addTab(self.trends_tab, "Performance Trends")

        # Benchmarks tab
        self.benchmarks_tab = self.create_benchmarks_tab()
        self.tabs.addTab(self.benchmarks_tab, "Benchmarks")

        layout.addWidget(self.tabs)

    def create_control_panel(self) -> QWidget:
        """Create the control panel with filters and refresh button."""
        panel = QGroupBox("Analytics Controls")
        layout = QHBoxLayout(panel)

        # Days back selector
        layout.addWidget(QLabel("Analysis Period:"))
        self.days_spinbox = QSpinBox()
        self.days_spinbox.setRange(7, 365)
        self.days_spinbox.setValue(90)
        self.days_spinbox.setSuffix(" days")
        layout.addWidget(self.days_spinbox)

        # Discipline filter
        layout.addWidget(QLabel("Discipline:"))
        self.discipline_combo = QComboBox()
        self.discipline_combo.addItems(["All Disciplines", "PT", "OT", "SLP"])
        layout.addWidget(self.discipline_combo)

        # Refresh button
        self.refresh_button = QPushButton("Refresh Analytics")
        self.refresh_button.clicked.connect(self.request_refresh)
        layout.addWidget(self.refresh_button)

        layout.addStretch()
        return panel

    def create_overview_tab(self) -> QWidget:
        """Create the team overview tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Metrics cards
        metrics_layout = QGridLayout()

        self.total_users_label = QLabel("Total Users: --")
        self.avg_score_label = QLabel("Avg Compliance: --%")
        self.total_findings_label = QLabel("Total Findings: --")
        self.total_analyses_label = QLabel("Total Analyses: --")

        metrics_layout.addWidget(self.total_users_label, 0, 0)
        metrics_layout.addWidget(self.avg_score_label, 0, 1)
        metrics_layout.addWidget(self.total_findings_label, 1, 0)
        metrics_layout.addWidget(self.total_analyses_label, 1, 1)

        layout.addLayout(metrics_layout)

        # Charts
        charts_layout = QHBoxLayout()

        # Discipline breakdown chart
        self.discipline_canvas = MplCanvas(width=6, height=4)
        charts_layout.addWidget(self.discipline_canvas)

        # Habit distribution chart
        self.habits_canvas = MplCanvas(width=6, height=4)
        charts_layout.addWidget(self.habits_canvas)

        layout.addLayout(charts_layout)

        # Insights section
        self.insights_widget = self.create_insights_widget()
        layout.addWidget(self.insights_widget)

        return tab

    def create_training_tab(self) -> QWidget:
        """Create the training needs tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Training needs chart
        self.training_canvas = MplCanvas(width=10, height=6)
        layout.addWidget(self.training_canvas)

        # Training recommendations
        self.training_recommendations = QLabel("No training data available")
        self.training_recommendations.setWordWrap(True)
        layout.addWidget(self.training_recommendations)

        return tab

    def create_trends_tab(self) -> QWidget:
        """Create the performance trends tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Trends chart
        self.trends_canvas = MplCanvas(width=12, height=8)
        layout.addWidget(self.trends_canvas)

        return tab

    def create_benchmarks_tab(self) -> QWidget:
        """Create the benchmarks tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Benchmarks chart
        self.benchmarks_canvas = MplCanvas(width=10, height=6)
        layout.addWidget(self.benchmarks_canvas)

        # Benchmarks summary
        self.benchmarks_summary = QLabel("No benchmark data available")
        self.benchmarks_summary.setWordWrap(True)
        layout.addWidget(self.benchmarks_summary)

        return tab

    def create_insights_widget(self) -> QWidget:
        """Create the insights display widget."""
        scroll_area = QScrollArea()
        scroll_area.setMaximumHeight(200)

        self.insights_content = QWidget()
        self.insights_layout = QVBoxLayout(self.insights_content)

        scroll_area.setWidget(self.insights_content)
        scroll_area.setWidgetResizable(True)

        return scroll_area

    def request_refresh(self):
        """Request data refresh with current parameters."""
        params = {
            "days_back": self.days_spinbox.value(),
            "discipline": None
            if self.discipline_combo.currentText() == "All Disciplines"
            else self.discipline_combo.currentText(),
        }
        self.refresh_requested.emit(params)

    def update_data(self, data: dict[str, Any]):
        """Update the widget with new analytics data."""
        self.current_data = data

        # Update overview tab
        self.update_overview_tab(data)

        # Update training tab
        self.update_training_tab(data)

        # Update trends tab
        self.update_trends_tab(data)

        # Update benchmarks tab
        self.update_benchmarks_tab(data)

    def update_overview_tab(self, data: dict[str, Any]):
        """Update the overview tab with new data."""
        metrics = data.get("organizational_metrics", {})

        # Update metric labels
        self.total_users_label.setText(f"Total Users: {metrics.get('total_users', 0)}")
        self.avg_score_label.setText(f"Avg Compliance: {metrics.get('avg_compliance_score', 0):.1f}%")
        self.total_findings_label.setText(f"Total Findings: {metrics.get('total_findings', 0)}")
        self.total_analyses_label.setText(f"Total Analyses: {metrics.get('total_analyses', 0)}")

        # Update discipline breakdown chart
        self.update_discipline_chart(metrics.get("discipline_breakdown", {}))

        # Update habits distribution chart
        self.update_habits_chart(metrics.get("team_habit_breakdown", {}))

        # Update insights
        self.update_insights(data.get("insights", []))

    def update_discipline_chart(self, discipline_data: dict[str, Any]):
        """Update the discipline breakdown chart."""
        ax = self.discipline_canvas.axes
        ax.clear()

        if not discipline_data:
            ax.text(0.5, 0.5, "No discipline data available", ha="center", va="center", transform=ax.transAxes)
        else:
            disciplines = list(discipline_data.keys())
            scores = [data.get("avg_compliance_score", 0) for data in discipline_data.values()]
            user_counts = [data.get("user_count", 0) for data in discipline_data.values()]

            # Create bar chart
            x = np.arange(len(disciplines))
            width = 0.35

            bars1 = ax.bar(x - width / 2, scores, width, label="Avg Compliance Score", alpha=0.8)
            ax2 = ax.twinx()
            bars2 = ax2.bar(x + width / 2, user_counts, width, label="User Count", alpha=0.8, color="orange")

            ax.set_xlabel("Discipline")
            ax.set_ylabel("Compliance Score (%)", color="blue")
            ax2.set_ylabel("User Count", color="orange")
            ax.set_title("Performance by Discipline")
            ax.set_xticks(x)
            ax.set_xticklabels(disciplines)

            # Add value labels on bars
            for bar in bars1:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2.0, height + 1, f"{height}%", ha="center", va="bottom")

            for bar in bars2:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width() / 2.0, height + 0.1, f"{int(height)}", ha="center", va="bottom")

            ax.legend(loc="upper left")
            ax2.legend(loc="upper right")

        self.discipline_canvas.draw()

    def update_habits_chart(self, habits_data: dict[str, Any]):
        """Update the habits distribution pie chart."""
        ax = self.habits_canvas.axes
        ax.clear()

        if not habits_data:
            ax.text(0.5, 0.5, "No habits data available", ha="center", va="center", transform=ax.transAxes)
        else:
            # Get top 5 habits by percentage
            sorted_habits = sorted(habits_data.items(), key=lambda x: x[1].get("percentage", 0), reverse=True)[:5]

            labels = [f"Habit {item[1]['habit_number']}: {item[1]['habit_name'][:20]}..." for _, item in sorted_habits]
            sizes = [item[1].get("percentage", 0) for _, item in sorted_habits]

            if sum(sizes) > 0:
                ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
                ax.set_title("Top 5 Habits Distribution")
            else:
                ax.text(0.5, 0.5, "No habit distribution data", ha="center", va="center", transform=ax.transAxes)

        self.habits_canvas.draw()

    def update_training_tab(self, data: dict[str, Any]):
        """Update the training needs tab."""
        training_needs = data.get("training_needs", [])

        # Update training chart
        ax = self.training_canvas.axes
        ax.clear()

        if not training_needs:
            ax.text(0.5, 0.5, "No training needs identified", ha="center", va="center", transform=ax.transAxes)
        else:
            # Create horizontal bar chart of training needs
            habits = [
                need["habit_name"][:30] + "..." if len(need["habit_name"]) > 30 else need["habit_name"]
                for need in training_needs[:10]
            ]
            percentages = [need["percentage_of_findings"] for need in training_needs[:10]]
            colors = ["red" if need["priority"] == "high" else "orange" for need in training_needs[:10]]

            bars = ax.barh(habits, percentages, color=colors, alpha=0.7)
            ax.set_xlabel("Percentage of Findings")
            ax.set_title("Training Needs by Habit Area")
            ax.set_xlim(0, max(percentages) * 1.1 if percentages else 1)

            # Add percentage labels
            for _i, (bar, pct) in enumerate(zip(bars, percentages, strict=False)):
                ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2, f"{pct}%", ha="left", va="center")

        self.training_canvas.draw()

        # Update recommendations text
        if training_needs:
            recommendations = []
            for need in training_needs[:3]:  # Top 3 needs
                recommendations.append(
                    f"• {need['habit_name']} ({need['percentage_of_findings']:.1f}% of findings)\n"
                    f"  Priority: {need['priority'].upper()}\n"
                    f"  Affected users: {need['affected_users']}\n"
                    f"  Focus: {need['training_focus']}\n"
                )

            self.training_recommendations.setText("Top Training Recommendations:\n\n" + "\n".join(recommendations))
        else:
            self.training_recommendations.setText("No specific training needs identified.")

    def update_trends_tab(self, data: dict[str, Any]):
        """Update the performance trends tab."""
        trends = data.get("team_trends", [])

        ax = self.trends_canvas.axes
        ax.clear()

        if not trends:
            ax.text(0.5, 0.5, "No trend data available", ha="center", va="center", transform=ax.transAxes)
        else:
            # Extract data for plotting
            weeks = [f"Week {i + 1}" for i in range(len(trends))]
            scores = [trend.get("avg_compliance_score", 0) for trend in trends]
            findings = [trend.get("total_findings", 0) for trend in trends]

            # Create dual-axis plot
            ax2 = ax.twinx()

            line1 = ax.plot(weeks, scores, "b-o", label="Avg Compliance Score", linewidth=2)
            line2 = ax2.plot(weeks, findings, "r-s", label="Total Findings", linewidth=2)

            ax.set_xlabel("Time Period")
            ax.set_ylabel("Compliance Score (%)", color="blue")
            ax2.set_ylabel("Total Findings", color="red")
            ax.set_title("Team Performance Trends Over Time")

            # Rotate x-axis labels for better readability
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

            # Add legends
            lines = line1 + line2
            labels = [line.get_label() for line in lines]
            ax.legend(lines, labels, loc="upper left")

            # Add trend line for compliance scores
            if len(scores) > 1:
                z = np.polyfit(range(len(scores)), scores, 1)
                p = np.poly1d(z)
                ax.plot(weeks, p(range(len(scores))), "b--", alpha=0.5, label="Trend")

        self.trends_canvas.draw()

    def update_benchmarks_tab(self, data: dict[str, Any]):
        """Update the benchmarks tab."""
        benchmarks = data.get("benchmarks", {})

        ax = self.benchmarks_canvas.axes
        ax.clear()

        if not benchmarks:
            ax.text(0.5, 0.5, "No benchmark data available", ha="center", va="center", transform=ax.transAxes)
        else:
            # Create box plot style visualization of percentiles
            compliance_percentiles = benchmarks.get("compliance_score_percentiles", {})

            if compliance_percentiles:
                percentiles = ["25th", "50th", "75th", "90th"]
                values = [
                    compliance_percentiles.get("p25", 0),
                    compliance_percentiles.get("p50", 0),
                    compliance_percentiles.get("p75", 0),
                    compliance_percentiles.get("p90", 0),
                ]

                bars = ax.bar(percentiles, values, color=["lightcoral", "lightblue", "lightgreen", "gold"])
                ax.set_ylabel("Compliance Score (%)")
                ax.set_title("Team Compliance Score Percentiles")
                ax.set_ylim(0, 100)

                # Add value labels on bars
                for bar, value in zip(bars, values, strict=False):
                    ax.text(
                        bar.get_x() + bar.get_width() / 2.0, bar.get_height() + 1, f"{value}%", ha="center", va="bottom"
                    )

        self.benchmarks_canvas.draw()

        # Update summary text
        if benchmarks:
            total_users = benchmarks.get("total_users_in_benchmark", 0)
            compliance_p50 = benchmarks.get("compliance_score_percentiles", {}).get("p50", 0)

            summary_text = f"""
Benchmark Summary (based on {total_users} users):
Benchmark Summary (based on {total_users} users):
Benchmark Summary (based on {total_users} users):

• Median compliance score: {compliance_p50}%
• 75th percentile: {benchmarks.get("compliance_score_percentiles", {}).get("p75", 0):.1f}%
• 90th percentile: {benchmarks.get("compliance_score_percentiles", {}).get("p90", 0):.1f}%

This data represents anonymous performance distribution across your organization.
            """.strip()

            self.benchmarks_summary.setText(summary_text)
        else:
            self.benchmarks_summary.setText("No benchmark data available.")

    def update_insights(self, insights: list[dict[str, Any]]):
        """Update the insights display."""
        # Clear existing insights
        for i in reversed(range(self.insights_layout.count())):
            self.insights_layout.itemAt(i).widget().setParent(None)

        if not insights:
            no_insights_label = QLabel("No insights available")
            self.insights_layout.addWidget(no_insights_label)
        else:
            for insight in insights:
                insight_widget = self.create_insight_widget(insight)
                self.insights_layout.addWidget(insight_widget)

    def create_insight_widget(self, insight: dict[str, Any]) -> QWidget:
        """Create a widget for displaying a single insight."""
        widget = QGroupBox(insight.get("title", "Insight"))
        layout = QVBoxLayout(widget)

        # Description
        description = QLabel(insight.get("description", ""))
        description.setWordWrap(True)
        layout.addWidget(description)

        # Recommendation
        recommendation = QLabel(f"Recommendation: {insight.get('recommendation', '')}")
        recommendation.setWordWrap(True)
        recommendation.setStyleSheet("font-weight: bold; color: #2E8B57;")
        layout.addWidget(recommendation)

        # Style based on level
        level = insight.get("level", "neutral")
        if level == "positive":
            widget.setStyleSheet("QGroupBox { border: 2px solid green; }")
        elif level == "concern":
            widget.setStyleSheet("QGroupBox { border: 2px solid red; }")
        elif level == "action_required":
            widget.setStyleSheet("QGroupBox { border: 2px solid orange; }")

        return widget


class MplCanvas(FigureCanvas):
    """A reusable Matplotlib canvas widget for PyQt."""

    def __init__(self, width=5, height=4, dpi=100, parent=None):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)

        # Create a single subplot by default
        self.axes = self.fig.add_subplot(111)
