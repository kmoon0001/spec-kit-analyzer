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
        """Run analysis in background thread, correctly handling async operations."""
        loop = None
        try:
            self.status_updated.emit("🤖 Initializing analysis...")
            self.progress_updated.emit(10)

            from pathlib import Path
            p = Path(self.file_path)
            if not p.exists():
                raise FileNotFoundError(f"File not found: {self.file_path}")

            self.status_updated.emit(f"📄 Reading file: {p.name}")
            self.progress_updated.emit(20)
            file_content = p.read_bytes()
            original_filename = p.name

            self.status_updated.emit("🔬 Analyzing document with AI...")
            self.progress_updated.emit(50)

            # Create and run a new asyncio event loop in this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            analysis_coro = self.analysis_service.analyze_document(
                file_content=file_content,
                original_filename=original_filename,
                discipline=self.discipline
            )
            result = loop.run_until_complete(analysis_coro)

            self.progress_updated.emit(80)
            self.status_updated.emit("📊 Finalizing report...")

            self.progress_updated.emit(100)
            self.status_updated.emit("✅ Analysis complete")
            self.analysis_completed.emit(result)

        except Exception as e:
            logger.exception("Analysis failed in worker: %s", e)
            self.analysis_failed.emit(f"An error occurred during analysis: {e}")
        finally:
            if loop and not loop.is_closed():
                loop.close()
            self.finished.emit()
