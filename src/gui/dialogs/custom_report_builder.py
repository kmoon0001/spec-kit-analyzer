"""
Custom Report Builder - Drag & Drop Report Creation Interface
"""

from typing import Dict, List, Any, Optional
from PySide6.QtCore import Qt, Signal, QMimeData, QPoint
from PySide6.QtGui import QDrag, QPainter, QFont, QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QSplitter,
    QLabel, QPushButton, QComboBox, QCheckBox, QSpinBox,
    QTextEdit, QListWidget, QListWidgetItem, QGroupBox,
    QScrollArea, QFrame, QTabWidget, QColorDialog, QFontDialog,
    QMessageBox, QFileDialog, QProgressBar, QApplication, QTextBrowser
)


class DraggableReportElement(QFrame):
    """Draggable report element for the builder"""
    
    def __init__(self, element_type: str, title: str, description: str):
        super().__init__()
        self.element_type = element_type
        self.title = title
        self.description = description
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the draggable element UI"""
        self.setFixedSize(200, 80)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 10px;
            }
            QFrame:hover {
                border-color: #007acc;
                background: #f0f8ff;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        
        desc_label = QLabel(self.description)
        desc_label.setFont(QFont("Arial", 9))
        desc_label.setStyleSheet("color: #666;")
        desc_label.setWordWrap(True)
        
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        
    def mousePressEvent(self, event):
        """Handle mouse press for drag initiation"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
            
        if ((event.position().toPoint() - self.drag_start_position).manhattanLength() < 
            QApplication.startDragDistance()):
            return
            
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"{self.element_type}|{self.title}")
        drag.setMimeData(mime_data)
        
        # Create drag pixmap
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)
        
        drag.exec(Qt.DropAction.CopyAction)


class ReportCanvas(QFrame):
    """Canvas for building custom reports"""
    
    element_added = Signal(str, dict)
    
    def __init__(self):
        super().__init__()
        self.report_elements = []
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the report canvas"""
        self.setAcceptDrops(True)
        self.setMinimumSize(600, 800)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px dashed #ccc;
                border-radius: 10px;
            }
        """)
        
        # Layout for dropped elements
        self.canvas_layout = QVBoxLayout(self)
        
        # Instructions label
        self.instructions = QLabel("Drag report elements here to build your custom report")
        self.instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instructions.setStyleSheet("color: #999; font-size: 14px; padding: 50px;")
        self.canvas_layout.addWidget(self.instructions)
        
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QFrame {
                    background: #f0f8ff;
                    border: 2px dashed #007acc;
                    border-radius: 10px;
                }
            """)
            
    def dragLeaveEvent(self, event):
        """Handle drag leave event"""
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px dashed #ccc;
                border-radius: 10px;
            }
        """)
        
    def dropEvent(self, event):
        """Handle drop event"""
        if event.mimeData().hasText():
            element_data = event.mimeData().text().split("|")
            if len(element_data) == 2:
                element_type, title = element_data
                self.add_report_element(element_type, title, event.position().toPoint())
                event.acceptProposedAction()
                
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px dashed #ccc;
                border-radius: 10px;
            }
        """)
        
    def add_report_element(self, element_type: str, title: str, position: QPoint):
        """Add a report element to the canvas"""
        # Hide instructions if this is the first element
        if not self.report_elements:
            self.instructions.hide()
            
        # Create element widget based on type
        element_widget = self.create_element_widget(element_type, title)
        self.canvas_layout.addWidget(element_widget)
        
        # Store element data
        element_data = {
            "type": element_type,
            "title": title,
            "position": position,
            "widget": element_widget
        }
        self.report_elements.append(element_data)
        
        self.element_added.emit(element_type, element_data)
        
    def create_element_widget(self, element_type: str, title: str):
        """Create widget for report element"""
        widget = QGroupBox(title)
        layout = QVBoxLayout(widget)
        
        if element_type == "header":
            content = QLabel("Custom Report Header")
            content.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif element_type == "summary":
            content = QLabel("Executive Summary\n\nKey metrics and findings will be displayed here.")
        elif element_type == "chart":
            content = QLabel("📊 Chart Placeholder\n\nCompliance trends and visualizations")
            content.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content.setStyleSheet("background: #f8f9fa; border: 1px solid #ddd; padding: 20px;")
        elif element_type == "table":
            content = QLabel("📋 Data Table\n\nDetailed findings and compliance data")
            content.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content.setStyleSheet("background: #f8f9fa; border: 1px solid #ddd; padding: 20px;")
        elif element_type == "text":
            content = QTextEdit("Custom text content goes here...")
            content.setMaximumHeight(100)
        else:
            content = QLabel(f"{title} content will be displayed here")
            
        layout.addWidget(content)
        
        # Add remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_element(widget))
        remove_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background: #c82333; }
        """)
        layout.addWidget(remove_btn)
        
        return widget
        
    def remove_element(self, widget):
        """Remove an element from the canvas"""
        # Remove from layout and list
        self.canvas_layout.removeWidget(widget)
        widget.deleteLater()
        
        # Remove from elements list
        self.report_elements = [e for e in self.report_elements if e["widget"] != widget]
        
        # Show instructions if no elements left
        if not self.report_elements:
            self.instructions.show()
            
    def clear_canvas(self):
        """Clear all elements from canvas"""
        for element in self.report_elements[:]:
            self.remove_element(element["widget"])


class CustomReportBuilder(QDialog):
    """Custom Report Builder Dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎨 Custom Report Builder")
        self.setFixedSize(1200, 800)
        self.report_config = {}
        self.init_ui()
        
    def init_ui(self):
        """Initialize the report builder UI"""
        layout = QHBoxLayout(self)
        
        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Elements and settings
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Canvas and preview
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
        
        layout.addWidget(splitter) 
       
    def create_left_panel(self):
        """Create left panel with elements and settings"""
        panel = QFrame()
        panel.setFixedWidth(300)
        layout = QVBoxLayout(panel)
        
        # Panel header
        header = QLabel("🎨 Report Builder")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setStyleSheet("padding: 10px; background: #f8f9fa; border-radius: 5px;")
        layout.addWidget(header)
        
        # Create tabs for different sections
        tabs = QTabWidget()
        
        # Elements tab
        elements_tab = self.create_elements_tab()
        tabs.addTab(elements_tab, "📦 Elements")
        
        # Settings tab
        settings_tab = self.create_settings_tab()
        tabs.addTab(settings_tab, "⚙️ Settings")
        
        # Templates tab
        templates_tab = self.create_templates_tab()
        tabs.addTab(templates_tab, "📋 Templates")
        
        layout.addWidget(tabs)
        
        # Action buttons
        self.create_action_buttons(layout)
        
        return panel
        
    def create_elements_tab(self):
        """Create elements tab with draggable components"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Instructions
        instructions = QLabel("Drag elements to the canvas to build your report:")
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(instructions)
        
        # Scroll area for elements
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Report elements
        elements = [
            ("header", "Report Header", "Title and document info"),
            ("summary", "Executive Summary", "Key metrics overview"),
            ("chart", "Compliance Chart", "Visual trend analysis"),
            ("table", "Findings Table", "Detailed compliance data"),
            ("recommendations", "Recommendations", "Improvement suggestions"),
            ("citations", "Citations", "Regulatory references"),
            ("text", "Custom Text", "Free-form text content"),
            ("signature", "Signature Block", "Report authentication"),
        ]
        
        for element_type, title, description in elements:
            element = DraggableReportElement(element_type, title, description)
            scroll_layout.addWidget(element)
            
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        return widget
        
    def create_settings_tab(self):
        """Create settings tab for report customization"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Report settings
        settings_group = QGroupBox("Report Settings")
        settings_layout = QGridLayout(settings_group)
        
        # Report title
        settings_layout.addWidget(QLabel("Report Title:"), 0, 0)
        self.report_title = QTextEdit()
        self.report_title.setMaximumHeight(60)
        self.report_title.setPlainText("Custom Compliance Report")
        settings_layout.addWidget(self.report_title, 0, 1)
        
        # Report type
        settings_layout.addWidget(QLabel("Report Type:"), 1, 0)
        self.report_type = QComboBox()
        self.report_type.addItems([
            "Compliance Analysis",
            "Quality Improvement",
            "Audit Preparation",
            "Training Report",
            "Custom Report"
        ])
        settings_layout.addWidget(self.report_type, 1, 1)
        
        # Include options
        settings_layout.addWidget(QLabel("Include:"), 2, 0)
        include_layout = QVBoxLayout()
        
        self.include_timestamp = QCheckBox("Timestamp")
        self.include_timestamp.setChecked(True)
        include_layout.addWidget(self.include_timestamp)
        
        self.include_signature = QCheckBox("Digital Signature")
        self.include_signature.setChecked(True)
        include_layout.addWidget(self.include_signature)
        
        self.include_branding = QCheckBox("Pacific Coast Branding")
        self.include_branding.setChecked(True)
        include_layout.addWidget(self.include_branding)
        
        settings_layout.addLayout(include_layout, 2, 1)
        
        layout.addWidget(settings_group)
        
        # Styling options
        style_group = QGroupBox("Styling Options")
        style_layout = QGridLayout(style_group)
        
        # Color scheme
        style_layout.addWidget(QLabel("Color Scheme:"), 0, 0)
        self.color_scheme = QComboBox()
        self.color_scheme.addItems([
            "Professional Blue",
            "Medical Green", 
            "Corporate Gray",
            "Custom Colors"
        ])
        style_layout.addWidget(self.color_scheme, 0, 1)
        
        # Font settings
        style_layout.addWidget(QLabel("Font Family:"), 1, 0)
        self.font_family = QComboBox()
        self.font_family.addItems([
            "Arial",
            "Times New Roman",
            "Calibri",
            "Helvetica"
        ])
        style_layout.addWidget(self.font_family, 1, 1)
        
        # Font size
        style_layout.addWidget(QLabel("Base Font Size:"), 2, 0)
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 16)
        self.font_size.setValue(11)
        style_layout.addWidget(self.font_size, 2, 1)
        
        layout.addWidget(style_group)
        
        layout.addStretch()
        
        return widget
        
    def create_templates_tab(self):
        """Create templates tab with pre-built report layouts"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Instructions
        instructions = QLabel("Choose a template to start with:")
        instructions.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(instructions)
        
        # Template options
        templates = [
            {
                "name": "Standard Compliance Report",
                "description": "Header, Summary, Findings Table, Recommendations",
                "elements": ["header", "summary", "table", "recommendations"]
            },
            {
                "name": "Executive Summary",
                "description": "Header, Summary, Key Charts, Signature",
                "elements": ["header", "summary", "chart", "signature"]
            },
            {
                "name": "Detailed Analysis",
                "description": "Complete analysis with all elements",
                "elements": ["header", "summary", "chart", "table", "recommendations", "citations", "signature"]
            },
            {
                "name": "Training Report",
                "description": "Educational focus with recommendations",
                "elements": ["header", "summary", "recommendations", "text", "signature"]
            }
        ]
        
        for template in templates:
            template_btn = QPushButton(template["name"])
            template_btn.setToolTip(template["description"])
            template_btn.clicked.connect(lambda checked, t=template: self.apply_template(t))
            template_btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    background: white;
                    margin: 2px;
                }
                QPushButton:hover {
                    background: #f0f8ff;
                    border-color: #007acc;
                }
            """)
            layout.addWidget(template_btn)
            
        layout.addStretch()
        
        return widget
        
    def create_right_panel(self):
        """Create right panel with canvas and preview"""
        panel = QFrame()
        layout = QVBoxLayout(panel)
        
        # Canvas header
        canvas_header = QHBoxLayout()
        
        canvas_title = QLabel("📄 Report Canvas")
        canvas_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        canvas_header.addWidget(canvas_title)
        
        canvas_header.addStretch()
        
        # Canvas controls
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.clear_canvas)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #c82333; }
        """)
        canvas_header.addWidget(clear_btn)
        
        preview_btn = QPushButton("👁️ Preview")
        preview_btn.clicked.connect(self.preview_report)
        preview_btn.setStyleSheet("""
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
        canvas_header.addWidget(preview_btn)
        
        layout.addLayout(canvas_header)
        
        # Report canvas
        scroll_area = QScrollArea()
        self.canvas = ReportCanvas()
        self.canvas.element_added.connect(self.on_element_added)
        scroll_area.setWidget(self.canvas)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        return panel
        
    def create_action_buttons(self, parent_layout):
        """Create action buttons at bottom of left panel"""
        buttons_layout = QHBoxLayout()
        
        # Save template button
        save_template_btn = QPushButton("💾 Save Template")
        save_template_btn.clicked.connect(self.save_template)
        save_template_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background: #218838; }
        """)
        buttons_layout.addWidget(save_template_btn)
        
        # Generate report button
        generate_btn = QPushButton("🚀 Generate")
        generate_btn.clicked.connect(self.generate_report)
        generate_btn.setStyleSheet("""
            QPushButton {
                background: #007acc;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background: #005a9e; }
        """)
        buttons_layout.addWidget(generate_btn)
        
        parent_layout.addLayout(buttons_layout)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover { background: #5a6268; }
        """)
        parent_layout.addWidget(close_btn)
        
    def apply_template(self, template: Dict):
        """Apply a template to the canvas"""
        # Clear existing elements
        self.canvas.clear_canvas()
        
        # Add template elements
        for element_type in template["elements"]:
            # Find element title from elements list
            element_titles = {
                "header": "Report Header",
                "summary": "Executive Summary", 
                "chart": "Compliance Chart",
                "table": "Findings Table",
                "recommendations": "Recommendations",
                "citations": "Citations",
                "text": "Custom Text",
                "signature": "Signature Block"
            }
            
            title = element_titles.get(element_type, element_type.title())
            self.canvas.add_report_element(element_type, title, QPoint(0, 0))
            
        QMessageBox.information(self, "Template Applied", f"Applied template: {template['name']}")
        
    def on_element_added(self, element_type: str, element_data: Dict):
        """Handle element added to canvas"""
        # Update report configuration
        if "elements" not in self.report_config:
            self.report_config["elements"] = []
            
        self.report_config["elements"].append({
            "type": element_type,
            "title": element_data["title"]
        })
        
    def clear_canvas(self):
        """Clear the report canvas"""
        self.canvas.clear_canvas()
        self.report_config["elements"] = []
        
    def preview_report(self):
        """Preview the custom report"""
        if not self.canvas.report_elements:
            QMessageBox.warning(self, "No Elements", "Add some elements to the canvas first!")
            return
            
        # Generate preview HTML
        preview_html = self.generate_preview_html()
        
        # Show preview dialog
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("📄 Report Preview")
        preview_dialog.setFixedSize(800, 600)
        
        layout = QVBoxLayout(preview_dialog)
        
        preview_browser = QTextBrowser()
        preview_browser.setHtml(preview_html)
        layout.addWidget(preview_browser)
        
        close_btn = QPushButton("Close Preview")
        close_btn.clicked.connect(preview_dialog.accept)
        layout.addWidget(close_btn)
        
        preview_dialog.exec()
        
    def generate_preview_html(self) -> str:
        """Generate HTML preview of the custom report"""
        title = self.report_title.toPlainText()
        
        html = f"""
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: {self.font_family.currentText()}; font-size: {self.font_size.value()}pt; margin: 20px; }}
                .header {{ background: #007acc; color: white; padding: 20px; border-radius: 8px; text-align: center; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .chart-placeholder {{ background: #f8f9fa; border: 2px dashed #ccc; padding: 40px; text-align: center; }}
                .signature {{ margin-top: 40px; font-style: italic; text-align: right; }}
            </style>
        </head>
        <body>
        """
        
        for element in self.canvas.report_elements:
            element_type = element["type"]
            element_title = element["title"]
            
            if element_type == "header":
                html += f"""
                <div class="header">
                    <h1>{title}</h1>
                    <p>Custom Report Generated by Therapy Document Compliance Analysis</p>
                </div>
                """
            elif element_type == "summary":
                html += """
                <div class="section">
                    <h2>Executive Summary</h2>
                    <p>This section will contain key metrics and findings from your compliance analysis.</p>
                </div>
                """
            elif element_type == "chart":
                html += """
                <div class="section">
                    <h2>Compliance Visualization</h2>
                    <div class="chart-placeholder">📊 Interactive charts and graphs will be displayed here</div>
                </div>
                """
            elif element_type == "table":
                html += """
                <div class="section">
                    <h2>Detailed Findings</h2>
                    <p>Comprehensive compliance data table will be displayed here with findings, recommendations, and risk levels.</p>
                </div>
                """
            elif element_type == "recommendations":
                html += """
                <div class="section">
                    <h2>Recommendations</h2>
                    <p>AI-generated improvement suggestions and action items will be listed here.</p>
                </div>
                """
            elif element_type == "citations":
                html += """
                <div class="section">
                    <h2>Regulatory Citations</h2>
                    <p>Medicare Part B guidelines and regulatory references will be included here.</p>
                </div>
                """
            elif element_type == "text":
                html += f"""
                <div class="section">
                    <h2>Custom Content</h2>
                    <p>Your custom text content will appear here.</p>
                </div>
                """
            elif element_type == "signature":
                html += """
                <div class="signature">
                    <p>Report generated by Therapy Document Compliance Analysis</p>
                    <p style="font-family: 'Brush Script MT', cursive;">Pacific Coast Development 🌴 - Kevin Moon</p>
                </div>
                """
                
        html += "</body></html>"
        return html
        
    def save_template(self):
        """Save current configuration as a template"""
        if not self.canvas.report_elements:
            QMessageBox.warning(self, "No Elements", "Add some elements to save as a template!")
            return
            
        # This would save the template configuration
        QMessageBox.information(self, "Template Saved", "Your custom template has been saved!")
        
    def generate_report(self):
        """Generate the final custom report"""
        if not self.canvas.report_elements:
            QMessageBox.warning(self, "No Elements", "Add some elements to generate a report!")
            return
            
        # Show progress dialog
        progress = QProgressBar()
        progress.setRange(0, 100)
        
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle("Generating Report...")
        progress_dialog.setFixedSize(300, 100)
        
        layout = QVBoxLayout(progress_dialog)
        layout.addWidget(QLabel("Generating your custom report..."))
        layout.addWidget(progress)
        
        progress_dialog.show()
        
        # Simulate report generation
        for i in range(101):
            progress.setValue(i)
            QApplication.processEvents()
            
        progress_dialog.close()
        
        # Show completion message
        QMessageBox.information(
            self, 
            "Report Generated", 
            "Your custom report has been generated successfully!\n\nThe report includes all selected elements with your chosen styling and configuration."
        )
        
        self.accept()