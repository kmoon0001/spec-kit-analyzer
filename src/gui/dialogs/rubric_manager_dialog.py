from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QListWidgetItem,
    QMessageBox,
    QTextEdit,
)

from src.config import get_settings

from ..workers.rubric_api_worker import RubricApiWorker

settings = get_settings()
API_URL = settings.paths.api_url


class RubricEditorDialog(QDialog):
    """Dialog for creating and editing a single rubric."""

    def __init__(self, rubric_data: dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Rubric")
        self.setMinimumWidth(450)
        self.layout = QFormLayout(self)

        self.name_editor = QLineEdit(rubric_data.get("name", ""))
        self.regulation_editor = QTextEdit()
        self.regulation_editor.setText(rubric_data.get("regulation", ""))
        self.common_pitfalls_editor = QTextEdit()
        self.common_pitfalls_editor.setText(rubric_data.get("common_pitfalls", ""))
        self.best_practice_editor = QTextEdit()
        self.best_practice_editor.setText(rubric_data.get("best_practice", ""))

        self.layout.addRow("Name:", self.name_editor)
        self.layout.addRow("Regulation:", self.regulation_editor)
        self.layout.addRow("Common Pitfalls:", self.common_pitfalls_editor)
        self.layout.addRow("Best Practice:", self.best_practice_editor)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_data(self) -> dict[str, Any]:
        """Returns the data entered in the editor fields."""
        return {
            "name": self.name_editor.text(),
            "regulation": self.regulation_editor.toPlainText(),
            "common_pitfalls": self.common_pitfalls_editor.toPlainText(),
            "best_practice": self.best_practice_editor.toPlainText(),
            "category": "default",  # Or derive this from UI if needed
        }


class RubricManagerDialog(QDialog):
    """Asynchronous dialog for managing compliance rubrics."""

    def _run_api_call(self, method: Callable, *args, on_success: Callable):
        """Generic method to run an API call in a background thread."""
        self.set_ui_busy(True)
        self.worker_thread = QThread()
        self.worker = RubricApiWorker(self.token)
        self.worker.moveToThread(self.worker_thread)

        self.worker.success.connect(on_success)
        self.worker.error.connect(self.on_api_error)

        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(lambda: self.set_ui_busy(False))

        worker_method = getattr(self.worker, method.__name__)
        self.worker_thread.started.connect(lambda: worker_method(*args))
        self.worker_thread.start()

    def set_ui_busy(self, busy: bool):
        """Disable buttons and show status while the worker is active."""
        self.button_box.setEnabled(not busy)
        if busy:
            self.status_label.setText("Communicating with API...")
        else:
            self.status_label.setText("")

    def on_api_error(self, error_message: str):
        """Handle and display API errors."""
        QMessageBox.critical(self, "API Error", error_message)
        self.status_label.setText("Error occurred.")

    # --- CRUD Operations ---

    def load_rubrics(self):
        """Loads all rubrics from the API asynchronously."""
        self._run_api_call(RubricApiWorker.get_all, on_success=self._on_load_success)

    def _on_load_success(self, rubrics: list[dict[str, Any]]):
        """Populate the list widget when rubrics are loaded."""
        self.rubric_list.clear()
        if not rubrics:
            self.status_label.setText("No rubrics found.")
            return

        for rubric in rubrics:
            item = QListWidgetItem(rubric.get("name", "Unnamed Rubric"))
            item.setData(Qt.ItemDataRole.UserRole, rubric)
            self.rubric_list.addItem(item)
        self.status_label.setText(f"Loaded {len(rubrics)} rubrics.")

    def add_rubric(self):
        """Opens the editor to add a new rubric."""
        editor = RubricEditorDialog({}, self)
        if not editor.exec():
            return

        new_data = editor.get_data()
        if not new_data.get("name"):
            QMessageBox.warning(self, "Input Error", "Rubric name cannot be empty.")
            return

        self._run_api_call(
            RubricApiWorker.create,
            new_data,
            on_success=lambda _: self.load_rubrics())

    def edit_rubric(self):
        """Opens the editor to modify the selected rubric."""
        selected_item = self.rubric_list.currentItem()
        if not selected_item:
            QMessageBox.information(self, "No Selection", "Please select a rubric to edit.")
            return

        rubric_data = selected_item.data(Qt.ItemDataRole.UserRole)
        editor = RubricEditorDialog(rubric_data, self)
        if not editor.exec():
            return

        updated_data = editor.get_data()
        rubric_id = rubric_data.get("id")
        if not rubric_id:
            self.on_api_error("Cannot edit rubric: Missing ID.")
            return

        self._run_api_call(
            RubricApiWorker.update,
            rubric_id,
            updated_data,
            on_success=lambda _: self.load_rubrics())

    def remove_rubric(self):
        """Removes the selected rubric after confirmation."""
        selected_item = self.rubric_list.currentItem()
        if not selected_item:
            QMessageBox.information(self, "No Selection", "Please select a rubric to remove.")
            return

        rubric_data = selected_item.data(Qt.ItemDataRole.UserRole)
        rubric_id = rubric_data.get("id")
        rubric_name = rubric_data.get("name", "the selected rubric")

        if not rubric_id:
            self.on_api_error("Cannot remove rubric: Missing ID.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete '{rubric_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._run_api_call(
            RubricApiWorker.delete,
            rubric_id,
            on_success=lambda _: self.load_rubrics())

    def closeEvent(self, event):
        """Ensure worker thread is stopped on close."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait(1000)  # Wait up to 1s
        super().closeEvent(event)
