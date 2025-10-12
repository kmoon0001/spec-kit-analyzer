"""
Comprehensive tests for the FileHandlers class.

This module tests all file-related operations including document selection,
file validation, content preview generation, and batch processing workflows.
"""

from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest
from PySide6.QtWidgets import QApplication, QMainWindow

from src.gui.handlers.file_handlers import FileHandlers


class TestFileHandlers:
    """Test suite for FileHandlers class."""

    @pytest.fixture
    def mock_main_window(self):
        """Create a mock main window for testing."""
        mock_window = Mock(spec=QMainWindow)
        mock_window.statusBar.return_value = Mock()
        mock_window.run_analysis_button = Mock()
        mock_window.file_display = Mock()
        mock_window._selected_file = None
        mock_window._cached_preview_content = ""
        return mock_window

    @pytest.fixture
    def file_handlers(self, mock_main_window):
        """Create FileHandlers instance with mock main window."""
        return FileHandlers(mock_main_window)

    def test_initialization_success(self, mock_main_window):
        """Test successful initialization of FileHandlers."""
        handlers = FileHandlers(mock_main_window)
        assert handlers.main_window == mock_main_window

    def test_initialization_invalid_window(self):
        """Test initialization with invalid main window raises TypeError."""
        invalid_window = Mock()
        # Remove statusBar attribute to make it invalid
        del invalid_window.statusBar

        with pytest.raises(TypeError, match="main_window must be a valid MainApplicationWindow instance"):
            FileHandlers(invalid_window)

    @patch("src.gui.handlers.file_handlers.QFileDialog")
    def test_prompt_for_document_file_selected(self, mock_dialog, file_handlers, mock_main_window):
        """Test file selection dialog when user selects a file."""
        # Setup
        test_file_path = "/path/to/test/document.pdf"
        mock_dialog.getOpenFileName.return_value = (test_file_path, "PDF files (*.pdf)")
        file_handlers.set_selected_file = Mock()

        # Execute
        file_handlers.prompt_for_document()

        # Verify
        mock_dialog.getOpenFileName.assert_called_once_with(
            mock_main_window, "Select clinical document", str(Path.home()), "Documents (*.pdf *.docx *.txt *.md *.json)"
        )
        file_handlers.set_selected_file.assert_called_once_with(Path(test_file_path))

    @patch("src.gui.handlers.file_handlers.QFileDialog")
    def test_prompt_for_document_no_file_selected(self, mock_dialog, file_handlers):
        """Test file selection dialog when user cancels."""
        # Setup
        mock_dialog.getOpenFileName.return_value = ("", "")
        file_handlers.set_selected_file = Mock()

        # Execute
        file_handlers.prompt_for_document()

        # Verify
        file_handlers.set_selected_file.assert_not_called()

    def test_set_selected_file_success(self, file_handlers, mock_main_window):
        """Test successful file selection and content loading."""
        # Setup
        test_file_path = Path("/path/to/test.txt")
        test_content = "This is test document content for compliance analysis."

        # Mock file stats to avoid FileNotFoundError
        mock_stat = Mock()
        mock_stat.st_mtime = 1640995200  # Fixed timestamp

        with (
            patch("builtins.open", mock_open(read_data=test_content)),
            patch("pathlib.Path.stat", return_value=mock_stat),
        ):
            # Execute
            file_handlers.set_selected_file(test_file_path)

            # Verify
            assert mock_main_window._selected_file == test_file_path
            assert mock_main_window._cached_preview_content == test_content
            # Should be called twice: first False (disable), then True (enable after success)
            assert mock_main_window.run_analysis_button.setEnabled.call_count == 2
            mock_main_window.run_analysis_button.setEnabled.assert_any_call(False)
            mock_main_window.run_analysis_button.setEnabled.assert_called_with(True)

    def test_set_selected_file_not_found(self, file_handlers, mock_main_window):
        """Test file selection when file doesn't exist."""
        # Setup
        test_file_path = Path("/path/to/nonexistent.txt")

        with patch("builtins.open", side_effect=FileNotFoundError()):
            # Execute
            file_handlers.set_selected_file(test_file_path)

            # Verify
            assert mock_main_window._selected_file == test_file_path
            assert "Preview unavailable" in mock_main_window._cached_preview_content
            mock_main_window.statusBar().showMessage.assert_called_with(f"File not found: {test_file_path.name}", 5000)

    def test_set_selected_file_large_content_truncation(self, file_handlers, mock_main_window):
        """Test content truncation for very large files."""
        # Setup
        test_file_path = Path("/path/to/large.txt")
        large_content = "x" * 3_000_000  # 3MB of content

        # Mock file stats to avoid FileNotFoundError
        mock_stat = Mock()
        mock_stat.st_mtime = 1640995200  # Fixed timestamp

        with (
            patch("builtins.open", mock_open(read_data=large_content)),
            patch("pathlib.Path.stat", return_value=mock_stat),
        ):
            # Execute
            file_handlers.set_selected_file(test_file_path)

            # Verify content was truncated to 2MB limit
            assert len(mock_main_window._cached_preview_content) == 2_000_000

    def test_set_selected_file_encoding_error_handling(self, file_handlers, mock_main_window):
        """Test handling of files with encoding issues."""
        # Setup
        test_file_path = Path("/path/to/binary.pdf")
        binary_content = b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a"  # PNG header bytes

        # Mock file stats to avoid FileNotFoundError
        mock_stat = Mock()
        mock_stat.st_mtime = 1640995200  # Fixed timestamp

        # Mock open to return binary content that will cause encoding issues
        mock_file = mock_open(read_data=binary_content.decode("utf-8", errors="ignore"))

        with patch("builtins.open", mock_file), patch("pathlib.Path.stat", return_value=mock_stat):
            # Execute
            file_handlers.set_selected_file(test_file_path)

            # Verify it handles encoding errors gracefully
            assert mock_main_window._selected_file == test_file_path
            # Content should be loaded with errors ignored
            assert mock_main_window._cached_preview_content is not None


class TestFileHandlersIntegration:
    """Integration tests for FileHandlers with real file operations."""

    @pytest.fixture(scope="class")
    def qapp(self):
        """Create QApplication for integration tests."""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app

    @pytest.fixture
    def temp_file(self, tmp_path):
        """Create a temporary test file."""
        test_file = tmp_path / "test_document.txt"
        test_content = """
        Patient: John Doe
        Date: 2024-01-15

        Progress Note:
        Patient demonstrates improved range of motion in left shoulder.
        Continuing with current treatment plan.
        """
        test_file.write_text(test_content)
        return test_file

    def test_real_file_loading(self, qapp, temp_file):
        """Test loading a real file with actual file I/O."""
        # Create real main window
        main_window = QMainWindow()
        main_window.statusBar()  # Initialize status bar
        main_window.run_analysis_button = Mock()
        main_window.file_display = Mock()  # Add missing file_display attribute
        main_window._selected_file = None
        main_window._cached_preview_content = ""

        # Create handlers
        handlers = FileHandlers(main_window)

        # Execute
        handlers.set_selected_file(temp_file)

        # Verify
        assert main_window._selected_file == temp_file
        assert "Patient: John Doe" in main_window._cached_preview_content
        assert "Progress Note:" in main_window._cached_preview_content

    def test_file_dialog_integration(self, qapp):
        """Test file dialog integration without actually opening dialog."""
        # Create real main window
        main_window = QMainWindow()
        main_window.statusBar()  # Initialize status bar

        # Create handlers
        handlers = FileHandlers(main_window)

        # Mock the dialog to avoid actually opening it
        with patch("src.gui.handlers.file_handlers.QFileDialog") as mock_dialog:
            mock_dialog.getOpenFileName.return_value = ("", "")  # User cancels

            # This should not crash
            handlers.prompt_for_document()

            # Verify dialog was configured correctly
            mock_dialog.getOpenFileName.assert_called_once()
            call_args = mock_dialog.getOpenFileName.call_args[0]
            assert call_args[0] == main_window  # Parent window
            assert "Select clinical document" in call_args[1]  # Dialog title
            assert "Documents" in call_args[3]  # File filter
