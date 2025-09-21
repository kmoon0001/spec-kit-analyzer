import pytest
from src import database

def test_get_setting():
    """
    Tests that the get_setting function in the database module runs without errors.
    """
    # This is a simple test to ensure the function can be called.
    # A more comprehensive test would involve setting up a test database.
    database.get_setting("test_key")
