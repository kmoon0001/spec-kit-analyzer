import os
import requests
from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
    QMainWindow,
    QStatusBar,
    QMenuBar,
    QFileDialog,
    QTextEdit,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from .dialogs.rubric_manager_dialog import RubricManagerDialog

API_URL = "http://127.0.0.1:8000"

class MainApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self._current_file_path = None

    def initUI(self):
        self.setWindowTitle('Therapy Compliance Analyzer')
        self.setGeometry(100, 100, 1024, 768)
        self.setAcceptDrops(True)

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

        button_layout = QHBoxLayout()
        self.upload_button = QPushButton('Upload Document')
        self.upload_button.clicked.connect(self.open_file_dialog)
        button_layout.addWidget(self.upload_button)
        self.clear_button = QPushButton('Clear Display')
        self.clear_button.clicked.connect(self.clear_document_display)
        button_layout.addWidget(self.clear_button)
        main_layout.addLayout(button_layout)

        rubric_layout = QHBoxLayout()
        self.run_analysis_button = QPushButton("Run Analysis")
        self.run_analysis_button.clicked.connect(self.run_rubric_analysis)
        rubric_layout.addWidget(self.run_analysis_button)

        self.rubric_list_widget = QListWidget()
        self.rubric_list_widget.setPlaceholderText("Select a Rubric")
        self.rubric_list_widget.setMaximumHeight(100)
        rubric_layout.addWidget(self.rubric_list_widget)
        main_layout.addLayout(rubric_layout)

        self.document_display_area = QTextEdit()
        self.document_display_area.setPlaceholderText("Drag and drop a document here, or use the 'Upload Document' button.")
        self.document_display_area.setReadOnly(True)
        main_layout.addWidget(self.document_display_area)

        self.analysis_results_area = QWebEngineView()
        self.analysis_results_area.setHtml("<p>Rubric analysis results will appear here.</p>")
        main_layout.addWidget(self.analysis_results_area)

        self.central_widget.setLayout(main_layout)
        self.load_rubrics_to_main_list()

    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Select Document', '', 'All Files (*.*)')
        if file_name:
            self.process_document(file_name)

    def process_document(self, file_path):
        self._current_file_path = file_path
        self.status_bar.showMessage(f"Loaded document: {os.path.basename(file_path)}")
        try:
            # We just display the path, not the content, to keep the frontend simple.
            # The file will be sent to the backend for processing.
            self.document_display_area.setText(f"File ready for analysis:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to handle file:\n{e}")
            self._current_file_path = None

    def clear_document_display(self):
        self.document_display_area.clear()
        self.analysis_results_area.setHtml("")
        self._current_file_path = None
        self.status_bar.showMessage('Display cleared.')

    def manage_rubrics(self):
        dialog = RubricManagerDialog(self)
        dialog.exec()
        self.load_rubrics_to_main_list()

    def load_rubrics_to_main_list(self):
        self.rubric_list_widget.clear()
        try:
            response = requests.get(f"{API_URL}/rubrics/")
            response.raise_for_status()
            rubrics = response.json()
            for rubric in rubrics:
                item = QListWidgetItem(rubric['name'])
                item.setData(Qt.ItemDataRole.UserRole, rubric['id'])
                self.rubric_list_widget.addItem(item)
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Error", f"Failed to load rubrics from backend:\n{e}")

    def run_rubric_analysis(self):
        if not self._current_file_path:
            QMessageBox.warning(self, "Analysis Error", "Please upload a document to analyze first.")
            return

        selected_items = self.rubric_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Analysis Error", "Please select a rubric to run the analysis.")
            return

        rubric_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self.status_bar.showMessage("Running analysis...")

        try:
            with open(self._current_file_path, 'rb') as f:
                files = {'file': (os.path.basename(self._current_file_path), f)}
                data = {'rubric_id': rubric_id}
                response = requests.post(f"{API_URL}/analyze", files=files, data=data)

            response.raise_for_status()
            self.analysis_results_area.setHtml(response.text)
            self.status_bar.showMessage("Analysis complete.")

        except requests.exceptions.RequestException as e:
            self.status_bar.showMessage("Analysis failed.")
            error_detail = e.response.text if e.response else str(e)
            QMessageBox.critical(self, "Analysis Error", f"Failed to run analysis on backend:\n{error_detail}")
        except Exception as e:
            self.status_bar.showMessage("Analysis failed.")
            QMessageBox.critical(self, "Error", f"An unexpected error occurred:\n{e}")
