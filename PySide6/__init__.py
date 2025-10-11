"""Lightweight stub of the PySide6 package for headless test environments."""
from __future__ import annotations

__all__ = ["QtCore", "QtGui", "QtWidgets", "QtTest"]
__version__ = "6.0.0"
__FAKE_PYSIDE6__ = True

from . import QtCore, QtGui, QtWidgets, QtTest  # noqa: E402  (re-exported modules)
