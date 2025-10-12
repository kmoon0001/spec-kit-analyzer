from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox

from src.gui.dialogs.batch_analysis_dialog import BatchAnalysisDialog


class StubScanner(QObject):
    file_found = Signal(str)
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, files: list[str] | None = None, error: str | None = None):
        super().__init__()
        self._files = files or []
        self._error = error
        self._running = True

    def run(self) -> None:
        if self._error:
            self.error.emit(self._error)
            return
        for file_path in self._files:
            if not self._running:
                break
            self.file_found.emit(Path(file_path).name)
        if self._running:
            self.finished.emit(self._files)

    def stop(self) -> None:
        self._running = False


class StubProcessor(QObject):
    progress = Signal(int, int, str)
    file_completed = Signal(str, str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, file_paths: list[str], fail_message: str | None = None):
        super().__init__()
        self.file_paths = file_paths
        self.fail_message = fail_message
        self._running = True

    def run(self) -> None:
        if self.fail_message:
            self.error.emit(self.fail_message)
            self.finished.emit()
            return

        total = len(self.file_paths)
        for index, file_path in enumerate(self.file_paths):
            if not self._running:
                break
            filename = Path(file_path).name
            self.progress.emit(index, total, filename)
            self.file_completed.emit(filename, "Completed")
        if self._running:
            self.finished.emit()

    def stop(self) -> None:
        self._running = False


@pytest.fixture
def base_kwargs(tmp_path):
    folder = tmp_path / "input"
    folder.mkdir()
    return {
        "folder_path": str(folder),
        "token": "token-123",
        "analysis_data": {"mode": "standard"},
    }


def test_batch_dialog_handles_empty_scan_results(qtbot, base_kwargs):
    dialog = BatchAnalysisDialog(
        **base_kwargs,
        scanner_factory=lambda folder, extensions: StubScanner(files=[]),
        processor_factory=lambda files, token, data: StubProcessor(files),
        use_async=False,
    )
    qtbot.addWidget(dialog)

    assert dialog.start_button.text() == "Close"
    assert dialog.start_button.isEnabled()
    assert "No supported documents" in dialog.status_label.text()


def test_batch_dialog_scan_error(monkeypatch, qtbot, base_kwargs):
    called = {}

    def fake_critical(*args, **kwargs):
        called["message"] = args[2]
        return QMessageBox.StandardButton.Ok

    monkeypatch.setattr("src.gui.dialogs.batch_analysis_dialog.QMessageBox.critical", fake_critical)

    dialog = BatchAnalysisDialog(
        **base_kwargs,
        scanner_factory=lambda folder, extensions: StubScanner(error="Disk not accessible"),
        processor_factory=lambda files, token, data: StubProcessor(files),
        use_async=False,
    )
    qtbot.addWidget(dialog)

    assert called["message"] == "Disk not accessible"
    assert dialog.result() == dialog.DialogCode.Accepted


def test_batch_dialog_processor_updates_status(qtbot, base_kwargs, tmp_path):
    files = [str(tmp_path / "report.pdf")]

    dialog = BatchAnalysisDialog(
        **base_kwargs,
        scanner_factory=lambda folder, extensions: StubScanner(files=files),
        processor_factory=lambda f, token, data: StubProcessor(f),
        use_async=False,
    )
    qtbot.addWidget(dialog)

    dialog.start_batch_analysis()

    assert dialog.status_label.text() == "Batch analysis complete."
    assert dialog.progress_bar.value() == dialog.progress_bar.maximum()
    assert dialog.results_table.item(0, 1).text() == "Completed"
