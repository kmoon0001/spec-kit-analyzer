from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates

class DashboardWidget(QWidget):
    """
    A widget to display compliance trends and other visualizations.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        
        # --- Compliance Trend Chart ---
        self.trends_canvas = MplCanvas(self, width=6, height=5, dpi=100)
        
        # --- Findings Summary Chart ---
        self.summary_canvas = MplCanvas(self, width=6, height=5, dpi=100)

        self.layout.addWidget(self.trends_canvas)
        self.layout.addWidget(self.summary_canvas)

    def update_dashboard(self, data: dict):
        """
        Updates both dashboard plots with new data from the API.
        
        Args:
            data: A dictionary containing 'reports' and 'summary' data.
        """
        reports_data = data.get('reports', [])
        summary_data = data.get('summary', [])

        self._update_trends_plot(reports_data)
        self._update_summary_plot(summary_data)

    def _update_trends_plot(self, reports):
        """Updates the compliance score trend plot."""
        ax = self.trends_canvas.axes
        ax.clear()

        if not reports:
            ax.text(0.5, 0.5, "No compliance trend data to display.", ha='center', va='center')
        else:
            # Matplotlib expects Python datetimes, so we parse the ISO strings
            dates = [mdates.datestr2num(r['analysis_date']) for r in reversed(reports)]
            scores = [r['compliance_score'] for r in reversed(reports)]

            ax.plot(dates, scores, marker='o', linestyle='-')
            ax.set_title("Compliance Score Over Time")
            ax.set_xlabel("Analysis Date")
            ax.set_ylabel("Compliance Score")
            ax.grid(True)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            self.trends_canvas.figure.autofmt_xdate() # Improve date formatting

        self.trends_canvas.draw()

    def _update_summary_plot(self, summary):
        """Updates the findings summary bar chart."""
        ax = self.summary_canvas.axes
        ax.clear()

        if not summary:
            ax.text(0.5, 0.5, "No findings summary data to display.", ha='center', va='center')
        else:
            rule_ids = [item['rule_id'] for item in summary]
            counts = [item['count'] for item in summary]

            ax.barh(rule_ids, counts)
            ax.set_title("Top 5 Most Common Findings")
            ax.set_xlabel("Number of Occurrences")
            ax.set_ylabel("Finding Type (Rule ID)")
            ax.invert_yaxis() # Display the highest count at the top

        self.summary_canvas.draw()

class MplCanvas(FigureCanvas):
    """A reusable Matplotlib canvas widget for PyQt."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)
        self.figure.tight_layout()
