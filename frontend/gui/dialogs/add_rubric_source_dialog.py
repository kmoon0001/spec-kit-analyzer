from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QDialogButtonBox,
)

class AddRubricSourceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Rubric Source")
        self.source = None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Where would you like to add a rubric from?"))
        self.library_button = QPushButton("From Pre-loaded Library")
        self.library_button.clicked.connect(self.select_library)
        layout.addWidget(self.library_button)
        self.file_button = QPushButton("From Local File")
        self.file_button.clicked.connect(self.select_file)
        layout.addWidget(self.file_button)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def select_library(self):
        self.source = 'library'
        self.accept()

    def select_file(self):
        self.source = 'file'
        self.accept()
