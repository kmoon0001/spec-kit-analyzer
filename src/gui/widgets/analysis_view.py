from PyQt6.QtWebEngineWidgets import QWebEngineView

class AnalysisView(QWebEngineView):
    def __init__(self):
        super().__init__()
        self.setHtml("<p>Analysis results will appear here.</p>")

