import requests
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QDialogButtonBox,
)
from PyQt6.QtCore import QThread, pyqtSignal as Signal
from typing import List, Dict

from ..workers.chat_worker import ChatWorker

from src.config import get_settings

settings = get_settings()
API_URL = settings.api_url


class ChatDialog(QDialog):
    def __init__(self, initial_context: str, token: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chat with AI Assistant")
        self.setMinimumSize(500, 400)
        self.token = token
        self.history: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": "You are a helpful assistant for clinical compliance.",
            },
            {"role": "user", "content": initial_context},
        ]

        # --- UI Setup ---
        self.main_layout = QVBoxLayout(self)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.main_layout.addWidget(self.chat_display)

        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message...")
        self.send_button = QPushButton("Send")

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        self.main_layout.addLayout(input_layout)

        self.close_button = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.main_layout.addWidget(self.close_button)

        # --- Connections ---
        self.send_button.clicked.connect(self.send_message)
        self.close_button.rejected.connect(self.reject)

        self.thread = None
        self.worker = None

        self.send_initial_message()

    def send_initial_message(self):
        self.update_chat_display("user", self.history[-1]["content"])
        self.send_message(is_initial=True)

    def send_message(self, is_initial=False):
        if not is_initial:
            user_message = self.message_input.text().strip()
            if not user_message:
                return
            self.history.append({"role": "user", "content": user_message})
            self.update_chat_display("user", user_message)
            self.message_input.clear()

        self.send_button.setEnabled(False)
        self.message_input.setEnabled(False)
        self.update_chat_display("assistant", "<i>...thinking...</i>")

        self.thread = QThread()
        self.worker = ChatWorker(self.history, self.token)
        self.worker.moveToThread(self.thread)
        self.worker.success.connect(self.on_chat_success)
        self.worker.error.connect(self.on_chat_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_chat_success(self, ai_response: str):
        self.history.append({"role": "assistant", "content": ai_response})
        # Remove the "...thinking..." message before adding the real one
        self.chat_display.undo()
        self.update_chat_display("assistant", ai_response)
        self.send_button.setEnabled(True)
        self.message_input.setEnabled(True)
        self.message_input.setFocus()

    def on_chat_error(self, error_message: str):
        self.chat_display.undo()
        self.update_chat_display(
            "system", f"<font color='red'>Error: {error_message}</font>"
        )
        self.send_button.setEnabled(True)
        self.message_input.setEnabled(True)

    def update_chat_display(self, role: str, text: str):
        if role == "user":
            self.chat_display.append(f"<b>You:</b> {text}")
        elif role == "assistant":
            self.chat_display.append(f"<b>Assistant:</b> {text}")
        else:  # system
            self.chat_display.append(f"<i>{text}</i>")
        self.chat_display.append("")  # Add a blank line for spacing
