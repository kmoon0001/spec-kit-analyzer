import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(autouse=True)
def mock_global_services(qtbot):
    """
    Globally mocks backend services, workers, and dialogs to isolate the GUI
    for testing, preventing real network calls and other side effects.
    """
    with (
        # 1. Prevent diagnostic checks from making real network calls
        patch("src.gui.main_window.diagnostics.run_full_diagnostic", return_value={}),

        # 2. Prevent background workers from starting
        patch("src.gui.main_window.HealthCheckWorker"),
        patch("src.gui.main_window.TaskMonitorWorker"),
        patch("src.gui.main_window.LogStreamWorker"),
        patch("src.gui.workers.ai_loader_worker.AILoaderWorker"),
        patch("src.gui.workers.dashboard_worker.DashboardWorker"),

        # 3. Mock login request (needed for main_app_window fixture)
        patch("src.gui.main_window.requests.post") as mock_post,

        # 4. Mock file and chat dialogs
        patch("src.gui.main_window.QFileDialog.getOpenFileName") as mock_open_file,
        patch("src.gui.main_window.ChatDialog"),
    ):
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {"access_token": "fake-token"}
        mock_open_file.return_value = ("/fake/path/document.txt", "All Files (*.*)")
        yield
