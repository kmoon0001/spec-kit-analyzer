import requests
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QDialogButtonBox, QMessageBox, 
    QInputDialog, QFileDialog, QListWidgetItem, QTextEdit, QLineEdit, QFormLayout
)
from PyQt6.QtCore import Qt

API_URL = "http://127.0.0.1:8000"

class RubricEditorDialog(QDialog):
    def __init__(self, rubric_name, rubric_content, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Rubric")
        self.layout = QFormLayout(self)
        self.name_editor = QLineEdit(rubric_name)
        self.content_editor = QTextEdit()
        self.content_editor.setText(rubric_content)
        self.layout.addRow("Name:", self.name_editor)
        self.layout.addRow("Content:", self.content_editor)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_data(self):
        return {"name": self.name_editor.text(), "content": self.content_editor.toPlainText()}

class RubricManagerDialog(QDialog):
    def __init__(self, token: str, parent=None):
        super().__init__(parent)
        self.token = token
        self.setWindowTitle("Rubric Manager")
        self.setGeometry(150, 150, 500, 400)
        layout = QVBoxLayout(self)
        self.rubric_list = QListWidget()
        self.rubric_list.itemDoubleClicked.connect(self.edit_rubric)
        layout.addWidget(self.rubric_list)

        button_box = QDialogButtonBox()
        add_button = button_box.addButton("Add from File...", QDialogButtonBox.ButtonRole.ActionRole)
        edit_button = button_box.addButton("Edit Selected", QDialogButtonBox.ButtonRole.ActionRole)
        remove_button = button_box.addButton("Remove Selected", QDialogButtonBox.ButtonRole.ActionRole)
        close_button = button_box.addButton(QDialogButtonBox.StandardButton.Close)

        close_button.clicked.connect(self.accept)
        add_button.clicked.connect(self.add_rubric_from_file)
        edit_button.clicked.connect(self.edit_rubric)
        remove_button.clicked.connect(self.remove_rubric)

        layout.addWidget(button_box)
        self.load_rubrics()

    def load_rubrics(self):
        self.rubric_list.clear()
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{API_URL}/rubrics/", headers=headers)
            response.raise_for_status()
            for rubric in response.json():
                item = QListWidgetItem(rubric['name'])
                item.setData(Qt.ItemDataRole.UserRole, rubric)
                self.rubric_list.addItem(item)
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Error", f"Failed to load rubrics: {e}")

    def add_rubric_from_file(self):
        rubric_name, ok = QInputDialog.getText(self, "Add Rubric", "Enter a unique name for the new rubric:")
        if not (ok and rubric_name): return

        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Rubric Document', '', 'Text Files (*.txt)')
        if not file_path: return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(f"{API_URL}/rubrics/", json={"name": rubric_name, "content": content}, headers=headers)
            response.raise_for_status()
            self.load_rubrics()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add rubric: {e}")

    def edit_rubric(self):
        selected_item = self.rubric_list.currentItem()
        if not selected_item: return

        rubric_data = selected_item.data(Qt.ItemDataRole.UserRole)
        dialog = RubricEditorDialog(rubric_data['name'], rubric_data['content'], self)
        if dialog.exec():
            new_data = dialog.get_data()
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                response = requests.put(f"{API_URL}/rubrics/{rubric_data['id']}", json=new_data, headers=headers)
                response.raise_for_status()
                self.load_rubrics()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update rubric: {e}")

    def remove_rubric(self):
        selected_item = self.rubric_list.currentItem()
        if not selected_item: return

        rubric_data = selected_item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "Confirm Deletion", f"Are you sure you want to delete '{rubric_data['name']}'?")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                response = requests.delete(f"{API_URL}/rubrics/{rubric_data['id']}", headers=headers)
                response.raise_for_status()
                self.load_rubrics()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete rubric: {e}")
