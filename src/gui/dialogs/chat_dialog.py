from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QKeySequence, QShortcut, QTextCursor
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QVBoxLayout, QWidget

from src.config import get_settings

from ..workers.chat_worker import ChatWorker

settings = get_settings()
API_URL = settings.paths.api_url


class ChatDialog(QDialog):
    def __init__(self, initial_context: str, token: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Compliance Assistant")
        self.setMinimumSize(600, 500)
        self.resize(700, 600)  # Better default size
        self.token = token
        self.history: list[dict[str, str]] = [
            {  # This system prompt is for the local history, the service has its own
                "role": "system",
                "content": "You are a helpful assistant for clinical compliance.",
            },
            {"role": "user", "content": initial_context},
        ]

        # --- UI Setup ---
        self.setStyleSheet("""
            ChatDialog {
                background-color: #f8fafc;
            }
        """)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 12)
        self.main_layout.setSpacing(12)

        # Header
        header_widget = QWidget()
        header_widget.setObjectName("headerWidget")
        header_widget.setStyleSheet("""
            #headerWidget {
                background-color: #ffffff;
                border-bottom: 1px solid #e2e8f0;
            }
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_label = QLabel("💬  AI Compliance Assistant")
        header_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #1e293b;
        """)
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        self.main_layout.addWidget(header_widget)

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8fafc;
                border: none;
                padding: 16px;
                font-size: 14px;
                color: #334155;
            }
        """)
        self.main_layout.addWidget(self.chat_display)

        # Input section
        input_container = QWidget()
        input_container.setStyleSheet("background-color: #f8fafc;")
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(16, 8, 16, 8)
        input_layout.setSpacing(8)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Ask about compliance, documentation tips, or specific findings...")
        self.message_input.setMinimumHeight(40)
        self.message_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 12px;
                background-color: white;
                font-size: 14px;
                color: #1e293b;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """)

        self.send_button = QPushButton("Send")
        self.send_button.setMinimumHeight(40)
        self.send_button.setMinimumWidth(80)
        self.send_button.setCursor(Qt.PointingHandCursor)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #cbd5e1;
                color: #64748b;
            }
        """)

        input_layout.addWidget(self.message_input, 1)
        input_layout.addWidget(self.send_button)
        input_container.setLayout(input_layout)
        self.main_layout.addWidget(input_container)

        # --- Connections ---
        self.send_button.clicked.connect(self.send_message)
        self.message_input.returnPressed.connect(self.send_message)  # Enter key support

        # Add Ctrl+Enter shortcut as an alternative for sending
        enter_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        enter_shortcut.activated.connect(self.send_message)

        self.worker_thread: QThread | None = None
        self.worker: ChatWorker | None = None

        # Don't send initial message automatically - let user initiate
        self.update_chat_display("assistant", "Hello! I'm your AI compliance assistant. How can I help you today?")

    def send_initial_message(self):
        """Send initial message - called manually if needed."""
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
        self.update_chat_display("assistant", "● ● ●")

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

        # A more robust way to remove the "thinking" message
        cursor = self.chat_display.textCursor()
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        cursor.removeSelectedText()

        self.update_chat_display("assistant", ai_response)
        self.send_button.setEnabled(True)
        self.message_input.setEnabled(True)
        self.message_input.setFocus()

    def on_chat_error(self, error_message: str):
        self.chat_display.undo()
        error_html = f"""
        <div style="background-color:#fee2e2; border-left:3px solid #ef4444; padding:8px 12px; border-radius:4px; margin:4px 0;">
            <p style="color:#991b1b; font-weight:600; margin:0;">Error</p>
            <p style="color:#b91c1c; margin:0;">{error_message}</p>
        </div>
        """
        self.chat_display.append(error_html)
        self.send_button.setEnabled(True)
        self.message_input.setEnabled(True)

    def update_chat_display(self, role: str, text: str):
        bubble_style = """
            padding: 10px 14px;
            border-radius: 12px;
            margin-bottom: 8px;
            max-width: 80%;
        """

        text = text.replace("\n", "<br>")

        if role == "user":
            html = f"""
            <div align="right">
                <div style="background-color:#dbeafe; color:#1e3a8a; {bubble_style} display:inline-block; text-align:left;">
                    {text}
                </div>
            </div>
            """
        elif role == "assistant":
            if text == "● ● ●":  # Thinking indicator
                html = f"""
                <div align="left">
                    <div style="background-color:#e2e8f0; color:#475569; {bubble_style} display:inline-block; text-align:left; font-style:italic;">
                        {text}
                    </div>
                </div>
                """
            else:
                html = f"""
                <div align="left">
                    <div style="background-color:#ffffff; border:1px solid #e2e8f0; color:#334155; {bubble_style} display:inline-block; text-align:left;">
                        {text}
                    </div>
                </div>
                """
        else:  # system or error
            return

        self.chat_display.append(html)
