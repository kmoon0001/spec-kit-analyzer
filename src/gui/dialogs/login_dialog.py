import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QDialogButtonBox, QLabel, QMessageBox
)

class LoginDialog(QDialog):
    """
    A dialog that prompts the user for a username and password.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Login')

        # Layout
        layout = QVBoxLayout(self)

        # Username
        self.username_label = QLabel('Username:')
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('Enter your username')
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)

        # Set default username if environment variable is set
        default_user = os.environ.get("DEFAULT_USER")
        if default_user:
            self.username_input.setText(default_user)

        # Password
        self.password_label = QLabel('Password:')
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText('Enter your password')
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        # OK and Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def accept(self):
        """
        Overrides the default accept behavior to validate input before closing.
        """
        if not self.username_input.text() or not self.password_input.text():
            QMessageBox.warning(self, "Input Error", "Username and password cannot be empty.")
        else:
            super().accept()

    def get_credentials(self) -> (str, str):
        """
        Returns the entered username and password.

        Returns:
            A tuple containing the username and password as strings.
        """
        return self.username_input.text(), self.password_input.text()