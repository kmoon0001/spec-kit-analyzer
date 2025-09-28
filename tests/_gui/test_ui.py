import pytest
from unittest.mock import patch
from PyQt6.QtWidgets import QDialog

# Import the main window we want to test
from src.gui.main_window import MainApplicationWindow


# This fixture ensures that all backend services and workers are mocked
# for all tests in this file, so no real models are loaded or APIs called.
@pytest.fixture(autouse=True)
def mock_backend_services():
    with (
        patch("src.gui.main_window.AILoaderWorker") as _mock_ai_loader,
        patch("src.gui.main_window.DashboardWorker") as _mock_dash_worker,
        patch("src.gui.main_window.AnalysisWorker") as _mock_analysis_worker,
        patch("src.gui.main_window.requests.post") as mock_post,
        patch("src.gui.main_window.QFileDialog.getOpenFileName") as mock_open_file,
    ):
        # Configure the mocks
        mock_post.return_value.json.return_value = {"access_token": "fake-token"}
        mock_open_file.return_value = ("/fake/path/document.txt", "All Files (*.*)")
        yield


@pytest.fixture
def main_app_window(qtbot):
    """Fixture to create and show the main application window."""
    # We don't call show_login_dialog here; we trigger it in the test
    # to have more control over the flow.
    window = MainApplicationWindow()
    qtbot.addWidget(window)
    return window


def test_main_window_initialization(main_app_window: MainApplicationWindow):
    """Tests that the main window initializes without crashing."""
    assert main_app_window.windowTitle() == "Therapy Compliance Analyzer"
    # The main UI should not be loaded yet because login has not happened
    assert main_app_window.centralWidget() is None


def test_login_and_main_ui_loads(main_app_window: MainApplicationWindow, qtbot):
    """Tests the critical path: successful login leads to the main UI loading."""
    # Arrange: Mock the LoginDialog to automatically accept
    with patch("src.gui.main_window.LoginDialog") as mock_login_dialog:
        mock_login_dialog.return_value.exec.return_value = QDialog.DialogCode.Accepted
        mock_login_dialog.return_value.get_credentials.return_value = ("user", "pass")
        # Act: Trigger the login process
        main_app_window.show_login_dialog()
    # Assert
    # 1. The main window should now be visible
    assert main_app_window.isVisible()
    # 2. The central widget should be our tabbed interface
    assert main_app_window.tabs is not None
    assert main_app_window.tabs.count() == 2  # Analysis and Dashboard tabs
    assert main_app_window.tabs.tabText(1) == "Dashboard"


def test_run_analysis_button_triggers_worker(
    main_app_window: MainApplicationWindow, qtbot
):
    """
    Tests that clicking the 'Run Analysis' button correctly starts the AnalysisWorker.
    """
    # Arrange: First, we need to get the app into a logged-in state
    with patch("src.gui.main_window.LoginDialog") as mock_login_dialog:
        mock_login_dialog.return_value.exec.return_value = QDialog.DialogCode.Accepted
        mock_login_dialog.return_value.get_credentials.return_value = ("user", "pass")
        main_app_window.show_login_dialog()
    # Act
    # 1. Simulate the user opening a file
    main_app_window.open_file_dialog()
    # 2. Simulate the user clicking the run button
    with patch("src.gui.main_window.AnalysisWorker") as mock_analysis_worker:
        qtbot.mouseClick(
            main_app_window.run_analysis_button, qtbot.button_enum.LeftButton
        )
    # Assert
    # The most important assertion: Was the worker created and started?
    mock_analysis_worker.assert_called_once()
    # We can also check that the run button was disabled as expected
    assert not main_app_window.run_analysis_button.isEnabled()
