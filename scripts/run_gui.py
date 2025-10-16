"""
GUI entry point script.

This script launches the PySide6 GUI application with proper authentication.
"""

import sys


from pathlib import Path




# Add project root to the Python path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# Set matplotlib backend before importing any GUI components

import os


try:
    import matplotlib  # type: ignore[import-not-found]

except Exception:
    matplotlib = None  # type: ignore[assignment]


# Prefer PySide6; avoid hard failure if matplotlib is absent

os.environ["QT_API"] = "pyside6"

if matplotlib is not None:
    try:
        matplotlib.use("Qt5Agg")

    except Exception:
        pass



import logging




logger = logging.getLogger(__name__)
