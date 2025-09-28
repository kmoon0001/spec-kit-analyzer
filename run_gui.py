import sys
import os
import logging

# --- The Definitive Path Solution ---
# 1. Get the absolute path of the directory where this script is located.
# This will be the project's root directory.
project_root = os.path.dirname(os.path.abspath(__file__))

# 2. Add the project root to the Python path.
# This ensures that any `import src. ...` statements will work correctly.
sys.path.insert(0, project_root)

# 3. Now that the path is correct, we can import and run the application.
from PyQt6.QtWidgets import QApplication  # noqa: E402
from src.gui.main_window import MainApplicationWindow  # noqa: E402

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def initialize_database():
    """Initialize database asynchronously."""
    try:
        from src.database import init_db
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        # Continue anyway - app can work without database for basic functionality

if __name__ == "__main__":
    import asyncio
    
    logger.info("Initializing database...")
    try:
        asyncio.run(initialize_database())
    except Exception as e:
        logger.warning(f"Database setup issue (continuing anyway): {e}")

    logger.info("Starting GUI application...")
    app = QApplication(sys.argv)
    main_win = MainApplicationWindow()
    # Start the application logic (loading models, showing login) after the window is created.
    main_win.start()
    # The main window will be shown by the start() method after a successful login.
    sys.exit(app.exec())
