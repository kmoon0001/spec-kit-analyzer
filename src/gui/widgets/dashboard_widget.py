from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class DashboardWidget(QWidget):
    """
    A widget to display compliance trends and other visualizations.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # --- Matplotlib Canvas ---
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.layout.addWidget(self.canvas)
        
        # Placeholder for data
        self.layout.addWidget(QLabel("Dashboard will display historical compliance data."))

    def update_plot(self, reports):
        """
        Updates the plot with new data from the API.
        
        Args:
            reports: A list of report dictionaries from the backend.
        """
        if not reports:
            self.canvas.axes.clear()
            self.canvas.axes.text(0.5, 0.5, "No data to display.", ha='center', va='center')
            self.canvas.draw()
            return

        # Extract data for plotting (in reverse order for chronological plot)
        dates = [r['analysis_date'] for r in reversed(reports)]
        scores = [r['compliance_score'] for r in reversed(reports)]

        # Update the plot
        self.canvas.axes.clear()
        self.canvas.axes.plot(dates, scores, marker='o', linestyle='-')
        self.canvas.axes.set_title("Compliance Score Over Time")
        self.canvas.axes.set_xlabel("Analysis Date")
        self.canvas.axes.set_ylabel("Compliance Score")
        self.canvas.axes.grid(True)
        self.canvas.figure.tight_layout()
        self.canvas.draw()

class MplCanvas(FigureCanvas):
    """A reusable Matplotlib canvas widget for PyQt."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)
