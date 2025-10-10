import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.gui.main_window import MainApplicationWindow

# --- Fixtures ---

@pytest.fixture
def main_app_window(qtbot, qapp, mocker):
    from src.gui.main_window import MainApplicationWindow, MainViewModel
    from src.database import models

    mock_user = MagicMock(spec=models.User)
    mock_user.username = "testuser"
    mock_token = "mock_token_string"

    # Create the actual MainApplicationWindow instance
    window = MainApplicationWindow(user=mock_user, token=mock_token)

    # Now, replace the view_model with a MagicMock and configure its signals/methods
    window.view_model = MagicMock(spec=MainViewModel)
    window.view_model.show_message_box_signal = MagicMock()
    window.view_model.meta_analytics_loaded = MagicMock()
    window.view_model.analysis_result_received = MagicMock() # Mock the signal too

    # Connect to the mocked signal
    window.view_model.analysis_result_received.connect(lambda result: (
        window.run_analysis_button.setEnabled(True),
        window.repeat_analysis_button.setEnabled(True)
    ))

    window.show()
    qtbot.addWidget(window)
    window.close()

# --- Stability Tests (Lighter Versions) ---

@pytest.mark.stability
def test_rapid_tab_switching(main_app_window: MainApplicationWindow, qtbot):
    """A stress test for rapid tab switching to ensure UI stability."""
    tabs = main_app_window.tab_widget
    qtbot.waitUntil(lambda: tabs.count() > 1, timeout=5000)

    for _ in range(20):
        tabs.setCurrentIndex(1)
        qtbot.wait(50)
        assert tabs.currentIndex() == 1

        tabs.setCurrentIndex(0)
        qtbot.wait(50)
        assert tabs.currentIndex() == 0

@pytest.mark.stability
def test_repeated_analysis_start(main_app_window: MainApplicationWindow, qtbot, mocker):
    """A stress test for the analysis workflow with cleanup."""
    def mock_start_analysis(self, file_path: str, options: dict) -> None:
        main_app_window.view_model.analysis_result_received.emit({"score": 0.9, "findings": []})

    mocker.patch.object(main_app_window.view_model, "start_analysis", mock_start_analysis)
    mocker.patch("src.gui.main_window.diagnostics")

    mock_qmessagebox = mocker.patch("src.gui.main_window.QMessageBox")
    mock_qmessagebox.return_value.exec.return_value = QMessageBox.StandardButton.Ok
    mock_qmessagebox.return_value.clickedButton.return_value = mock_qmessagebox.return_value.addButton("Ok", QMessageBox.ButtonRole.AcceptRole)

    mock_qdialog = mocker.patch("PySide6.QtWidgets.QDialog")
    main_app_window._set_selected_file(Path("dummy_document.txt"))
    main_app_window.rubric_selector.addItem("Dummy Rubric", "dummy_rubric_data")
    main_app_window.rubric_selector.setCurrentIndex(0)
    mock_qdialog.return_value.exec.return_value = QDialog.DialogCode.Accepted

    for _ in range(2):
        main_app_window.run_analysis_button.click()

        # Wait until the analysis button is re-enabled
        qtbot.waitUntil(lambda: main_app_window.run_analysis_button.isEnabled(), timeout=20000)
        assert main_app_window.run_analysis_button.isEnabled()
        assert main_app_window.repeat_analysis_button.isEnabled()


@pytest.mark.stability
def test_rapid_dialog_opening(main_app_window: MainApplicationWindow, qtbot):
    """A stress test for rapid dialog opening."""
    for _ in range(20):
        with patch("src.gui.main_window.ChangePasswordDialog") as mock_dialog:
            mock_instance = mock_dialog.return_value
            QTimer.singleShot(10, mock_instance.accept)
            main_app_window.show_change_password_dialog()
            mock_instance.exec.assert_called_once()
        qtbot.wait(20)
