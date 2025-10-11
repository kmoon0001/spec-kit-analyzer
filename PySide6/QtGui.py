"""Simplified QtGui module used for non-GUI test execution."""
from __future__ import annotations

from typing import Any

from .QtCore import QObject, QCoreApplication, Signal


class QGuiApplication(QCoreApplication):
    pass


class QAction(QObject):
    def __init__(self, text: str = "", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._text = text
        self.triggered = Signal()

    def setText(self, text: str) -> None:
        self._text = text

    def text(self) -> str:
        return self._text


class QIcon:
    def __init__(self, path: str = "") -> None:
        self._path = path


class QFont:
    def __init__(self, family: str = "", size: int = 10) -> None:
        self.family = family
        self.pointSize = size


class QColor:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs


def __getattr__(name: str) -> type:
    cls = type(name, (QObject,), {"__module__": __name__})
    globals()[name] = cls
    return cls


__all__ = ["QGuiApplication", "QAction", "QIcon", "QFont", "QColor"]
