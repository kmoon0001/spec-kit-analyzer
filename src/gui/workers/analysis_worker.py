import asyncio
import logging

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal as Signal

from src.core.analysis_service import AnalysisService

logger = logging.getLogger(__name__)


class AnalysisWorker(QObject):
    """Background worker for document analysis."""

    progress_updated = Signal(int)
    status_updated = Signal(str)
    analysis_completed = Signal(dict)
    analysis_failed = Signal(str)
    finished = Signal()  # Add this line

    def __init__(
        self,
        file_path: str,
        discipline: str,
        analysis_service: AnalysisService):
        super().__init__()
        self.file_path = file_path
        self.discipline = discipline
        self.analysis_service = analysis_service

    def run(self):
        """Run analysis in background thread."""
        try:
            self.status_updated.emit("🤖 Initializing AI models...")
            self.progress_updated.emit(10)

            self.status_updated.emit("📄 Processing document...")
            self.progress_updated.emit(30)

            # Run the actual analysis
            result = self.analysis_service.analyze_document(
                file_path=self.file_path,
                discipline=self.discipline)

            self.progress_updated.emit(80)
            self.status_updated.emit("📊 Generating report...")

            # Handle async result if needed
            if hasattr(result, "__await__"):
                # This is an async result, we need to handle it properly
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(result)
                finally:
                    loop.close()

            self.progress_updated.emit(100)
            self.status_updated.emit("✅ Analysis complete")
            self.analysis_completed.emit(result)

        except Exception as e:
            logger.exception("Analysis failed: %s", e)
            self.analysis_failed.emit(str(e))
