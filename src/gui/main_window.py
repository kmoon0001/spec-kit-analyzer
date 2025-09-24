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
    QComboBox,
    QLabel,
    QSplitter,
    QGroupBox
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt
from .dialogs.rubric_manager_dialog import RubricManagerDialog

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

        # Controls Group
        controls_group = QGroupBox("Controls")
        controls_layout = QVBoxLayout(controls_group)

        # File operations
        file_ops_layout = QHBoxLayout()
        self.upload_button = QPushButton('Upload Document')
        self.upload_button.clicked.connect(self.open_file_dialog)
        file_ops_layout.addWidget(self.upload_button)
        self.clear_button = QPushButton('Clear Display')
        self.clear_button.clicked.connect(self.clear_display)
        file_ops_layout.addWidget(self.clear_button)
        controls_layout.addLayout(file_ops_layout)

        # Analysis options
        analysis_ops_layout = QHBoxLayout()

        discipline_layout = QVBoxLayout()
        discipline_layout.addWidget(QLabel("Discipline:"))
        self.discipline_combo = QComboBox()
        self.discipline_combo.addItems(["All", "PT", "OT", "SLP"])
        discipline_layout.addWidget(self.discipline_combo)
        analysis_ops_layout.addLayout(discipline_layout)

        rubric_layout = QVBoxLayout()
        rubric_layout.addWidget(QLabel("OR Select a Rubric:"))
        self.rubric_list_widget = QListWidget()
        self.rubric_list_widget.setPlaceholderText("No rubric selected")
        self.rubric_list_widget.setMaximumHeight(100)
        rubric_layout.addWidget(self.rubric_list_widget)
        analysis_ops_layout.addLayout(rubric_layout)

        analysis_ops_layout.addStretch()

        self.run_analysis_button = QPushButton("Run Analysis")
        self.run_analysis_button.clicked.connect(self.run_analysis)
        analysis_ops_layout.addWidget(self.run_analysis_button, 0, Qt.AlignBottom)

        controls_layout.addLayout(analysis_ops_layout)

        main_layout.addWidget(controls_group)

        # Document and results display
        splitter = QSplitter(Qt.Horizontal)

        self.document_display_area = QTextEdit()
        self.document_display_area.setPlaceholderText("Upload a document to see its content here.")
        self.document_display_area.setReadOnly(True)
        splitter.addWidget(self.document_display_area)

        self.analysis_results_area = QWebEngineView()
        self.analysis_results_area.setHtml("<p>Analysis results will appear here.</p>")
        splitter.addWidget(self.analysis_results_area)

        splitter.setSizes([500, 700])
        main_layout.addWidget(splitter)

        self.load_rubrics_to_list()
        self.apply_stylesheet()

    def apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #003c6a;
            }
            QTextEdit, QListWidget, QComboBox {
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 5px;
            }
            QStatusBar {
                background-color: #0078d7;
                color: white;
            }
        """)

    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Select Document', '', 'All Files (*.*)')
        if file_name:
            self._current_file_path = file_name
            self.status_bar.showMessage(f"Loaded document: {os.path.basename(file_name)}")
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    self.document_display_area.setText(f.read())
            except Exception:
                 self.document_display_area.setText(f"Could not display preview for: {file_name}")


    def run_analysis(self):
        if not self._current_file_path:
            QMessageBox.warning(self, "Analysis Error", "Please upload a document to analyze first.")
            return

        selected_items = self.rubric_list_widget.selectedItems()
        data = {}
        if selected_items:
            # Rubric-based analysis
            rubric_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
            data['rubric_id'] = rubric_id
            self.status_bar.showMessage(f"Running analysis with rubric: {selected_items[0].text()}...")
        else:
            # Discipline-based analysis
            discipline = self.discipline_combo.currentText()
            data['discipline'] = discipline
            self.status_bar.showMessage(f"Running analysis with discipline: {discipline}...")

        try:
            with open(self._current_file_path, 'rb') as f:
                files = {'file': (os.path.basename(self._current_file_path), f)}
                response = requests.post(f"{API_URL}/analyze", files=files, data=data)

            if response.status_code == 200:
                self.analysis_results_area.setHtml(response.text)
                self.status_bar.showMessage("Analysis complete.")
            else:
                error_text = f"Error from backend: {response.status_code}\n\n{response.text}"
                QMessageBox.critical(self, "Analysis Error", error_text)
                self.status_bar.showMessage("Backend analysis failed.")
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect to backend or perform analysis:\n{e}")
            self.status_bar.showMessage("Connection to backend failed.")

    def manage_rubrics(self):
        dialog = RubricManagerDialog(self)
        dialog.exec()
        self.load_rubrics_to_list()

    def load_rubrics_to_list(self):
        self.rubric_list_widget.clear()
        try:
            response = requests.get(f"{API_URL}/rubrics/")
            response.raise_for_status()
            rubrics = response.json()
            for rubric in rubrics:
                item = QListWidgetItem(rubric['name'])
                item.setData(Qt.ItemDataRole.UserRole, rubric['id'])
                self.rubric_list_widget.addItem(item)
        except Exception as e:
            self.handle_error(f"Failed to load rubrics from backend:\n{e}")

    def clear_display(self):
        self.document_display_area.clear()
        self.analysis_results_area.setHtml("")
        self._current_file_path = None
        self.status_bar.showMessage("Display cleared.")

    def handle_error(self, message):
        QMessageBox.critical(self, "Error", message)
        self.status_bar.showMessage("An error occurred.")
