from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, Qt, Signal

from src.gui.dialogs.chat_dialog import ChatDialog, THINKING_MESSAGE


class _BaseStubWorker(QObject):
    success = Signal(str)
    error = Signal(str)
    finished = Signal()

    def __init__(self, history: list[dict[str, str]], token: str):
        super().__init__()
        self.history = history
        self.token = token


class SuccessfulWorker(_BaseStubWorker):
    def run(self) -> None:
        self.success.emit("Here is the insight you requested.")
        self.finished.emit()


class ErrorWorker(_BaseStubWorker):
    def run(self) -> None:
        self.error.emit("Service unavailable")
        self.finished.emit()


class SpyFactory:
    def __init__(self):
        self.called = False

    def __call__(self, history: list[dict[str, str]], token: str) -> _BaseStubWorker:
        self.called = True
        return SuccessfulWorker(history, token)


@pytest.fixture
def dialog(qtbot):
    chat_dialog = ChatDialog(
        "Summary of the latest compliance audit.",
        token="token-123",
        use_async=False,
        worker_factory=SuccessfulWorker,
    )
    qtbot.addWidget(chat_dialog)
    return chat_dialog


def test_chat_dialog_send_message_success(dialog, qtbot):
    dialog.message_input.setText("Can you draft an overview?")
    qtbot.mouseClick(dialog.send_button, Qt.LeftButton)

    qtbot.waitUntil(lambda: "overview" in dialog.chat_display.toHtml().lower())

    assert dialog.history[-1]["content"] == "Here is the insight you requested."
    assert THINKING_MESSAGE not in dialog.chat_display.toHtml()
    assert dialog.send_button.isEnabled()
    assert dialog.message_input.isEnabled()


def test_chat_dialog_send_message_error(qtbot):
    chat_dialog = ChatDialog(
        "Need to validate documentation",
        token="token-456",
        use_async=False,
        worker_factory=ErrorWorker,
    )
    qtbot.addWidget(chat_dialog)

    chat_dialog.message_input.setText("What compliance risks remain?")
    qtbot.mouseClick(chat_dialog.send_button, Qt.LeftButton)

    qtbot.waitUntil(lambda: "service unavailable" in chat_dialog.chat_display.toHtml().lower())

    assert THINKING_MESSAGE not in chat_dialog.chat_display.toHtml()
    assert chat_dialog.send_button.isEnabled()
    assert chat_dialog.message_input.isEnabled()
    assert chat_dialog.history[-1]["role"] == "user"


def test_chat_dialog_ignores_empty_message(qtbot):
    spy_factory = SpyFactory()
    chat_dialog = ChatDialog(
        "Reminder of policy updates",
        token="token-789",
        use_async=False,
        worker_factory=spy_factory,
    )
    qtbot.addWidget(chat_dialog)

    chat_dialog.message_input.setText("   ")
    chat_dialog.send_message()

    assert not spy_factory.called
    assert chat_dialog.worker is None
    assert chat_dialog.history[-1]["role"] == "user"
