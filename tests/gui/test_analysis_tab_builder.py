"""
Comprehensive tests for the AnalysisTabBuilder class.

This module tests the construction and configuration of the Analysis tab
including all UI components, layout management, and event handling setup.
"""

from unittest.mock import Mock, patch

import pytest
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

from src.gui.components.analysis_tab_builder import AnalysisTabBuilder


class TestAnalysisTabBuilder:
    """Test suite for AnalysisTabBuilder class."""

    @pytest.fixture
    def mock_main_window(self):
        """Create a mock main window for testing."""
        mock_window = Mock(spec=QMainWindow)
        mock_window.statusBar.return_value = Mock()

        # Mock UI components that the builder will create/reference
        mock_window.rubric_selector = Mock()
        mock_window.strictness_buttons = []
        mock_window.strictness_levels = []
        mock_window.strictness_description = Mock()
        mock_window.section_checkboxes = {}
        mock_window.file_display = Mock()
        mock_window.open_file_button = Mock()
        mock_window.open_folder_button = Mock()
        mock_window.run_analysis_button = Mock()
        mock_window.repeat_analysis_button = Mock()
        mock_window.stop_analysis_button = Mock()
        mock_window.view_report_button = Mock()
        mock_window.analysis_summary_browser = Mock()
        mock_window.detailed_results_browser = Mock()

        # Mock handler methods
        mock_window._prompt_for_document = Mock()
        mock_window._prompt_for_folder = Mock()
        mock_window._start_analysis = Mock()
        mock_window._repeat_analysis = Mock()
        mock_window._stop_analysis = Mock()
        mock_window._open_report_popup = Mock()
        mock_window._export_report_pdf = Mock()
        mock_window._export_report_html = Mock()
        mock_window._handle_report_link = Mock()
        mock_window._on_strictness_selected_with_description = Mock()
        mock_window._update_strictness_description = Mock()

        return mock_window

    @pytest.fixture
    def tab_builder(self, mock_main_window):
        """Create AnalysisTabBuilder instance with mock main window."""
        return AnalysisTabBuilder(mock_main_window)

    def test_initialization_success(self, mock_main_window):
        """Test successful initialization of AnalysisTabBuilder."""
        builder = AnalysisTabBuilder(mock_main_window)
        assert builder.main_window == mock_main_window

    def test_initialization_invalid_window(self):
        """Test initialization with invalid main window raises TypeError."""
        invalid_window = Mock()
        # Remove statusBar attribute to make it invalid
        del invalid_window.statusBar

        with pytest.raises(TypeError, match="main_window must be a valid MainApplicationWindow instance"):
            AnalysisTabBuilder(invalid_window)

    @patch("src.gui.components.analysis_tab_builder.medical_theme")
    @patch("src.gui.components.analysis_tab_builder.QWidget")
    @patch("src.gui.components.analysis_tab_builder.QHBoxLayout")
    def test_create_analysis_tab_structure(self, mock_layout, mock_widget, mock_theme, tab_builder, mock_main_window):
        """Test that create_analysis_tab creates the correct structure."""
        # Setup mocks
        mock_tab = Mock()
        mock_widget.return_value = mock_tab
        mock_layout_instance = Mock()
        mock_layout.return_value = mock_layout_instance

        # Mock the panel creation methods
        tab_builder._create_rubric_selection_panel = Mock(return_value=Mock())
        tab_builder._create_middle_column_panel = Mock(return_value=Mock())
        tab_builder._create_analysis_results_with_chat = Mock(return_value=Mock())

        # Execute
        result = tab_builder.create_analysis_tab()

        # Verify structure
        assert result == mock_tab
        mock_widget.assert_called_once_with(mock_main_window)
        mock_layout.assert_called_once_with(mock_tab)

        # Verify layout configuration
        mock_layout_instance.setContentsMargins.assert_called_once_with(15, 15, 15, 15)
        mock_layout_instance.setSpacing.assert_called_once_with(15)

        # Verify panels are created and added
        tab_builder._create_rubric_selection_panel.assert_called_once()
        tab_builder._create_middle_column_panel.assert_called_once()
        tab_builder._create_analysis_results_with_chat.assert_called_once()

        # Verify panels are added with correct stretch factors
        assert mock_layout_instance.addWidget.call_count == 3

        # Check stretch factors in the calls
        calls = mock_layout_instance.addWidget.call_args_list
        assert calls[0][1]["stretch"] == 25  # Left column
        assert calls[1][1]["stretch"] == 30  # Middle column
        assert calls[2][1]["stretch"] == 45  # Right column

    @patch("src.gui.components.analysis_tab_builder.medical_theme")
    def test_create_rubric_selection_panel(self, mock_theme, tab_builder, mock_main_window):
        """Test creation of rubric selection panel."""
        # Setup theme mock
        mock_theme.get_color.return_value = "#ffffff"

        # Mock the sub-panel creation methods
        tab_builder._create_document_upload_section = Mock(return_value=Mock())
        tab_builder._create_rubric_selector_section = Mock(return_value=Mock())
        tab_builder._create_action_buttons_section = Mock(return_value=Mock())

        # Execute
        with (
            patch("src.gui.components.analysis_tab_builder.QWidget") as mock_widget,
            patch("src.gui.components.analysis_tab_builder.QVBoxLayout") as mock_layout,
        ):
            mock_panel = Mock()
            mock_widget.return_value = mock_panel
            mock_layout_instance = Mock()
            mock_layout.return_value = mock_layout_instance

            result = tab_builder._create_rubric_selection_panel()

            # Verify panel creation
            assert result == mock_panel
            mock_widget.assert_called_once_with(mock_main_window)

            # Verify layout configuration
            mock_layout_instance.setContentsMargins.assert_called_once_with(0, 0, 0, 0)
            mock_layout_instance.setSpacing.assert_called_once_with(15)

            # Verify sub-sections are created and added
            tab_builder._create_document_upload_section.assert_called_once()
            tab_builder._create_rubric_selector_section.assert_called_once()
            tab_builder._create_action_buttons_section.assert_called_once()

            # Verify addStretch is called for proper spacing
            mock_layout_instance.addStretch.assert_called_once_with(1)

    @patch("src.gui.components.analysis_tab_builder.medical_theme")
    @patch("src.gui.components.analysis_tab_builder.QComboBox")
    @patch("src.gui.components.analysis_tab_builder.QLabel")
    def test_create_rubric_selector_section(self, mock_label, mock_combo, mock_theme, tab_builder, mock_main_window):
        """Test creation of rubric selector section."""
        # Setup theme mock
        mock_theme.get_color.return_value = "#ffffff"

        # Setup component mocks
        mock_combo_instance = Mock()
        mock_combo.return_value = mock_combo_instance
        mock_label_instance = Mock()
        mock_label.return_value = mock_label_instance

        # Execute
        with (
            patch("src.gui.components.analysis_tab_builder.QWidget") as mock_widget,
            patch("src.gui.components.analysis_tab_builder.QVBoxLayout") as mock_layout,
        ):
            mock_section = Mock()
            mock_widget.return_value = mock_section
            mock_layout_instance = Mock()
            mock_layout.return_value = mock_layout_instance

            result = tab_builder._create_rubric_selector_section()

            # Verify section creation
            assert result == mock_section

            # Verify rubric selector is created and configured
            mock_combo.assert_called_once_with(mock_section)
            mock_combo_instance.setMinimumHeight.assert_called_once_with(40)

            # Verify the combo box is assigned to main window
            assert mock_main_window.rubric_selector == mock_combo_instance

            # Verify label creation
            mock_label.assert_called_once_with("📚 Select Rubric", mock_section)

    def test_create_middle_column_panel(self, tab_builder, mock_main_window):
        """Test creation of middle column panel."""
        # Mock the sub-panel creation methods
        tab_builder._create_compliance_guidelines_section = Mock(return_value=Mock())
        tab_builder._create_report_sections_panel = Mock(return_value=Mock())

        # Execute
        with (
            patch("src.gui.components.analysis_tab_builder.QWidget") as mock_widget,
            patch("src.gui.components.analysis_tab_builder.QVBoxLayout") as mock_layout,
        ):
            mock_panel = Mock()
            mock_widget.return_value = mock_panel
            mock_layout_instance = Mock()
            mock_layout.return_value = mock_layout_instance

            result = tab_builder._create_middle_column_panel()

            # Verify panel creation
            assert result == mock_panel

            # Verify layout configuration
            mock_layout_instance.setContentsMargins.assert_called_once_with(0, 0, 0, 0)
            mock_layout_instance.setSpacing.assert_called_once_with(15)

            # Verify sub-sections are created and added with stretch
            tab_builder._create_compliance_guidelines_section.assert_called_once()
            tab_builder._create_report_sections_panel.assert_called_once()

            # Verify both sections are added with stretch factor 1
            assert mock_layout_instance.addWidget.call_count == 2
            calls = mock_layout_instance.addWidget.call_args_list
            assert calls[0][1]["stretch"] == 1
            assert calls[1][1]["stretch"] == 1


class TestAnalysisTabBuilderIntegration:
    """Integration tests for AnalysisTabBuilder with real Qt components."""

    @pytest.fixture(scope="class")
    def qapp(self):
        """Create QApplication for integration tests."""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app

    def test_tab_creation_integration(self, qapp):
        """Test tab creation with real Qt components."""
        # Create real main window
        main_window = QMainWindow()
        main_window.statusBar()  # Initialize status bar

        # Initialize required attributes
        main_window.rubric_selector = None
        main_window.strictness_buttons = []
        main_window.strictness_levels = []
        main_window.strictness_description = None
        main_window.section_checkboxes = {}

        # Mock handler methods to avoid dependencies
        main_window._prompt_for_document = Mock()
        main_window._prompt_for_folder = Mock()
        main_window._start_analysis = Mock()
        main_window._repeat_analysis = Mock()
        main_window._stop_analysis = Mock()
        main_window._open_report_popup = Mock()
        main_window._export_report_pdf = Mock()
        main_window._export_report_html = Mock()
        main_window._handle_report_link = Mock()
        main_window._on_strictness_selected_with_description = Mock()
        main_window._update_strictness_description = Mock()

        # Create builder
        builder = AnalysisTabBuilder(main_window)

        # This should create a real widget without crashing
        with patch("src.gui.components.analysis_tab_builder.medical_theme") as mock_theme:
            mock_theme.get_color.return_value = "#ffffff"
            mock_theme.get_button_stylesheet.return_value = "QPushButton { background: white; }"

            tab = builder.create_analysis_tab()

            # Verify it's a real QWidget
            assert isinstance(tab, QWidget)

            # Verify main window attributes were set
            assert main_window.rubric_selector is not None
            assert isinstance(main_window.strictness_buttons, list)
            assert isinstance(main_window.section_checkboxes, dict)
