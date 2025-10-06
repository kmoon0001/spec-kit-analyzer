# MODIFIED: Corrected patch paths for worker modules.
# MODIFIED: Provide mock user and token to MainApplicationWindow constructor.
import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QDialog
from src.gui.main_window import MainApplicationWindow


# --- Fixtures ---
@pytest.fixture(autouse=True)
def mock_all_backend_services():
    """Mocks all backend services to isolate the GUI for stability testing."""
    with (
        patch("src.gui.workers.ai_loader_worker.AILoaderWorker") as _,
        patch("src.gui.workers.dashboard_worker.DashboardWorker") as _,
        patch("src.gui.workers.analysis_starter_worker.AnalysisStarterWorker") as _,
        patch("src.gui.main_window.requests.post") as mock_post,
        patch("src.gui.main_window.QFileDialog.getOpenFileName") as mock_open_file,
        patch("src.gui.main_window.ChatDialog") as _,
    ):
        mock_post.return_value.json.return_value = {"access_token": "fake-token"}
        mock_open_file.return_value = ("/fake/path/document.txt", "All Files (*.*)")
        yield


@pytest.fixture
def main_app_window(qtbot):
    """Fixture to create the main window and get it into a logged-in state."""
    mock_user = MagicMock()
    mock_user.username = "testuser"
    mock_token = "fake-token"
    window = MainApplicationWindow(user=mock_user, token=mock_token)
    qtbot.addWidget(window)
    return window


# --- Stability Tests ---
@pytest.mark.stability
def test_rapid_tab_switching(main_app_window: MainApplicationWindow, qtbot):
    """Simulates a user rapidly switching between the main tabs."""
    for _ in range(100):
        qtbot.waitUntil(
            lambda: main_app_window.tabs.setCurrentIndex(1)
        )  # Switch to Dashboard
        qtbot.wait(10)  # Small wait to allow UI to update
        qtbot.waitUntil(
            lambda: main_app_window.tabs.setCurrentIndex(0)
        )  # Switch to Analysis
        qtbot.wait(10)
    # The test passes if no crashes or hangs occur.


@pytest.mark.stability
def test_repeated_analysis_start(main_app_window: MainApplicationWindow, qtbot):
    """Simulates a user repeatedly starting and stopping an analysis."""
    main_app_window.open_file_dialog()  # Load a file to enable the button
    for _ in range(50):
        # Simulate clicking "Run Analysis"
        with patch("src.gui.workers.analysis_starter_worker.AnalysisStarterWorker") as _mock_starter:
            qtbot.mouseClick(
                main_app_window.run_analysis_button, qtbot.button_enum.LeftButton
            )
            qtbot.waitUntil(lambda: not main_app_window.run_analysis_button.isEnabled())
        # Simulate the analysis finishing or failing
        main_app_window.on_analysis_error("Simulated failure")
        qtbot.waitUntil(main_app_window.run_analysis_button.isEnabled)
        qtbot.wait(10)
    # The test passes if no crashes or memory leaks occur.


@pytest.mark.stability
def test_rapid_dialog_opening(main_app_window: MainApplicationWindow, qtbot):
    """Simulates rapidly opening and closing a dialog."""
    for _ in range(100):
        with patch("src.gui.main_window.ChangePasswordDialog") as mock_dialog:
            main_app_window.show_change_password_dialog()
            # In a real test, we would interact with the dialog, but for stability,
            # just creating and destroying it is a good test.
            mock_dialog.return_value.close()
        qtbot.wait(5)
    # The test passes if the application remains responsive.
