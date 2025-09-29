from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QListWidget,
    QDialogButtonBox,
    QMessageBox,
    QInputDialog,
    QFileDialog,
    QListWidgetItem,
    QTextEdit,
    QLineEdit,
    QFormLayout,
    QPushButton,
)
from PyQt6.QtCore import Qt, QThread
from typing import Dict, Any, List

from ..workers.rubric_management_worker import (
    RubricLoaderWorker,
    RubricAdderWorker,
    RubricEditorWorker,
    RubricDeleterWorker,
)

class RubricEditorDialog(QDialog):
    """A dialog for editing the name and content of a rubric."""
    def __init__(self, rubric_name: str, rubric_content: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Rubric")
        self.layout = QFormLayout(self)
        self.name_editor = QLineEdit(rubric_name)
        self.content_editor = QTextEdit()
        self.content_editor.setText(rubric_content)
        self.layout.addRow("Name:", self.name_editor)
        self.layout.addRow("Content:", self.content_editor)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_data(self) -> Dict[str, str]:
        return {
            "name": self.name_editor.text(),
            "content": self.content_editor.toPlainText(),
        }

class RubricManagerDialog(QDialog):
    """A dialog for managing compliance rubrics asynchronously."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker_thread: QThread | None = None
        self.worker: QObject | None = None
        self.setWindowTitle("Rubric Manager")
        self.setGeometry(150, 150, 500, 400)
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)
        self.rubric_list = QListWidget()
        self.rubric_list.itemDoubleClicked.connect(self.edit_rubric)
        layout.addWidget(self.rubric_list)

        self.button_box = QDialogButtonBox()
        self.add_button = self.button_box.addButton(
            "Add from File...", QDialogButtonBox.ButtonRole.ActionRole
        )
        self.edit_button = self.button_box.addButton(
            "Edit Selected", QDialogButtonBox.ButtonRole.ActionRole
        )
        self.remove_button = self.button_box.addButton(
            "Remove Selected", QDialogButtonBox.ButtonRole.ActionRole
        )
        close_button = self.button_box.addButton(QDialogButtonBox.StandardButton.Close)

        close_button.clicked.connect(self.accept)
        self.add_button.clicked.connect(self.add_rubric_from_file)
        self.edit_button.clicked.connect(self.edit_rubric)
        self.remove_button.clicked.connect(self.remove_rubric)

        layout.addWidget(self.button_box)
        self.load_rubrics()

    def _run_worker(self, worker: QObject):
        """Helper to run a worker on a new thread."""
        if self.worker_thread and self.worker_thread.isRunning():
            QMessageBox.warning(self, "Busy", "An operation is already in progress.")
            return

        self.set_buttons_enabled(False)
        self.worker_thread = QThread()
        self.worker = worker
        self.worker.moveToThread(self.worker_thread)

        # Connect signals from the worker
        if hasattr(self.worker, "success"):
            self.worker.success.connect(self.load_rubrics)
        if hasattr(self.worker, "error"):
            self.worker.error.connect(self._on_worker_error)

        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(lambda: self.set_buttons_enabled(True))

        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

    def set_buttons_enabled(self, enabled: bool):
        """Enable or disable action buttons."""
        self.add_button.setEnabled(enabled)
        self.edit_button.setEnabled(enabled)
        self.remove_button.setEnabled(enabled)

    def load_rubrics(self):
        """Loads all rubrics asynchronously."""
        self.set_buttons_enabled(False)
        self.rubric_list.clear()
        self.rubric_list.addItem("Loading rubrics...")

        self.worker_thread = QThread()
        self.worker = RubricLoaderWorker()
        self.worker.moveToThread(self.worker_thread)

        self.worker.success.connect(self._on_rubrics_loaded)
        self.worker.error.connect(self._on_worker_error)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(lambda: self.set_buttons_enabled(True))

        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

    def _on_rubrics_loaded(self, rubrics: List[Dict[str, Any]]):
        """Slot to handle successfully loaded rubrics."""
        self.rubric_list.clear()
        if not rubrics:
            self.rubric_list.addItem("No rubrics found.")
            return
        for rubric in rubrics:
            item = QListWidgetItem(rubric["name"])
            item.setData(Qt.ItemDataRole.UserRole, rubric)
            self.rubric_list.addItem(item)

    def _on_worker_error(self, error_message: str):
        """Slot to display an error message from a worker."""
        QMessageBox.critical(self, "Error", f"An error occurred: {error_message}")
        self.load_rubrics() # Refresh the list on error

    def add_rubric_from_file(self):
        rubric_name, ok = QInputDialog.getText(
            self, "Add Rubric", "Enter a unique name for the new rubric:"
        )
        if not (ok and rubric_name):
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Rubric Document", "", "Text Files (*.txt)"
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            data = {"name": rubric_name, "content": content, "category": "general"}
            self._run_worker(RubricAdderWorker(data=data))
        except IOError as e:
            QMessageBox.critical(self, "File Error", f"Failed to read file: {e}")

    def edit_rubric(self):
        selected_item = self.rubric_list.currentItem()
        if not selected_item or not selected_item.data(Qt.ItemDataRole.UserRole):
            return

        rubric_data = selected_item.data(Qt.ItemDataRole.UserRole)
        dialog = RubricEditorDialog(rubric_data["name"], rubric_data["content"], self)
        if dialog.exec():
            new_data = dialog.get_data()
            new_data["category"] = rubric_data.get("category", "general")
            self._run_worker(RubricEditorWorker(rubric_id=rubric_data["id"], data=new_data))

    def remove_rubric(self):
        selected_item = self.rubric_list.currentItem()
        if not selected_item or not selected_item.data(Qt.ItemDataRole.UserRole):
            return

        rubric_data = selected_item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete '{rubric_data['name']}'?",
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._run_worker(RubricDeleterWorker(rubric_id=rubric_data["id"]))

    def closeEvent(self, event):
        """Ensure worker thread is stopped on close."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait(1000) # Wait up to 1 second
        super().closeEvent(event)