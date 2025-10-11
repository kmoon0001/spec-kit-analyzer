from __future__ import annotations

import os
import sys
from typing import Iterator
from unittest.mock import patch

import pytest

try:  # pragma: no cover - environment dependent
    import PySide6  # type: ignore[import-not-found]
    from PySide6.QtWidgets import QApplication
except Exception as exc:  # pragma: no cover - handled via skip logic
    PySide6 = None  # type: ignore[assignment]
    QApplication = None  # type: ignore[assignment]
    _QT_IMPORT_ERROR: Exception | None = exc
    _QT_IS_STUB = False
else:  # pragma: no cover - environment dependent
    _QT_IMPORT_ERROR = None
    _QT_IS_STUB = bool(getattr(PySide6, "__FAKE_PYSIDE6__", False))

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def _ensure_qapplication() -> QApplication:
    if (
        QApplication is None
        or _QT_IMPORT_ERROR is not None
        or _QT_IS_STUB
    ):  # pragma: no cover - skip handled elsewhere
        raise RuntimeError("Qt application cannot be created without GUI dependencies.")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def qapp() -> Iterator[QApplication]:
    """Provide a QApplication instance or skip if Qt cannot initialize."""

    if _QT_IMPORT_ERROR is not None:
        pytest.skip(f"Qt GUI dependencies unavailable: {_QT_IMPORT_ERROR}")
    if _QT_IS_STUB:
        pytest.skip("Qt GUI dependencies replaced with stub implementation.")

    app = _ensure_qapplication()
    yield app


@pytest.fixture
def qtbot(qapp):
    """Fallback qtbot fixture that defers to pytest-qt when available."""

    if _QT_IMPORT_ERROR is not None:
        pytest.skip(f"Qt GUI dependencies unavailable: {_QT_IMPORT_ERROR}")
    if _QT_IS_STUB:
        pytest.skip("Qt GUI dependencies replaced with stub implementation.")

    from pytestqt.qtbot import QtBot  # Lazy import to avoid ImportError during collection

    bot = QtBot(qapp)
    yield bot
    bot._close_widgets()


@pytest.fixture(autouse=True)
def mock_global_services():
    """
    Globally mocks backend services, workers, and dialogs to isolate the GUI
    for testing, preventing real network calls and other side effects.
    """
    # For now, let's use a minimal mock setup that doesn't interfere with the new structure
    with patch("requests.post") as mock_post:
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {"access_token": "fake-token"}
        yield


def pytest_ignore_collect(path, config):  # pragma: no cover - collection control
    del config  # config unused by this helper
    if _QT_IS_STUB:
        path_str = str(path)
        if any(segment in path_str for segment in ("tests/gui", "tests/_stability", "tests/integration")):
            return True
    return False
