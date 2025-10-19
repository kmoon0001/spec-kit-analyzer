#!/usr/bin/env python3
"""
Enhanced file cleanup service for Electron + Python architecture.
Implements automatic cleanup of temporary files and prevents disk space issues.
"""

import asyncio
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Optional

from src.config import get_settings

logger = logging.getLogger(__name__)


class FileCleanupService:
    """Service for managing temporary files and preventing disk space issues."""

    def __init__(self):
        self.settings = get_settings()
        self.temp_dirs = [
            Path(self.settings.paths.temp_upload_dir),
            Path(self.settings.paths.cache_dir),
            Path("uploads"),  # Legacy upload directory
        ]
        self.cleanup_interval = 3600  # 1 hour
        self.file_max_age = 3600  # 1 hour
        self.is_running = False

    async def start_cleanup_service(self):
        """Start the background cleanup service."""
        if self.is_running:
            return

        self.is_running = True
        logger.info("Starting file cleanup service...")

        # Run cleanup immediately
        await self.cleanup_old_files()

        # Schedule periodic cleanup
        while self.is_running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_old_files()
            except Exception as e:
                logger.error(f"Error in cleanup service: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    def stop_cleanup_service(self):
        """Stop the background cleanup service."""
        self.is_running = False
        logger.info("File cleanup service stopped")

    async def cleanup_old_files(self):
        """Clean up old temporary files."""
        cutoff_time = time.time() - self.file_max_age
        total_cleaned = 0
        total_size_freed = 0

        for temp_dir in self.temp_dirs:
            if not temp_dir.exists():
                continue

            try:
                cleaned_count, size_freed = await self._cleanup_directory(temp_dir, cutoff_time)
                total_cleaned += cleaned_count
                total_size_freed += size_freed

            except Exception as e:
                logger.error(f"Error cleaning directory {temp_dir}: {e}")

        if total_cleaned > 0:
            logger.info(f"Cleaned {total_cleaned} files, freed {total_size_freed / 1024 / 1024:.2f} MB")

    async def _cleanup_directory(self, directory: Path, cutoff_time: float) -> tuple[int, int]:
        """Clean up files in a specific directory."""
        cleaned_count = 0
        size_freed = 0

        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    file_stat = file_path.stat()
                    if file_stat.st_mtime < cutoff_time:
                        size_freed += file_stat.st_size
                        file_path.unlink()
                        cleaned_count += 1

                except (OSError, PermissionError) as e:
                    logger.warning(f"Could not delete {file_path}: {e}")

        return cleaned_count, size_freed

    async def cleanup_task_files(self, task_id: str):
        """Clean up files associated with a specific task."""
        for temp_dir in self.temp_dirs:
            if not temp_dir.exists():
                continue

            # Look for files with task_id in the name
            for file_path in temp_dir.glob(f"*{task_id}*"):
                try:
                    if file_path.is_file():
                        file_path.unlink()
                        logger.debug(f"Cleaned up task file: {file_path}")
                except (OSError, PermissionError) as e:
                    logger.warning(f"Could not delete task file {file_path}: {e}")

    def get_disk_usage(self) -> dict[str, float]:
        """Get disk usage statistics for temp directories."""
        usage = {}

        for temp_dir in self.temp_dirs:
            if temp_dir.exists():
                try:
                    total_size = sum(f.stat().st_size for f in temp_dir.rglob('*') if f.is_file())
                    usage[str(temp_dir)] = total_size / 1024 / 1024  # MB
                except Exception as e:
                    logger.error(f"Error calculating disk usage for {temp_dir}: {e}")
                    usage[str(temp_dir)] = 0.0
            else:
                usage[str(temp_dir)] = 0.0

        return usage


# Global cleanup service instance
_cleanup_service: Optional[FileCleanupService] = None


def get_cleanup_service() -> FileCleanupService:
    """Get the global cleanup service instance."""
    global _cleanup_service
    if _cleanup_service is None:
        _cleanup_service = FileCleanupService()
    return _cleanup_service


async def start_cleanup_service():
    """Start the global cleanup service."""
    service = get_cleanup_service()
    await service.start_cleanup_service()


def stop_cleanup_service():
    """Stop the global cleanup service."""
    service = get_cleanup_service()
    service.stop_cleanup_service()
