import requests
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QListWidget,
    QDialogButtonBox,
    QMessageBox,
    QInputDialog,
    QFileDialog,
    QListWidgetItem,
    QTextEdit,
)
from PySide6.QtCore import Qt

API_URL = "http://127.0.0.1:8000"

class RubricEditorDialog(QDialog):
    def __init__(self, rubric_name, rubric_content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Rubric: {rubric_name}")
        self.layout = QVBoxLayout(self)
        self.content_editor = QTextEdit()
        self.content_editor.setText(rubric_content)
        self.layout.addWidget(self.content_editor)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_content(self):
        return self.content_editor.toPlainText()

class RubricManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rubric Manager")
        self.setGeometry(150, 150, 500, 400)
        layout = QVBoxLayout(self)
        self.rubric_list = QListWidget()
        self.rubric_list.itemDoubleClicked.connect(self.edit_rubric)
        layout.addWidget(self.rubric_list)

        self.load_rubrics()

        button_box = QDialogButtonBox()
        self.add_button = button_box.addButton("Add from File...", QDialogButtonBox.ButtonRole.ActionRole)
        self.edit_button = button_box.addButton("Edit Selected", QDialogButtonBox.ButtonRole.ActionRole)
        self.remove_button = button_box.addButton("Remove Selected", QDialogButtonBox.ButtonRole.ActionRole)
        close_button = button_box.addButton(QDialogButtonBox.StandardButton.Close)

        close_button.clicked.connect(self.accept)
        self.add_button.clicked.connect(self.add_rubric_from_file)
        self.edit_button.clicked.connect(self.edit_rubric)
        self.remove_button.clicked.connect(self.remove_rubric)

        layout.addWidget(button_box)

    def load_rubrics(self):
        self.rubric_list.clear()
        try:
            response = requests.get(f"{API_URL}/rubrics/")
            response.raise_for_status()
            rubrics = response.json()
            for rubric in rubrics:
                item = QListWidgetItem(rubric['name'])
                item.setData(Qt.ItemDataRole.UserRole, rubric)
                self.rubric_list.addItem(item)
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Error", f"Failed to load rubrics from backend:\n{e}")

    def add_rubric_from_file(self):
        rubric_name, ok = QInputDialog.getText(self, "Add Rubric From File", "Enter a unique name for the new rubric:")
        if not (ok and rubric_name):
            return

        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Rubric Document', '', 'Text Files (*.txt);;All Files (*.*)')
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read file:\n{e}")
            return

        try:
            response = requests.post(f"{API_URL}/rubrics/", json={"name": rubric_name, "content": content})
            response.raise_for_status()
            QMessageBox.information(self, "Success", f"Rubric '{rubric_name}' added successfully.")
            self.load_rubrics()
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Error", f"Failed to save rubric to backend:\n{e.response.json()['detail'] if e.response else e}")

    def edit_rubric(self):
        selected_items = self.rubric_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Edit Rubric", "Please select a rubric to edit.")
            return

        item = selected_items[0]
        rubric_data = item.data(Qt.ItemDataRole.UserRole)

        dialog = RubricEditorDialog(rubric_data['name'], rubric_data['content'], self)
        if dialog.exec():
            new_content = dialog.get_content()
            new_name, ok = QInputDialog.getText(self, "Update Rubric Name", "Enter the new name for the rubric:", text=rubric_data['name'])
            if not (ok and new_name):
                return

            try:
                payload = {"name": new_name, "content": new_content}
                response = requests.put(f"{API_URL}/rubrics/{rubric_data['id']}", json=payload)
                response.raise_for_status()
                QMessageBox.information(self, "Success", "Rubric updated successfully.")
                self.load_rubrics()
            except requests.exceptions.RequestException as e:
                QMessageBox.critical(self, "Error", f"Failed to update rubric:\n{e.response.json()['detail'] if e.response else e}")


    def remove_rubric(self):
        selected_items = self.rubric_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Remove Rubric", "Please select a rubric to remove.")
            return

        item = selected_items[0]
        rubric_data = item.data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(self, "Confirm Deletion", f"Are you sure you want to delete '{rubric_data['name']}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                response = requests.delete(f"{API_URL}/rubrics/{rubric_data['id']}")
                response.raise_for_status()
                QMessageBox.information(self, "Success", f"Rubric '{rubric_data['name']}' has been deleted.")
                self.load_rubrics()
            except requests.exceptions.RequestException as e:
                QMessageBox.critical(self, "Database Error", f"Failed to delete rubric:\n{e.response.json()['detail'] if e.response else e}")
