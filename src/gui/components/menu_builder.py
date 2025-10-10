"""Menu builder for the main application window."""

from __future__ import annotations

import webbrowser
from typing import TYPE_CHECKING

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu

if TYPE_CHECKING:
    from src.gui.main_window import MainApplicationWindow


class MenuBuilder:
    """Builds menus for the main application window."""

    def __init__(self, main_window: MainApplicationWindow) -> None:
        self.main_window = main_window

    def build_all_menus(self) -> None:
        """Build all menus for the application."""
        menu_bar = self.main_window.menuBar()
        self._build_file_menu(menu_bar)
        self._build_view_menu(menu_bar)
        self._build_tools_menu(menu_bar)
        self._build_admin_menu(menu_bar)
        self._build_help_menu(menu_bar)

    def _build_file_menu(self, menu_bar) -> None:
        file_menu = menu_bar.addMenu("&File")
        open_file_action = QAction("Open Document…", self.main_window)
        open_file_action.triggered.connect(self.main_window._prompt_for_document)
        file_menu.addAction(open_file_action)
        open_folder_action = QAction("Open Folder…", self.main_window)
        open_folder_action.triggered.connect(self.main_window._prompt_for_folder)
        file_menu.addAction(open_folder_action)
        file_menu.addSeparator()
        export_action = QAction("Export Report…", self.main_window)
        export_action.triggered.connect(self.main_window._export_report)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self.main_window)
        exit_action.triggered.connect(self.main_window.close)
        file_menu.addAction(exit_action)

    def _build_view_menu(self, menu_bar) -> None:
        view_menu = menu_bar.addMenu("&View")

        # Optional docks (hidden by default)
        if self.main_window.performance_dock:
            view_menu.addAction(self.main_window.performance_dock.toggleViewAction())

        view_menu.addSeparator()

        # Theme submenu
        theme_menu = QMenu("Theme", self.main_window)

        light_action = QAction("Light Theme", self.main_window)
        light_action.triggered.connect(lambda: self.main_window._apply_theme("light"))
        theme_menu.addAction(light_action)

        dark_action = QAction("Dark Theme", self.main_window)
        dark_action.triggered.connect(lambda: self.main_window._apply_theme("dark"))
        theme_menu.addAction(dark_action)

        theme_menu.addSeparator()
        toggle_action = QAction("🔄 Toggle Theme", self.main_window)
        toggle_action.setShortcut("Ctrl+T")
        toggle_action.triggered.connect(self.main_window._toggle_theme)
        theme_menu.addAction(toggle_action)

        view_menu.addMenu(theme_menu)

    def _build_tools_menu(self, menu_bar) -> None:
        tools_menu = menu_bar.addMenu("&Tools")

        # Meta Analytics
        try:
            from src.gui.widgets.meta_analytics_widget import MetaAnalyticsWidget

            if MetaAnalyticsWidget:
                meta_action = QAction("Meta Analytics", self.main_window, checkable=True)
                meta_action.setShortcut("Ctrl+Shift+A")
                meta_action.triggered.connect(self.main_window._toggle_meta_analytics_dock)
                tools_menu.addAction(meta_action)
                self.main_window.meta_analytics_action = meta_action
        except ImportError:
            pass

        # Performance Status
        try:
            from src.gui.widgets.performance_status_widget import PerformanceStatusWidget

            if PerformanceStatusWidget:
                perf_action = QAction("Performance Status", self.main_window, checkable=True)
                perf_action.setShortcut("Ctrl+Shift+P")
                perf_action.triggered.connect(self.main_window._toggle_performance_dock)
                tools_menu.addAction(perf_action)
                self.main_window.performance_action = perf_action
        except ImportError:
            pass

        tools_menu.addSeparator()

        # Refresh
        refresh_action = QAction("🔄 Refresh All Data", self.main_window)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.main_window._load_initial_state)
        tools_menu.addAction(refresh_action)

        # Clear Cache
        clear_cache_action = QAction("🗑️ Clear Cache", self.main_window)
        clear_cache_action.triggered.connect(self.main_window._clear_all_caches)
        tools_menu.addAction(clear_cache_action)

        tools_menu.addSeparator()

        # Diagnostic Tools
        diagnostic_action = QAction("🔍 Run Diagnostics", self.main_window)
        diagnostic_action.triggered.connect(self.main_window._run_diagnostics)
        tools_menu.addAction(diagnostic_action)

        start_api_action = QAction("🚀 Start API Server", self.main_window)
        start_api_action.triggered.connect(self.main_window._start_api_server)
        tools_menu.addAction(start_api_action)

    def _build_admin_menu(self, menu_bar) -> None:
        admin_menu = menu_bar.addMenu("&Admin")

        # Non-critical features available to all users
        # Change Password (all users need this)
        password_action = QAction("Change Password", self.main_window)
        password_action.triggered.connect(self.main_window.show_change_password_dialog)
        admin_menu.addAction(password_action)

        # Settings (all users need this)
        settings_action = QAction("Settings…", self.main_window)
        settings_action.triggered.connect(self.main_window._open_settings_dialog)
        admin_menu.addAction(settings_action)

        # System Info (informational, safe for all users)
        system_info_action = QAction("System Information", self.main_window)
        system_info_action.triggered.connect(self.main_window._show_system_info)
        admin_menu.addAction(system_info_action)

        # CRITICAL ADMIN-ONLY FEATURES (keep protected)
        if self.main_window.current_user.is_admin:
            admin_menu.addSeparator()

            # Rubric Management (ADMIN ONLY - affects compliance rules)
            rubrics_action = QAction("Manage Rubrics… (Admin)", self.main_window)
            rubrics_action.triggered.connect(self.main_window._open_rubric_manager)
            admin_menu.addAction(rubrics_action)

            # User Management (ADMIN ONLY - security critical)
            users_action = QAction("Manage Users (Admin)", self.main_window)
            users_action.triggered.connect(self.main_window._show_user_management)
            admin_menu.addAction(users_action)

    def _build_help_menu(self, menu_bar) -> None:
        help_menu = menu_bar.addMenu("&Help")
        docs_action = QAction("Open Documentation", self.main_window)
        docs_action.triggered.connect(lambda: webbrowser.open("https://github.com/your-username/your-repo-name"))
        help_menu.addAction(docs_action)
        about_action = QAction("About", self.main_window)
        about_action.triggered.connect(self.main_window._show_about_dialog)
        help_menu.addAction(about_action)
