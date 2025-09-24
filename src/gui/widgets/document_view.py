from PySide6.QtWidgets import QTextEdit

class DocumentView(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setPlaceholderText("Upload a document to see its content here.")
        self.setReadOnly(True)
 
