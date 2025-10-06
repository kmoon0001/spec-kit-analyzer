import pytest
import logging
from src.api.main import WebSocketLogHandler

@pytest.fixture(autouse=True)
def disable_websocket_logging():
    """Fixture to disable the conflicting WebSocketLogHandler for all unit tests."""
    root_logger = logging.getLogger()
    # Find and remove any existing instances of WebSocketLogHandler
    for handler in root_logger.handlers[:]:
        if isinstance(handler, WebSocketLogHandler):
            root_logger.removeHandler(handler)
    yield
    # No cleanup needed, the handler is removed for the duration of the test session
