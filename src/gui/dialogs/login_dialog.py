from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QDialogButtonBox,
    QMessageBox,
)
from src.gui.dialogs.registration_dialog import RegistrationDialog
from src.auth import create_user


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.username = None
        self.password = None

        layout = QVBoxLayout(self)

        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)

        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.register_button = self.button_box.addButton("Register", QDialogButtonBox.ButtonRole.ActionRole)
        self.register_button.clicked.connect(self.show_registration_dialog)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def show_registration_dialog(self):
        reg_dialog = RegistrationDialog(self)
        if reg_dialog.exec() == QDialog.DialogCode.Accepted:
            username, password = reg_dialog.get_credentials()
            success, message = create_user(username, password)
            if success:
                QMessageBox.information(self, "Registration", message)
                self.username_input.setText(username)
                self.password_input.clear()
            else:
                QMessageBox.warning(self, "Registration Failed", message)

    def accept(self):
        self.username = self.username_input.text().strip()
        self.password = self.password_input.text()
        if not self.username or not self.password:
            QMessageBox.warning(self, "Input Error", "Username and password cannot be empty.")
            return
        super().accept()

    def get_credentials(self):
        return self.username, self.password
