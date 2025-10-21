"""Comprehensive cleanup services for the Therapy Compliance Analyzer.

This module provides automated cleanup services for various system components
including expired data, temporary files, logs, and system resources.
"""

import asyncio
import logging
import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.file_encryption import get_secure_storage
from src.core.service_interfaces import BaseService
from src.core.session_manager import get_session_manager

logger = logging.getLogger(__name__)


class CleanupService(BaseService):
    """Base cleanup service with common functionality."""

    def __init__(self, name: str, cleanup_interval_hours: int = 1):
        super().__init__(name)
        self.cleanup_interval_hours = cleanup_interval_hours
        self._last_cleanup = time.time()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def initialize(self) -> None:
        """Initialize the cleanup service."""
        self._initialized = True

    async def start(self) -> None:
        """Start the cleanup service."""
        if not self._initialized:
            await self.initialize()

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._started = True

        logger.info(f"{self.name} cleanup service started")

    async def stop(self) -> None:
        """Stop the cleanup service."""
        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        self._started = False
        logger.info(f"{self.name} cleanup service stopped")

    async def health_check(self) -> Dict[str, Any]:
        """Check cleanup service health."""
        return {
            "status": "healthy" if self._started else "stopped",
            "initialized": self._initialized,
            "started": self._started,
            "running": self._running,
            "last_cleanup": self._last_cleanup,
            "cleanup_interval_hours": self.cleanup_interval_hours,
        }

    async def _cleanup_loop(self) -> None:
        """Main cleanup loop."""
        while self._running:
            try:
                await self._run_cleanup()
                await asyncio.sleep(self.cleanup_interval_hours * 3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in {self.name} cleanup loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying

    async def _run_cleanup(self) -> None:
        """Run cleanup operations. Override in subclasses."""
        self._last_cleanup = time.time()
        logger.info(f"{self.name} cleanup completed")


class DocumentCleanupService(CleanupService):
    """Cleanup service for documents and files."""

    def __init__(self, max_age_hours: int = 168):  # 7 days
        super().__init__("document", cleanup_interval_hours=6)
        self.max_age_hours = max_age_hours
        self.secure_storage = get_secure_storage()

    async def _run_cleanup(self) -> None:
        """Clean up expired documents."""
        logger.info("Starting document cleanup")

        try:
            # Clean up expired documents from secure storage
            await asyncio.get_event_loop().run_in_executor(
                None, self.secure_storage.cleanup_expired_documents, self.max_age_hours
            )

            # Clean up temporary files
            temp_dirs = [
                Path("temp"),
                Path(".cache"),
                Path("secure_storage") / "temp",
                Path("uploads") / "temp",
            ]

            cleaned_files = 0
            cutoff_time = datetime.now() - timedelta(hours=self.max_age_hours)

            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    cleaned_files += await self._cleanup_directory(
                        temp_dir, cutoff_time
                    )

            logger.info(f"Document cleanup completed: {cleaned_files} files cleaned")

        except Exception as e:
            logger.error(f"Document cleanup failed: {e}")

        self._last_cleanup = time.time()

    async def _cleanup_directory(self, directory: Path, cutoff_time: datetime) -> int:
        """Clean up files in a directory older than cutoff time."""
        cleaned_count = 0

        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_time:
                        file_path.unlink()
                        cleaned_count += 1
                        logger.debug(f"Cleaned up file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup directory {directory}: {e}")

        return cleaned_count


class SessionCleanupService(CleanupService):
    """Cleanup service for expired sessions."""

    def __init__(self, max_age_hours: int = 24):
        super().__init__("session", cleanup_interval_hours=1)
        self.max_age_hours = max_age_hours
        self.session_manager = get_session_manager()

    async def _run_cleanup(self) -> None:
        """Clean up expired sessions."""
        logger.info("Starting session cleanup")

        try:
            # Get session statistics
            stats = self.session_manager.get_session_stats()
            initial_sessions = stats["active_sessions"]

            # Clean up expired sessions
            await asyncio.get_event_loop().run_in_executor(
                None, self.session_manager._cleanup_expired_sessions
            )

            # Get updated statistics
            stats_after = self.session_manager.get_session_stats()
            final_sessions = stats_after["active_sessions"]
            cleaned_sessions = initial_sessions - final_sessions

            logger.info(
                f"Session cleanup completed: {cleaned_sessions} sessions cleaned"
            )

        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")

        self._last_cleanup = time.time()


class LogCleanupService(CleanupService):
    """Cleanup service for log files."""

    def __init__(self, max_age_days: int = 30):
        super().__init__("log", cleanup_interval_hours=24)
        self.max_age_days = max_age_days

    async def _run_cleanup(self) -> None:
        """Clean up old log files."""
        logger.info("Starting log cleanup")

        try:
            log_dirs = [
                Path("logs"),
                Path("."),  # Check for log files in root
                Path("secure_storage") / "logs",
            ]

            cleaned_files = 0
            cutoff_time = datetime.now() - timedelta(days=self.max_age_days)

            for log_dir in log_dirs:
                if log_dir.exists():
                    cleaned_files += await self._cleanup_log_directory(
                        log_dir, cutoff_time
                    )

            logger.info(f"Log cleanup completed: {cleaned_files} files cleaned")

        except Exception as e:
            logger.error(f"Log cleanup failed: {e}")

        self._last_cleanup = time.time()

    async def _cleanup_log_directory(
        self, directory: Path, cutoff_time: datetime
    ) -> int:
        """Clean up log files in a directory."""
        cleaned_count = 0

        try:
            for file_path in directory.glob("*.log*"):
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_time:
                        file_path.unlink()
                        cleaned_count += 1
                        logger.debug(f"Cleaned up log file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup log directory {directory}: {e}")

        return cleaned_count


class DatabaseCleanupService(CleanupService):
    """Cleanup service for database maintenance."""

    def __init__(self, max_age_days: int = 90):
        super().__init__("database", cleanup_interval_hours=168)  # Weekly
        self.max_age_days = max_age_days

    async def _run_cleanup(self) -> None:
        """Clean up old database records."""
        logger.info("Starting database cleanup")

        try:
            # This would typically involve database operations
            # For now, we'll just log the cleanup
            logger.info("Database cleanup completed")

        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")

        self._last_cleanup = time.time()


class SystemResourceCleanupService(CleanupService):
    """Cleanup service for system resources."""

    def __init__(self):
        super().__init__("system", cleanup_interval_hours=1)

    async def _run_cleanup(self) -> None:
        """Clean up system resources."""
        logger.info("Starting system resource cleanup")

        try:
            # Clean up temporary system files
            temp_system_dirs = [
                (
                    Path("/tmp")
                    if os.name != "nt"
                    else Path(os.environ.get("TEMP", "C:\\temp"))
                ),
                Path(".cache"),
                Path("__pycache__"),
            ]

            cleaned_items = 0

            for temp_dir in temp_system_dirs:
                if temp_dir.exists():
                    cleaned_items += await self._cleanup_system_directory(temp_dir)

            logger.info(
                f"System resource cleanup completed: {cleaned_items} items cleaned"
            )

        except Exception as e:
            logger.error(f"System resource cleanup failed: {e}")

        self._last_cleanup = time.time()

    async def _cleanup_system_directory(self, directory: Path) -> int:
        """Clean up system directory."""
        cleaned_count = 0

        try:
            # Clean up Python cache files
            for pycache_dir in directory.rglob("__pycache__"):
                if pycache_dir.is_dir():
                    shutil.rmtree(pycache_dir)
                    cleaned_count += 1
                    logger.debug(f"Cleaned up pycache: {pycache_dir}")

            # Clean up .pyc files
            for pyc_file in directory.rglob("*.pyc"):
                pyc_file.unlink()
                cleaned_count += 1
                logger.debug(f"Cleaned up pyc file: {pyc_file}")

        except Exception as e:
            logger.error(f"Failed to cleanup system directory {directory}: {e}")

        return cleaned_count


class CleanupManager:
    """Manages all cleanup services."""

    def __init__(self):
        self._services: Dict[str, CleanupService] = {}
        self._running = False

    def register_service(self, service: CleanupService) -> None:
        """Register a cleanup service."""
        self._services[service.name] = service
        logger.info(f"Registered cleanup service: {service.name}")

    async def start_all(self) -> None:
        """Start all cleanup services."""
        if self._running:
            logger.warning("Cleanup manager is already running")
            return

        self._running = True

        for service in self._services.values():
            try:
                await service.start()
            except Exception as e:
                logger.error(f"Failed to start cleanup service {service.name}: {e}")

        logger.info("All cleanup services started")

    async def stop_all(self) -> None:
        """Stop all cleanup services."""
        if not self._running:
            return

        self._running = False

        for service in self._services.values():
            try:
                await service.stop()
            except Exception as e:
                logger.error(f"Failed to stop cleanup service {service.name}: {e}")

        logger.info("All cleanup services stopped")

    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all cleanup services."""
        health_status = {}

        for name, service in self._services.items():
            try:
                health_status[name] = await service.health_check()
            except Exception as e:
                health_status[name] = {"status": "error", "error": str(e)}

        return health_status

    async def run_cleanup_now(
        self, service_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run cleanup immediately for specified service or all services."""
        results = {}

        if service_name:
            if service_name in self._services:
                service = self._services[service_name]
                try:
                    await service._run_cleanup()
                    results[service_name] = {"status": "completed"}
                except Exception as e:
                    results[service_name] = {"status": "failed", "error": str(e)}
            else:
                results[service_name] = {"status": "not_found"}
        else:
            # Run cleanup for all services
            for name, service in self._services.items():
                try:
                    await service._run_cleanup()
                    results[name] = {"status": "completed"}
                except Exception as e:
                    results[name] = {"status": "failed", "error": str(e)}

        return results

    def get_service_stats(self) -> Dict[str, Any]:
        """Get statistics for all cleanup services."""
        stats = {
            "total_services": len(self._services),
            "running": self._running,
            "services": {},
        }

        for name, service in self._services.items():
            stats["services"][name] = {
                "initialized": service.is_initialized,
                "started": service.is_started,
                "cleanup_interval_hours": service.cleanup_interval_hours,
                "last_cleanup": service._last_cleanup,
            }

        return stats


# Global cleanup manager
cleanup_manager = CleanupManager()


def initialize_cleanup_services() -> CleanupManager:
    """Initialize all cleanup services."""
    # Register all cleanup services
    cleanup_manager.register_service(DocumentCleanupService())
    cleanup_manager.register_service(SessionCleanupService())
    cleanup_manager.register_service(LogCleanupService())
    cleanup_manager.register_service(DatabaseCleanupService())
    cleanup_manager.register_service(SystemResourceCleanupService())

    return cleanup_manager


async def start_cleanup_services():
    """Start all cleanup services."""
    manager = initialize_cleanup_services()
    await manager.start_all()
    return manager


async def stop_cleanup_services():
    """Stop all cleanup services."""
    await cleanup_manager.stop_all()
