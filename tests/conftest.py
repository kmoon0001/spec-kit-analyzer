import os
import sys
from unittest.mock import patch

import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


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
