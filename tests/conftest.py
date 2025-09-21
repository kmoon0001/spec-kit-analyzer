import pytest

# This is a guarded import.
# The tests will only try to import QApplication if pytest-qt is installed.
@pytest.fixture(scope="session")
def qapp_args():
    """
    Session-wide Qapplication arguments.
    """
    return []

@pytest.fixture(scope="session")
def qapp(qapp_args):
    """
    Session-wide QApplication instance.
    """
    try:
        from PyQt6.QtWidgets import QApplication
        return QApplication(qapp_args)
    except ImportError:
        return None
