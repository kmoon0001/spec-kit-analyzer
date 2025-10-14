import logging

import pytest

try:  # pragma: no cover - dependency availability
    from src.api.main import WebSocketLogHandler
except ModuleNotFoundError:  # pragma: no cover - handled via skip logic
    WebSocketLogHandler = None  # type: ignore[assignment]


@pytest.fixture(autouse=True)
def disable_websocket_logging():
    """Fixture to disable the conflicting WebSocketLogHandler for all unit tests."""
    if WebSocketLogHandler is None:
        yield
        return

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        if isinstance(handler, WebSocketLogHandler):
            root_logger.removeHandler(handler)
    yield
    # No cleanup needed, the handler is removed for the duration of the test session
