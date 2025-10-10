"""Settings tab builder - extracted from tab_builder for better maintainability."""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QScrollArea, QTabWidget, QVBoxLayout, QWidget

from src.gui.widgets.medical_theme import medical_theme
from src.gui.widgets.micro_interactions import AnimatedButton
from src.gui.widgets.mission_control_widget import SettingsEditorWidget

if TYPE_CHECKING:
    from src.gui.main_window import MainApplicationWindow


class SettingsTabBuilder:
    """Builds the Settings tab and its components."""

    def __init__(self, main_window: MainApplicationWindow) -> None:
        self.main_window = main_window

    def create_settings_tab(self) -> QWidget:
        """Create the Settings tab with comprehensive options."""
        tab = QWidget(self.main_window)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title
        title = QLabel("⚙️ Application Settings", tab)
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {medical_theme.get_color('primary_blue')};")
        layout.addWidget(title)

        # Settings tabs
        settings_tabs = QTabWidget(tab)
        settings_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 8px;
                background: {medical_theme.get_color('bg_secondary')};
            }}
            QTabBar::tab {{
                padding: 10px 20px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                background: {medical_theme.get_color('bg_tertiary')};
                color: {medical_theme.get_color('text_secondary')};
            }}
            QTabBar::tab:selected {{
                background: {medical_theme.get_color('primary_blue')};
                color: white;
            }}
        """)

        # User Preferences
        user_prefs_widget = self._create_user_preferences_widget()
        settings_tabs.addTab(user_prefs_widget, "👤 User Preferences")

        # Analysis Settings
        analysis_settings_widget = self._create_analysis_settings_widget()
        settings_tabs.addTab(analysis_settings_widget, "📊 Analysis Settings")

        # Report Settings
        report_settings_widget = self._create_report_settings_widget()
        settings_tabs.addTab(report_settings_widget, "📄 Report Settings")

        # Performance Settings
        perf_widget = self._create_performance_settings_widget()
        settings_tabs.addTab(perf_widget, "⚡ Performance")

        # Admin Settings (if admin)
        if self.main_window.current_user.is_admin:
            self.main_window.settings_editor = SettingsEditorWidget(tab)
            self.main_window.settings_editor.save_requested.connect(self.main_window.view_model.save_settings)
            settings_tabs.addTab(self.main_window.settings_editor, "🔧 Advanced (Admin)")

        layout.addWidget(settings_tabs)
        return tab

    def _create_user_preferences_widget(self) -> QWidget:
        """Create user preferences settings widget."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(25)

        # Theme selection
        theme_section = self._create_theme_section()
        layout.addWidget(theme_section)

        # Account settings
        account_section = self._create_account_section()
        layout.addWidget(account_section)

        # UI Preferences
        ui_section = self._create_ui_preferences_section()
        layout.addWidget(ui_section)

        layout.addStretch()
        scroll_area.setWidget(widget)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(scroll_area)

        return container

    def _create_theme_section(self) -> QWidget:
        """Create theme selection section."""
        theme_section = QWidget()
        theme_section.setStyleSheet(f"""
            QWidget {{
                background: {medical_theme.get_color('bg_primary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        theme_layout = QVBoxLayout(theme_section)
        theme_layout.setContentsMargins(20, 20, 20, 20)
        theme_layout.setSpacing(15)

        theme_label = QLabel("🎨 Theme Selection", theme_section)
        theme_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        theme_label.setStyleSheet("margin-bottom: 10px;")
        theme_layout.addWidget(theme_label)

        theme_buttons = QHBoxLayout()
        light_button = AnimatedButton("☀️ Light Theme", theme_section)
        light_button.clicked.connect(lambda: self.main_window._apply_theme("light"))
        light_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        light_button.setMinimumHeight(40)
        theme_buttons.addWidget(light_button)

        dark_button = AnimatedButton("🌙 Dark Theme", theme_section)
        dark_button.clicked.connect(lambda: self.main_window._apply_theme("dark"))
        dark_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        dark_button.setMinimumHeight(40)
        theme_buttons.addWidget(dark_button)

        theme_layout.addLayout(theme_buttons)
        return theme_section

    def _create_account_section(self) -> QWidget:
        """Create account settings section."""
        account_section = QWidget()
        account_section.setStyleSheet(f"""
            QWidget {{
                background: {medical_theme.get_color('bg_primary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        account_layout = QVBoxLayout(account_section)
        account_layout.setContentsMargins(20, 20, 20, 20)
        account_layout.setSpacing(15)

        account_label = QLabel("👤 Account Settings", account_section)
        account_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        account_label.setStyleSheet("margin-bottom: 10px;")
        account_layout.addWidget(account_label)

        user_info = QLabel(f"Logged in as: {self.main_window.current_user.username}", account_section)
        user_info.setStyleSheet("color: #64748b; padding: 5px;")
        account_layout.addWidget(user_info)

        password_button = AnimatedButton("🔒 Change Password", account_section)
        password_button.clicked.connect(self.main_window.show_change_password_dialog)
        password_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        password_button.setMinimumHeight(40)
        account_layout.addWidget(password_button)

        return account_section

    def _create_ui_preferences_section(self) -> QWidget:
        """Create UI preferences section."""
        ui_section = QWidget()
        ui_section.setStyleSheet(f"""
            QWidget {{
                background: {medical_theme.get_color('bg_primary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        ui_layout = QVBoxLayout(ui_section)

        ui_label = QLabel("🖥️ Interface Preferences", ui_section)
        ui_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        ui_layout.addWidget(ui_label)

        show_tooltips = QCheckBox("Show helpful tooltips", ui_section)
        show_tooltips.setChecked(True)
        ui_layout.addWidget(show_tooltips)

        auto_save = QCheckBox("Auto-save analysis results", ui_section)
        auto_save.setChecked(True)
        ui_layout.addWidget(auto_save)

        show_animations = QCheckBox("Enable button animations", ui_section)
        show_animations.setChecked(True)
        ui_layout.addWidget(show_animations)

        return ui_section

    def _create_analysis_settings_widget(self) -> QWidget:
        """Create analysis settings widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        section = QWidget()
        section.setStyleSheet(f"""
            QWidget {{
                background: {medical_theme.get_color('bg_primary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        section_layout = QVBoxLayout(section)

        title = QLabel("📊 Default Analysis Settings", section)
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        section_layout.addWidget(title)

        auto_analyze = QCheckBox("Auto-analyze on document upload", section)
        section_layout.addWidget(auto_analyze)

        include_7habits = QCheckBox("Include 7 Habits Framework in reports", section)
        include_7habits.setChecked(True)
        section_layout.addWidget(include_7habits)

        include_education = QCheckBox("Include educational resources", section)
        include_education.setChecked(True)
        section_layout.addWidget(include_education)

        show_confidence = QCheckBox("Show AI confidence scores", section)
        show_confidence.setChecked(True)
        section_layout.addWidget(show_confidence)

        layout.addWidget(section)
        layout.addStretch()
        return widget

    def _create_report_settings_widget(self) -> QWidget:
        """Create report settings widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        section = QWidget()
        section.setStyleSheet(f"""
            QWidget {{
                background: {medical_theme.get_color('bg_primary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        section_layout = QVBoxLayout(section)

        title = QLabel("📄 Report Content Settings", section)
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        section_layout.addWidget(title)

        # Add checkboxes with descriptions
        checkboxes_with_descriptions = [
            ("✅ Medicare Guidelines Compliance", "Includes CMS compliance requirements and Medicare documentation standards", True),
            ("💪 Strengths & Best Practices", "Highlights well-documented areas and exemplary practices", True),
            ("⚠️ Weaknesses & Areas for Improvement", "Identifies documentation gaps and areas that need attention", True),
            ("💡 Actionable Suggestions", "Provides specific, implementable recommendations", True),
            ("📚 Educational Resources", "Includes links to relevant guidelines and training materials", True),
            ("🎯 7 Habits Framework Integration", "Incorporates professional development strategies", True),
            ("📊 Compliance Score & Risk Level", "Shows overall compliance percentage and risk assessment", True),
            ("🔍 Detailed Findings Analysis", "Comprehensive breakdown of all compliance issues", True)
        ]

        for checkbox_text, description, checked in checkboxes_with_descriptions:
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(5)

            checkbox = QCheckBox(checkbox_text, section)
            checkbox.setChecked(checked)
            container_layout.addWidget(checkbox)

            desc_label = QLabel(f"   {description}")
            desc_label.setStyleSheet("color: #64748b; font-size: 11px; margin-left: 20px;")
            desc_label.setWordWrap(True)
            container_layout.addWidget(desc_label)

            section_layout.addWidget(container)

        layout.addWidget(section)
        layout.addStretch()
        return widget

    def _create_performance_settings_widget(self) -> QWidget:
        """Create performance settings widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        section = QWidget()
        section.setStyleSheet(f"""
            QWidget {{
                background: {medical_theme.get_color('bg_primary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        section_layout = QVBoxLayout(section)

        title = QLabel("⚡ Performance Settings", section)
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        section_layout.addWidget(title)

        enable_cache = QCheckBox("Enable analysis caching", section)
        enable_cache.setChecked(True)
        section_layout.addWidget(enable_cache)

        parallel_processing = QCheckBox("Enable parallel processing", section)
        parallel_processing.setChecked(True)
        section_layout.addWidget(parallel_processing)

        auto_cleanup = QCheckBox("Auto-cleanup temporary files", section)
        auto_cleanup.setChecked(True)
        section_layout.addWidget(auto_cleanup)

        layout.addWidget(section)

        info_label = QLabel("💡 Tip: Enable caching for faster repeated analyses", widget)
        info_label.setStyleSheet("color: #64748b; font-style: italic; padding: 10px;")
        layout.addWidget(info_label)

        layout.addStretch()
        return widget
