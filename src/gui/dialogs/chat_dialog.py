from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QLabel,
)
from PyQt6.QtCore import QThread
from PyQt6.QtGui import QKeySequence, QShortcut
from typing import List, Dict

from ..workers.chat_worker import ChatWorker

from src.config import get_settings

settings = get_settings()
API_URL = settings.paths.api_url


class ChatDialog(QDialog):
    def __init__(self, initial_context: str, token: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💬 AI Compliance Assistant")
        self.setMinimumSize(600, 500)
        self.resize(700, 600)  # Better default size
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
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)

        # Header
        header_label = QLabel("💬 AI Compliance Assistant")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #1e40af;
                padding: 12px;
                background-color: #dbeafe;
                border-radius: 8px;
                margin-bottom: 8px;
            }
        """)
        self.main_layout.addWidget(header_label)

        # Chat display with better styling
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
                background-color: #f8fafc;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        self.main_layout.addWidget(self.chat_display)

        # Input section with label
        input_label = QLabel("💭 Your message (Press Enter to send):")
        input_label.setStyleSheet("font-weight: 600; color: #475569; font-size: 13px;")
        self.main_layout.addWidget(input_label)

        # Input layout with proper scaling
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Ask about compliance, documentation tips, or specific findings...")
        self.message_input.setMinimumHeight(36)
        self.message_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                background-color: white;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """)
        
        self.send_button = QPushButton("📤 Send")
        self.send_button.setMinimumHeight(36)
        self.send_button.setMinimumWidth(80)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #cbd5e1;
                color: #94a3b8;
            }
        """)

        input_layout.addWidget(self.message_input, 1)
        input_layout.addWidget(self.send_button)
        self.main_layout.addLayout(input_layout)

        # Close button with proper label
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("✅ Close Chat")
        close_button.setMinimumHeight(36)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #64748b;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #475569;
            }
        """)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        self.main_layout.addLayout(button_layout)

        # --- Connections ---
        self.send_button.clicked.connect(self.send_message)
        self.message_input.returnPressed.connect(self.send_message)  # Enter key support
        
        # Add Ctrl+Enter shortcut as alternative
        enter_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        enter_shortcut.activated.connect(self.send_message)

        self.worker_thread: QThread | None = None
        self.worker: ChatWorker | None = None

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

        self.worker_thread = QThread()
        self.worker = ChatWorker(self.history, self.token)
        self.worker.moveToThread(self.worker_thread)
        self.worker.success.connect(self.on_chat_success)
        self.worker.error.connect(self.on_chat_error)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

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
