import requests
from PyQt6.QtCore import QObject, Signal
from typing import List, Dict

API_URL = "http://127.0.0.1:8000"

class ChatWorker(QObject):
    """
    A worker to handle a single turn in a chat conversation with the backend.
    """
    success = Signal(str)  # Emits the AI's response message
    error = Signal(str)

    def __init__(self, history: List[Dict[str, str]], token: str):
        super().__init__()
        self.history = history
        self.token = token

    def run(self):
        """
        Sends the conversation history to the chat endpoint and emits the response.
        """
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {"history": self.history}
            
            response = requests.post(f"{API_URL}/chat/", json=payload, headers=headers)
            response.raise_for_status()
            
            ai_response = response.json()['response']
            self.success.emit(ai_response)

        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            if e.response is not None:
                try:
                    error_detail = e.response.json().get('detail', str(e))
                except requests.exceptions.JSONDecodeError:
                    pass
            self.error.emit(f"Chat API error: {error_detail}")
        except Exception as e:
            self.error.emit(f"An unexpected error occurred during chat: {e}")
