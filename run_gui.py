"""
GUI entry point script.

This script launches the PyQt6 GUI application.
"""
import sys
from pathlib import Path
import asyncio

# Add project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.gui.main import main as gui_main

if __name__ == "__main__":
    # The main function in src.gui.main is async
    # and handles its own event loop logic.
    asyncio.run(gui_main())
