import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from src.auth import AuthService
from src.gui.dialogs.login_dialog import LoginDialog
from src.gui.main_window import MainApplicationWindow


def authenticate_user() -> tuple[str, str] | None:
    """Handles the user authentication process, returning username and JWT on success."""
    dialog = LoginDialog()
    auth_service = AuthService()

    while True:
        if dialog.exec():
            username, password = dialog.get_credentials()

            # For now, use simple authentication without database
            # In production, this would check against the database
            if username and password:  # Basic validation
                # Create a mock user for the session
                access_token = auth_service.create_access_token(data={"sub": username})
                return username, access_token
            QMessageBox.warning(dialog, "Login Failed", "Please enter both username and password.")
        else:
            # User cancelled the login dialog
            return None


def main():
    """Main function to run the application."""
    app = QApplication(sys.argv)

    # Authenticate user
    auth_result = authenticate_user()

    if auth_result:
        username, access_token = auth_result

        # Create a mock user object for compatibility
        class MockUser:
            def __init__(self, username: str):
                self.username = username
                self.is_admin = True  # For demo purposes

        mock_user = MockUser(username)

        # Pass the authenticated user and token to the main window
        main_win = MainApplicationWindow(user=mock_user, token=access_token)
        main_win.show()
        return app.exec()
    return 0  # User cancelled login


if __name__ == "__main__":
    pass
if __name__ == "__main__":
    pass
if __name__ == "__main__":
    sys.exit(main())
