#!/usr/bin/env python3
"""
Fixed startup script for Therapy Compliance Analyzer.
Uses lightweight configuration to avoid freezing issues.
"""

import os
import sys
import time
import signal
import subprocess
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def setup_logging():
    """Setup basic logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are available."""
    logger = logging.getLogger(__name__)
    
    try:
        import PyQt6
        logger.info("✅ PyQt6 available")
    except ImportError:
        logger.error("❌ PyQt6 not available - GUI will not work")
        return False
    
    try:
        from src.core.ner import NERAnalyzer
        logger.info("✅ NER module available")
    except ImportError as e:
        logger.error(f"❌ NER module not available: {e}")
        return False
    
    try:
        from src.core.analysis_service import AnalysisService
        logger.info("✅ Analysis service available")
    except ImportError as e:
        logger.error(f"❌ Analysis service not available: {e}")
        return False
    
    return True

def use_lite_config():
    """Switch to lightweight configuration."""
    logger = logging.getLogger(__name__)
    
    # Backup original config
    if os.path.exists("config.yaml") and not os.path.exists("config_original.yaml"):
        os.rename("config.yaml", "config_original.yaml")
        logger.info("📁 Backed up original config to config_original.yaml")
    
    # Use lite config
    if os.path.exists("config_lite.yaml"):
        if os.path.exists("config.yaml"):
            os.remove("config.yaml")
        os.rename("config_lite.yaml", "config.yaml")
        logger.info("⚡ Switched to lightweight configuration")
        return True
    else:
        logger.error("❌ config_lite.yaml not found")
        return False

def start_api_server():
    """Start the API server in background."""
    logger = logging.getLogger(__name__)
    
    try:
        # Start API server
        cmd = [sys.executable, "-m", "uvicorn", "src.api.main:app", "--host", "127.0.0.1", "--port", "8000"]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        logger.info(f"🚀 API server started with PID: {process.pid}")
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            logger.info("✅ API server is running")
            return process
        else:
            stdout, stderr = process.communicate()
            logger.error(f"❌ API server failed to start: {stderr.decode()}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Failed to start API server: {e}")
        return None

def start_gui():
    """Start the GUI application."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🖥️ Starting GUI application...")
        
        # Import and start GUI
        from src.gui.main_window import MainApplicationWindow
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        window = MainApplicationWindow()
        window.show()
        
        logger.info("✅ GUI started successfully")
        return app.exec()
        
    except Exception as e:
        logger.error(f"❌ GUI failed to start: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    """Main startup function."""
    logger = setup_logging()
    
    print("🚀 Therapy Compliance Analyzer - Fixed Startup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed")
        return 1
    
    # Use lightweight config
    if not use_lite_config():
        print("❌ Failed to switch to lightweight config")
        return 1
    
    # Start API server
    api_process = start_api_server()
    if not api_process:
        print("❌ Failed to start API server")
        return 1
    
    try:
        # Start GUI
        result = start_gui()
        return result
        
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
        return 0
        
    finally:
        # Cleanup API server
        if api_process and api_process.poll() is None:
            logger.info("🧹 Shutting down API server...")
            api_process.terminate()
            api_process.wait(timeout=5)
            logger.info("✅ API server shut down")

if __name__ == "__main__":
    sys.exit(main())