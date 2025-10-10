"""Tab builder for the main application window."""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QLabel, QScrollArea,
    QSizePolicy, QTabWidget, QTextBrowser, QTextEdit, QVBoxLayout, QWidget
)

from src.gui.widgets.medical_theme import medical_theme
from src.gui.widgets.micro_interactions import AnimatedButton
from src.gui.widgets.mission_control_widget import MissionControlWidget, SettingsEditorWidget
from src.gui.widgets.dashboard_widget import DashboardWidget

if TYPE_CHECKING:
    from src.gui.main_window import MainApplicationWindow


class TabBuilder:
    """Builds tabs for the main application window."""
    
    def __init__(self, main_window: MainApplicationWindow) -> None:
        self.main_window = main_window
    
    def create_analysis_tab(self) -> QWidget:
        """Create the Analysis tab with improved layout and scaling."""
        tab = QWidget(self.main_window)
        main_layout = QHBoxLayout(tab)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Left column: Rubric Selection (25%)
        left_column = self._create_rubric_selection_panel()
        main_layout.addWidget(left_column, stretch=25)
        
        # Middle column: Compliance Guidelines & Report Sections (30%)
        middle_column = self._create_middle_column_panel()
        main_layout.addWidget(middle_column, stretch=30)
        
        # Right column: Analysis Results with Chat (45%)
        right_column = self._create_analysis_results_with_chat()
        main_layout.addWidget(right_column, stretch=45)
        
        return tab
    
    def _create_rubric_selection_panel(self) -> QWidget:
        """Create left panel with rubric selection and document upload."""
        panel = QWidget(self.main_window)
        panel.setMinimumWidth(280)
        panel.setMaximumWidth(400)
        panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Document Upload Section
        upload_section = self._create_document_upload_section()
        layout.addWidget(upload_section)
        
        # Rubric Selection Section (moved here from middle)
        rubric_section = self._create_rubric_selector_section()
        layout.addWidget(rubric_section)
        
        # Action Buttons
        actions_section = self._create_action_buttons_section()
        layout.addWidget(actions_section)
        
        layout.addStretch(1)
        return panel
    
    def _create_rubric_selector_section(self) -> QWidget:
        """Create rubric selector section."""
        section = QWidget(self.main_window)
        section.setStyleSheet(f"""
            QWidget {{
                background-color: {medical_theme.get_color("bg_secondary")};
                border: 2px solid {medical_theme.get_color("border_light")};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("📚 Select Rubric", section)
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {medical_theme.get_color('primary_blue')}; background: transparent; border: none;")
        layout.addWidget(title)
        
        # Rubric selector
        self.main_window.rubric_selector = QComboBox(section)
        self.main_window.rubric_selector.setMinimumHeight(40)
        self.main_window.rubric_selector.setStyleSheet(f"""
            QComboBox {{
                padding: 10px 12px;
                border: 2px solid {medical_theme.get_color('border_medium')};
                border-radius: 8px;
                background: white;
                font-size: 11px;
                font-weight: 500;
                color: {medical_theme.get_color('text_primary')};
            }}
            QComboBox:hover {{
                border-color: {medical_theme.get_color('primary_blue')};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 35px;
            }}
        """)
        layout.addWidget(self.main_window.rubric_selector)
        
        return section
    
    def _create_middle_column_panel(self) -> QWidget:
        """Create middle panel with compliance guidelines and report sections."""
        panel = QWidget(self.main_window)
        panel.setMinimumWidth(300)
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Compliance Guidelines Section (moved from left, above report sections)
        guidelines_section = self._create_compliance_guidelines_section()
        layout.addWidget(guidelines_section, stretch=1)
        
        # Report Sections (moved from middle)
        report_section = self._create_report_sections_panel()
        layout.addWidget(report_section, stretch=1)
        
        return panel
    
    def _create_compliance_guidelines_section(self) -> QWidget:
        """Create compliance guidelines section with smaller buttons."""
        section = QWidget(self.main_window)
        section.setStyleSheet(f"""
            QWidget {{
                background-color: {medical_theme.get_color("bg_secondary")};
                border: 2px solid {medical_theme.get_color("border_light")};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("⚙️ Review Strictness", section)
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {medical_theme.get_color('primary_blue')}; background: transparent; border: none;")
        layout.addWidget(title)
        
        # Strictness buttons (smaller)
        strictness_layout = QHBoxLayout()
        strictness_layout.setSpacing(8)
        self.main_window.strictness_buttons = []
        
        # Strictness definitions with detailed descriptions
        self.main_window.strictness_levels = [
            ("Lenient", "😊", {
                "description": "Lenient analysis focusing on major compliance issues only",
                "details": "• Identifies critical Medicare violations\n• Overlooks minor documentation gaps\n• Faster processing time\n• Suitable for initial reviews",
                "use_case": "Best for: Quick assessments, high-volume processing"
            }),
            ("Standard", "📋", {
                "description": "Balanced analysis covering most compliance requirements", 
                "details": "• Comprehensive Medicare compliance checking\n• Identifies moderate to severe issues\n• Standard processing time\n• Recommended for most users",
                "use_case": "Best for: Regular compliance reviews, quality assurance"
            }),
            ("Strict", "🔍", {
                "description": "Thorough analysis with detailed scrutiny of all elements",
                "details": "• Exhaustive compliance verification\n• Identifies all potential issues\n• Longer processing time\n• Maximum regulatory protection",
                "use_case": "Best for: Audit preparation, high-risk documentation"
            })
        ]
        
        for i, (level, emoji, info) in enumerate(self.main_window.strictness_levels):
            btn = AnimatedButton(f"{emoji}\n{level}", section)
            btn.setCheckable(True)
            btn.setMinimumHeight(45)
            btn.setMaximumHeight(50)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: white;
                    border: 2px solid {medical_theme.get_color('border_medium')};
                    border-radius: 8px;
                    color: {medical_theme.get_color('text_primary')};
                    font-size: 10px;
                    font-weight: 600;
                    padding: 4px;
                }}
                QPushButton:hover {{
                    background-color: {medical_theme.get_color('hover_bg')};
                    border-color: {medical_theme.get_color('primary_blue')};
                }}
                QPushButton:checked {{
                    background-color: {medical_theme.get_color('primary_blue')};
                    color: white;
                    border-color: {medical_theme.get_color('primary_blue')};
                }}
            """)
            btn.clicked.connect(lambda checked, idx=i: self.main_window._on_strictness_selected_with_description(idx))
            self.main_window.strictness_buttons.append(btn)
            strictness_layout.addWidget(btn)
        
        layout.addLayout(strictness_layout)
        
        # Dynamic description area with complementary background
        self.main_window.strictness_description = QLabel()
        self.main_window.strictness_description.setWordWrap(True)
        self.main_window.strictness_description.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f0f9ff, stop:1 #e0f2fe);
                border: 2px solid #0ea5e9;
                border-radius: 8px;
                padding: 15px;
                color: #0c4a6e;
                font-size: 13px;
                line-height: 1.4;
            }
        """)
        self.main_window.strictness_description.setMinimumHeight(120)
        layout.addWidget(self.main_window.strictness_description)
        
        # Set default to Standard and show its description
        if len(self.main_window.strictness_buttons) >= 2:
            self.main_window.strictness_buttons[1].setChecked(True)
            self.main_window._update_strictness_description(1)
        
        return section
    
    def _create_report_sections_panel(self) -> QWidget:
        """Create report sections panel."""
        section = QWidget(self.main_window)
        section.setStyleSheet(f"""
            QWidget {{
                background-color: {medical_theme.get_color("bg_secondary")};
                border: 2px solid {medical_theme.get_color("border_light")};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("📋 Report Sections", section)
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {medical_theme.get_color('primary_blue')}; background: transparent; border: none;")
        layout.addWidget(title)
        
        # Checkboxes in grid
        grid = QGridLayout()
        grid.setSpacing(8)
        
        sections = [
            "Executive Summary", "Detailed Findings",
            "Risk Assessment", "Recommendations",
            "Regulatory Citations", "Action Plan",
            "AI Transparency", "Improvement Strategies"
        ]
        
        self.main_window.section_checkboxes = {}
        for i, section_name in enumerate(sections):
            checkbox = QCheckBox(section_name)
            checkbox.setChecked(True)
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    color: {medical_theme.get_color('text_primary')};
                    font-size: 10px;
                    spacing: 6px;
                    background: transparent;
                    border: none;
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                    border: 2px solid {medical_theme.get_color('border_medium')};
                    border-radius: 4px;
                    background: white;
                }}
                QCheckBox::indicator:checked {{
                    background: {medical_theme.get_color('primary_blue')};
                    border-color: {medical_theme.get_color('primary_blue')};
                }}
            """)
            self.main_window.section_checkboxes[section_name] = checkbox
            grid.addWidget(checkbox, i // 2, i % 2)
        
        layout.addLayout(grid)
        
        # Export buttons
        export_layout = QHBoxLayout()
        export_layout.setSpacing(8)
        
        pdf_btn = AnimatedButton("📄 PDF", section)
        pdf_btn.clicked.connect(self.main_window._export_report_pdf)
        pdf_btn.setMinimumHeight(35)
        pdf_btn.setStyleSheet(medical_theme.get_button_stylesheet("primary"))
        export_layout.addWidget(pdf_btn)
        
        html_btn = AnimatedButton("🌐 HTML", section)
        html_btn.clicked.connect(self.main_window._export_report_html)
        html_btn.setMinimumHeight(35)
        html_btn.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        export_layout.addWidget(html_btn)
        
        layout.addLayout(export_layout)
        
        return section
    
    def _create_analysis_results_with_chat(self) -> QWidget:
        """Create right panel with analysis results and integrated chat bar."""
        panel = QWidget(self.main_window)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Analysis results (existing)
        results_panel = self._create_analysis_right_panel_content()
        layout.addWidget(results_panel, stretch=1)
        
        return panel
    
    def _create_analysis_right_panel_content(self) -> QWidget:
        """Create the analysis results content."""
        panel = QWidget(self.main_window)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Modern styled tabs
        results_tabs = QTabWidget(panel)
        results_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 8px;
                background: white;
                top: -1px;
            }}
            QTabBar::tab {{
                background: {medical_theme.get_color('bg_secondary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 10px 20px;
                margin-right: 4px;
                color: {medical_theme.get_color('text_secondary')};
                font-weight: 600;
                font-size: 11px;
            }}
            QTabBar::tab:selected {{
                background: white;
                color: {medical_theme.get_color('primary_blue')};
                border-bottom: 2px solid white;
            }}
            QTabBar::tab:hover {{
                background: {medical_theme.get_color('hover_bg')};
            }}
        """)
        
        # Summary tab
        self.main_window.analysis_summary_browser = QTextBrowser(panel)
        self.main_window.analysis_summary_browser.setOpenExternalLinks(False)
        self.main_window.analysis_summary_browser.anchorClicked.connect(self.main_window._handle_report_link)
        self.main_window.analysis_summary_browser.setPlaceholderText(
            "📊 ANALYSIS SUMMARY\n\n"
            "Upload a document and run analysis to see:\n"
            "• Compliance score and risk assessment\n"
            "• Key findings and recommendations\n"
            "• Medicare guideline compliance status\n"
            "• Actionable improvement suggestions\n\n"
            "Select a rubric and click 'Run Analysis' to begin."
        )
        self.main_window.analysis_summary_browser.setStyleSheet(f"""
            QTextBrowser {{
                border: 2px solid {medical_theme.get_color('border_light')};
                background: {medical_theme.get_color('bg_primary')};
                padding: 20px;
                font-size: 13px;
                line-height: 1.6;
                border-radius: 8px;
                color: {medical_theme.get_color('text_primary')};
            }}
        """)
        results_tabs.addTab(self.main_window.analysis_summary_browser, "📊 Summary")
        
        # Detailed results tab
        self.main_window.detailed_results_browser = QTextBrowser(panel)
        self.main_window.detailed_results_browser.setOpenExternalLinks(False)
        self.main_window.detailed_results_browser.anchorClicked.connect(self.main_window._handle_report_link)
        self.main_window.detailed_results_browser.setPlaceholderText(
            "📋 DETAILED ANALYSIS RESULTS\n\n"
            "This section will display:\n"
            "• Complete analysis payload data\n"
            "• Technical details and confidence scores\n"
            "• Raw AI model outputs\n"
            "• Processing timestamps and metadata\n"
            "• Full compliance rule matching results\n\n"
            "Run an analysis to populate this section with detailed technical information."
        )
        self.main_window.detailed_results_browser.setStyleSheet(f"""
            QTextBrowser {{
                border: 2px solid {medical_theme.get_color('border_light')};
                background: {medical_theme.get_color('bg_primary')};
                padding: 20px;
                font-size: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                border-radius: 8px;
                color: {medical_theme.get_color('text_primary')};
            }}
        """)
        results_tabs.addTab(self.main_window.detailed_results_browser, "📋 Details")
        
        layout.addWidget(results_tabs)
        return panel
    
    def _create_document_upload_section(self) -> QWidget:
        """Create the document upload section."""
        section = QWidget(self.main_window)
        section.setStyleSheet(f"""
            QWidget {{
                background-color: {medical_theme.get_color("bg_secondary")};
                border: 2px solid {medical_theme.get_color("border_light")};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("📁 Upload Document", section)
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {medical_theme.get_color('primary_blue')}; background: transparent; border: none;")
        layout.addWidget(title)
        
        # File display
        self.main_window.file_display = QTextEdit(section)
        self.main_window.file_display.setReadOnly(True)
        self.main_window.file_display.setMinimumHeight(90)
        self.main_window.file_display.setMaximumHeight(110)
        self.main_window.file_display.setPlaceholderText("📋 DOCUMENT UPLOAD CENTER\n\n📁 This window displays your selected document for compliance analysis\n\n🔹 Click 'Upload Document' to browse and select a file\n🔹 Supported formats: PDF, DOCX, TXT\n🔹 Maximum file size: 50MB\n\n✨ Once uploaded, document details will appear here")
        self.main_window.file_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: {medical_theme.get_color("bg_primary")};
                border: 2px dashed {medical_theme.get_color("border_medium")};
                border-radius: 8px;
                padding: 12px;
                font-size: 11px;
                color: {medical_theme.get_color("text_secondary")};
            }}
        """)
        layout.addWidget(self.main_window.file_display)
        
        # Upload buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.main_window.open_file_button = AnimatedButton("📄 Upload Document", section)
        self.main_window.open_file_button.clicked.connect(self.main_window._prompt_for_document)
        self.main_window.open_file_button.setStyleSheet(medical_theme.get_button_stylesheet("primary"))
        self.main_window.open_file_button.setMinimumHeight(42)
        buttons_layout.addWidget(self.main_window.open_file_button)
        
        self.main_window.open_folder_button = AnimatedButton("📂 Batch", section)
        self.main_window.open_folder_button.clicked.connect(self.main_window._prompt_for_folder)
        self.main_window.open_folder_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        self.main_window.open_folder_button.setMinimumHeight(42)
        self.main_window.open_folder_button.setMaximumWidth(100)
        buttons_layout.addWidget(self.main_window.open_folder_button)
        
        layout.addLayout(buttons_layout)
        return section

    def _create_action_buttons_section(self) -> QWidget:
        """Create the action buttons section."""
        section = QWidget(self.main_window)
        section.setStyleSheet(f"""
            QWidget {{
                background-color: {medical_theme.get_color("bg_secondary")};
                border: 2px solid {medical_theme.get_color("border_light")};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Run Analysis button (big and prominent)
        self.main_window.run_analysis_button = AnimatedButton("▶️  Run Compliance Analysis", section)
        self.main_window.run_analysis_button.clicked.connect(self.main_window._start_analysis)
        self.main_window.run_analysis_button.setEnabled(False)
        self.main_window.run_analysis_button.setStyleSheet(medical_theme.get_button_stylesheet("success"))
        self.main_window.run_analysis_button.setMinimumHeight(55)
        self.main_window.run_analysis_button.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        layout.addWidget(self.main_window.run_analysis_button)
        
        # Secondary actions
        secondary_layout = QHBoxLayout()
        secondary_layout.setSpacing(10)
        
        self.main_window.repeat_analysis_button = AnimatedButton("🔄 Repeat", section)
        self.main_window.repeat_analysis_button.clicked.connect(self.main_window._repeat_analysis)
        self.main_window.repeat_analysis_button.setEnabled(False)
        self.main_window.repeat_analysis_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        self.main_window.repeat_analysis_button.setMinimumHeight(42)
        secondary_layout.addWidget(self.main_window.repeat_analysis_button)
        
        # Stop Analysis button - professional implementation
        self.main_window.stop_analysis_button = AnimatedButton("⏹️ Stop Analysis", section)
        self.main_window.stop_analysis_button.clicked.connect(self.main_window._stop_analysis)
        self.main_window.stop_analysis_button.setEnabled(False)
        self.main_window.stop_analysis_button.setStyleSheet(medical_theme.get_button_stylesheet("error"))
        self.main_window.stop_analysis_button.setMinimumHeight(42)
        secondary_layout.addWidget(self.main_window.stop_analysis_button)
        
        self.main_window.view_report_button = AnimatedButton("📊 View Report", section)
        self.main_window.view_report_button.clicked.connect(self.main_window._open_report_popup)
        self.main_window.view_report_button.setEnabled(False)
        self.main_window.view_report_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        self.main_window.view_report_button.setMinimumHeight(42)
        secondary_layout.addWidget(self.main_window.view_report_button)
        
        layout.addLayout(secondary_layout)
        return section

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
        """Create user preferences settings widget with professional layout."""
        # Create scroll area for better organization
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(25)  # Proper spacing between sections
        
        # Theme selection
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
        theme_layout.setContentsMargins(20, 20, 20, 20)  # Internal padding
        theme_layout.setSpacing(15)  # Spacing within section
        
        theme_label = QLabel("🎨 Theme Selection", theme_section)
        theme_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        theme_label.setStyleSheet("margin-bottom: 10px;")  # Extra space after title
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
        layout.addWidget(theme_section)
        
        # Account settings
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
        account_layout.setContentsMargins(20, 20, 20, 20)  # Internal padding
        account_layout.setSpacing(15)  # Spacing within section
        
        account_label = QLabel("👤 Account Settings", account_section)
        account_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        account_label.setStyleSheet("margin-bottom: 10px;")  # Extra space after title
        account_layout.addWidget(account_label)
        
        user_info = QLabel(f"Logged in as: {self.main_window.current_user.username}", account_section)
        user_info.setStyleSheet("color: #64748b; padding: 5px;")
        account_layout.addWidget(user_info)
        
        password_button = AnimatedButton("🔒 Change Password", account_section)
        password_button.clicked.connect(self.main_window.show_change_password_dialog)
        password_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        password_button.setMinimumHeight(40)
        account_layout.addWidget(password_button)
        
        layout.addWidget(account_section)
        
        # UI Preferences
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
        
        layout.addWidget(ui_section)
        
        layout.addStretch()
        
        # Set up scroll area
        scroll_area.setWidget(widget)
        
        # Create container for scroll area
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(scroll_area)
        
        return container
    
    def _create_analysis_settings_widget(self) -> QWidget:
        """Create analysis settings widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Default Analysis Settings
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
        
        # Report Content Settings
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
        
        # Medicare Guidelines with description
        medicare_container = QWidget()
        medicare_layout = QVBoxLayout(medicare_container)
        medicare_layout.setContentsMargins(0, 0, 0, 0)
        medicare_layout.setSpacing(5)
        
        include_medicare = QCheckBox("✅ Medicare Guidelines Compliance", section)
        include_medicare.setChecked(True)
        medicare_layout.addWidget(include_medicare)
        
        medicare_desc = QLabel("   Includes CMS compliance requirements and Medicare documentation standards")
        medicare_desc.setStyleSheet("color: #64748b; font-size: 11px; margin-left: 20px;")
        medicare_desc.setWordWrap(True)
        medicare_layout.addWidget(medicare_desc)
        section_layout.addWidget(medicare_container)
        
        # Add more checkboxes with descriptions...
        checkboxes_with_descriptions = [
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