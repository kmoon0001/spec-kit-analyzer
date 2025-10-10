
"""
Tests for the MainApplicationWindow.
"""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.database.models import User
from src.gui.main_window import MainApplicationWindow

@pytest.fixture
def mock_user():
    """Fixture for a mock user object."""
    user = User(id=1, username='testuser', is_admin=True)
    return user

@pytest.fixture
def app(qtbot, mock_user):
    """Fixture to create the MainApplicationWindow."""
    # Mock the view model to prevent it from starting workers and API calls
    with patch('src.gui.main_window.MainViewModel') as MockViewModel:
        # Make sure the mock view model can be instantiated
        mock_instance = MockViewModel.return_value
        
        # Mock the necessary attributes and methods on the view model instance
        mock_instance.status_message_changed = MagicMock()
        mock_instance.api_status_changed = MagicMock()
        mock_instance.task_list_changed = MagicMock()
        mock_instance.log_message_received = MagicMock()
        mock_instance.settings_loaded = MagicMock()
        mock_instance.analysis_result_received = MagicMock()
        mock_instance.rubrics_loaded = MagicMock()
        mock_instance.dashboard_data_loaded = MagicMock()
        mock_instance.meta_analytics_loaded = MagicMock()
        mock_instance.start_workers = MagicMock()
        mock_instance.load_settings = MagicMock()

        window = MainApplicationWindow(user=mock_user, token='fake_token')
        qtbot.addWidget(window)
        yield window
        window.close()



def test_main_window_initialization(app):

    """Test if the main window and its widgets are initialized."""

    assert app is not None

    assert app.windowTitle() == "THERAPY DOCUMENTATION COMPLIANCE ANALYSIS"

    

    # Check for the existence of key widgets

    assert app.tab_widget is not None

    assert app.analysis_tab is not None

    assert app.dashboard_tab is not None

    assert app.mission_control_tab is not None

    assert app.settings_tab is not None

    

    assert app.run_analysis_button is not None

    assert app.rubric_selector is not None

    assert app.file_display is not None

    

    # Check that the view model was initialized and its setup methods called

    app.view_model.start_workers.assert_called_once()

    if app.current_user.is_admin:

        app.view_model.load_settings.assert_called_once()



def test_run_analysis_click(app, qtbot, monkeypatch):

    """Test that clicking the run analysis button calls the view model."""

    # Preconditions: a file must be selected and a rubric chosen.

    app._selected_file = Path("C:/fake/path/to/document.txt")

    app.rubric_selector.clear() # Clear default rubrics

    app.rubric_selector.addItem("Test Rubric", "test_rubric_id")

    app.rubric_selector.setCurrentIndex(0)



    # Mock the diagnostics to prevent it from showing message boxes

    mock_diagnostics = MagicMock()

    mock_diagnostics.run_full_diagnostic.return_value = {}

    mock_diagnostics.validate_file_format.return_value = MagicMock(status=MagicMock(value="success"))

    monkeypatch.setattr("src.gui.main_window.diagnostics", mock_diagnostics)



    # Mock the workflow logger

    mock_workflow_logger = MagicMock()

    monkeypatch.setattr("src.gui.main_window.workflow_logger", mock_workflow_logger)



    # Mock the status tracker

    mock_status_tracker = MagicMock()

    monkeypatch.setattr("src.gui.main_window.status_tracker", mock_status_tracker)



    # Simulate the button click by calling the method directly

    app._start_analysis()



    # Assert that the view_model.start_analysis method was called

    app.view_model.start_analysis.assert_called_once()

    

    # Check the arguments passed to start_analysis

    args, kwargs = app.view_model.start_analysis.call_args

    assert args[0] == str(Path("C:/fake/path/to/document.txt"))

    assert args[1]["discipline"] == "test_rubric_id"



def test_open_file_click(app, qtbot, monkeypatch):

    """Test that clicking the open file button opens a dialog and updates the UI."""

    # Mock the QFileDialog to return a specific file path

    mock_file_dialog = MagicMock()

    mock_file_dialog.getOpenFileName.return_value = ("C:/fake/path/to/document.txt", "All Files (*)")

    monkeypatch.setattr("src.gui.main_window.QFileDialog", mock_file_dialog)



    # Simulate the button click

    qtbot.mouseClick(app.open_file_button, qtbot.button_enum.LeftButton)



    # Assert that the _selected_file attribute is updated

    assert app._selected_file == Path("C:/fake/path/to/document.txt")



    # Assert that the file display is updated

    assert "document.txt" in app.file_display.toPlainText()



