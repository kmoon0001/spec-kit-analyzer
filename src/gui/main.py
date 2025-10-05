
import sys
import asyncio
from typing import Optional, Tuple
from PySide6.QtWidgets import QApplication, QMessageBox

from src.gui.main_window import MainApplicationWindow
from src.gui.dialogs.login_dialog import LoginDialog
from src.database import init_db, crud, models
from src.auth import AuthService
from src.database.database import get_async_db

async def authenticate_user(db_session) -> Optional[Tuple[models.User, str]]:
    """Handles the user authentication process, returning the user and a JWT on success."""
    dialog = LoginDialog()
    auth_service = AuthService()

    while True:
        if dialog.exec():
            username, password = dialog.get_credentials()
            user = await crud.get_user_by_username(db_session, username=username)

            if user and auth_service.verify_password(password, user.hashed_password):
                # On successful login, create an access token
                access_token = auth_service.create_access_token(data={"sub": user.username})
                return user, access_token
            else:
                QMessageBox.warning(dialog, "Login Failed", "Invalid username or password.")
        else:
            # User cancelled the login dialog
            return None

async def main():
    """Main async function to run the application."""
    await init_db()

    app = QApplication(sys.argv)

    auth_result = None
    async for db_session in get_async_db():
        auth_result = await authenticate_user(db_session)
        break  # We only need one session

    if auth_result:
        authenticated_user, access_token = auth_result
        # Pass the authenticated user and token to the main window
        main_win = MainApplicationWindow(user=authenticated_user, token=access_token)
        main_win.show()
        sys.exit(app.exec())
    else:
        sys.exit(0) # User cancelled login

if __name__ == "__main__":
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        print("Asyncio loop is already running. Scheduling main.")
        loop.create_task(main())
    else:
        print("Starting new asyncio event loop.")
        asyncio.run(main())
