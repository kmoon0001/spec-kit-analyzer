import asyncio
import json
import logging
import websockets
from PyQt6.QtCore import QObject, pyqtSignal

from src.config import get_settings

logger = logging.getLogger(__name__)

class TaskStatusWorker(QObject):
    """
    Connects to a WebSocket to receive real-time status updates for a task.
    """
    progress = pyqtSignal(int, str)
    success = pyqtSignal(dict)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, task_id: str):
        super().__init__()
        self.task_id = task_id
        self._is_running = True

    def run(self):
        """Runs the asyncio event loop to manage the WebSocket connection."""
        try:
            asyncio.run(self._listen_for_updates())
        except Exception as e:
            logger.error("Error running WebSocket worker: %s", e, exc_info=True)
            self.error.emit(f"WebSocket connection failed: {e}")
        finally:
            self.finished.emit()

    async def _listen_for_updates(self):
        """The main async function that connects and listens to the WebSocket."""
        settings = get_settings()
        # Ensure the ws:// or wss:// scheme is used
        uri = f"{settings.api_url.replace('http', 'ws')}/analysis/ws/tasks/{self.task_id}"
        logger.info("Connecting to WebSocket at %s", uri)

        try:
            async with websockets.connect(uri) as websocket:
                while self._is_running:
                    try:
                        message_str = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                        message = json.loads(message_str)

                        status = message.get("status")
                        if status == "processing":
                            self.progress.emit(message.get("progress", 0), message.get("message", ""))
                        elif status == "completed":
                            self.success.emit(message.get("result", {}))
                            break # Task is done
                        elif status == "failed":
                            self.error.emit(message.get("error", "Unknown error from task."))
                            break # Task is done

                    except asyncio.TimeoutError:
                        logger.warning("WebSocket connection timed out waiting for message.")
                        continue # Or break, depending on desired behavior
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("WebSocket connection closed unexpectedly.")
                        self.error.emit("Connection to server lost.")
                        break
        except Exception as e:
            logger.error("Failed to connect or listen to WebSocket: %s", e, exc_info=True)
            self.error.emit(f"Failed to establish connection: {e}")

    def stop(self):
        """Stops the worker."""
        self._is_running = False
        logger.info("WebSocket worker stopping...")
