import os
import requests
import json
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QMessageBox,
    QMainWindow,
    QStatusBar,
    QMenuBar,
    QFileDialog,
    QSplitter,           # from feature branch
    QTextEdit,           # from main branch
    QHBoxLayout,         # from main branch
    QListWidget,         # from main branch
    QListWidgetItem,     # from both
    QComboBox,           # from main branch
    QLabel,              # from main branch
    QGroupBox,           # from main branch
    QProgressBar,         # from main branch
    QCheckBox,
    QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtGui import QTextDocument
from .dialogs.rubric_manager_dialog import RubricManagerDialog
from .widgets.control_panel import ControlPanel
from .widgets.document_view import DocumentView
from .widgets.analysis_view import AnalysisView
from .workers.analysis_worker import AnalysisWorker
from .workers.ai_loader_worker import AILoaderWorker
from src.core.compliance_analyzer import ComplianceAnalyzer
from src.gui.export import generate_pdf_report

API_URL = "http://127.0.0.1:8000"

class MainApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._current_file_path = None
        self.analyzer = None
        self.initUI()
        self.load_ai_models()

    def initUI(self):
        self.setWindowTitle('Therapy Compliance Analyzer')
        self.setGeometry(100, 100, 1200, 800)

        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        self.file_menu = self.menu_bar.addMenu('File')
        self.export_action = self.file_menu.addAction('Export to PDF', self.export_to_pdf)
        self.print_action = self.file_menu.addAction('Print', self.print_report)
        self.file_menu.addSeparator()
        self.file_menu.addAction('Exit', self.close)

        self.export_action.setEnabled(False)
        self.print_action.setEnabled(False)
        self.tools_menu = self.menu_bar.addMenu('Tools')
        self.tools_menu.addAction('Manage Rubrics', self.manage_rubrics)
        self.theme_menu = self.menu_bar.addMenu('Theme')
        self.theme_menu.addAction('Light', self.set_light_theme)
        self.theme_menu.addAction('Dark', self.set_dark_theme)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('Ready')

        self.ai_status_label = QLabel("Loading AI models...")
        self.status_bar.addPermanentWidget(self.ai_status_label)

        self.progress_bar = QProgressBar(self.status_bar)
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # ---- Controls Group ----
        controls_group = QGroupBox("Analysis Controls")
        controls_layout = QHBoxLayout()
        controls_group.setLayout(controls_layout)
        main_layout.addWidget(controls_group)

        self.upload_button = QPushButton('Upload Document')
        self.upload_button.clicked.connect(self.open_file_dialog)
        controls_layout.addWidget(self.upload_button)

        self.clear_button = QPushButton('Clear Display')
        self.clear_button.clicked.connect(self.clear_display)
        controls_layout.addWidget(self.clear_button)

        controls_layout.addStretch()

        controls_layout.addWidget(QLabel("Discipline:"))
        self.discipline_combo = QComboBox()
        self.discipline_combo.addItems(["All", "PT", "OT", "SLP"])
        controls_layout.addWidget(self.discipline_combo)

        controls_layout.addWidget(QLabel("OR Select a Rubric:"))
        self.rubric_list_widget = QListWidget()
        self.rubric_list_widget.setMaximumHeight(100)
        self.rubric_list_widget.addItem("No rubric selected")
        self.rubric_list_widget.item(0).setFlags(self.rubric_list_widget.item(0).flags() & ~Qt.ItemIsEnabled)
        self.rubric_list_widget.setEnabled(False)
        controls_layout.addWidget(self.rubric_list_widget)

        self.hybrid_analysis_checkbox = QCheckBox("Hybrid Analysis")
        controls_layout.addWidget(self.hybrid_analysis_checkbox)

        self.run_analysis_button = QPushButton("Run Analysis")
        self.run_analysis_button.clicked.connect(self.run_analysis)
        controls_layout.addWidget(self.run_analysis_button)

        # ---- Splitter for Document/Results Groups ----
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Document group
        document_group = QGroupBox("Document")
        document_layout = QVBoxLayout()
        document_group.setLayout(document_layout)
        self.document_display_area = QTextEdit()
        self.document_display_area.setPlaceholderText("Upload a document to see its content here.")
        self.document_display_area.setReadOnly(True)
        document_layout.addWidget(self.document_display_area)
        splitter.addWidget(document_group)

        # Results group
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout()
        results_group.setLayout(results_layout)
        self.analysis_results_area = QTextEdit()
        self.analysis_results_area.setPlaceholderText("Analysis results will appear here.")
        self.analysis_results_area.setReadOnly(True)
        results_layout.addWidget(self.analysis_results_area)
        splitter.addWidget(results_group)

        # (Optional) If you have a load_theme_setting method:
        theme = self.load_theme_setting()
        self.apply_stylesheet(theme)
        self.load_rubrics_to_list()

    def get_light_theme_stylesheet(self):
        return """
            QMainWindow {
                background-color: #f0f0f0;
                color: #000000;
            }
            QGroupBox {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
                background-color: #ffffff;
            }
            QLabel {
                color: #000000;
            }
            QPushButton {
                background-color: #e0e0e0;
                color: #000000;
                border: 1px solid #c0c0c0;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
            QTextEdit, QListWidget, QComboBox {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
            }
            QMenuBar {
                background-color: #f0f0f0;
                color: #000000;
            }
            QMenuBar::item:selected {
                background-color: #d0d0d0;
            }
            QMenu {
                background-color: #f0f0f0;
                color: #000000;
            }
            QMenu::item:selected {
                background-color: #d0d0d0;
            }
            QStatusBar {
                background-color: #f0f0f0;
                color: #000000;
            }
        """

    def get_dark_theme_stylesheet(self):
        return """
            QMainWindow {
                background-color: #2b2b2b;
                color: #f0f0f0;
            }
            QGroupBox {
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                color: #f0f0f0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                box-shadow: 0 2px 3px rgba(0, 0, 0, 0.1);
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #003c6a;
            }
            QTextEdit, QListWidget, QComboBox {
                background-color: #3c3c3c;
                color: #f0f0f0;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
            }
            QStatusBar {
                background-color: #007acc;
                color: white;
            }
            QLabel {
                color: #f0f0f0;
            }
        """

    def apply_stylesheet(self, theme="dark"):
        if theme == "light":
            self.setStyleSheet(self.get_light_theme_stylesheet())
        else:
            self.setStyleSheet(self.get_dark_theme_stylesheet())

    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Select Document', '', 'All Files (*.*)')
        if file_name:
            self._current_file_path = file_name
            self.status_bar.showMessage(f"Loaded document: {os.path.basename(file_name)}")
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    self.document_view.setText(f.read())
            except Exception:
                 self.document_view.setText(f"Could not display preview for: {file_name}")


    def run_analysis(self):
        if not self._current_file_path:
            QMessageBox.warning(self, "Analysis Error", "Please upload a document to analyze first.")
            return

        selected_items = self.control_panel.rubric_list_widget.selectedItems()
        data = {}
        if selected_items:
            rubric_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
            data['rubric_id'] = rubric_id
            self.status_bar.showMessage(f"Running analysis with rubric: {selected_items[0].text()}...")
        else:
            discipline = self.control_panel.discipline_combo.currentText()
            data['discipline'] = discipline
            self.status_bar.showMessage(f"Running analysis with discipline: {discipline}...")

        # Start progress bar and disable run_analysis button
        self.progress_bar.setRange(0, 0)
        self.progress_bar.show()
        self.control_panel.run_analysis_button.setEnabled(False)
        self.status_bar.showMessage("Running analysis...")
        if self.hybrid_analysis_checkbox.isChecked():
            data['analysis_mode'] = 'hybrid'
            self.status_bar.showMessage("Running hybrid analysis...")
        else:
            data['analysis_mode'] = 'llm_only'

        self.run_analysis_threaded(data)

    def run_analysis_threaded(self, data):
        # Threaded/worker-based analysis approach
        self.thread = QThread()
        self.worker = AnalysisWorker(self._current_file_path, data)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.on_analysis_success)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_analysis_success(self, result):
        self.progress_bar.hide()
        self.analysis_results_area.setText(result)
        self.status_bar.showMessage("Analysis complete.")
        self.control_panel.run_analysis_button.setEnabled(True)
        self.export_action.setEnabled(True)
        self.print_action.setEnabled(True)

    def on_analysis_error(self, error_message):
        self.progress_bar.hide()
        QMessageBox.critical(self, "Analysis Error", error_message)
        self.status_bar.showMessage("Backend analysis failed.")
        self.control_panel.run_analysis_button.setEnabled(True)

    def manage_rubrics(self):
        dialog = RubricManagerDialog(self)
        dialog.exec()
        self.load_rubrics_to_list()

    def load_rubrics_to_list(self):
        self.control_panel.rubric_list_widget.clear()
        try:
            response = requests.get(f"{API_URL}/rubrics/")
            response.raise_for_status()
            rubrics = response.json()
            if rubrics:
                for rubric in rubrics:
                    item = QListWidgetItem(rubric['name'])
                    item.setData(Qt.ItemDataRole.UserRole, rubric['id'])
                    self.rubric_list_widget.addItem(item)
                self.rubric_list_widget.setEnabled(True)
            else:
                self.rubric_list_widget.addItem("No rubrics found")
                self.rubric_list_widget.item(0).setFlags(
                    self.rubric_list_widget.item(0).flags() & ~Qt.ItemIsEnabled
                )
                self.rubric_list_widget.setEnabled(False)
        except Exception as e:
            self.rubric_list_widget.clear()
            self.rubric_list_widget.addItem("Error loading rubrics")
            self.rubric_list_widget.item(0).setFlags(self.rubric_list_widget.item(0).flags() & ~Qt.ItemIsEnabled)
            self.rubric_list_widget.setEnabled(False)
            self.handle_error(f"Failed to load rubrics from backend:\n{e}")

    def clear_display(self):
        self.document_display_area.clear()
        self.analysis_results_area.clear()
        self._current_file_path = None
        self.status_bar.showMessage("Display cleared.")
        self.export_action.setEnabled(False)
        self.print_action.setEnabled(False)

    def handle_error(self, message):
        QMessageBox.critical(self, "Error", message)
        self.status_bar.showMessage("An error occurred.")

    def save_theme_setting(self, theme):
        with open("theme.cfg", "w") as f:
            f.write(theme)

    def load_theme_setting(self):
        try:
            with open("theme.cfg", "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return "dark"

    def set_light_theme(self):
        self.apply_stylesheet("light")
        self.save_theme_setting("light")

    def set_dark_theme(self):
        self.apply_stylesheet("dark")
        self.save_theme_setting("dark")

    def load_ai_models(self):
        self.thread = QThread()
        self.worker = AILoaderWorker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_ai_loaded)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_ai_loaded(self, analyzer, is_healthy, status_message):
        self.analyzer = analyzer
        self.ai_status_label.setText(status_message)
        self.ai_status_label.setStyleSheet(
            "color: green;" if is_healthy else "color: red;"
        )

    def export_to_pdf(self):
        analysis_results = self.analysis_results_area.toPlainText()
        if not analysis_results:
            QMessageBox.warning(self, "Export Error", "No analysis results to export.")
            return

        success, message = generate_pdf_report(analysis_results, self)
        if success:
            self.status_bar.showMessage(f"Report successfully exported to {message}")
        else:
            QMessageBox.critical(self, "Export Error", message)

    def print_report(self):
        analysis_results_str = self.analysis_results_area.toPlainText()
        if not analysis_results_str:
            QMessageBox.warning(self, "Print Error", "No analysis results to print.")
            return

        try:
            analysis_results = json.loads(analysis_results_str)
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Print Error", "Failed to decode analysis results.")
            return

        # Define the path for the template
        template_path = os.path.join(os.path.dirname(__file__), '..', 'report_template.html')

        # Read the template file
        try:
            with open(template_path, 'r') as f:
                template_content = f.read()
        except FileNotFoundError:
            QMessageBox.critical(self, "Print Error", f"Report template not found at {template_path}")
            return

        # Create a Jinja2 template object
        from jinja2 import Template
        template = Template(template_content)

        # Transform the analysis results to match the template's expectations
        findings = []
        for finding in analysis_results.get('findings', []):
            findings.append({
                'title': finding.get('rule_id', 'N/A'),
                'category': finding.get('risk_description', 'N/A'),
                'justification': finding.get('text_quote', 'N/A'),
                'observation': finding.get('suggestion', 'N/A')
            })

        # Render the template with the analysis results
        html_content = template.render(
            findings=findings,
            guidelines=analysis_results.get('guidelines', [])
        )

        # Print the rendered HTML
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)

        if dialog.exec() == QPrintDialog.Accepted:
            doc = QTextDocument()
            doc.setHtml(html_content)
            doc.print_(printer)
            self.status_bar.showMessage("Report sent to printer.")
