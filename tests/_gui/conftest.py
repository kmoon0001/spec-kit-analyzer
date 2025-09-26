import pytest
from PyQt6.QtWidgets import QApplication
import sys

# This is a standard fixture for pytest-qt, which provides the `qtbot` fixture.
# It ensures that a single QApplication instance is created for the entire test session,
# which is much more efficient than creating one for every test.


@pytest.fixture(scope="session")
def qapp(request):
    """Session-scoped fixture to manage the QApplication instance."""
    app = QApplication.instance()
    if app is None:
        # Pass sys.argv to QApplication to ensure it can parse command-line arguments,
        # which is standard practice.
        app = QApplication(sys.argv)
    return app
