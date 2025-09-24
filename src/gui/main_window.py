import os
import requests
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
from PySide6.QtCore import Qt, QThread  # keep QThread only if it's used elsewhere!
from .dialogs.rubric_manager_dialog import RubricManagerDialog
from .widgets.control_panel import ControlPanel
from .widgets.document_view import DocumentView
from .widgets.analysis_view import AnalysisView
from .workers.analysis_worker import AnalysisWorker
from .workers.folder_analysis_worker import FolderAnalysisWorker
from .workers.ai_loader_worker import AILoaderWorker
from src.compliance_analyzer import ComplianceAnalyzer

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
        self.file_menu.addAction('Exit', self.close)
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

        self.upload_folder_button = QPushButton('Upload Folder')
        self.upload_folder_button.clicked.connect(self.open_folder_dialog)
        controls_layout.addWidget(self.upload_folder_button)

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

    def open_folder_dialog(self):
        folder_name = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder_name:
            self._current_folder_path = folder_name
            self.status_bar.showMessage(f"Loaded folder: {os.path.basename(folder_name)}")
            self.run_folder_analysis()


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

        try:
            with open(self._current_file_path, 'rb') as f:
                files = {'file': (os.path.basename(self._current_file_path), f)}
                response = requests.post(f"{API_URL}/analyze", files=files, data=data)
            response.raise_for_status()
            result = response.json()
            task_id = result['task_id']
            self.run_analysis_threaded(data, task_id)
        except Exception as e:
            self.on_analysis_error(f"Failed to start analysis: {e}")

    def run_folder_analysis(self):
        if not self._current_folder_path:
            QMessageBox.warning(self, "Analysis Error", "Please upload a folder to analyze first.")
            return

        data = {}
        discipline = self.control_panel.discipline_combo.currentText()
        data['discipline'] = discipline
        self.status_bar.showMessage(f"Running analysis with discipline: {discipline}...")

        # Start progress bar and disable run_analysis button
        self.progress_bar.setRange(0, 0)
        self.progress_bar.show()
        self.control_panel.run_analysis_button.setEnabled(False)
        self.status_bar.showMessage("Running analysis...")

        try:
            files = []
            for filename in os.listdir(self._current_folder_path):
                file_path = os.path.join(self._current_folder_path, filename)
                if os.path.isfile(file_path):
                    files.append(('files', (filename, open(file_path, 'rb'))))

            response = requests.post(f"{API_URL}/analyze_folder", files=files, data=data)
            response.raise_for_status()
            result = response.json()
            task_id = result['task_id']
            self.run_folder_analysis_threaded(data, task_id)
        except Exception as e:
            self.on_analysis_error(f"Failed to start analysis: {e}")

    def run_analysis_threaded(self, data, task_id):
        # Threaded/worker-based analysis approach
        self.thread = QThread()
        self.worker = AnalysisWorker(self._current_file_path, data, task_id)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.on_analysis_success)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.progress.connect(self.on_analysis_progress)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def run_folder_analysis_threaded(self, data, task_id):
        # Threaded/worker-based analysis approach
        self.thread = QThread()
        self.worker = FolderAnalysisWorker(data, task_id)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.success.connect(self.on_analysis_success)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.progress.connect(self.on_analysis_progress)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_analysis_progress(self, progress):
        self.progress_bar.setValue(progress)

    def on_analysis_success(self, result):
        self.progress_bar.hide()
        self.analysis_results_area.setText(result)
        self.status_bar.showMessage("Analysis complete.")
        self.control_panel.run_analysis_button.setEnabled(True)

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
