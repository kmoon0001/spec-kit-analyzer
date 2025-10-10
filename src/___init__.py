try:
    from PySide6.QtCore import Qt
    from pytestqt.qtbot import QtBot  # type: ignore

    if not hasattr(QtBot, "button_enum"):
        QtBot.button_enum = Qt.MouseButton
except Exception:
    pass
