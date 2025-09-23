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
    QInputDialog,
    QCheckBox,
    QComboBox,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from .dialogs.rubric_manager_dialog import RubricManagerDialog

API_URL = "http://127.0.0.1:8000"

class MainApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._current_file_path = None
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
        self.manage_rubrics_button = QPushButton("Manage Rubrics")
        self.manage_rubrics_button.clicked.connect(self.manage_rubrics)
        rubric_layout.addWidget(self.manage_rubrics_button)
        self.discipline_combo = QComboBox()
        self.discipline_combo.addItems(["All", "PT", "OT", "SLP"])
        rubric_layout.addWidget(QLabel("Discipline:"))
        rubric_layout.addWidget(self.discipline_combo)


        self.run_analysis_button = QPushButton("Run Analysis")
        self.run_analysis_button.clicked.connect(self.run_backend_analysis)
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
import os
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QListWidgetItem
from PyQt6.QtPrintSupport import QPrinter

class DocumentAnalyzerMainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurable analysis mode: "offline" or "backend"
        self.analysis_mode = "backend"  # or "offline"
        # ... (initialize your widgets here) ...

    def display_file(self, file_path):
        try:
            if self.analysis_mode == "backend":
                self.document_display_area.setText(f"File ready for analysis:\n{file_path}")
            else:
                self.document_display_area.setText(
                    f"Loaded '{os.path.basename(file_path)}'.\n\nSelect a discipline and click 'Run Analysis'."
                )
            self.analysis_results_area.clear()  # Always clear results on new load
            self._current_file_path = file_path
        except Exception as e:
            self._current_file_path = None
            self.handle_error(f"Failed to handle file:\n{e}")

    def run_analysis(self):
        if not self._current_file_path:
            self.handle_error("Please upload a document to analyze first.", warning=True)
            return

        if self.analysis_mode == "backend":
            discipline = self.discipline_combo.currentText()
            self.status_bar.showMessage(
                f"Sending {os.path.basename(self._current_file_path)} to backend for analysis..."
            )
            self.analysis_results_area.setText(f"Analyzing with discipline: {discipline}...")
            self._set_busy(True)
            self._call_backend_for_analysis(self._current_file_path, discipline)
            self._set_busy(False)
        else:
            # Offline: implement your offline logic here, e.g., run local model/rubric analysis
            self.status_bar.showMessage(f"Analyzing {os.path.basename(self._current_file_path)} offline...")
            try:
                # Example of local analysis, replace with real function as needed
                results_html = self._build_report_html()
                self.analysis_results_area.setHtml(results_html)
                self.status_bar.showMessage("Offline analysis complete.")
            except Exception as e:
                self.handle_error(f"Offline analysis failed:\n{e}")

    def _call_backend_for_analysis(self, file_path, discipline):
        try:
            import requests
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                data = {'discipline': discipline}
                response = requests.post("http://127.0.0.1:8000/analyze", files=files, data=data)

            if response.status_code == 200:
                self.analysis_results_area.setHtml(response.text)
                self.status_bar.showMessage("Analysis complete.")
            else:
                self.handle_error(f"Error from backend: {response.status_code}\n\n{response.text}")
                self.status_bar.showMessage("Backend analysis failed.")
        except Exception as e:
            self.handle_error(f"Failed to connect to backend or perform analysis:\n{e}")
            self.status_bar.showMessage("Connection to backend failed.")

    def clear_document_display(self):
        self.document_display_area.clear()
        if hasattr(self.analysis_results_area, "setHtml"):
            self.analysis_results_area.setHtml("")
        else:
            self.analysis_results_area.clear()
        self._current_file_path = None
        if hasattr(self, "_current_raw_text"):
            self._current_raw_text = ""
        if hasattr(self, "_current_sentences_with_source"):
            self._current_sentences_with_source = []
        self.status_bar.showMessage("Display cleared.")

    def handle_error(self, message, warning=False):
        """Unified error handling for all modes."""
        if warning:
            QMessageBox.warning(self, "Analysis Error", message)
        else:
            QMessageBox.critical(self, "Error", message)
        self.analysis_results_area.setText(message)
        self.status_bar.showMessage(message)

    def _build_report_html(self) -> str:
        text_for_report = scrub_phi(getattr(self, "_current_raw_text", "") or "")
        html = (
            f"<html><head><meta charset='utf-8'>"
            "<style>body { font-family: Arial, sans-serif; }"
            "h1 { font-size: 18pt; } h2 { font-size: 14pt; margin-top: 12pt; }"
            "pre { white-space: pre-wrap; font-family: Consolas, monospace; background: #f4f4f4; padding: 8px; }</style>"
            "</head><body>"
            "<h1>Therapy Compliance Analysis Report</h1>"
            "<p><b>Mode:</b> Offline | <b>PHI Scrubbing:</b> Enabled for export</p>"
            "<h2>Extracted Text (scrubbed)</h2>"
            f"<pre>{text_for_report}</pre></body></html>"
        )
        return html

    def generate_report_pdf(self):
        if not getattr(self, "_current_raw_text", ""):
            QMessageBox.information(self, "Generate Report", "No document data to export.")
            return
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Report as PDF", "", "PDF Files (*.pdf)")
        if not save_path:
            return
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            if not save_path.lower().endswith(".pdf"):
                save_path += ".pdf"
            printer.setOutputFileName(save_path)
            from PySide6.QtGui import QTextDocument
            doc = QTextDocument()
            doc.setHtml(self._build_report_html())
            doc.print(printer)
            QMessageBox.information(self, "Generate Report", f"PDF saved to:\n{save_path}")
        except Exception as e:
            self.handle_error(f"Failed to create PDF:\n{e}")

    # Main branch rubric functions (optionally included by mode)
    def manage_rubrics(self):
        dialog = RubricManagerDialog(self)
        dialog.exec()
        self.load_rubrics_to_main_list()

    def load_rubrics_to_main_list(self):
        self.rubric_list_widget.clear()
        try:
            import requests
            response = requests.get(f"{API_URL}/rubrics/")
            response.raise_for_status()
            rubrics = response.json()
            for rubric in rubrics:
                item = QListWidgetItem(rubric['name'])
                item.setData(Qt.ItemDataRole.UserRole, rubric['id'])
                self.rubric_list_widget.addItem(item)
        except Exception as e:
            self.handle_error(f"Failed to load rubrics from backend:\n{e}")

    def run_rubric_analysis(self):
        if not self._current_file_path:
            self.handle_error("Please upload a document to analyze first.", warning=True)
            return
        selected_items = self.rubric_list_widget.selectedItems()
        if not selected_items:
            self.handle_error("Please select a rubric to run the analysis.", warning=True)
            return
        rubric_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self.status_bar.showMessage("Running analysis...")
        # Add backend rubric analysis logic as needed

# Helper function (example for PHI scrubbing)
def scrub_phi(text):
    # Dummy example; replace with your real PHI scrubbing function
    return text.replace("John Doe", "[REDACTED]")

# Constants
API_URL = "http://127.0.0.1:8000"

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
