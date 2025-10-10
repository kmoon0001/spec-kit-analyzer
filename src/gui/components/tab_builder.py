"""Tab builder for the main application window - Refactored for maintainability."""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

from src.gui.widgets.dashboard_widget import DashboardWidget
from src.gui.widgets.mission_control_widget import MissionControlWidget

from .analysis_tab_builder import AnalysisTabBuilder
from .settings_tab_builder import SettingsTabBuilder

if TYPE_CHECKING:
    from src.gui.main_window import MainApplicationWindow


class TabBuilder:
    """Builds tabs for the main application window using specialized builders."""

    def __init__(self, main_window: MainApplicationWindow) -> None:
        self.main_window = main_window
        self.analysis_builder = AnalysisTabBuilder(main_window)
        self.settings_builder = SettingsTabBuilder(main_window)

    def create_analysis_tab(self) -> QWidget:
        """Create the Analysis tab using specialized builder."""
        return self.analysis_builder.create_analysis_tab()

    def create_settings_tab(self) -> QWidget:
        """Create the Settings tab using specialized builder."""
        return self.settings_builder.create_settings_tab()

    def create_dashboard_tab(self) -> QWidget:
        """Create the Dashboard tab."""
        tab = QWidget(self.main_window)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        try:
            self.main_window.dashboard_widget = DashboardWidget()
            self.main_window.dashboard_widget.refresh_requested.connect(self.main_window.view_model.load_dashboard_data)
        except (ImportError, NameError):
            self.main_window.dashboard_widget = QTextBrowser()
            self.main_window.dashboard_widget.setPlainText("Dashboard component unavailable.")
        layout.addWidget(self.main_window.dashboard_widget)
        return tab

    def create_mission_control_tab(self) -> QWidget:
        """Create the Mission Control tab."""
        tab = QWidget(self.main_window)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.main_window.mission_control_widget = MissionControlWidget(tab)
        self.main_window.mission_control_widget.start_analysis_requested.connect(self.main_window._handle_mission_control_start)
        self.main_window.mission_control_widget.review_document_requested.connect(self.main_window._handle_mission_control_review)
        layout.addWidget(self.main_window.mission_control_widget)
        return tab
