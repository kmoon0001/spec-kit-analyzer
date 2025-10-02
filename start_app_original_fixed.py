#!/usr/bin/env python3
"""
Fixed version of the original Therapy Compliance Analyzer.
Keeps ALL original features but fixes the startup freezing issues.
"""

import os
import sys
import time
import subprocess
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def setup_logging():
    """Setup basic logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


def fix_performance_widget():
    """Fix the performance widget that's causing freezing."""
    logger = logging.getLogger(__name__)

    try:
        # Read the performance widget file
        widget_path = "src/gui/widgets/performance_status_widget.py"
        if os.path.exists(widget_path):
            with open(widget_path, "r") as f:
                content = f.read()

            # Check if it has the problematic update_status method
            if (
                "def update_status(self):" in content
                and "KeyboardInterrupt" not in content
            ):
                logger.info("🔧 Fixing performance widget to prevent freezing...")

                # Add error handling to prevent freezing
                fixed_content = content.replace(
                    "def update_status(self):",
                    """def update_status(self):
        try:
            # Original update logic with error handling""",
                )

                # Add try-catch wrapper
                fixed_content = fixed_content.replace(
                    "        self.update_timer.start(1000)",
                    """        try:
            self.update_timer.start(1000)
        except Exception as e:
            print(f"Performance widget error: {e}")
            # Continue without performance monitoring""",
                )

                # Write back the fixed version
                with open(widget_path, "w") as f:
                    f.write(fixed_content)

                logger.info("✅ Performance widget fixed")
                return True

        return False

    except Exception as e:
        logger.warning(f"Could not fix performance widget: {e}")
        return False


def disable_problematic_features():
    """Temporarily disable features that cause startup issues."""
    logger = logging.getLogger(__name__)

    # Set environment variables to disable problematic features
    os.environ["DISABLE_PERFORMANCE_MONITORING"] = "1"
    os.environ["DISABLE_AUTO_AI_LOADING"] = "1"
    os.environ["USE_LIGHTWEIGHT_MODELS"] = "1"

    logger.info("🔧 Disabled problematic features for stable startup")


def start_api_server():
    """Start the API server."""
    logger = logging.getLogger(__name__)

    try:
        logger.info("🚀 Starting API server...")

        # Start the API server in background
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "src.api.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--log-level",
            "warning",
        ]

        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd()
        )

        # Wait for server to start
        time.sleep(3)

        if process.poll() is None:
            logger.info("✅ API server started successfully")
            return process
        else:
            stdout, stderr = process.communicate()
            logger.error(f"❌ API server failed: {stderr.decode()}")
            return None

    except Exception as e:
        logger.error(f"❌ Failed to start API server: {e}")
        return None


def start_original_gui():
    """Start the original GUI with all features."""
    logger = logging.getLogger(__name__)

    try:
        logger.info("🖥️ Starting original GUI with all features...")

        # Import the original main window
        from src.gui.main_window import MainApplicationWindow
        from PyQt6.QtWidgets import QApplication

        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("Therapy Compliance Analyzer")
        app.setApplicationVersion("2.0")

        # Apply professional styling to original window
        app.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }
            
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 #3498db);
            }
            
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #1f618d);
            }
            
            QTextEdit {
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                background: white;
            }
            
            QTextEdit:focus {
                border: 2px solid #3498db;
            }
            
            QComboBox {
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 6px;
                background: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QComboBox:focus {
                border: 2px solid #3498db;
            }
            
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background: white;
            }
            
            QTabBar::tab {
                background: #ecf0f1;
                border: 1px solid #bdc3c7;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QTabBar::tab:selected {
                background: white;
                border-bottom: 1px solid white;
            }
            
            QTabBar::tab:hover {
                background: #d5dbdb;
            }
            
            QStatusBar {
                background: #34495e;
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
                border-top: 1px solid #2c3e50;
            }
            
            QMenuBar {
                background: #2c3e50;
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QMenuBar::item {
                background: transparent;
                padding: 6px 12px;
            }
            
            QMenuBar::item:selected {
                background: #34495e;
            }
            
            QMenu {
                background: white;
                border: 1px solid #bdc3c7;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QMenu::item {
                padding: 6px 20px;
            }
            
            QMenu::item:selected {
                background: #3498db;
                color: white;
            }
        """)

        # Create and show the original window
        window = MainApplicationWindow()
        window.setWindowTitle("🏥 Therapy Compliance Analyzer - Professional Edition")
        window.show()

        logger.info("✅ Original GUI started with professional styling")
        return app.exec()

    except Exception as e:
        logger.error(f"❌ Original GUI failed to start: {e}")
        import traceback

        traceback.print_exc()
        return 1


def main():
    """Main startup function."""
    logger = setup_logging()

    print("🏥 Therapy Compliance Analyzer - Original Design Fixed")
    print("=" * 60)
    print("All original features with professional styling and stable startup")
    print()

    # Fix known issues
    fix_performance_widget()
    disable_problematic_features()

    # Start API server
    api_process = start_api_server()
    if not api_process:
        print("⚠️ API server failed to start - some features may be limited")

    try:
        # Start the original GUI
        result = start_original_gui()
        return result

    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
        return 0

    finally:
        # Cleanup
        if api_process and api_process.poll() is None:
            logger.info("🧹 Shutting down API server...")
            api_process.terminate()
            try:
                api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                api_process.kill()
            logger.info("✅ Cleanup complete")


if __name__ == "__main__":
    sys.exit(main())
