import pytest
from src.main import MainWindow

def test_main_window_creation(qapp):
    """
    Tests that the MainWindow can be created without crashing.
    """
    window = MainWindow()
    assert window is not None
