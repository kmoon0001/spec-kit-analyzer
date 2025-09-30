#!/usr/bin/env python3
"""
Safe startup script for the Therapy Compliance Analyzer GUI.
Handles common startup issues gracefully.
"""
import sys
import os
import logging
import asyncio
import traceback

# --- Path Setup ---
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def safe_database_init():
    """Safely initialize database with error handling."""
    try:
        logger.info("Initializing database...")
        from src.database import init_db
        await init_db()
        logger.info("[OK] Database initialized successfully")
        return True
    except Exception as e:
        logger.warning(f"[WARN] Database initialization issue: {e}")
        logger.info("Continuing without database (some features may be limited)")
        return False

def check_dependencies():
    """Check critical dependencies."""
    try:
        import PyQt6
        logger.info("[OK] PyQt6 available")

        from src.gui.main_window import MainApplicationWindow
        logger.info("[OK] Main window imports OK")

        from src.core.performance_manager import performance_manager
        logger.info("[OK] Performance manager OK")

        return True
    except Exception as e:
        logger.error(f"[ERROR] Critical dependency missing: {e}")
        return False

def main():
    """Main application entry point with error handling."""
    try:
        logger.info("[START] Starting Therapy Compliance Analyzer...")

        # Check dependencies
        if not check_dependencies():
            logger.error("[ERROR] Cannot start - missing critical dependencies")
            return 1

        # Initialize database
        try:
            asyncio.run(safe_database_init())
        except Exception as e:
            logger.warning(f"Database setup issue (continuing): {e}")

        # Start GUI application
        logger.info("Starting GUI application...")
        from PyQt6.QtWidgets import QApplication
        from src.gui.main_window import MainApplicationWindow

        app = QApplication(sys.argv)

        # Set application properties
        app.setApplicationName("Therapy Compliance Analyzer")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("Clinical AI Solutions")

        # Create and start main window
        main_win = MainApplicationWindow()

        # Force window to appear
        main_win.show()
        main_win.raise_()
        main_win.activateWindow()

        # Start the application logic
        main_win.start()

        logger.info("[OK] Application started successfully")
        logger.info(f"Window visible: {main_win.isVisible()}")
        logger.info(f"Window size: {main_win.size().width()}x{main_win.size().height()}")

        return app.exec()

    except KeyboardInterrupt:
        logger.info("[STOP] Application stopped by user")
        return 0
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error: {e}")
        logger.error("Full traceback:")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
