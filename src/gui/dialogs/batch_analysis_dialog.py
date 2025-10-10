from typing import Any

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ..workers.batch_processor_worker import BatchProcessorWorker
from ..workers.file_scanner_worker import FileScannerWorker


class BatchAnalysisDialog(QDialog):
    """Dialog to manage scanning a folder and running a real-time batch analysis."""

    SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".txt", ".md", ".json"]

    def __init__(self, folder_path: str, token: str, analysis_data: dict[str, Any], parent=None):
        super().__init__(parent)
        self.folder_path = folder_path
        self.token = token
        self.analysis_data = analysis_data
        self.files_to_process: list[str] = []
        self.worker_thread: QThread | None = None
        self.scanner_worker: FileScannerWorker | None = None
        self.processor_worker: BatchProcessorWorker | None = None

        self.setWindowTitle("Batch Analysis")
        self.setMinimumSize(700, 500)

        # --- UI Setup ---
        self.main_layout = QVBoxLayout(self)

        self.status_label = QLabel(f"Scanning {folder_path}...")
        self.main_layout.addWidget(self.status_label)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(2)
        self.results_table.setHorizontalHeaderLabels(["File", "Status"])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.main_layout.addWidget(self.results_table)

        self.progress_bar = QProgressBar()
        self.main_layout.addWidget(self.progress_bar)

        self.button_box = QDialogButtonBox()
        self.start_button = self.button_box.addButton("Start Analysis", QDialogButtonBox.ButtonRole.AcceptRole)
        self.start_button.setEnabled(False)
        self.close_button = self.button_box.addButton(QDialogButtonBox.StandardButton.Close)
        self.main_layout.addWidget(self.button_box)

        # --- Connections ---
        self.start_button.clicked.connect(self.start_batch_analysis)
        self.close_button.clicked.connect(self.close)

        self.scan_folder()

    def scan_folder(self):
        """Starts the worker to scan the folder for files."""
        self.worker_thread = QThread()
        self.scanner_worker = FileScannerWorker(self.folder_path, self.SUPPORTED_EXTENSIONS)
        self.scanner_worker.moveToThread(self.worker_thread)

        self.scanner_worker.file_found.connect(self.add_file_to_table)
        self.scanner_worker.finished.connect(self.on_scan_finished)
        self.scanner_worker.error.connect(self.on_scan_error)

        self.worker_thread.started.connect(self.scanner_worker.run)
        self.worker_thread.start()

    def add_file_to_table(self, file_name: str):
        row_position = self.results_table.rowCount()
        self.results_table.insertRow(row_position)
        self.results_table.setItem(row_position, 0, QTableWidgetItem(file_name))
        self.results_table.setItem(row_position, 1, QTableWidgetItem("Pending"))

    def on_scan_finished(self, found_files: list[str]):
        self.files_to_process = found_files
        if not found_files:
            self.status_label.setText(f"No supported documents found in {self.folder_path}.")
            self.start_button.setText("Close")
            self.start_button.setEnabled(True)
            self.start_button.clicked.disconnect()
            self.start_button.clicked.connect(self.accept)
        else:
            self.status_label.setText(f"Found {len(found_files)} documents. Ready to analyze.")
            self.start_button.setEnabled(True)
        self.worker_thread.quit()

    def on_scan_error(self, error_message: str):
        QMessageBox.critical(self, "Scan Error", error_message)
        self.accept()

    def start_batch_analysis(self):
        """Starts the batch processor worker."""
        self.start_button.setEnabled(False)
        self.close_button.setText("Cancel")

        self.worker_thread = QThread()
        self.processor_worker = BatchProcessorWorker(self.files_to_process, self.token, self.analysis_data)
        self.processor_worker.moveToThread(self.worker_thread)

        self.processor_worker.progress.connect(self.update_progress)
        self.processor_worker.file_completed.connect(self.update_file_status)
        self.processor_worker.finished.connect(self.on_batch_finished)
        self.processor_worker.error.connect(self.on_scan_error)  # Can reuse scan error handler

        self.worker_thread.started.connect(self.processor_worker.run)
        self.worker_thread.start()

    def update_progress(self, current: int, total: int, filename: str):
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Processing {current + 1}/{total}: {filename}")

    def update_file_status(self, filename: str, status: str):
        for row in range(self.results_table.rowCount()):
            item = self.results_table.item(row, 0)
            if item and item.text() == filename:
                self.results_table.setItem(row, 1, QTableWidgetItem(status))
                break

    def on_batch_finished(self):
        self.status_label.setText("Batch analysis complete.")
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.close_button.setText("Close")
        self.worker_thread.quit()

    def closeEvent(self, event):
        """Ensure worker threads are stopped on close."""
        if self.scanner_worker and self.worker_thread.isRunning():
            self.scanner_worker.stop()
        if self.processor_worker and self.worker_thread.isRunning():
            self.processor_worker.stop()
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait(1000)
        super().closeEvent(event)
