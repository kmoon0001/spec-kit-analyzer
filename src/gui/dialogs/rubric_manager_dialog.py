import requests
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QListWidget,
    QDialogButtonBox,
    QMessageBox,
    QListWidgetItem,
    QTextEdit,
    QLineEdit,
    QFormLayout,
)
from PyQt6.QtCore import Qt

from src.config import get_settings

settings = get_settings()
API_URL = settings.paths.api_url


class RubricEditorDialog(QDialog):
    def __init__(self, rubric_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Rubric")
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
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_data(self):
        return {
            "name": self.name_editor.text(),
            "regulation": self.regulation_editor.toPlainText(),
            "common_pitfalls": self.common_pitfalls_editor.toPlainText(),
            "best_practice": self.best_practice_editor.toPlainText(),
            "category": "default",
        }


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
        add_button = button_box.addButton(
            "Add Rubric...", QDialogButtonBox.ButtonRole.ActionRole
        )
        edit_button = button_box.addButton(
            "Edit Selected", QDialogButtonBox.ButtonRole.ActionRole
        )
        remove_button = button_box.addButton(
            "Remove Selected", QDialogButtonBox.ButtonRole.ActionRole
        )
        close_button = button_box.addButton(QDialogButtonBox.StandardButton.Close)

        if close_button:
            close_button.clicked.connect(self.accept)
        if add_button:
            add_button.clicked.connect(self.add_rubric)
        if edit_button:
            edit_button.clicked.connect(self.edit_rubric)
        if remove_button:
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
                item = QListWidgetItem(rubric["name"])
                item.setData(Qt.ItemDataRole.UserRole, rubric)
                self.rubric_list.addItem(item)
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Error", f"Failed to load rubrics: {e}")

    def add_rubric(self):
        dialog = RubricEditorDialog({}, self)
        if dialog.exec():
            new_data = dialog.get_data()
            if not new_data.get("name"):
                QMessageBox.warning(self, "Input Error", "Rubric name cannot be empty.")
                return
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                response = requests.post(
                    f"{API_URL}/rubrics/",
                    json=new_data,
                    headers=headers,
                )
                response.raise_for_status()
                self.load_rubrics()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add rubric: {e}")

    def edit_rubric(self):
        selected_item = self.rubric_list.currentItem()
        if not selected_item:
            return

        rubric_data = selected_item.data(Qt.ItemDataRole.UserRole)
        dialog = RubricEditorDialog(rubric_data, self)
        if dialog.exec():
            new_data = dialog.get_data()
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                response = requests.put(
                    f"{API_URL}/rubrics/{rubric_data['id']}",
                    json=new_data,
                    headers=headers,
                )
                response.raise_for_status()
                self.load_rubrics()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update rubric: {e}")

    def remove_rubric(self):
        selected_item = self.rubric_list.currentItem()
        if not selected_item:
            return

        rubric_data = selected_item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete '{rubric_data['name']}'?",
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                response = requests.delete(
                    f"{API_URL}/rubrics/{rubric_data['id']}", headers=headers
                )
                response.raise_for_status()
                self.load_rubrics()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete rubric: {e}")
