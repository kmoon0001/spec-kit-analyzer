#!/usr/bin/env python3
"""
GUI startup that ensures the window is visible immediately.
"""
import sys
import os
import logging
import asyncio

# Path setup
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def safe_database_init():
    """Initialize database safely."""
    try:
        from src.database import init_db
        await init_db()
        logger.info("✅ Database initialized")
        return True
    except Exception as e:
        logger.warning(f"Database issue (continuing): {e}")
        return False

def main():
    """Main function with immediate window display."""
    try:
        logger.info("🚀 Starting Therapy Compliance Analyzer...")

        # Initialize database first
        try:
            asyncio.run(safe_database_init())
        except Exception as e:
            logger.warning(f"Database setup issue: {e}")

        # Import GUI components
        from PyQt6.QtWidgets import QApplication
        from src.gui.main_window_working import ModernMainWindow

        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("Therapy Compliance Analyzer")

        # Create main window
        logger.info("Creating modern main window...")
        main_win = ModernMainWindow()

        # FORCE the window to show immediately
        main_win.show()
        main_win.raise_()
        main_win.activateWindow()

        logger.info("✅ Modern window should now be visible!")
        logger.info(f"Window visible: {main_win.isVisible()}")
        logger.info(f"Window size: {main_win.size().width()}x{main_win.size().height()}")

        # Process events to ensure window appears
        app.processEvents()

        # Start the application with modern loading
        logger.info("Starting modern application...")
        try:
            main_win.start()
        except Exception as e:
            logger.error(f"Error starting application: {e}")
            # Continue anyway - window should still be visible

        logger.info("🎯 Application ready! Window should be visible.")

        # Run the application
        return app.exec()

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
