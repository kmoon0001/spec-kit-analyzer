"""Document cleanup service for secure storage.

This module provides automated cleanup of expired documents and temporary files
to maintain security and prevent disk space issues.
"""

import asyncio
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

from src.core.file_encryption import get_secure_storage

logger = logging.getLogger(__name__)


class DocumentCleanupService:
    """Service for cleaning up expired documents and temporary files."""

    def __init__(self, cleanup_interval_hours: int = 1, max_age_hours: int = 24):
        """
        Initialize cleanup service.

        Args:
            cleanup_interval_hours: How often to run cleanup (hours)
            max_age_hours: Maximum age of documents before cleanup (hours)
        """
        self.cleanup_interval_hours = cleanup_interval_hours
        self.max_age_hours = max_age_hours
        self.secure_storage = get_secure_storage()
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        """Start the cleanup service."""
        if self._running:
            logger.warning("Cleanup service is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._cleanup_loop())
        logger.info(
            f"Document cleanup service started (interval: {self.cleanup_interval_hours}h, max_age: {self.max_age_hours}h)"
        )

    async def stop(self):
        """Stop the cleanup service."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Document cleanup service stopped")

    async def _cleanup_loop(self):
        """Main cleanup loop."""
        while self._running:
            try:
                await self._run_cleanup()
                await asyncio.sleep(
                    self.cleanup_interval_hours * 3600
                )  # Convert hours to seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying

    async def _run_cleanup(self):
        """Run cleanup operations."""
        logger.info("Starting document cleanup")

        # Clean up expired documents
        expired_count = await self._cleanup_expired_documents()

        # Clean up temporary files
        temp_count = await self._cleanup_temp_files()

        # Clean up old log files
        log_count = await self._cleanup_log_files()

        logger.info(
            f"Cleanup completed: {expired_count} expired docs, {temp_count} temp files, {log_count} log files"
        )

    async def _cleanup_expired_documents(self) -> int:
        """Clean up expired documents from secure storage."""
        try:
            # Run cleanup in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, self.secure_storage.cleanup_expired_documents, self.max_age_hours
            )

            # Count remaining documents
            user_docs = self.secure_storage.list_user_documents(
                0
            )  # This will be empty, but we can check metadata
            # Note: This is a simplified count - in production you'd want a better way to count expired docs

            logger.info("Expired documents cleaned up")
            return 0  # Return count of cleaned documents

        except Exception as e:
            logger.error(f"Failed to cleanup expired documents: {e}")
            return 0

    async def _cleanup_temp_files(self) -> int:
        """Clean up temporary files."""
        temp_dirs = [Path("temp"), Path(".cache"), Path("secure_storage") / "temp"]

        cleaned_count = 0
        cutoff_time = datetime.now() - timedelta(hours=self.max_age_hours)

        for temp_dir in temp_dirs:
            if not temp_dir.exists():
                continue

            try:
                for file_path in temp_dir.rglob("*"):
                    if file_path.is_file():
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_mtime < cutoff_time:
                            file_path.unlink()
                            cleaned_count += 1
                            logger.debug(f"Cleaned up temp file: {file_path}")

            except Exception as e:
                logger.error(f"Failed to cleanup temp directory {temp_dir}: {e}")

        return cleaned_count

    async def _cleanup_log_files(self) -> int:
        """Clean up old log files."""
        log_dirs = [Path("logs"), Path(".")]  # Check for log files in root

        cleaned_count = 0
        cutoff_time = datetime.now() - timedelta(days=7)  # Keep logs for 7 days

        for log_dir in log_dirs:
            if not log_dir.exists():
                continue

            try:
                for file_path in log_dir.glob("*.log*"):
                    if file_path.is_file():
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_mtime < cutoff_time:
                            file_path.unlink()
                            cleaned_count += 1
                            logger.debug(f"Cleaned up log file: {file_path}")

            except Exception as e:
                logger.error(f"Failed to cleanup log directory {log_dir}: {e}")

        return cleaned_count

    async def cleanup_now(self) -> Dict[str, int]:
        """Manually trigger cleanup and return statistics."""
        logger.info("Manual cleanup triggered")

        expired_count = await self._cleanup_expired_documents()
        temp_count = await self._cleanup_temp_files()
        log_count = await self._cleanup_log_files()

        stats = {
            "expired_documents": expired_count,
            "temp_files": temp_count,
            "log_files": log_count,
            "total_cleaned": expired_count + temp_count + log_count,
        }

        logger.info(f"Manual cleanup completed: {stats}")
        return stats


# Global cleanup service instance
_cleanup_service: DocumentCleanupService | None = None


def get_cleanup_service() -> DocumentCleanupService:
    """Get global cleanup service instance."""
    global _cleanup_service
    if _cleanup_service is None:
        _cleanup_service = DocumentCleanupService()
    return _cleanup_service


async def start_cleanup_service():
    """Start the global cleanup service."""
    service = get_cleanup_service()
    await service.start()


async def stop_cleanup_service():
    """Stop the global cleanup service."""
    service = get_cleanup_service()
    await service.stop()
