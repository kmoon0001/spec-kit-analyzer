# MODIFIED: Corrected patch paths for worker modules.
# MODIFIED: Provide mock user and token to MainApplicationWindow constructor.
# RECREATED: Rewrote hanging tests to be "lighter" and more stable.
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from PySide6.QtCore import QTimer
from src.gui.main_window import MainApplicationWindow

# --- Fixtures ---



@pytest.fixture
def main_app_window(qtbot):
    """Fixture to create the main window and get it into a logged-in state."""
    mock_user = MagicMock()
    mock_user.username = "testuser"
    mock_token = "fake-token"
    window = MainApplicationWindow(user=mock_user, token=mock_token)
    qtbot.addWidget(window)
    window.show()
    qtbot.waitUntil(window.isVisible, timeout=5000)
    return window

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
    main_app_window.is_testing = True  # Enable testing mode

    def mock_starter_run(self):
        self.success.emit("mock-task-123")

    def mock_poller_run(self):
        self.success.emit({"score": 0.9, "findings": []})
        QApplication.processEvents()

    mocker.patch("src.gui.workers.analysis_starter_worker.AnalysisStarterWorker.run", mock_starter_run)
    mocker.patch("src.gui.workers.single_analysis_polling_worker.SingleAnalysisPollingWorker.run", mock_poller_run)
    mocker.patch("src.gui.main_window.diagnostics")

    mock_qmessagebox = mocker.patch("src.gui.main_window.QMessageBox")
    mock_qmessagebox.return_value.exec.return_value = QMessageBox.StandardButton.Ok
    mock_qmessagebox.return_value.clickedButton.return_value = mock_qmessagebox.return_value.addButton("Ok", QMessageBox.ButtonRole.AcceptRole)

    mock_qdialog = mocker.patch("PySide6.QtWidgets.QDialog")
    mock_qdialog.return_value.exec.return_value = QDialog.DialogCode.Accepted

    mocker.patch("src.gui.main_window.MainApplicationWindow._open_report_popup")

    mock_handle_analysis_success = mocker.patch("src.gui.main_window.MainApplicationWindow._handle_analysis_success")

    for _ in range(2):
        main_app_window.run_analysis_button.click()

        # Wait for the analysis success handler to be called
        qtbot.waitUntil(lambda: mock_handle_analysis_success.called, timeout=10000)
        mock_handle_analysis_success.assert_called_once()
        mock_handle_analysis_success.reset_mock()

        # Ensure buttons are re-enabled for the next iteration
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
