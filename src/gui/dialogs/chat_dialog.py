from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QHBoxLayout, QDialogButtonBox
)
from PyQt6.QtCore import QThread
from typing import List, Dict

from ..workers.chat_worker import ChatWorker

class ChatDialog(QDialog):
    """
    A dialog window for a conversational chat session with the AI about a specific topic.
    """
    def __init__(self, initial_context: str, token: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Discuss with AI")
        self.setGeometry(200, 200, 500, 600)

        self.token = token
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": initial_context}
        ]

        # --- UI Setup ---
        self.main_layout = QVBoxLayout(self)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.main_layout.addWidget(self.chat_display)

        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Ask a follow-up question...")
        self.send_button = QPushButton("Send")

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        self.main_layout.addLayout(input_layout)

        self.close_button = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.main_layout.addWidget(self.close_button)

        # --- Connections ---
        self.send_button.clicked.connect(self.send_message)
        self.message_input.returnPressed.connect(self.send_message)
        self.close_button.rejected.connect(self.reject)

    def send_message(self):
        user_message = self.message_input.text().strip()
        if not user_message:
            return

        # Add user message to history and display
        self.history.append({"role": "user", "content": user_message})
        self.chat_display.append(f"<b>You:</b> {user_message}")
        self.message_input.clear()
        self.send_button.setEnabled(False)

        # Run the worker to get the AI's response
        self.thread = QThread()
        self.worker = ChatWorker(self.history, self.token)
        self.worker.moveToThread(self.thread)

        self.worker.success.connect(self.on_ai_response)
        self.worker.error.connect(self.on_chat_error)

        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.start()

    def on_ai_response(self, ai_message: str):
        self.history.append({"role": "assistant", "content": ai_message})
        self.chat_display.append(f"<b>AI:</b> {ai_message}")
        self.send_button.setEnabled(True)
        self.message_input.setFocus()

    def on_chat_error(self, error_message: str):
        self.chat_display.append(f'<i style="color: red;">Error: {error_message}</i>')
        self.send_button.setEnabled(True)
