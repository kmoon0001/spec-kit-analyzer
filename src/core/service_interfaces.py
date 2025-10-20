"""Service interfaces and implementations.

This module provides service interfaces and their implementations
for core application services.
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol

from src.core.interfaces import (
    AnalysisServiceInterface,
    AuditLoggerInterface,
    EncryptionServiceInterface,
    ErrorHandlerInterface,
    NotificationServiceInterface,
    SessionManagerInterface,
    StorageServiceInterface,
    TaskManagerInterface,
    ValidatorInterface,
)


class ServiceRegistry:
    """Registry for service instances."""

    def __init__(self):
        self._services: Dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        """Register a service."""
        self._services[name] = service

    def get(self, name: str) -> Any:
        """Get a service by name."""
        if name not in self._services:
            raise ValueError(f"Service '{name}' not found")
        return self._services[name]

    def unregister(self, name: str) -> None:
        """Unregister a service."""
        if name in self._services:
            del self._services[name]

    def list_services(self) -> List[str]:
        """List all registered services."""
        return list(self._services.keys())


# Global service registry
service_registry = ServiceRegistry()


class BaseService(ABC):
    """Base class for all services."""

    def __init__(self, name: str):
        self.name = name
        self._initialized = False
        self._started = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service."""
        pass

    @abstractmethod
    async def start(self) -> None:
        """Start the service."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the service."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        pass

    @property
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._initialized

    @property
    def is_started(self) -> bool:
        """Check if service is started."""
        return self._started


class AnalysisService(BaseService):
    """Analysis service implementation."""

    def __init__(self, name: str = "analysis"):
        super().__init__(name)
        self._tasks: Dict[str, Dict[str, Any]] = {}

    async def initialize(self) -> None:
        """Initialize the analysis service."""
        self._initialized = True

    async def start(self) -> None:
        """Start the analysis service."""
        if not self._initialized:
            await self.initialize()
        self._started = True

    async def stop(self) -> None:
        """Stop the analysis service."""
        self._started = False

    async def health_check(self) -> Dict[str, Any]:
        """Check analysis service health."""
        return {
            "status": "healthy" if self._started else "stopped",
            "initialized": self._initialized,
            "started": self._started,
            "active_tasks": len(self._tasks),
        }

    async def analyze_document(
        self,
        content: bytes,
        filename: str,
        discipline: str,
        analysis_mode: str,
        strictness: str,
    ) -> Dict[str, Any]:
        """Analyze a document for compliance."""
        if not self._started:
            raise RuntimeError("Analysis service is not started")

        # Mock implementation
        task_id = f"task_{len(self._tasks) + 1}"
        self._tasks[task_id] = {
            "status": "processing",
            "filename": filename,
            "created_at": datetime.utcnow(),
        }

        # Simulate analysis
        await asyncio.sleep(1)

        result = {
            "task_id": task_id,
            "status": "completed",
            "compliance_score": 85.5,
            "findings": [
                {
                    "rule_id": "rule_001",
                    "risk_level": "medium",
                    "description": "Missing required documentation",
                    "confidence": 0.95,
                }
            ],
        }

        self._tasks[task_id]["result"] = result
        self._tasks[task_id]["status"] = "completed"

        return result


class EncryptionService(BaseService):
    """Encryption service implementation."""

    def __init__(self, name: str = "encryption"):
        super().__init__(name)
        self._key: Optional[str] = None

    async def initialize(self) -> None:
        """Initialize the encryption service."""
        # In production, load from secure configuration
        self._key = "default-encryption-key-change-in-production"
        self._initialized = True

    async def start(self) -> None:
        """Start the encryption service."""
        if not self._initialized:
            await self.initialize()
        self._started = True

    async def stop(self) -> None:
        """Stop the encryption service."""
        self._started = False

    async def health_check(self) -> Dict[str, Any]:
        """Check encryption service health."""
        return {
            "status": "healthy" if self._started else "stopped",
            "initialized": self._initialized,
            "started": self._started,
            "key_configured": self._key is not None,
        }

    def encrypt(self, data: str) -> str:
        """Encrypt data."""
        if not self._started:
            raise RuntimeError("Encryption service is not started")

        # Simple XOR encryption for demo
        encrypted = ""
        for i, char in enumerate(data):
            encrypted += chr(ord(char) ^ ord(self._key[i % len(self._key)]))

        return encrypted.encode().hex()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data."""
        if not self._started:
            raise RuntimeError("Encryption service is not started")

        # Simple XOR decryption for demo
        data = bytes.fromhex(encrypted_data).decode()
        decrypted = ""
        for i, char in enumerate(data):
            decrypted += chr(ord(char) ^ ord(self._key[i % len(self._key)]))

        return decrypted


class SessionService(BaseService):
    """Session management service implementation."""

    def __init__(self, name: str = "session"):
        super().__init__(name)
        self._sessions: Dict[str, Dict[str, Any]] = {}

    async def initialize(self) -> None:
        """Initialize the session service."""
        self._initialized = True

    async def start(self) -> None:
        """Start the session service."""
        if not self._initialized:
            await self.initialize()
        self._started = True

    async def stop(self) -> None:
        """Stop the session service."""
        self._started = False

    async def health_check(self) -> Dict[str, Any]:
        """Check session service health."""
        return {
            "status": "healthy" if self._started else "stopped",
            "initialized": self._initialized,
            "started": self._started,
            "active_sessions": len(self._sessions),
        }

    def create_session(self, user_id: int, client_info: Dict[str, Any]) -> str:
        """Create a new session."""
        if not self._started:
            raise RuntimeError("Session service is not started")

        session_id = f"session_{len(self._sessions) + 1}"
        self._sessions[session_id] = {
            "user_id": user_id,
            "client_info": client_info,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "is_active": True,
        }

        return session_id

    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate a session."""
        if not self._started:
            raise RuntimeError("Session service is not started")

        return self._sessions.get(session_id)

    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session."""
        if not self._started:
            raise RuntimeError("Session service is not started")

        if session_id in self._sessions:
            del self._sessions[session_id]
            return True

        return False


class NotificationService(BaseService):
    """Notification service implementation."""

    def __init__(self, name: str = "notification"):
        super().__init__(name)
        self._notifications: List[Dict[str, Any]] = []

    async def initialize(self) -> None:
        """Initialize the notification service."""
        self._initialized = True

    async def start(self) -> None:
        """Start the notification service."""
        if not self._initialized:
            await self.initialize()
        self._started = True

    async def stop(self) -> None:
        """Stop the notification service."""
        self._started = False

    async def health_check(self) -> Dict[str, Any]:
        """Check notification service health."""
        return {
            "status": "healthy" if self._started else "stopped",
            "initialized": self._initialized,
            "started": self._started,
            "pending_notifications": len(self._notifications),
        }

    async def send_notification(
        self,
        user_id: int,
        message: str,
        notification_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send a notification to a user."""
        if not self._started:
            raise RuntimeError("Notification service is not started")

        notification = {
            "user_id": user_id,
            "message": message,
            "type": notification_type,
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
            "sent": False,
        }

        self._notifications.append(notification)

        # Simulate sending
        await asyncio.sleep(0.1)
        notification["sent"] = True

        return True


class AuditService(BaseService):
    """Audit logging service implementation."""

    def __init__(self, name: str = "audit"):
        super().__init__(name)
        self._events: List[Dict[str, Any]] = []

    async def initialize(self) -> None:
        """Initialize the audit service."""
        self._initialized = True

    async def start(self) -> None:
        """Start the audit service."""
        if not self._initialized:
            await self.initialize()
        self._started = True

    async def stop(self) -> None:
        """Stop the audit service."""
        self._started = False

    async def health_check(self) -> Dict[str, Any]:
        """Check audit service health."""
        return {
            "status": "healthy" if self._started else "stopped",
            "initialized": self._initialized,
            "started": self._started,
            "logged_events": len(self._events),
        }

    def log_event(
        self,
        event_type: str,
        user_id: Optional[int],
        details: Dict[str, Any],
        request_id: Optional[str] = None,
    ) -> None:
        """Log an audit event."""
        if not self._started:
            raise RuntimeError("Audit service is not started")

        event = {
            "event_type": event_type,
            "user_id": user_id,
            "details": details,
            "request_id": request_id,
            "timestamp": datetime.utcnow(),
        }

        self._events.append(event)


# Service factory functions
def create_analysis_service() -> AnalysisService:
    """Create analysis service instance."""
    return AnalysisService()


def create_encryption_service() -> EncryptionService:
    """Create encryption service instance."""
    return EncryptionService()


def create_session_service() -> SessionService:
    """Create session service instance."""
    return SessionService()


def create_notification_service() -> NotificationService:
    """Create notification service instance."""
    return NotificationService()


def create_audit_service() -> AuditService:
    """Create audit service instance."""
    return AuditService()


# Service manager
class ServiceManager:
    """Manages all application services."""

    def __init__(self):
        self._services: Dict[str, BaseService] = {}

    async def register_service(self, name: str, service: BaseService) -> None:
        """Register a service."""
        self._services[name] = service
        service_registry.register(name, service)

    async def initialize_all(self) -> None:
        """Initialize all services."""
        for service in self._services.values():
            await service.initialize()

    async def start_all(self) -> None:
        """Start all services."""
        for service in self._services.values():
            await service.start()

    async def stop_all(self) -> None:
        """Stop all services."""
        for service in self._services.values():
            await service.stop()

    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all services."""
        health_status = {}
        for name, service in self._services.items():
            health_status[name] = await service.health_check()
        return health_status

    def get_service(self, name: str) -> BaseService:
        """Get a service by name."""
        if name not in self._services:
            raise ValueError(f"Service '{name}' not found")
        return self._services[name]
