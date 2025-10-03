import sys
import asyncio
from PyQt6.QtWidgets import QApplication, QMessageBox

from src.gui.main_window import MainApplicationWindow
from src.gui.dialogs.login_dialog import LoginDialog
from src.database import init_db, crud
from src.auth import AuthService
from src.database.database import get_async_db

async def authenticate_user(db_session):
    """Handles the user authentication process."""
    dialog = LoginDialog()
    while True:
        if dialog.exec():
            username, password = dialog.get_credentials()
            user = await crud.get_user_by_username(db_session, username=username)

            if user and AuthService.verify_password(password, user.hashed_password):
                return user
            else:
                QMessageBox.warning(dialog, "Login Failed", "Invalid username or password.")
        else:
            # User cancelled the login dialog
            return None

async def main():
    """Main async function to run the application."""
    # Initialize the database
    await init_db()

    app = QApplication(sys.argv)

    # Get a database session
    authenticated_user = None
    async for db_session in get_async_db():
        authenticated_user = await authenticate_user(db_session)
        break  # We only need one session

    if authenticated_user:
        main_win = MainApplicationWindow()
        main_win.show()
        sys.exit(app.exec())
    else:
        sys.exit(0) # User cancelled login

if __name__ == "__main__":
    # In some environments, the asyncio event loop might already be running.
    # This handles the case where we are running in such an environment.
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # 'RuntimeError: There is no current event loop...'
        loop = None

    if loop and loop.is_running():
        print("Asyncio loop is already running. Scheduling main.")
        loop.create_task(main())
    else:
        print("Starting new asyncio event loop.")
        asyncio.run(main())