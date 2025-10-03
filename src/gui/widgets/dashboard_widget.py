from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates


class DashboardWidget(QWidget):
    """A widget to display compliance trends and other visualizations."""

    # Add the custom signal
    refresh_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # Use a QVBoxLayout to stack the refresh button on top of the charts
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(15)

        # --- Refresh Button ---
        self.refresh_button = QPushButton("🔄 Refresh Dashboard")
        self.refresh_button.setFixedHeight(40)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background: #007acc;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background: #005a9e; }
        """)
        self.refresh_button.clicked.connect(self.refresh_requested.emit)

        # A container for the charts with proper spacing
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(20)

        # --- Compliance Trend Chart with better sizing ---
        self.trends_canvas = MplCanvas(self, width=5, height=4, dpi=80)

        # --- Findings Summary Chart with better sizing ---
        self.summary_canvas = MplCanvas(self, width=5, height=4, dpi=80)

        charts_layout.addWidget(self.trends_canvas, 1)
        charts_layout.addWidget(self.summary_canvas, 1)

        # Add widgets to the main layout
        self.layout.addWidget(self.refresh_button)
        self.layout.addLayout(charts_layout, 1)

    def update_dashboard(self, data: dict):
        """
        Updates both dashboard plots with new data from the API.

        Args:
            data: A dictionary containing 'reports' and 'summary' data.
        """
        reports_data = data.get("reports", [])
        summary_data = data.get("summary", [])

        self._update_trends_plot(reports_data)
        self._update_summary_plot(summary_data)

    def _update_trends_plot(self, reports):
        """Updates the compliance score trend plot."""
        ax = self.trends_canvas.axes
        ax.clear()

        if not reports:
            ax.text(
                0.5,
                0.5,
                "No compliance trend data to display.",
                ha="center",
                va="center",
                fontsize=12
            )
        else:
            dates = []
            scores = []
            for r in reversed(reports):
                try:
                    dates.append(mdates.datestr2num(r["analysis_date"]))
                    scores.append(r["compliance_score"])
                except (ValueError, TypeError):
                    continue

            if not dates:
                ax.text(
                    0.5,
                    0.5,
                    "No valid trend data to display.",
                    ha="center",
                    va="center",
                    fontsize=12
                )
            else:
                ax.plot(dates, scores, marker="o", linestyle="-", linewidth=2, markersize=6)
                ax.set_title("Compliance Score Over Time", fontsize=14, fontweight='bold')
                ax.set_xlabel("Analysis Date", fontsize=12)
                ax.set_ylabel("Compliance Score", fontsize=12)
                ax.grid(True, alpha=0.3)
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
                
        # Apply tight layout to prevent overlap
        self.trends_canvas.figure.tight_layout(pad=2.0)
        self.trends_canvas.draw()

    def _update_summary_plot(self, summary):
        """Updates the findings summary bar chart."""
        ax = self.summary_canvas.axes
        ax.clear()

        if not summary:
            ax.text(
                0.5,
                0.5,
                "No findings summary data to display.",
                ha="center",
                va="center",
                fontsize=12
            )
        else:
            top_n = 8  # Reduce number to prevent overlap
            summary = summary[:top_n]

            rule_ids = [item["rule_id"][:20] + "..." if len(item["rule_id"]) > 20 else item["rule_id"] for item in summary]
            counts = [item["count"] for item in summary]

            bars = ax.barh(rule_ids, counts, color='#007acc', alpha=0.7)
            ax.set_title(f"Top {len(rule_ids)} Most Common Findings", fontsize=14, fontweight='bold')
            ax.set_xlabel("Number of Occurrences", fontsize=12)
            ax.set_ylabel("Finding Type", fontsize=12)
            ax.invert_yaxis()
            
            # Add value labels on bars
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                       f'{counts[i]}', ha='left', va='center', fontsize=10)
            
        # Apply tight layout to prevent overlap
        self.summary_canvas.figure.tight_layout(pad=2.0)
        self.summary_canvas.draw()


class MplCanvas(FigureCanvas):
    """A reusable Matplotlib canvas widget for PyQt."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.patch.set_facecolor('white')
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)
        self.setParent(parent)
        
        # Set size policy to allow proper resizing
        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Apply tight layout with padding
        self.figure.tight_layout(pad=2.0)
