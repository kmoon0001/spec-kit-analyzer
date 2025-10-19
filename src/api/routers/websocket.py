"""
WebSocket Router for Real-Time Updates

Provides WebSocket endpoints for:
    - Real-time analysis progress
    - System health monitoring
    - Live log streaming
    - Bidirectional communication

Uses FastAPI WebSocket support for efficient real-time updates.
"""

import asyncio
import logging
import json
from typing import Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from datetime import datetime

from src.api.dependencies import get_db
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """
    Manage WebSocket connections.

    Handles:
        - Multiple concurrent connections
        - Broadcasting to all clients
        - Connection lifecycle
        - Message routing
    """

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str):
        """
        Accept new WebSocket connection.

        Args:
            websocket: WebSocket connection
            channel: Channel name (e.g., "analysis_123")
        """
        await websocket.accept()

        if channel not in self.active_connections:
            self.active_connections[channel] = []

        self.active_connections[channel].append(websocket)
        logger.info(f"WebSocket connected to channel: {channel}")

    def disconnect(self, websocket: WebSocket, channel: str):
        """
        Remove WebSocket connection.

        Args:
            websocket: WebSocket connection
            channel: Channel name
        """
        if channel in self.active_connections:
            if websocket in self.active_connections[channel]:
                self.active_connections[channel].remove(websocket)

            # Clean up empty channels
            if not self.active_connections[channel]:
                del self.active_connections[channel]

        logger.info(f"WebSocket disconnected from channel: {channel}")

    async def send_message(self, channel: str, message: dict[str, Any]):
        """
        Send message to all connections in a channel.

        Args:
            channel: Channel name
            message: Message dict (will be JSON encoded)
        """
        if channel not in self.active_connections:
            return

        # Send to all connections in channel
        dead_connections = []

        for websocket in self.active_connections[channel]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                dead_connections.append(websocket)

        # Remove dead connections
        for websocket in dead_connections:
            self.disconnect(websocket, channel)

    async def broadcast(self, message: dict[str, Any]):
        """
        Broadcast message to all connections in all channels.

        Args:
            message: Message dict
        """
        for channel in list(self.active_connections.keys()):
            await self.send_message(channel, message)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/analysis/{task_id}")
async def websocket_analysis_progress(websocket: WebSocket, task_id: str, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time analysis progress.

    Streams progress updates for a specific analysis task.

    Args:
        websocket: WebSocket connection
        task_id: Analysis task ID
        db: Database session

    Message Format:
        {
            "type": "progress" | "status" | "complete" | "error",
            "current": int,
            "total": int,
            "message": str,
            "timestamp": str
        }

    Example Client (Python):
        ```python
        import websockets
        import json

        async with websockets.connect('ws://localhost:8001/ws/analysis/123') as ws:
            while True:
                message = await ws.recv()
                data = json.loads(message)
                print(f"Progress: {data['current']}/{data['total']} - {data['message']}")
        ```
    """
    channel = f"analysis_{task_id}"
    await manager.connect(websocket, channel)

    try:
        # Send initial connection confirmation
        await websocket.send_json(
            {
                "type": "connected",
                "task_id": task_id,
                "message": "Connected to analysis progress stream",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive messages from client (optional - for bidirectional communication)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                # Handle client messages (e.g., pause, cancel)
                message = json.loads(data)
                action = message.get("action")

                if action == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})

                elif action == "cancel":
                    # Cancel analysis task
                    try:
                        from src.api.routers.analysis import tasks
                        if task_id in tasks:
                            tasks[task_id]["status"] = "cancelled"
                            tasks[task_id]["cancelled_at"] = datetime.utcnow().isoformat()
                            await websocket.send_json(
                                {
                                    "type": "status",
                                    "message": "Analysis task cancelled successfully",
                                    "timestamp": datetime.utcnow().isoformat(),
                                }
                            )
                        else:
                            await websocket.send_json(
                                {
                                    "type": "error",
                                    "message": "Task not found or already completed",
                                    "timestamp": datetime.utcnow().isoformat(),
                                }
                            )
                    except Exception as e:
                        logger.error(f"Failed to cancel task {task_id}: {e}")
                        await websocket.send_json(
                            {
                                "type": "error",
                                "message": f"Failed to cancel task: {str(e)}",
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )

            except TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()})

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from analysis_{task_id}")
    except Exception as e:
        logger.error(f"WebSocket error for analysis_{task_id}: {e}")
    finally:
        manager.disconnect(websocket, channel)


@router.websocket("/health")
async def websocket_health_monitoring(websocket: WebSocket):
    """
    WebSocket endpoint for real-time health monitoring.

    Streams system health metrics every second.

    Message Format:
        {
            "type": "health",
            "cpu_percent": float,
            "ram_percent": float,
            "api_status": str,
            "active_tasks": int,
            "timestamp": str
        }
    """
    channel = "health_monitoring"
    await manager.connect(websocket, channel)

    try:
        import psutil

        while True:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            # Get active tasks count
            try:
                from src.api.routers.analysis import tasks
                active_tasks = len([t for t in tasks.values() if t.get("status") in ["running", "queued"]])
            except ImportError:
                active_tasks = 0

            # Send health data
            await websocket.send_json(
                {
                    "type": "health",
                    "cpu_percent": cpu_percent,
                    "ram_percent": memory.percent,
                    "ram_available_mb": memory.available / (1024 * 1024),
                    "api_status": "running",
                    "active_tasks": active_tasks,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Update every second
            await asyncio.sleep(1.0)

    except WebSocketDisconnect:
        logger.info("Health monitoring client disconnected")
    except Exception as e:
        logger.error(f"WebSocket health monitoring error: {e}")
    finally:
        manager.disconnect(websocket, channel)


# Log streaming handled via FastAPI app-level route with shared manager.


# Helper function to send progress updates from other parts of the app
async def send_analysis_progress(task_id: str, current: int, total: int, message: str, status: str = "progress"):
    """
    Send progress update to WebSocket clients.

    Call this from your analysis code to stream progress.

    Args:
        task_id: Analysis task ID
        current: Current progress value
        total: Total progress value
        message: Status message
        status: Update type ("progress", "complete", "error")

    Example:
        ```python
        # In your analysis code
        await send_analysis_progress(
            task_id="123",
            current=50,
            total=100,
            message="Extracting entities..."
        )
        ```
    """
    channel = f"analysis_{task_id}"

    await manager.send_message(
        channel,
        {
            "type": status,
            "current": current,
            "total": total,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )
