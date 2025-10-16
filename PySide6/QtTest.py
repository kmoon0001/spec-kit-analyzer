"""Simplified QtTest module for compatibility with pytest-qt."""

from __future__ import annotations

from typing import Any

from .QtCore import Qt
from .QtWidgets import QWidget


class QTest:
    @staticmethod
    def qWait(_ms: int) -> None:  # pragma: no cover - no event loop
        return None

    @staticmethod
    def mouseClick(widget: QWidget, _button: int = Qt.MouseButton.LeftButton) -> None:
        if hasattr(widget, "click"):
            widget.click()

    @staticmethod
    def keyClick(_widget: QWidget, _key: int) -> None:  # pragma: no cover - unused
        return None


__all__ = ["QTest"]
