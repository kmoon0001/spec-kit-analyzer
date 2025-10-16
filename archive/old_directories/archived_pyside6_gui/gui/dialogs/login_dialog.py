from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit


class LoginDialog(QDialog):
    """Standard dialog for user authentication."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QFormLayout(self)
        self.username_input = QLineEdit(self)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.layout.addRow(QLabel("Username:"), self.username_input)
        self.layout.addRow(QLabel("Password:"), self.password_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.layout.addWidget(self.button_box)

    def get_credentials(self):
        """Returns the entered username and password."""
        return self.username_input.text(), self.password_input.text()
