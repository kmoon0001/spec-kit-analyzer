import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
)


class LibrarySelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select from Library")
        self.selected_path = None
        self.selected_name = None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select a pre-loaded rubric to add:"))
        self.library_list = QListWidget()
        layout.addWidget(self.library_list)
        self.populate_library_list()
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        )
        button_box.accepted.connect(self.confirm_selection)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def populate_library_list(self):
        rubrics_dir = os.path.join("resources", "rubrics")
        if not os.path.isdir(rubrics_dir):
            self.library_list.addItem("No library found.")
            self.library_list.setEnabled(False)
            return
        for filename in os.listdir(rubrics_dir):
            if filename.endswith(".txt"):
                display_name = os.path.splitext(filename)[0].replace("_", " ").title()
                item = QListWidgetItem(display_name)
                item.setData(
                    Qt.ItemDataRole.UserRole, os.path.join(rubrics_dir, filename),
                )
                self.library_list.addItem(item)

    def confirm_selection(self):
        selected_items = self.library_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self, "Selection Required", "Please select a rubric from the list.",
            )
            return
        item = selected_items[0]
        self.selected_name = item.text()
        self.selected_path = item.data(Qt.ItemDataRole.UserRole)
        self.accept()
