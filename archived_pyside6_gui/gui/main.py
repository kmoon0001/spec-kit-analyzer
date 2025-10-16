import sys
import yaml

from PySide6.QtWidgets import QApplication, QMessageBox
import requests

from src.gui.dialogs.login_dialog import LoginDialog
from src.gui.main_window import MainApplicationWindow
from src.database.models import User


def authenticate_user() -> tuple[str, str] | None:
    """Handles the user authentication process, returning username and JWT on success."""
    dialog = LoginDialog()

    # Load API URL from config.yaml
    try:
        with open("config.yaml") as f:
            config = yaml.safe_load(f)
        api_url = config.get("paths", {}).get("api_url", "http://localhost:8100")
    except Exception as e:
        QMessageBox.critical(None, "Configuration Error", f"Could not load config.yaml: {e}")
        return None

    while True:
        if dialog.exec():
            username, password = dialog.get_credentials()

            if not username or not password:
                QMessageBox.warning(dialog, "Login Failed", "Please enter both username and password.")
                continue

            try:
                response = requests.post(
                    f"{api_url}/auth/token",
                    data={"username": username, "password": password},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
                token_data = response.json()
                access_token = token_data.get("access_token")
                if access_token:
                    return username, access_token
                else:
                    QMessageBox.warning(
                        dialog, "Login Failed", "Authentication successful, but no access token received."
                    )
            except requests.exceptions.ConnectionError:
                QMessageBox.critical(
                    dialog,
                    "Connection Error",
                    "Could not connect to the authentication server. Please ensure the backend API is running.",
                )
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    QMessageBox.warning(dialog, "Login Failed", "Invalid username or password.")
                else:
                    QMessageBox.critical(dialog, "Authentication Error", f"An unexpected error occurred: {e}")
            except Exception as e:
                QMessageBox.critical(dialog, "Login Error", f"An unexpected error occurred: {e}")
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

        # Load API URL from config.yaml
        try:
            with open("config.yaml") as f:
                config = yaml.safe_load(f)
            api_url = config.get("paths", {}).get("api_url", "http://localhost:8100")
        except Exception as e:
            QMessageBox.critical(None, "Configuration Error", f"Could not load config.yaml: {e}")
            return 1

        # Fetch user details from the backend
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(f"{api_url}/users/me", headers=headers)
            response.raise_for_status()
            user_data = response.json()

            # Create a User object from the fetched data
            # Note: This is a simplified instantiation. In a real scenario, you might want to
            # use a Pydantic model or a more robust way to construct the User object.
            current_user = User(
                id=user_data.get("id"),
                username=user_data.get("username"),
                hashed_password="",  # Password hash is not needed on the client side
                is_active=user_data.get("is_active", True),
                is_admin=user_data.get("is_admin", False),
                license_key=user_data.get("license_key"),
                created_at=user_data.get("created_at"),
                updated_at=user_data.get("updated_at"),
                preferences=user_data.get("preferences"),
            )

            # Pass the authenticated user and token to the main window
            main_win = MainApplicationWindow(user=current_user, token=access_token)
            main_win.show()
            return app.exec()
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(None, "Connection Error", "Could not connect to the API server to fetch user details.")
        except requests.exceptions.HTTPError as e:
            QMessageBox.critical(None, "User Fetch Error", f"Failed to fetch user details: {e}")
        except Exception as e:
            QMessageBox.critical(None, "Application Error", f"An unexpected error occurred during user setup: {e}")

    return 0  # User cancelled login or an error occurred


if __name__ == "__main__":
    sys.exit(main())
