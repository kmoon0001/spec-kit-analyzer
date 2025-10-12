from __future__ import annotations

import asyncio
from pathlib import Path

from src.gui.workers.analysis_worker import AnalysisWorker


class StubAnalysisService:
    async def analyze_document(self, *, progress_callback=None, **_kwargs):  # type: ignore[override]
        if progress_callback:
            progress_callback(25, "Reading document")
            await asyncio.sleep(0)
            progress_callback(80, None)
        await asyncio.sleep(0)
        return {"status": "ok"}


def test_analysis_worker_emits_progress_and_results(qtbot, tmp_path: Path):
    note_path = tmp_path / "note.txt"
    note_path.write_text("sample note", encoding="utf-8")

    worker = AnalysisWorker(str(note_path), "pt", StubAnalysisService())

    progress_values: list[int] = []
    status_messages: list[str] = []
    result_payload: dict | None = None

    worker.progress_updated.connect(progress_values.append)
    worker.status_updated.connect(status_messages.append)

    def _capture_result(payload):
        nonlocal result_payload
        result_payload = payload

    worker.analysis_completed.connect(_capture_result)

    worker.run()

    assert result_payload == {"status": "ok"}
    assert progress_values[0] == 0
    assert progress_values[-1] == 100
    assert status_messages[-1] == "Analysis complete."
