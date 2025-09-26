import pytest
from unittest.mock import patch

from src.gui.main_window import MainApplicationWindow

# --- Fixtures ---


@pytest.fixture(autouse=True)
def mock_backend_services():
    """Mocks all backend services to isolate the GUI for stability testing."""
    with patch("src.gui.main_window.AILoaderWorker"), patch(
        "src.gui.main_window.DashboardWorker"
    ), patch("src.gui.main_window.AnalysisStarterWorker"), patch(
        "src.gui.main_window.requests.post"
    ), patch(
        "src.gui.main_window.QMessageBox"
    ) as mock_msg_box:  # Mock message box to prevent popups
        yield mock_msg_box


@pytest.fixture
def main_app_window(qtbot):
    """Fixture to create the main window in a logged-in state."""
    # This setup is simplified as we don't need to test the login flow here
    window = MainApplicationWindow()
    window.access_token = "fake-token"
    window.load_main_ui()
    qtbot.addWidget(window)
    return window


# --- Edge Case Tests ---


@pytest.mark.stability
def test_large_file_upload(main_app_window: MainApplicationWindow, qtbot, tmp_path):
    """
    Tests the GUI's ability to handle a very large text file without crashing.
    """
    # Arrange: Create a large temporary file
    large_file_content = "This is a test sentence. " * 5 * 1024 * 1024  # Approx 50MB
    large_file = tmp_path / "large_file.txt"
    large_file.write_text(large_file_content)

    # Act: Simulate opening the large file
    with patch(
        "src.gui.main_window.QFileDialog.getOpenFileName",
        return_value=(str(large_file), "All Files (*.*)"),
    ):
        main_app_window.open_file_dialog()

    # Assert: The application should not crash, and the text area should contain the content.
    # We check a substring to avoid loading the whole 50MB into the test assertion.
    assert (
        "This is a test sentence."
        in main_app_window.document_display_area.toPlainText()
    )
    assert main_app_window.run_analysis_button.isEnabled()


@pytest.mark.stability
def test_corrupted_file_upload(
    main_app_window: MainApplicationWindow, qtbot, mock_backend_services
):
    """
    Tests that the application handles a corrupted or unreadable file gracefully.
    """
    # Arrange: Simulate the file dialog returning a path to a fake corrupted file
    # and simulate the open() call failing with a UnicodeDecodeError.
    with patch(
        "src.gui.main_window.QFileDialog.getOpenFileName",
        return_value=("/fake/path/corrupted.pdf", "All Files (*.*)"),
    ), patch(
        "builtins.open",
        side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte"),
    ):

        # Act
        main_app_window.open_file_dialog()

    # Assert: The application should not crash. It should display an error message in the text area.
    assert (
        "Could not display preview"
        in main_app_window.document_display_area.toPlainText()
    )
    # The run button should remain disabled because no valid document was loaded.
    assert not main_app_window.run_analysis_button.isEnabled()
