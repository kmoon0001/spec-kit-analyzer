from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QKeyEvent

class ChatInput(QTextEdit):
    """
    A custom QTextEdit that emits a signal when Enter is pressed.
    """
    sendMessage = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, event: QKeyEvent):
        """
        Overrides the key press event to send a message on Enter.
        """
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                self.sendMessage.emit()
                return  # Consume the event
        super().keyPressEvent(event)