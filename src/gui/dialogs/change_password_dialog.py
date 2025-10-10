from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
)


class ChangePasswordDialog(QDialog):
    """A dialog for changing the user's password."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change Password")

        self.layout = QFormLayout(self)
        self.current_password_input = QLineEdit(self)
        self.current_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.new_password_input = QLineEdit(self)
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.confirm_password_input = QLineEdit(self)
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.layout.addRow(QLabel("Current Password:"), self.current_password_input)
        self.layout.addRow(QLabel("New Password:"), self.new_password_input)
        self.layout.addRow(QLabel("Confirm New Password:"), self.confirm_password_input)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        )
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)

        self.layout.addWidget(self.button_box)

    def validate_and_accept(self):
        """Validates the form before accepting the dialog."""
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not all(
            [self.current_password_input.text(), new_password, confirm_password],
        ):
            QMessageBox.warning(self, "Input Error", "All fields are required.")
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "Input Error", "The new passwords do not match.")
            return

        self.accept()

    def get_passwords(self):
        """Returns the current and new passwords."""
        return self.current_password_input.text(), self.new_password_input.text()
