"""Simplified QtCore module used for non-GUI test execution."""
from __future__ import annotations

from typing import Any, Callable, Optional

__version__ = "6.0.0"


class QObject:
    """Minimal QObject implementation."""

    def __init__(self, parent: Optional[QObject] = None) -> None:
        self._parent = parent


class QEvent:
    """Placeholder event object."""

    pass


class QMessageLogger:
    """Stub message logger that discards log messages."""

    def info(self, msg: str) -> None:  # pragma: no cover - side effect free
        _ = msg


def qDebug(msg: str) -> None:  # pragma: no cover - side effect free
    _ = msg


def qWarning(msg: str) -> None:  # pragma: no cover - side effect free
    _ = msg


def qCritical(msg: str) -> None:  # pragma: no cover - side effect free
    _ = msg


def qFatal(msg: str) -> None:  # pragma: no cover - side effect free
    _ = msg


def qVersion() -> str:
    return "6.0.0"


def qInstallMessageHandler(handler: Callable[[Any, str], None] | None):
    previous = getattr(qInstallMessageHandler, "_handler", None)
    qInstallMessageHandler._handler = handler
    return previous


def Signal(*_args: Any, **_kwargs: Any) -> "_Signal":  # pragma: no cover - simple factory
    return _Signal()


class _Signal:
    def __init__(self) -> None:
        self._callbacks: list[Callable[..., Any]] = []

    def connect(self, callback: Callable[..., Any]) -> None:
        self._callbacks.append(callback)

    def emit(self, *args: Any, **kwargs: Any) -> None:
        for callback in list(self._callbacks):
            callback(*args, **kwargs)


def Slot(*_args: Any, **_kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return func

    return decorator


def Property(_type: Any, fget: Callable[..., Any], fset: Optional[Callable[..., Any]] = None) -> property:
    return property(fget, fset)


class _Key:
    Key_Up = 0
    Key_Down = 1
    Key_Left = 2
    Key_Right = 3
    Key_B = 4
    Key_A = 5

    def __getattr__(self, name: str) -> int:
        value = abs(hash(name)) % (1 << 16)
        setattr(self, name, value)
        return value


class _AlignmentFlag:
    AlignLeft = 0
    AlignRight = 1
    AlignTop = 2
    AlignBottom = 3


class _MouseButton:
    LeftButton = 0
    RightButton = 1

    def __getattr__(self, name: str) -> int:
        value = abs(hash(name)) % (1 << 16)
        setattr(self, name, value)
        return value


class _KeyboardModifier:
    NoModifier = 0
    ShiftModifier = 1
    ControlModifier = 2
    AltModifier = 4
    MetaModifier = 8

    def __getattr__(self, name: str) -> int:
        value = abs(hash(name)) % (1 << 16)
        setattr(self, name, value)
        return value


class Qt:
    Key = _Key()
    AlignmentFlag = _AlignmentFlag()
    MouseButton = _MouseButton()
    KeyboardModifier = _KeyboardModifier()
    CursorShape = _Key()  # Reuse dynamic lookup for cursor constants


class QEasingCurve:
    OutCubic = 0
    InOutQuad = 1

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        pass


class QThread(QObject):
    def __init__(self) -> None:
        super().__init__(None)
        self._running = False

    def start(self) -> None:
        self._running = True

    def quit(self) -> None:
        self._running = False

    def wait(self, _timeout: int | None = None) -> None:  # pragma: no cover - no threading
        self._running = False


class QUrl:
    def __init__(self, url: str = "") -> None:
        self._url = url

    def toString(self) -> str:
        return self._url

class QPoint:
    def __init__(self, x: int = 0, y: int = 0) -> None:
        self._x = x
        self._y = y

    def x(self) -> int:
        return self._x

    def y(self) -> int:
        return self._y
class QRect:
    def __init__(self, x: int = 0, y: int = 0, width: int = 0, height: int = 0) -> None:
        self._x = x
        self._y = y
        self._width = width
        self._height = height

    def adjusted(self, dx1: int, dy1: int, dx2: int, dy2: int) -> "QRect":
        return QRect(
            self._x + dx1,
            self._y + dy1,
            self._width + dx2,
            self._height + dy2,
        )

    def width(self) -> int:
        return self._width

    def height(self) -> int:
        return self._height


class QPropertyAnimation(QObject):
    def __init__(self, target: QObject | None = None, property_name: bytes | bytearray = b"") -> None:
        super().__init__(target)
        self._property_name = property_name
        self._duration = 0
        self._start_value: Any = None
        self._end_value: Any = None
        self._easing_curve: Any = None

    def setDuration(self, duration: int) -> None:
        self._duration = duration

    def setEasingCurve(self, curve: Any) -> None:
        self._easing_curve = curve

    def setStartValue(self, value: Any) -> None:
        self._start_value = value

    def setEndValue(self, value: Any) -> None:
        self._end_value = value

    def start(self) -> None:  # pragma: no cover - no animation loop
        return None

class QAbstractAnimation(QObject):
    def start(self) -> None:  # pragma: no cover - stub
        return None


class QSequentialAnimationGroup(QAbstractAnimation):
    def __init__(self) -> None:
        super().__init__()
        self._animations: list[QAbstractAnimation] = []

    def addAnimation(self, animation: QAbstractAnimation) -> None:
        self._animations.append(animation)

class _QtVersion:
    def __init__(self, version: str = "6.0.0") -> None:
        self._version = version

    def segments(self) -> tuple[int, ...]:
        return tuple(int(part) for part in self._version.split("."))


class QLibraryInfo:
    @staticmethod
    def version() -> _QtVersion:
        return _QtVersion()


class QTimer(QObject):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._interval = 0
        self._active = False
        self.timeout = Signal()

    def setInterval(self, interval: int) -> None:
        self._interval = interval

    def start(self) -> None:
        self._active = True

    def stop(self) -> None:
        self._active = False

    def isActive(self) -> bool:
        return self._active


class QCoreApplication(QObject):
    _instance: Optional["QCoreApplication"] = None

    def __init__(self, args: Optional[list[str]] = None) -> None:
        super().__init__(None)
        self._args = args or []
        self._app_name = ""
        QCoreApplication._instance = self

    @classmethod
    def instance(cls) -> Optional["QCoreApplication"]:
        return cls._instance

    def setApplicationName(self, name: str) -> None:
        self._app_name = name

    def applicationName(self) -> str:
        return self._app_name

    def exec(self) -> int:  # pragma: no cover - no event loop
        return 0


class QSettings(QObject):
    """Very small in-memory QSettings replacement."""

    _store: dict[str, Any] = {}

    def __init__(self, organization: str, application: str) -> None:
        super().__init__(None)
        self._organization = organization
        self._application = application

    def value(self, key: str, default: Any = None) -> Any:
        return self._store.get((self._organization, self._application, key), default)

    def setValue(self, key: str, value: Any) -> None:
        self._store[(self._organization, self._application, key)] = value


__all__ = [
    "QObject",
    "QEvent",
    "QMessageLogger",
    "qDebug",
    "qWarning",
    "qCritical",
    "qFatal",
    "qVersion",
    "Signal",
    "Slot",
    "Property",
    "Qt",
    "QEasingCurve",
    "QThread",
    "QUrl",
    "QPoint",
    "QRect",
    "QPropertyAnimation",
    "QAbstractAnimation",
    "QSequentialAnimationGroup",
    "QLibraryInfo",
    "QTimer",
    "QCoreApplication",
    "QSettings",
]
