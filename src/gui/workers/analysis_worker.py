import asyncio
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from src.core.analysis_service import AnalysisService

logger = logging.getLogger(__name__)


class AnalysisWorker(QObject):
    """Background worker that executes document analysis in a separate thread."""

    progress_updated = Signal(int)
    status_updated = Signal(str)
    analysis_completed = Signal(dict)
    analysis_failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        file_path: str,
        discipline: str,
        analysis_service: AnalysisService,
        *,
        loop_factory: Callable[[], asyncio.AbstractEventLoop] | None = None,
    ) -> None:
        super().__init__()
        self.file_path = file_path
        self.discipline = discipline
        self.analysis_service = analysis_service
        self._loop_factory = loop_factory or asyncio.new_event_loop
        self._progress_reached_finish = False
        self._should_stop = False

    def _emit_progress(self, percentage: int) -> None:
        clamped = max(0, min(int(percentage), 100))
        if clamped >= 100:
            self._progress_reached_finish = True
        self.progress_updated.emit(clamped)

    def _emit_status(self, message: str) -> None:
        if message:
            self.status_updated.emit(message)

    def run(self) -> None:
        """Execute the analysis logic, relaying progress updates from the service."""
        if self._should_stop:
            return

        loop: asyncio.AbstractEventLoop | None = None
        self._progress_reached_finish = False

        try:
            if not self._should_stop:
                self._emit_status("Preparing analysis...")
                self._emit_progress(0)

            path = Path(self.file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {self.file_path}")

            if not self._should_stop:
                self._emit_status(f"Reading document: {path.name}")
                file_content = path.read_bytes()
                original_filename = path.name

            def progress_callback(percentage: int, message: str | None = None) -> None:
                if not self._should_stop:
                    self._emit_progress(percentage)
                    if message is not None:
                        self._emit_status(message)

            if not self._should_stop:
                self._emit_status("Running analysis pipeline...")

            loop = self._loop_factory()
            asyncio.set_event_loop(loop)

            if not self._should_stop:
                result: dict[str, Any] = loop.run_until_complete(
                    self.analysis_service.analyze_document(
                        file_content=file_content,
                        original_filename=original_filename,
                        discipline=self.discipline,
                        progress_callback=progress_callback,
                    )
                )

                if not self._progress_reached_finish:
                    self._emit_progress(100)

                self._emit_status("Analysis complete.")
                self.analysis_completed.emit(result)

        except Exception as exc:  # pragma: no cover - logged for diagnostics
            logger.exception("Analysis failed in worker: %s", exc)
            if not self._should_stop:
                self.analysis_failed.emit(f"An error occurred during analysis: {exc}")
        finally:
            if loop is not None and not loop.is_closed():
                loop.close()
            self.finished.emit()

    def stop(self) -> None:
        """Stop the worker gracefully."""
        self._should_stop = True
