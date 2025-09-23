import os
import sqlite3
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QListWidget,
    QDialogButtonBox,
    QMessageBox,
    QInputDialog,
    QFileDialog,
    QListWidgetItem,
)
from src.parsing import parse_document_content
from .add_rubric_source_dialog import AddRubricSourceDialog
from .library_selection_dialog import LibrarySelectionDialog

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, '..', '..', 'data', 'compliance.db')

class RubricManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rubric Manager")
        self.setGeometry(150, 150, 400, 300)
        layout = QVBoxLayout(self)
        self.rubric_list = QListWidget()
        layout.addWidget(self.rubric_list)
        self.load_rubrics()
        button_box = QDialogButtonBox()
        self.add_button = button_box.addButton("Add...", QDialogButtonBox.ButtonRole.ActionRole)
        self.remove_button = button_box.addButton("Remove", QDialogButtonBox.ButtonRole.ActionRole)
        close_button = button_box.addButton(QDialogButtonBox.StandardButton.Close)
        close_button.clicked.connect(self.accept)
        self.add_button.clicked.connect(self.add_rubric)
        self.remove_button.clicked.connect(self.remove_rubric)
        layout.addWidget(button_box)

    def load_rubrics(self):
        self.rubric_list.clear()
        try:
            if not os.path.exists(DATABASE_PATH):
                return
            with sqlite3.connect(DATABASE_PATH) as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, name FROM rubrics ORDER BY name ASC")
                for rubric_id, name in cur.fetchall():
                    item = QListWidgetItem(name)
                    item.setData(Qt.ItemDataRole.UserRole, rubric_id)
                    self.rubric_list.addItem(item)
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to load rubrics from database:\n{e}")

    def add_rubric(self):
        source_dialog = AddRubricSourceDialog(self)
        if not source_dialog.exec():
            return
        if source_dialog.source == 'file':
            self.add_rubric_from_file()
        elif source_dialog.source == 'library':
            self.add_rubric_from_library()

    def add_rubric_from_file(self):
        rubric_name, ok = QInputDialog.getText(self, "Add Rubric From File", "Enter a unique name for the new rubric:")
        if not (ok and rubric_name):
            return
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Rubric Document', '', 'Supported Files(*.pdf *.docx *.xlsx *.xls *.csv *.png *.jpg *.jpeg *.gif *.bmp *.tiff);;All Files(*.*)')
        if not file_path:
            return
        content = parse_document_content(file_path)
        if content[0][0].startswith("Error:"):
            QMessageBox.critical(self, "Error", f"Failed to parse rubric document:\n{content[0][0]}")
            return
        content_str = "\n".join([text for text, source in content])
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO rubrics (name, content) VALUES(?, ?)", (rubric_name, content_str))
                conn.commit()
                QMessageBox.information(self, "Success", f"Rubric '{rubric_name}' added successfully.")
                self.load_rubrics()
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Error", f"A rubric with the name '{rubric_name}' already exists. Please choose a unique name.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save rubric to database:\n{e}")

    def add_rubric_from_library(self):
        lib_dialog = LibrarySelectionDialog(self)
        if not lib_dialog.exec():
            return
        rubric_name = lib_dialog.selected_name
        rubric_path = lib_dialog.selected_path
        content = parse_document_content(rubric_path)
        if content[0][0].startswith("Error:"):
            QMessageBox.critical(self, "Error", f"Failed to parse library rubric:\n{content[0][0]}")
            return
        content_str = "\n".join([text for text, source in content])
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO rubrics (name, content) VALUES(?, ?)", (rubric_name, content_str))
                conn.commit()
                QMessageBox.information(self, "Success", f"Rubric '{rubric_name}' added from library.")
                self.load_rubrics()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Already Exists", f"The library rubric '{rubric_name}' is already in your database.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save rubric to database:\n{e}")

    def remove_rubric(self):
        selected_items = self.rubric_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Remove Rubric", "Please select a rubric to remove.")
            return
        item = selected_items[0]
        rubric_id = item.data(Qt.ItemDataRole.UserRole)
        rubric_name = item.text()
        reply = QMessageBox.question(self, "Confirm Deletion", f"Are you sure you want to permanently delete the rubric '{rubric_name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM rubrics WHERE id = ?", (rubric_id,))
                    conn.commit()
                QMessageBox.information(self, "Success", f"Rubric '{rubric_name}' has been deleted.")
                self.load_rubrics()
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to delete rubric:\n{e}")
