"""
Comprehensive tests for the UIHandlers class.

This module tests all UI-related event handling functionality including
theme management, dialog operations, and user interactions.
"""

from unittest.mock import Mock, patch

import pytest
from PySide6.QtWidgets import QApplication, QMainWindow

from src.gui.handlers.ui_handlers import UIHandlers


class TestUIHandlers:
    """Test suite for UIHandlers class."""

    @pytest.fixture
    def mock_main_window(self):
        """Create a mock main window for testing."""
        mock_window = Mock(spec=QMainWindow)
        mock_window.statusBar.return_value = Mock()
        mock_window._apply_medical_theme = Mock()
        return mock_window

    @pytest.fixture
    def ui_handlers(self, mock_main_window):
        """Create UIHandlers instance with mock main window."""
        return UIHandlers(mock_main_window)

    def test_initialization_success(self, mock_main_window):
        """Test successful initialization of UIHandlers."""
        handlers = UIHandlers(mock_main_window)
        assert handlers.main_window == mock_main_window

    def test_initialization_invalid_window(self):
        """Test initialization with invalid main window raises TypeError."""
        invalid_window = Mock()
        # Remove statusBar attribute to make it invalid
        del invalid_window.statusBar

        with pytest.raises(TypeError, match="main_window must be a valid MainApplicationWindow instance"):
            UIHandlers(invalid_window)

    @patch("src.gui.handlers.ui_handlers.medical_theme")
    def test_toggle_theme_light_to_dark(self, mock_theme, ui_handlers, mock_main_window):
        """Test toggling theme from light to dark."""
        # Setup
        mock_theme.current_theme = "dark"
        mock_theme.toggle_theme = Mock()

        # Execute
        ui_handlers.toggle_theme()

        # Verify
        mock_theme.toggle_theme.assert_called_once()
        mock_main_window._apply_medical_theme.assert_called_once()
        mock_main_window.statusBar().showMessage.assert_called_once_with("Switched to Dark theme", 3000)

    @patch("src.gui.handlers.ui_handlers.medical_theme")
    def test_toggle_theme_dark_to_light(self, mock_theme, ui_handlers, mock_main_window):
        """Test toggling theme from dark to light."""
        # Setup
        mock_theme.current_theme = "light"
        mock_theme.toggle_theme = Mock()

        # Execute
        ui_handlers.toggle_theme()

        # Verify
        mock_theme.toggle_theme.assert_called_once()
        mock_main_window._apply_medical_theme.assert_called_once()
        mock_main_window.statusBar().showMessage.assert_called_once_with("Switched to Light theme", 3000)

    @patch("src.gui.handlers.ui_handlers.medical_theme")
    def test_apply_theme_valid_light(self, mock_theme, ui_handlers, mock_main_window):
        """Test applying light theme."""
        # Setup
        mock_theme.set_theme = Mock()

        # Execute
        ui_handlers.apply_theme("light")

        # Verify
        mock_theme.set_theme.assert_called_once_with("light")
        mock_main_window._apply_medical_theme.assert_called_once()

    @patch("src.gui.handlers.ui_handlers.medical_theme")
    def test_apply_theme_valid_dark(self, mock_theme, ui_handlers, mock_main_window):
        """Test applying dark theme."""
        # Setup
        mock_theme.set_theme = Mock()

        # Execute
        ui_handlers.apply_theme("dark")

        # Verify
        mock_theme.set_theme.assert_called_once_with("dark")
        mock_main_window._apply_medical_theme.assert_called_once()

    @patch("src.gui.handlers.ui_handlers.medical_theme")
    def test_apply_theme_valid_auto(self, mock_theme, ui_handlers, mock_main_window):
        """Test applying auto theme."""
        # Setup
        mock_theme.set_theme = Mock()

        # Execute
        ui_handlers.apply_theme("auto")

        # Verify
        mock_theme.set_theme.assert_called_once_with("auto")
        mock_main_window._apply_medical_theme.assert_called_once()

    def test_apply_theme_invalid_name(self, ui_handlers):
        """Test applying invalid theme name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid theme name: invalid. Must be 'light', 'dark', or 'auto'"):
            ui_handlers.apply_theme("invalid")

    def test_apply_theme_empty_name(self, ui_handlers):
        """Test applying empty theme name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid theme name: . Must be 'light', 'dark', or 'auto'"):
            ui_handlers.apply_theme("")

    def test_apply_theme_none_name(self, ui_handlers):
        """Test applying None theme name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid theme name: None. Must be 'light', 'dark', or 'auto'"):
            ui_handlers.apply_theme(None)


class TestUIHandlersIntegration:
    """Integration tests for UIHandlers with real Qt components."""

    @pytest.fixture(scope="class")
    def qapp(self):
        """Create QApplication for integration tests."""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app
        # Don't quit the app as it might be used by other tests

    def test_theme_integration_with_real_window(self, qapp):
        """Test theme operations with a real QMainWindow."""
        # Create real main window
        main_window = QMainWindow()
        main_window._apply_medical_theme = Mock()  # Mock the theme application

        # Create handlers
        handlers = UIHandlers(main_window)

        # Test theme operations don't crash
        with patch("src.gui.handlers.ui_handlers.medical_theme") as mock_theme:
            mock_theme.current_theme = "light"
            handlers.toggle_theme()

            # Verify operations completed
            mock_theme.toggle_theme.assert_called_once()
            main_window._apply_medical_theme.assert_called_once()
