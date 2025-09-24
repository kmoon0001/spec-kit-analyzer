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
    QSplitter,
    QListWidgetItem
)
from PySide6.QtCore import Qt, QThread
from .dialogs.rubric_manager_dialog import RubricManagerDialog
from .widgets.control_panel import ControlPanel
from .widgets.document_view import DocumentView
from .widgets.analysis_view import AnalysisView
from .workers.analysis_worker import AnalysisWorker

API_URL = "http://127.0.0.1:8000"

class MainApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._current_file_path = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Therapy Compliance Analyzer')
        self.setGeometry(100, 100, 1200, 800)

        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        self.file_menu = self.menu_bar.addMenu('File')
        self.file_menu.addAction('Exit', self.close)
        self.tools_menu = self.menu_bar.addMenu('Tools')
        self.tools_menu.addAction('Manage Rubrics', self.manage_rubrics)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('Ready')

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.control_panel = ControlPanel(self)
        main_layout.addWidget(self.control_panel)

        splitter = QSplitter(Qt.Horizontal)

        self.document_view = DocumentView()
        splitter.addWidget(self.document_view)

        self.analysis_view = AnalysisView()
        splitter.addWidget(self.analysis_view)

        splitter.setSizes([500, 700])
        main_layout.addWidget(splitter)

        self.load_rubrics_to_list()
        self.apply_stylesheet()

    def apply_stylesheet(self):
        self.setStyleSheet("""
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
        """)

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

        self.control_panel.run_analysis_button.setEnabled(False)
        self.status_bar.showMessage("Running analysis...")

    def on_analysis_success(self, result):
        self.analysis_view.setHtml(result)
        self.status_bar.showMessage("Analysis complete.")
        self.control_panel.run_analysis_button.setEnabled(True)

    def on_analysis_error(self, error_message):
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
            for rubric in rubrics:
                item = QListWidgetItem(rubric['name'])
                item.setData(Qt.ItemDataRole.UserRole, rubric['id'])
                self.control_panel.rubric_list_widget.addItem(item)
        except Exception as e:
            self.handle_error(f"Failed to load rubrics from backend:\n{e}")

    def clear_display(self):
        self.document_view.clear()
        self.analysis_view.setHtml("")
        self._current_file_path = None
        self.status_bar.showMessage("Display cleared.")

    def handle_error(self, message):
        QMessageBox.critical(self, "Error", message)
        self.status_bar.showMessage("An error occurred.")
