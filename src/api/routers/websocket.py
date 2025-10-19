"""
WebSocket Router for Real-Time Updates

Provides WebSocket endpoints for:
    - Real-time analysis progress
    - System health monitoring
    - Live log streaming
    - Bidirectional communication

Uses FastAPI WebSocket support for efficient real-time updates.
All endpoints require proper JWT authentication for security.
"""

import asyncio
import logging
import json
from typing import Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException, status
from datetime import datetime
from jose import JWTError, jwt
from sqlalchemy import select

from src.api.dependencies import get_db
from src.auth import get_auth_service
from src.database import models
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])


async def authenticate_websocket_user(websocket: WebSocket, token: str, db: Session) -> models.User:
    """
    Authenticate WebSocket user using JWT token.

    Args:
        websocket: WebSocket connection
        token: JWT token from query parameters
        db: Database session

    Returns:
        Authenticated user

    Raises:
        WebSocketDisconnect: If authentication fails
    """
    if not token:
        await websocket.close(code=1008, reason="Authentication token required")
        raise WebSocketDisconnect(1008, "Authentication token required")

    auth_service = get_auth_service()
    try:
        payload = jwt.decode(token, auth_service.secret_key, algorithms=[auth_service.algorithm])
        username = payload.get("sub")
        if not username:
            await websocket.close(code=1008, reason="Invalid token payload")
            raise WebSocketDisconnect(1008, "Invalid token payload")
    except JWTError as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        await websocket.close(code=1008, reason="Invalid token")
        raise WebSocketDisconnect(1008, "Invalid token")

    # Verify user exists and is active
    result = await db.execute(select(models.User).where(models.User.username == username))
    user = result.scalars().first()

    if not user or not user.is_active:
        await websocket.close(code=1008, reason="User not found or inactive")
        raise WebSocketDisconnect(1008, "User not found or inactive")

    return user


class ConnectionManager:
    """
    Manage WebSocket connections with user authentication.

    Handles:
        - Multiple concurrent connections per user
        - Broadcasting to authenticated clients only
        - Connection lifecycle with user tracking
        - Message routing with access control
    """

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: dict[str, list[dict[str, Any]]] = {}
        # Structure: {channel: [{"websocket": ws, "user": user, "connected_at": datetime}]}

    async def connect(self, websocket: WebSocket, channel: str, user: models.User):
        """
        Accept new authenticated WebSocket connection.

        Args:
            websocket: WebSocket connection
            channel: Channel name (e.g., "analysis_123")
            user: Authenticated user
        """
        await websocket.accept()

        if channel not in self.active_connections:
            self.active_connections[channel] = []

        connection_info = {
            "websocket": websocket,
            "user": user,
            "connected_at": datetime.utcnow(),
            "user_id": user.id,
            "username": user.username
        }

        self.active_connections[channel].append(connection_info)
        logger.info(f"WebSocket connected to channel: {channel} by user: {user.username}")

    def disconnect(self, websocket: WebSocket, channel: str):
        """
        Remove WebSocket connection.

        Args:
            websocket: WebSocket connection
            channel: Channel name
        """
        if channel in self.active_connections:
            # Find and remove the specific connection
            for i, conn_info in enumerate(self.active_connections[channel]):
                if conn_info["websocket"] == websocket:
                    username = conn_info["username"]
                    self.active_connections[channel].pop(i)
                    logger.info(f"WebSocket disconnected from channel: {channel} by user: {username}")
                    break

            # Clean up empty channels
            if not self.active_connections[channel]:
                del self.active_connections[channel]

    async def send_message(self, channel: str, message: dict[str, Any], target_user_id: int | None = None):
        """
        Send message to authenticated connections in a channel.

        Args:
            channel: Channel name
            message: Message dict (will be JSON encoded)
            target_user_id: Optional user ID to send only to specific user
        """
        if channel not in self.active_connections:
            return

        # Send to all connections in channel (or specific user)
        dead_connections = []

        for conn_info in self.active_connections[channel]:
            # Skip if targeting specific user and this isn't them
            if target_user_id is not None and conn_info["user_id"] != target_user_id:
                continue

            websocket = conn_info["websocket"]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to user {conn_info['username']}: {e}")
                dead_connections.append(websocket)

        # Remove dead connections
        for websocket in dead_connections:
            self.disconnect(websocket, channel)

    async def broadcast(self, message: dict[str, Any], target_user_id: int | None = None):
        """
        Broadcast message to all authenticated connections in all channels.

        Args:
            message: Message dict
            target_user_id: Optional user ID to send only to specific user
        """
        for channel in list(self.active_connections.keys()):
            await self.send_message(channel, message, target_user_id)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/analysis/{task_id}")
async def websocket_analysis_progress(
    websocket: WebSocket,
    task_id: str,
    token: str = Query(..., description="JWT authentication token"),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time analysis progress with authentication.

    Streams progress updates for a specific analysis task to authenticated users only.

    Args:
        websocket: WebSocket connection
        task_id: Analysis task ID
        token: JWT authentication token (required)
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

        async with websockets.connect('ws://localhost:8001/ws/analysis/123?token=your_jwt_token') as ws:
            while True:
                message = await ws.recv()
                data = json.loads(message)
                print(f"Progress: {data['current']}/{data['total']} - {data['message']}")
        ```
    """
    try:
        # Authenticate user before accepting connection
        user = await authenticate_websocket_user(websocket, token, db)

        channel = f"analysis_{task_id}"
        await manager.connect(websocket, channel, user)

        # Send initial connection confirmation
        await websocket.send_json(
            {
                "type": "connected",
                "task_id": task_id,
                "user": user.username,
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
                    # Cancel analysis task (only if user owns it)
                    try:
                        from src.api.routers.analysis import tasks
                        if task_id in tasks:
                            # Verify user has permission to cancel this task
                            task = tasks[task_id]
                            if task.get("user_id") == user.id or user.is_admin:
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
                                        "message": "Not authorized to cancel this task",
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
                        logger.error(f"Failed to cancel task {task_id} for user {user.username}: {e}")
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
async def websocket_health_monitoring(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token"),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time health monitoring with authentication.

    Streams system health metrics every second to authenticated users only.

    Args:
        websocket: WebSocket connection
        token: JWT authentication token (required)
        db: Database session

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
    try:
        # Authenticate user before accepting connection
        user = await authenticate_websocket_user(websocket, token, db)

        channel = "health_monitoring"
        await manager.connect(websocket, channel, user)

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
                    "user": user.username,
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
async def send_analysis_progress(
    task_id: str,
    current: int,
    total: int,
    message: str,
    status: str = "progress",
    target_user_id: int | None = None
):
    """
    Send progress update to authenticated WebSocket clients.

    Call this from your analysis code to stream progress.

    Args:
        task_id: Analysis task ID
        current: Current progress value
        total: Total progress value
        message: Status message
        status: Update type ("progress", "complete", "error")
        target_user_id: Optional user ID to send only to specific user

    Example:
        ```python
        # In your analysis code
        await send_analysis_progress(
            task_id="123",
            current=50,
            total=100,
            message="Extracting entities...",
            target_user_id=user.id  # Send only to task owner
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
        target_user_id=target_user_id
    )
