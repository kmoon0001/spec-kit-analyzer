"""Simplified QtWidgets module for running tests without a GUI stack."""

from __future__ import annotations

from typing import Any, Optional

from .QtCore import QObject, QCoreApplication, Qt, Signal


class QApplication(QCoreApplication):
    _instance: Optional["QApplication"] = None

    def __init__(self, args: Optional[list[str]] = None) -> None:
        super().__init__(args)
        QApplication._instance = self

    @classmethod
    def instance(cls) -> Optional["QApplication"]:
        return cls._instance

    def exec(self) -> int:  # pragma: no cover - no event loop
        return 0

    def quit(self) -> None:  # pragma: no cover - no event loop
        QApplication._instance = None


class QWidget(QObject):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._enabled = True
        self._visible = False
        self._layout: Optional["QLayout"] = None

    def show(self) -> None:  # pragma: no cover - no GUI
        self._visible = True

    def close(self) -> None:  # pragma: no cover - no GUI
        self._visible = False

    def setEnabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def isEnabled(self) -> bool:
        return self._enabled

    def setLayout(self, layout: "QLayout") -> None:
        self._layout = layout


class QLayout(QObject):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._items: list[QWidget] = []

    def addWidget(self, widget: QWidget) -> None:
        self._items.append(widget)


class QVBoxLayout(QLayout):
    pass


class QStatusBar(QWidget):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._message = ""

    def showMessage(self, message: str, _timeout: int | None = None) -> None:
        self._message = message


class QProgressBar(QWidget):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._value = 0

    def setValue(self, value: int) -> None:
        self._value = value

    def value(self) -> int:
        return self._value


class QTextEdit(QWidget):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._text = ""

    def setPlainText(self, text: str) -> None:
        self._text = text

    def toPlainText(self) -> str:
        return self._text

    def append(self, text: str) -> None:
        self._text += f"\n{text}" if self._text else text


class QTextBrowser(QTextEdit):
    pass


class QComboBox(QWidget):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._items: list[tuple[str, Any]] = []
        self._current_index = -1

    def addItem(self, text: str, user_data: Any = None) -> None:
        self._items.append((text, user_data))
        if self._current_index == -1:
            self._current_index = 0

    def clear(self) -> None:
        self._items.clear()
        self._current_index = -1

    def count(self) -> int:
        return len(self._items)

    def setCurrentIndex(self, index: int) -> None:
        self._current_index = index

    def currentIndex(self) -> int:
        return self._current_index

    def currentText(self) -> str:
        if 0 <= self._current_index < len(self._items):
            return self._items[self._current_index][0]
        return ""

    def itemData(self, index: int) -> Any:
        if 0 <= index < len(self._items):
            return self._items[index][1]
        return None


class QTabWidget(QWidget):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._tabs: list[tuple[QWidget, str, bool]] = []
        self._current_index = 0

    def addTab(self, widget: QWidget, title: str) -> None:
        self._tabs.append((widget, title, True))

    def count(self) -> int:
        return len(self._tabs)

    def tabText(self, index: int) -> str:
        if 0 <= index < len(self._tabs):
            return self._tabs[index][1]
        return ""

    def setTabEnabled(self, index: int, enabled: bool) -> None:
        if 0 <= index < len(self._tabs):
            widget, title, _ = self._tabs[index]
            self._tabs[index] = (widget, title, enabled)

    def isTabEnabled(self, index: int) -> bool:
        if 0 <= index < len(self._tabs):
            return self._tabs[index][2]
        return False

    def setCurrentIndex(self, index: int) -> None:
        if 0 <= index < len(self._tabs):
            self._current_index = index

    def currentIndex(self) -> int:
        return self._current_index


class QPushButton(QWidget):
    def __init__(self, text: str = "", parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._text = text
        self.clicked = Signal()

    def setText(self, text: str) -> None:
        self._text = text

    def text(self) -> str:
        return self._text

    def click(self) -> None:  # pragma: no cover - manual triggering
        self.clicked.emit()


class QDialog(QWidget):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._result = 0

    def exec(self) -> int:
        return self._result

    def accept(self) -> None:
        self._result = 1


class QMessageBox:
    @staticmethod
    def information(*_args: Any, **_kwargs: Any) -> int:
        return 0

    @staticmethod
    def warning(*_args: Any, **_kwargs: Any) -> int:
        return 0

    @staticmethod
    def critical(*_args: Any, **_kwargs: Any) -> int:
        return 0


class QDockWidget(QWidget):
    pass


class QMainWindow(QWidget):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._central_widget: Optional[QWidget] = None
        self._status_bar = QStatusBar(self)
        self._menu_bar: Optional[QWidget] = None
        self._window_title = ""

    def setCentralWidget(self, widget: QWidget) -> None:
        self._central_widget = widget

    def centralWidget(self) -> Optional[QWidget]:
        return self._central_widget

    def statusBar(self) -> QStatusBar:
        return self._status_bar

    def setMenuBar(self, menu: QWidget) -> None:
        self._menu_bar = menu

    def setWindowTitle(self, title: str) -> None:
        self._window_title = title

    def windowTitle(self) -> str:
        return self._window_title


class QFileDialog:
    @staticmethod
    def getOpenFileName(*_args: Any, **_kwargs: Any) -> tuple[str, str]:
        return "", ""

    @staticmethod
    def getSaveFileName(*_args: Any, **_kwargs: Any) -> tuple[str, str]:
        return "", ""


class QTextBrowser(QTextEdit):
    pass


class QLabel(QWidget):
    def __init__(self, text: str = "", parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._text = text

    def setText(self, text: str) -> None:
        self._text = text

    def text(self) -> str:
        return self._text


def __getattr__(name: str) -> type:
    cls = type(name, (QWidget,), {"__module__": __name__})
    globals()[name] = cls
    return cls


__all__ = [
    "QApplication",
    "QWidget",
    "QLayout",
    "QVBoxLayout",
    "QStatusBar",
    "QProgressBar",
    "QTextEdit",
    "QTextBrowser",
    "QComboBox",
    "QTabWidget",
    "QPushButton",
    "QDialog",
    "QMessageBox",
    "QDockWidget",
    "QMainWindow",
    "QFileDialog",
    "QLabel",
]
