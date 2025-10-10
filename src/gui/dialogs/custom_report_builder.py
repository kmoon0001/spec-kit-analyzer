"""
Custom Report Builder Dialog - Advanced Report Customization
"""

from datetime import datetime, timedelta

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class ReportTemplate:
    """Report template configuration"""

    def __init__(self, name: str, description: str, sections: list[str]):
        self.name = name
        self.description = description
        self.sections = sections
        self.created_date = datetime.now()
        self.last_modified = datetime.now()


class CustomReportBuilder(QDialog):
    """Advanced Custom Report Builder with template management"""

    report_generated = Signal(dict)
    template_saved = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Custom Report Builder - Advanced Edition")
        self.setFixedSize(1000, 700)
        self.setModal(True)

        # Report configuration
        self.report_config = {
            "title": "Custom Compliance Report",
            "date_range": {"start": datetime.now() - timedelta(days=30), "end": datetime.now()},
            "sections": [],
            "filters": {},
            "formatting": {},
            "export_format": "html"
        }

        # Available report sections
        self.available_sections = {
            "executive_summary": {
                "name": "Executive Summary",
                "description": "High-level compliance overview with key metrics",
                "icon": "📋",
                "required_data": ["compliance_scores", "risk_assessment"]
            },
            "detailed_findings": {
                "name": "Detailed Findings",
                "description": "Comprehensive analysis of compliance issues",
                "icon": "🔍",
                "required_data": ["analysis_results", "findings"]
            },
            "trend_analysis": {
                "name": "Trend Analysis",
                "description": "Historical compliance trends and patterns",
                "icon": "📈",
                "required_data": ["historical_data", "trends"]
            },
            "risk_assessment": {
                "name": "Risk Assessment",
                "description": "Current risk levels and mitigation strategies",
                "icon": "⚠️",
                "required_data": ["risk_scores", "audit_risk"]
            },
            "benchmarking": {
                "name": "Industry Benchmarking",
                "description": "Comparison with industry standards",
                "icon": "🏆",
                "required_data": ["benchmark_data", "industry_averages"]
            },
            "recommendations": {
                "name": "AI Recommendations",
                "description": "Personalized improvement suggestions",
                "icon": "💡",
                "required_data": ["ai_recommendations", "action_items"]
            },
            "compliance_checklist": {
                "name": "Compliance Checklist",
                "description": "Detailed compliance verification checklist",
                "icon": "✅",
                "required_data": ["checklist_items", "compliance_status"]
            },
            "regulatory_updates": {
                "name": "Regulatory Updates",
                "description": "Recent changes in compliance requirements",
                "icon": "📜",
                "required_data": ["regulatory_changes", "updates"]
            }
        }

        # Predefined templates
        self.templates = {
            "comprehensive": ReportTemplate(
                "Comprehensive Audit Report",
                "Complete compliance analysis with all sections",
                ["executive_summary", "detailed_findings", "trend_analysis", "risk_assessment", "recommendations"]
            ),
            "executive": ReportTemplate(
                "Executive Summary Report",
                "High-level overview for management",
                ["executive_summary", "risk_assessment", "benchmarking"]
            ),
            "clinical": ReportTemplate(
                "Clinical Focus Report",
                "Detailed clinical compliance analysis",
                ["detailed_findings", "compliance_checklist", "recommendations"]
            ),
            "trend_focused": ReportTemplate(
                "Trend Analysis Report",
                "Historical performance and predictive insights",
                ["trend_analysis", "benchmarking", "recommendations"]
            )
        }

        self.init_ui()
        self.setup_connections()
        self.load_default_template()

    def init_ui(self):
        """Initialize the report builder UI"""
        layout = QVBoxLayout(self)

        # Header
        self.create_header(layout)

        # Main content with tabs
        self.create_main_content(layout)

        # Footer with actions
        self.create_footer(layout)

    def create_header(self, parent_layout):
        """Create header with title and template selector"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
            }
        """)

        header_layout = QHBoxLayout(header_frame)

        # Title
        title = QLabel("📊 Custom Report Builder")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Template selector
        template_label = QLabel("Template:")
        template_label.setStyleSheet("color: white; background: transparent; font-weight: bold;")
        header_layout.addWidget(template_label)

        self.template_combo = QComboBox()
        self.template_combo.addItem("Custom Report", "custom")
        for key, template in self.templates.items():
            self.template_combo.addItem(template.name, key)
        self.template_combo.setStyleSheet("""
            QComboBox {
                background: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                margin-left: 10px;
                min-width: 200px;
            }
        """)
        header_layout.addWidget(self.template_combo)

        parent_layout.addWidget(header_frame)

    def create_main_content(self, parent_layout):
        """Create main tabbed content area"""
        self.tab_widget = QTabWidget()

        # Report Configuration Tab
        self.create_config_tab()

        # Section Selection Tab
        self.create_sections_tab()

        # Formatting Options Tab
        self.create_formatting_tab()

        # Preview Tab
        self.create_preview_tab()

        parent_layout.addWidget(self.tab_widget)

    def create_config_tab(self):
        """Create report configuration tab"""
        config_widget = QWidget()
        layout = QVBoxLayout(config_widget)

        # Basic Information
        basic_group = QGroupBox("📋 Basic Information")
        basic_layout = QGridLayout(basic_group)

        # Report title
        basic_layout.addWidget(QLabel("Report Title:"), 0, 0)
        self.title_edit = QLineEdit(self.report_config["title"])
        self.title_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus { border-color: #007acc; }
        """)
        basic_layout.addWidget(self.title_edit, 0, 1, 1, 2)

        # Date range
        basic_layout.addWidget(QLabel("Date Range:"), 1, 0)
        self.start_date = QDateEdit(self.report_config["date_range"]["start"])
        self.start_date.setCalendarPopup(True)
        self.end_date = QDateEdit(self.report_config["date_range"]["end"])
        self.end_date.setCalendarPopup(True)

        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("From:"))
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("To:"))
        date_layout.addWidget(self.end_date)
        date_layout.addStretch()

        basic_layout.addLayout(date_layout, 1, 1, 1, 2)

        # Export format
        basic_layout.addWidget(QLabel("Export Format:"), 2, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["HTML Report", "PDF Document", "Excel Spreadsheet", "Word Document"])
        basic_layout.addWidget(self.format_combo, 2, 1)

        layout.addWidget(basic_group)

        # Filters
        filters_group = QGroupBox("🔍 Data Filters")
        filters_layout = QGridLayout(filters_group)

        # Compliance score filter
        filters_layout.addWidget(QLabel("Minimum Compliance Score:"), 0, 0)
        self.min_score_slider = QSlider(Qt.Orientation.Horizontal)
        self.min_score_slider.setRange(0, 100)
        self.min_score_slider.setValue(70)
        self.min_score_label = QLabel("70%")
        self.min_score_slider.valueChanged.connect(
            lambda v: self.min_score_label.setText(f"{v}%")
        )

        score_layout = QHBoxLayout()
        score_layout.addWidget(self.min_score_slider)
        score_layout.addWidget(self.min_score_label)
        filters_layout.addLayout(score_layout, 0, 1)

        # Risk level filter
        filters_layout.addWidget(QLabel("Include Risk Levels:"), 1, 0)
        risk_layout = QHBoxLayout()
        self.high_risk_cb = QCheckBox("High Risk")
        self.high_risk_cb.setChecked(True)
        self.medium_risk_cb = QCheckBox("Medium Risk")
        self.medium_risk_cb.setChecked(True)
        self.low_risk_cb = QCheckBox("Low Risk")
        self.low_risk_cb.setChecked(False)

        risk_layout.addWidget(self.high_risk_cb)
        risk_layout.addWidget(self.medium_risk_cb)
        risk_layout.addWidget(self.low_risk_cb)
        risk_layout.addStretch()
        filters_layout.addLayout(risk_layout, 1, 1)

        # Document type filter
        filters_layout.addWidget(QLabel("Document Types:"), 2, 0)
        doc_layout = QHBoxLayout()
        self.progress_notes_cb = QCheckBox("Progress Notes")
        self.progress_notes_cb.setChecked(True)
        self.evaluations_cb = QCheckBox("Evaluations")
        self.evaluations_cb.setChecked(True)
        self.treatment_plans_cb = QCheckBox("Treatment Plans")
        self.treatment_plans_cb.setChecked(True)

        doc_layout.addWidget(self.progress_notes_cb)
        doc_layout.addWidget(self.evaluations_cb)
        doc_layout.addWidget(self.treatment_plans_cb)
        doc_layout.addStretch()
        filters_layout.addLayout(doc_layout, 2, 1)

        layout.addWidget(filters_group)

        layout.addStretch()

        self.tab_widget.addTab(config_widget, "⚙️ Configuration")

    def create_sections_tab(self):
        """Create section selection tab"""
        sections_widget = QWidget()
        layout = QHBoxLayout(sections_widget)

        # Available sections
        available_group = QGroupBox("📚 Available Sections")
        available_layout = QVBoxLayout(available_group)

        self.available_list = QListWidget()
        self.available_list.setDragDropMode(QListWidget.DragDropMode.DragOnly)

        for key, section in self.available_sections.items():
            item = QListWidgetItem(f"{section['icon']} {section['name']}")
            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setToolTip(section['description'])
            self.available_list.addItem(item)

        available_layout.addWidget(self.available_list)

        # Control buttons
        controls_layout = QVBoxLayout()
        controls_layout.addStretch()

        add_btn = QPushButton("➡️ Add")
        add_btn.clicked.connect(self.add_section)
        add_btn.setStyleSheet("""
            QPushButton {
                background: #007acc;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background: #005a9e; }
        """)
        controls_layout.addWidget(add_btn)

        remove_btn = QPushButton("⬅️ Remove")
        remove_btn.clicked.connect(self.remove_section)
        remove_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background: #c82333; }
        """)
        controls_layout.addWidget(remove_btn)

        controls_layout.addStretch()

        move_up_btn = QPushButton("⬆️ Move Up")
        move_up_btn.clicked.connect(self.move_section_up)
        move_down_btn = QPushButton("⬇️ Move Down")
        move_down_btn.clicked.connect(self.move_section_down)

        controls_layout.addWidget(move_up_btn)
        controls_layout.addWidget(move_down_btn)
        controls_layout.addStretch()

        # Selected sections
        selected_group = QGroupBox("📝 Selected Sections (Report Order)")
        selected_layout = QVBoxLayout(selected_group)

        self.selected_list = QListWidget()
        self.selected_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        selected_layout.addWidget(self.selected_list)

        # Layout assembly
        layout.addWidget(available_group, 2)
        layout.addLayout(controls_layout, 0)
        layout.addWidget(selected_group, 2)

        self.tab_widget.addTab(sections_widget, "📋 Sections")

    def create_formatting_tab(self):
        """Create formatting options tab"""
        formatting_widget = QWidget()
        layout = QVBoxLayout(formatting_widget)

        # Visual Style
        style_group = QGroupBox("🎨 Visual Style")
        style_layout = QGridLayout(style_group)

        # Theme selection
        style_layout.addWidget(QLabel("Report Theme:"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            "Professional Blue",
            "Medical Green",
            "Corporate Gray",
            "Modern Purple",
            "Classic Black & White"
        ])
        style_layout.addWidget(self.theme_combo, 0, 1)

        # Logo inclusion
        self.include_logo_cb = QCheckBox("Include Organization Logo")
        self.include_logo_cb.setChecked(True)
        style_layout.addWidget(self.include_logo_cb, 1, 0, 1, 2)

        # Page numbering
        self.page_numbers_cb = QCheckBox("Include Page Numbers")
        self.page_numbers_cb.setChecked(True)
        style_layout.addWidget(self.page_numbers_cb, 2, 0, 1, 2)

        # Table of contents
        self.toc_cb = QCheckBox("Generate Table of Contents")
        self.toc_cb.setChecked(True)
        style_layout.addWidget(self.toc_cb, 3, 0, 1, 2)

        layout.addWidget(style_group)

        # Content Options
        content_group = QGroupBox("📄 Content Options")
        content_layout = QGridLayout(content_group)

        # Detail level
        content_layout.addWidget(QLabel("Detail Level:"), 0, 0)
        self.detail_combo = QComboBox()
        self.detail_combo.addItems(["Summary", "Standard", "Detailed", "Comprehensive"])
        self.detail_combo.setCurrentText("Standard")
        content_layout.addWidget(self.detail_combo, 0, 1)

        # Include charts
        self.include_charts_cb = QCheckBox("Include Charts and Graphs")
        self.include_charts_cb.setChecked(True)
        content_layout.addWidget(self.include_charts_cb, 1, 0, 1, 2)

        # Include recommendations
        self.include_recommendations_cb = QCheckBox("Include AI Recommendations")
        self.include_recommendations_cb.setChecked(True)
        content_layout.addWidget(self.include_recommendations_cb, 2, 0, 1, 2)

        # Include raw data
        self.include_raw_data_cb = QCheckBox("Include Raw Data Appendix")
        self.include_raw_data_cb.setChecked(False)
        content_layout.addWidget(self.include_raw_data_cb, 3, 0, 1, 2)

        layout.addWidget(content_group)

        # Custom Branding
        branding_group = QGroupBox("🏢 Custom Branding")
        branding_layout = QGridLayout(branding_group)

        # Organization name
        branding_layout.addWidget(QLabel("Organization Name:"), 0, 0)
        self.org_name_edit = QLineEdit("Your Healthcare Organization")
        branding_layout.addWidget(self.org_name_edit, 0, 1)

        # Department
        branding_layout.addWidget(QLabel("Department:"), 1, 0)
        self.department_edit = QLineEdit("Therapy Services")
        branding_layout.addWidget(self.department_edit, 1, 1)

        # Contact information
        branding_layout.addWidget(QLabel("Contact Info:"), 2, 0)
        self.contact_edit = QLineEdit("compliance@organization.com")
        branding_layout.addWidget(self.contact_edit, 2, 1)

        layout.addWidget(branding_group)

        layout.addStretch()

        self.tab_widget.addTab(formatting_widget, "🎨 Formatting")

    def create_preview_tab(self):
        """Create report preview tab"""
        preview_widget = QWidget()
        layout = QVBoxLayout(preview_widget)

        # Preview controls
        controls_layout = QHBoxLayout()

        refresh_btn = QPushButton("🔄 Refresh Preview")
        refresh_btn.clicked.connect(self.refresh_preview)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #007acc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #005a9e; }
        """)
        controls_layout.addWidget(refresh_btn)

        controls_layout.addStretch()

        # Preview scale
        controls_layout.addWidget(QLabel("Preview Scale:"))
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["50%", "75%", "100%", "125%", "150%"])
        self.scale_combo.setCurrentText("75%")
        controls_layout.addWidget(self.scale_combo)

        layout.addLayout(controls_layout)

        # Preview area
        self.preview_area = QScrollArea()
        self.preview_content = QLabel("Click 'Refresh Preview' to generate report preview...")
        self.preview_content.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.preview_content.setWordWrap(True)
        self.preview_content.setStyleSheet("""
            QLabel {
                background: white;
                border: 1px solid #ddd;
                padding: 20px;
                margin: 10px;
            }
        """)

        self.preview_area.setWidget(self.preview_content)
        self.preview_area.setWidgetResizable(True)
        layout.addWidget(self.preview_area)

        self.tab_widget.addTab(preview_widget, "👁️ Preview")

    def create_footer(self, parent_layout):
        """Create footer with action buttons"""
        footer_layout = QHBoxLayout()

        # Template management
        save_template_btn = QPushButton("💾 Save as Template")
        save_template_btn.clicked.connect(self.save_template)
        save_template_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background: #218838; }
        """)
        footer_layout.addWidget(save_template_btn)

        footer_layout.addStretch()

        # Main actions
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background: #5a6268; }
        """)
        footer_layout.addWidget(cancel_btn)

        generate_btn = QPushButton("📊 Generate Report")
        generate_btn.clicked.connect(self.generate_report)
        generate_btn.setStyleSheet("""
            QPushButton {
                background: #007acc;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background: #005a9e; }
        """)
        footer_layout.addWidget(generate_btn)

        parent_layout.addLayout(footer_layout)

    def setup_connections(self):
        """Setup signal connections"""
        self.template_combo.currentTextChanged.connect(self.load_template)
        self.title_edit.textChanged.connect(self.update_config)
        self.start_date.dateChanged.connect(self.update_config)
        self.end_date.dateChanged.connect(self.update_config)

    def load_template(self, template_name: str):
        """Load a predefined template"""
        template_key = self.template_combo.currentData()

        if template_key == "custom":
            return

        if template_key in self.templates:
            template = self.templates[template_key]

            # Clear current selections
            self.selected_list.clear()

            # Add template sections
            for section_key in template.sections:
                if section_key in self.available_sections:
                    section = self.available_sections[section_key]
                    item = QListWidgetItem(f"{section['icon']} {section['name']}")
                    item.setData(Qt.ItemDataRole.UserRole, section_key)
                    self.selected_list.addItem(item)

            # Update title
            self.title_edit.setText(template.name)

    def load_default_template(self):
        """Load the default comprehensive template"""
        self.template_combo.setCurrentText("Comprehensive Audit Report")
        self.load_template("Comprehensive Audit Report")

    def add_section(self):
        """Add selected section to report"""
        current_item = self.available_list.currentItem()
        if current_item:
            section_key = current_item.data(Qt.ItemDataRole.UserRole)
            section = self.available_sections[section_key]

            # Check if already added
            for i in range(self.selected_list.count()):
                if self.selected_list.item(i).data(Qt.ItemDataRole.UserRole) == section_key:
                    QMessageBox.information(self, "Section Already Added",
                                          f"The section '{section['name']}' is already in your report.")
                    return

            # Add to selected list
            item = QListWidgetItem(f"{section['icon']} {section['name']}")
            item.setData(Qt.ItemDataRole.UserRole, section_key)
            self.selected_list.addItem(item)

    def remove_section(self):
        """Remove selected section from report"""
        current_row = self.selected_list.currentRow()
        if current_row >= 0:
            self.selected_list.takeItem(current_row)

    def move_section_up(self):
        """Move selected section up in order"""
        current_row = self.selected_list.currentRow()
        if current_row > 0:
            item = self.selected_list.takeItem(current_row)
            self.selected_list.insertItem(current_row - 1, item)
            self.selected_list.setCurrentRow(current_row - 1)

    def move_section_down(self):
        """Move selected section down in order"""
        current_row = self.selected_list.currentRow()
        if current_row < self.selected_list.count() - 1:
            item = self.selected_list.takeItem(current_row)
            self.selected_list.insertItem(current_row + 1, item)
            self.selected_list.setCurrentRow(current_row + 1)

    def update_config(self):
        """Update report configuration"""
        self.report_config.update({
            "title": self.title_edit.text(),
            "date_range": {
                "start": self.start_date.date().toPython(),
                "end": self.end_date.date().toPython()
            }
        })

    def refresh_preview(self):
        """Refresh the report preview"""
        # Generate preview HTML
        preview_html = self.generate_preview_html()
        self.preview_content.setText(preview_html)

    def generate_preview_html(self) -> str:
        """Generate HTML preview of the report"""
        sections = []
        for i in range(self.selected_list.count()):
            item = self.selected_list.item(i)
            section_key = item.data(Qt.ItemDataRole.UserRole)
            section = self.available_sections[section_key]
            sections.append(f"<h2>{section['icon']} {section['name']}</h2>")
            sections.append(f"<p><em>{section['description']}</em></p>")
            sections.append("<p>[Section content would appear here based on actual data]</p>")
            sections.append("<hr>")

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #007acc; border-bottom: 2px solid #007acc; }}
                h2 {{ color: #333; margin-top: 30px; }}
                .header {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .date-range {{ color: #666; font-style: italic; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{self.title_edit.text()}</h1>
                <p class="date-range">Report Period: {self.start_date.date().toString()} to {self.end_date.date().toString()}</p>
                <p><strong>Organization:</strong> {self.org_name_edit.text()}</p>
                <p><strong>Department:</strong> {self.department_edit.text()}</p>
            </div>

            {''.join(sections)}

            <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px;">
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by Therapy Compliance Analyzer</p>
                <p>Contact: {self.contact_edit.text()}</p>
            </footer>
        </body>
        </html>
        """

        return html

    def save_template(self):
        """Save current configuration as template"""
        template_name, ok = self.get_template_name()
        if ok and template_name:
            # Get selected sections
            sections = []
            for i in range(self.selected_list.count()):
                item = self.selected_list.item(i)
                section_key = item.data(Qt.ItemDataRole.UserRole)
                sections.append(section_key)

            # Create template
            template = ReportTemplate(
                template_name,
                f"Custom template created on {datetime.now().strftime('%Y-%m-%d')}",
                sections
            )

            # Add to templates (in a real implementation, this would be saved to file/database)
            template_key = template_name.lower().replace(" ", "_")
            self.templates[template_key] = template

            # Update combo box
            self.template_combo.addItem(template.name, template_key)

            self.template_saved.emit(template_name)

            QMessageBox.information(self, "Template Saved",
                                  f"Template '{template_name}' has been saved successfully!")

    def get_template_name(self) -> tuple[str, bool]:
        """Get template name from user"""
        from PySide6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(
            self,
            "Save Template",
            "Enter template name:",
            text=f"Custom Template {len(self.templates) + 1}"
        )

        return name, ok

    def generate_report(self):
        """Generate the final report"""
        # Collect all configuration
        config = {
            "title": self.title_edit.text(),
            "date_range": {
                "start": self.start_date.date().toPython(),
                "end": self.end_date.date().toPython()
            },
            "sections": [],
            "formatting": {
                "theme": self.theme_combo.currentText(),
                "include_logo": self.include_logo_cb.isChecked(),
                "page_numbers": self.page_numbers_cb.isChecked(),
                "table_of_contents": self.toc_cb.isChecked(),
                "detail_level": self.detail_combo.currentText(),
                "include_charts": self.include_charts_cb.isChecked(),
                "include_recommendations": self.include_recommendations_cb.isChecked(),
                "include_raw_data": self.include_raw_data_cb.isChecked()
            },
            "branding": {
                "organization": self.org_name_edit.text(),
                "department": self.department_edit.text(),
                "contact": self.contact_edit.text()
            },
            "filters": {
                "min_compliance_score": self.min_score_slider.value(),
                "risk_levels": {
                    "high": self.high_risk_cb.isChecked(),
                    "medium": self.medium_risk_cb.isChecked(),
                    "low": self.low_risk_cb.isChecked()
                },
                "document_types": {
                    "progress_notes": self.progress_notes_cb.isChecked(),
                    "evaluations": self.evaluations_cb.isChecked(),
                    "treatment_plans": self.treatment_plans_cb.isChecked()
                }
            },
            "export_format": self.format_combo.currentText().lower()
        }

        # Get selected sections in order
        for i in range(self.selected_list.count()):
            item = self.selected_list.item(i)
            section_key = item.data(Qt.ItemDataRole.UserRole)
            config["sections"].append(section_key)

        # Validate configuration
        if not config["sections"]:
            QMessageBox.warning(self, "No Sections Selected",
                              "Please select at least one section for your report.")
            return

        if not config["title"].strip():
            QMessageBox.warning(self, "Missing Title",
                              "Please enter a title for your report.")
            return

        # Emit signal with configuration
        self.report_generated.emit(config)

        # Show success message
        QMessageBox.information(self, "Report Generated",
                              f"Custom report '{config['title']}' has been generated successfully!")

        self.accept()
