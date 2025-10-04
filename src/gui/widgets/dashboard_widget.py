from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel

# For now, use simple Qt-based charts until matplotlib integration is resolved
MATPLOTLIB_AVAILABLE = False

# Future: Will implement proper matplotlib integration
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.figure import Figure
# import matplotlib.dates as mdates


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

        # Create chart widgets (using Qt-native charts for now)
        self.trends_canvas = SimpleChartWidget(self, chart_type="line")
        self.trends_canvas.set_title("📈 Compliance Trends Over Time")
        
        self.summary_canvas = SimpleChartWidget(self, chart_type="bar")
        self.summary_canvas.set_title("📊 Findings Summary")
        
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
        if not reports:
            self.trends_canvas.update_data([], "📈 Compliance Trends Over Time")
            return
        
        # Extract scores for simple display
        scores = []
        for r in reports:
            try:
                score = r.get("compliance_score", 0)
                scores.append(score)
            except (ValueError, TypeError):
                continue
        
        self.trends_canvas.update_data(scores, f"📈 Compliance Trends ({len(reports)} reports)")
        return  # Skip matplotlib code below
        
        # Original matplotlib code (disabled for now)
        ax = self.trends_canvas.axes
        ax.clear()

        if not reports:
            ax.text(
                0.5,
                0.5,
                "No compliance trend data to display.",
                ha="center",
                va="center",
                fontsize=12,
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
                    fontsize=12,
                )
            else:
                ax.plot(
                    dates, scores, marker="o", linestyle="-", linewidth=2, markersize=6
                )
                ax.set_title(
                    "Compliance Score Over Time", fontsize=14, fontweight="bold"
                )
                ax.set_xlabel("Analysis Date", fontsize=12)
                ax.set_ylabel("Compliance Score", fontsize=12)
                ax.grid(True, alpha=0.3)
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
                ax.plot(
                    dates, scores, marker="o", linestyle="-", linewidth=2, markersize=6
                )
                ax.set_title(
                    "Compliance Score Over Time", fontsize=14, fontweight="bold"
                )
                ax.set_xlabel("Analysis Date", fontsize=12)
                ax.set_ylabel("Compliance Score", fontsize=12)
                ax.grid(True, alpha=0.3)
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        
        # Apply tight layout to prevent overlap
        self.trends_canvas.fig.tight_layout(pad=2.0)
        self.trends_canvas.draw()

    def _update_summary_plot(self, summary):
        """Updates the findings summary bar chart."""
        if not summary:
            self.summary_canvas.update_data([], "📊 Findings Summary")
            return
        
        # Extract summary data for simple display
        summary_data = []
        if isinstance(summary, list):
            summary_data = summary
        elif isinstance(summary, dict):
            summary_data = list(summary.values())
        
        self.summary_canvas.update_data(summary_data, f"📊 Findings Summary ({len(summary)} items)")
        return  # Skip matplotlib code below
        
        # Original matplotlib code (disabled for now)
        ax = self.summary_canvas.axes
        ax.clear()

        if not summary:
            ax.text(
                0.5,
                0.5,
                "No findings summary data to display.",
                ha="center",
                va="center",
                fontsize=12,
            )
        else:
            top_n = 8  # Reduce number to prevent overlap
            summary = summary[:top_n]

            rule_ids = [
                item["rule_id"][:20] + "..."
               if len(item["rule_id"]) > 20
                else item["rule_id"]
               [:20] + "..." if len(item["rule_id"]) > 20
                else item["rule_id"]
                for item in summary
            ]
            counts = [item["count"] for item in summary]

            bars = ax.barh(rule_ids, counts, color="#007acc", alpha=0.7)
            ax.set_title(
                f"Top {len(rule_ids)} Most Common Findings",
                fontsize=14,
                fontweight="bold",
            )
            ax.set_xlabel("Number of Occurrences", fontsize=12)
            ax.set_ylabel("Finding Type", fontsize=12)
            ax.invert_yaxis()

            # Add value labels on bars
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax.text(
                    width + 0.1,
                    bar.get_y() + bar.get_height() / 2,
                    f"{counts[i]}",
                    ha="left",
                    va="center",
                    fontsize=10,
                )
        # Apply tight layout to prevent overlap
        self.summary_canvas.fig.tight_layout(pad=2.0)
        self.summary_canvas.draw()


class SimpleChartWidget(QWidget):
    """A simple chart widget using Qt native capabilities."""

    def __init__(self, parent=None, chart_type="line"):
        super().__init__(parent)
        self.chart_type = chart_type
        self.data = []
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Chart title
        self.title_label = QLabel("Chart Title")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px; text-align: center;")
        layout.addWidget(self.title_label)
        
        # Chart area (placeholder for now)
        self.chart_area = QLabel("📊 Chart data will be displayed here")
        self.chart_area.setStyleSheet("""
            border: 2px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            background: white;
            text-align: center;
            color: #666;
            min-height: 200px;
        """)
        layout.addWidget(self.chart_area, 1)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.status_label)
    
    def set_title(self, title):
        """Set chart title."""
        self.title_label.setText(title)
    
    def update_data(self, data, title="Chart"):
        """Update chart with new data."""
        self.data = data
        self.set_title(title)
        
        if not data:
            self.chart_area.setText("📊 No data to display")
            self.status_label.setText("No data available")
        else:
            # Simple text-based representation for now
            data_summary = f"📊 {len(data)} data points\n"
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict):
                    # Handle dict data
                    data_summary += f"Latest: {list(data[-1].values())[0] if data[-1] else 'N/A'}"
                else:
                    # Handle simple list
                    data_summary += f"Range: {min(data)} - {max(data)}"
            
            self.chart_area.setText(data_summary)
            self.status_label.setText(f"Updated with {len(data)} points")
    
    def clear(self):
        """Clear chart data."""
        self.data = []
        self.chart_area.setText("📊 Chart cleared")
        self.status_label.setText("Cleared")

# Alias for compatibility
MplCanvas = SimpleChartWidget
