"""
WebSocket Worker (Production Version)

Handles WebSocket connections for real-time updates with:
    - Automatic reconnection
    - Heartbeat/ping-pong
    - Message queuing
    - Error recovery
    - Clean shutdown

Provides real-time progress updates without polling!
"""

import json
import time
import logging
from typing import Any
from collections.abc import Callable
from queue import Queue, Empty

try:
    from websockets.sync.client import connect, ClientConnection

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("websockets package not available - WebSocket features disabled")

from src.gui.core import BaseWorker, WebSocketSignals, ResourceMonitor


logger = logging.getLogger(__name__)


class WebSocketWorker(BaseWorker):
    """
    WebSocket client worker for real-time communication.

    Features:
        - Automatic reconnection on disconnect
        - Heartbeat to keep connection alive
        - Message queue for outgoing messages
        - Thread-safe message sending
        - Clean shutdown handling

    Usage:
        ```python
        worker = WebSocketWorker(
            url="ws://127.0.0.1:8001/ws/analysis/123",
            on_message=handle_progress_update
        )
        worker.signals.message_received.connect(update_ui)
        worker.signals.connected.connect(on_connected)
        worker.signals.disconnected.connect(on_disconnected)

        threadpool.start(worker)

        # Later, send a message
        worker.send_message({'action': 'pause'})

        # When done
        worker.cancel()
        ```
    """

    def __init__(
        self,
        url: str,
        on_message: Callable[[dict], None] | None = None,
        heartbeat_interval: float = 30.0,
        reconnect_delay: float = 5.0,
        max_reconnect_attempts: int = 5,
        timeout_seconds: float = 0,  # 0 = run indefinitely
        resource_monitor: ResourceMonitor | None = None,
    ):
        """
        Initialize WebSocket worker.

        Args:
            url: WebSocket URL (ws:// or wss://)
            on_message: Callback for incoming messages
            heartbeat_interval: Seconds between heartbeat pings
            reconnect_delay: Delay before reconnection attempt
            max_reconnect_attempts: Max reconnection attempts (0 = infinite)
            timeout_seconds: Max runtime (0 = indefinite)
            resource_monitor: Resource monitor instance
        """
        super().__init__(timeout_seconds=timeout_seconds, resource_monitor=resource_monitor, job_type="general")

        if not WEBSOCKETS_AVAILABLE:
            raise ImportError("websockets package required for WebSocket support")

        self.url = url
        self.on_message = on_message
        self.heartbeat_interval = heartbeat_interval
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts

        # Connection state
        self._connection: ClientConnection | None = None
        self._message_queue: Queue = Queue()
        self._last_heartbeat = 0.0
        self._reconnect_count = 0

    def create_signals(self) -> WebSocketSignals:
        """Use specialized WebSocket signals."""
        return WebSocketSignals()

    def do_work(self) -> dict[str, Any]:
        """
        Manage WebSocket connection.

        Returns:
            Connection statistics
        """
        messages_received = 0
        messages_sent = 0

        while not self.is_cancelled():
            try:
                # Connect or reconnect
                if not self._connection:
                    self._connect()

                # Send queued messages
                self._process_outgoing_messages()
                messages_sent += self._send_queued_messages()

                # Check for incoming messages (non-blocking)
                try:
                    message = self._connection.recv(timeout=0.1)
                    if message:
                        self._handle_message(message)
                        messages_received += 1
                except TimeoutError:
                    # No message received, continue
                    pass

                # Send heartbeat if needed
                self._send_heartbeat_if_needed()

                # Small sleep to prevent CPU spinning
                time.sleep(0.01)

            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.signals.connection_error.emit(str(e))

                # Try to reconnect
                self._handle_disconnect()

                if not self._should_reconnect():
                    break

                time.sleep(self.reconnect_delay)

        return {
            "messages_received": messages_received,
            "messages_sent": messages_sent,
            "reconnect_attempts": self._reconnect_count,
        }

    def _connect(self):
        """Establish WebSocket connection."""
        try:
            self.report_status(f"Connecting to {self.url}...")

            self._connection = connect(self.url)
            self._last_heartbeat = time.time()
            self._reconnect_count = 0

            self.signals.connected.emit(self.url)
            logger.info(f"WebSocket connected: {self.url}")

        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.signals.connection_error.emit(str(e))
            raise

    def _handle_message(self, message: str):
        """
        Handle incoming message.

        Args:
            message: Raw message string
        """
        try:
            # Parse JSON
            data = json.loads(message)

            # Call user callback
            if self.on_message:
                self.on_message(data)

            # Emit signal
            self.signals.message_received.emit(data)

        except json.JSONDecodeError:
            # Not JSON, emit as text
            self.signals.message_received.emit({"text": message})

    def _send_queued_messages(self) -> int:
        """
        Send all queued outgoing messages.

        Returns:
            Number of messages sent
        """
        sent_count = 0

        while not self._message_queue.empty():
            try:
                message = self._message_queue.get_nowait()

                if isinstance(message, dict):
                    message = json.dumps(message)

                self._connection.send(message)
                sent_count += 1

            except Empty:
                break
            except Exception as e:
                logger.error(f"Failed to send message: {e}")

        return sent_count

    def _send_heartbeat_if_needed(self):
        """Send heartbeat ping if interval elapsed."""
        if time.time() - self._last_heartbeat >= self.heartbeat_interval:
            try:
                self._connection.ping()
                self._last_heartbeat = time.time()
            except Exception as e:
                logger.warning(f"Heartbeat failed: {e}")

    def _handle_disconnect(self):
        """Handle connection loss."""
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                pass

            self._connection = None

        self._reconnect_count += 1
        self.signals.disconnected.emit(f"Disconnect (attempt {self._reconnect_count})")

    def _should_reconnect(self) -> bool:
        """Check if should attempt reconnection."""
        if self.max_reconnect_attempts == 0:
            return True  # Infinite retries

        return self._reconnect_count < self.max_reconnect_attempts

    def _process_outgoing_messages(self):
        """Process any pending outgoing messages."""
        # Process messages from the outgoing queue if needed
        # This is a base implementation that can be overridden by subclasses
        return

    def send_message(self, message: dict[str, Any]):
        """
        Queue a message to be sent.

        Thread-safe - can be called from GUI thread.

        Args:
            message: Message dict (will be JSON encoded)
        """
        self._message_queue.put(message)

    def cleanup(self):
        """Clean up WebSocket connection."""
        if self._connection:
            try:
                # Send close frame
                self._connection.close()
                logger.info("WebSocket connection closed cleanly")
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
            finally:
                self._connection = None


class AnalysisWebSocketWorker(WebSocketWorker):
    """
    Specialized WebSocket worker for analysis progress updates.

    Automatically handles analysis-specific messages and emits
    appropriate signals for GUI updates.
    """

    def _process_outgoing_messages(self):
        """Handle analysis-specific outgoing messages."""
        pass  # Can add analysis-specific message handling

    def _handle_message(self, message: str):
        """Handle analysis progress messages."""
        try:
            data = json.loads(message)

            # Handle different message types
            msg_type = data.get("type", "unknown")

            if msg_type == "progress":
                # Progress update
                current = data.get("current", 0)
                total = data.get("total", 100)
                status = data.get("message", "")
                self.report_progress(current, total, status)

            elif msg_type == "status":
                # Status message
                self.report_status(data.get("message", ""))

            elif msg_type == "error":
                # Error occurred
                self.signals.connection_error.emit(data.get("message", "Unknown error"))

            elif msg_type == "complete":
                # Analysis complete
                self.signals.message_received.emit(data)
                self.cancel()  # Done, close connection

            # Call parent handler
            super()._handle_message(message)

        except Exception as e:
            logger.error(f"Error handling analysis message: {e}")
