try:
    from pytestqt.qtbot import QtBot  # type: ignore
    from PySide6.QtCore = Qt

    if not hasattr(QtBot, "button_enum"):
        QtBot.button_enum = Qt.MouseButton
except Exception:
    pass
