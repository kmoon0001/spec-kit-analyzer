import sys
from PyQt6.QtWidgets import QDialog, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class ChartsDialog(QDialog):
    def __init__(self, metrics_data, parent=None):
        super().__init__(parent)
        self.metrics_data = metrics_data
        self.setWindowTitle("Analysis Metrics")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Create a Matplotlib figure and canvas
        # Using a single figure with two subplots
        fig = Figure(figsize=(10, 8))
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)

        # Bar chart for risks by category
        ax1 = fig.add_subplot(2, 1, 1)
        categories = self.metrics_data.get('by_category', {})
        ax1.bar(categories.keys(), categories.values())
        ax1.set_title('Risks by Category')
        ax1.set_ylabel('Number of Risks')

        # Pie chart for risks by severity
        ax2 = fig.add_subplot(2, 1, 2)
        severities = self.metrics_data.get('by_severity', {})
        if severities:
            ax2.pie(severities.values(), labels=severities.keys(), autopct='%1.1f%%', startangle=90)
            ax2.set_title('Risks by Severity')
        else:
            ax2.text(0.5, 0.5, 'No severity data available', horizontalalignment='center', verticalalignment='center')

        fig.tight_layout()

        self.setLayout(layout)
