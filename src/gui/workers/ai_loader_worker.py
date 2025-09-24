from PySide6.QtCore import QObject, Signal
from src.compliance_analyzer import ComplianceAnalyzer

class AILoaderWorker(QObject):
    finished = Signal(object, bool, str)  # analyzer, is_healthy, status_message

    def run(self):
        try:
            analyzer = ComplianceAnalyzer()
            is_healthy, status_message = analyzer.check_ai_systems_health()
            self.finished.emit(analyzer, is_healthy, status_message)
        except Exception as e:
            self.finished.emit(None, False, f"AI Systems: Offline - {e}")