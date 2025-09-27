from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QLabel
)

class LoginDialog(QDialog):
<<<<<<< HEAD
    """
    A mock dialog for user login.
    """
||||||| c46cdd8
    """
    A placeholder for the missing LoginDialog.
    This class is intended to resolve an ImportError and allow the test suite to run.
    """
=======
    """A mock dialog for user login."""
>>>>>>> origin/main
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")

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
<<<<<<< HEAD
        """Returns the entered username and password."""
        return self.username_input.text(), self.password_input.text()
||||||| c46cdd8
        return "user", "password"
=======
        """Returns the entered username and password."""
        return self.username_input.text(), self.password_input.text()
>>>>>>> origin/main
