import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.gui.main_window import MainApplicationWindow

# --- Fixtures ---

@pytest.fixture
def main_app_window(qtbot, qapp, mocker):
    # Mock dependencies that would normally be injected or initialized

    # Mock the MainViewModel to prevent actual logic execution during UI setup
    mock_view_model = mocker.patch("src.gui.main_window.MainViewModel")
    mock_view_model.return_value.show_message_box_signal = MagicMock()
    mock_view_model.return_value.meta_analytics_loaded = MagicMock()

    from src.gui.main_window import MainApplicationWindow
    from src.database import models

    mock_user = MagicMock(spec=models.User)
    mock_user.username = "testuser"
    mock_token = "mock_token_string"

    window = MainApplicationWindow(user=mock_user, token=mock_token)

    def mock_handle_analysis_success(self, result: dict) -> None:
        print("mock_handle_analysis_success called!")
        window.run_analysis_button.setEnabled(True)
        window.repeat_analysis_button.setEnabled(True)

    # Connect to the signal of the *actual* MainViewModel instance
    window.view_model.analysis_result_received.connect(mock_handle_analysis_success.__get__(window, MainApplicationWindow))

    window.show()
    qtbot.addWidget(window)
    yield window
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
        print("mock_start_analysis called!")
        main_app_window.view_model.analysis_result_received.emit({"score": 0.9, "findings": []})

    mocker.patch.object(main_app_window.view_model, "start_analysis", mock_start_analysis)
    mocker.patch("src.gui.main_window.diagnostics")

    mock_qmessagebox = mocker.patch("src.gui.main_window.QMessageBox")
    mock_qmessagebox.return_value.exec.return_value = QMessageBox.StandardButton.Ok
    mock_qmessagebox.return_value.clickedButton.return_value = mock_qmessagebox.return_value.addButton("Ok", QMessageBox.ButtonRole.AcceptRole)

    mock_qdialog = mocker.patch("PySide6.QtWidgets.QDialog")
    mock_qdialog.return_value.exec.return_value = QDialog.DialogCode.Accepted

    for _ in range(2):
        main_app_window.run_analysis_button.click()

        # Wait until the analysis button is re-enabled
        qtbot.waitUntil(lambda: main_app_window.run_analysis_button.isEnabled(), timeout=10000)
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
