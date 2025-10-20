"""Async File Handler - Phase 1 Hybrid Async Processing
Low-risk async I/O operations for improved performance
Professional implementation following best practices
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import yaml

try:
    import aiofiles
except ImportError:
    aiofiles = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class AsyncFileHandler:
    """Async file operations for improved I/O performance.

    Phase 1 Implementation:
    - Async file reading/writing
    - Non-blocking document processing
    - Improved progress reporting
    - Better cancellation support
    """

    def __init__(self):
        self.max_file_size = 50 * 1024 * 1024  # 50MB limit

    async def read_document_async(self, file_path: Path) -> str | None:
        """Asynchronously read document content.

        Args:
            file_path: Path to document file

        Returns:
            Document content or None if failed

        """
        if not aiofiles:
            # Fallback to sync reading if aiofiles not available
            return await asyncio.to_thread(self._read_document_sync, file_path)

        try:
            # Check file size
            if file_path.stat().st_size > self.max_file_size:
                logger.warning("File too large: %s", file_path)
                return None

            # Read file asynchronously
            async with aiofiles.open(
                file_path, "r", encoding="utf-8", errors="ignore"
            ) as f:
                content = await f.read()

            logger.info("Successfully read document: %s", file_path.name)
            return content

        except OSError as e:
            logger.exception("Failed to read document %s: %s", file_path, e)
            return None

    def _read_document_sync(self, file_path: Path) -> str | None:
        """Synchronous fallback for document reading."""
        try:
            if file_path.stat().st_size > self.max_file_size:
                logger.warning("File too large: %s", file_path)
                return None

            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            logger.info("Successfully read document: %s", file_path.name)
            return content

        except OSError as e:
            logger.exception("Failed to read document %s: %s", file_path, e)
            return None

    async def write_report_async(self, report_path: Path, content: str) -> bool:
        """Asynchronously write report content.

        Args:
            report_path: Path to output report
            content: Report content to write

        Returns:
            True if successful

        """
        if not aiofiles:
            # Fallback to sync writing if aiofiles not available
            return await asyncio.to_thread(
                self._write_report_sync, report_path, content
            )

        try:
            # Ensure directory exists
            report_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file asynchronously
            async with aiofiles.open(report_path, "w", encoding="utf-8") as f:
                await f.write(content)

            logger.info("Successfully wrote report: %s", report_path.name)
            return True

        except OSError as e:
            logger.exception("Failed to write report %s: %s", report_path, e)
            return False

    def _write_report_sync(self, report_path: Path, content: str) -> bool:
        """Synchronous fallback for report writing."""
        try:
            report_path.parent.mkdir(parents=True, exist_ok=True)

            with open(report_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info("Successfully wrote report: %s", report_path.name)
            return True

        except OSError as e:
            logger.exception("Failed to write report %s: %s", report_path, e)
            return False

    async def read_config_async(self, config_path: Path) -> dict[str, Any] | None:
        """Asynchronously read configuration file.

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary or None if failed

        """
        if not aiofiles:
            return await asyncio.to_thread(self._read_config_sync, config_path)

        try:
            async with aiofiles.open(config_path, "r", encoding="utf-8") as f:
                content = await f.read()

            # Parse JSON/YAML based on extension
            if config_path.suffix.lower() == ".json":
                config = json.loads(content)
            elif config_path.suffix.lower() in [".yaml", ".yml"]:
                try:
                    import yaml

                    config = yaml.safe_load(content)
                except ImportError:
                    logger.warning(
                        "YAML support not available, skipping %s", config_path
                    )
                    return None
            else:
                logger.warning("Unsupported config format: %s", config_path.suffix)
                return None

            logger.info("Successfully loaded config: %s", config_path.name)
            return config

        except (OSError, json.JSONDecodeError) as e:
            logger.exception("Failed to read config %s: %s", config_path, e)
            return None

    def _read_config_sync(self, config_path: Path) -> dict[str, Any] | None:
        """Synchronous fallback for config reading."""
        try:
            with open(config_path, encoding="utf-8") as f:
                content = f.read()

            if config_path.suffix.lower() == ".json":
                config = json.loads(content)
            elif config_path.suffix.lower() in [".yaml", ".yml"]:
                try:
                    config = yaml.safe_load(content)
                except ImportError:
                    logger.warning(
                        "YAML support not available, skipping %s", config_path
                    )
                    return None
            else:
                logger.warning("Unsupported config format: %s", config_path.suffix)
                return None

            logger.info("Successfully loaded config: %s", config_path.name)
            return config

        except (OSError, json.JSONDecodeError) as e:
            logger.exception("Failed to read config %s: %s", config_path, e)
            return None

    async def batch_read_documents(
        self, file_paths: list[Path], progress_callback=None
    ) -> dict[Path, str | None]:
        """Asynchronously read multiple documents with progress reporting.

        Args:
            file_paths: List of document paths to read
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary mapping file paths to their content

        """
        results: dict[Path, str | None] = {}
        total_files = len(file_paths)

        if not file_paths:
            return results

        try:
            # Create semaphore to limit concurrent operations
            semaphore = asyncio.Semaphore(5)  # Max 5 concurrent reads

            async def read_with_semaphore(file_path: Path, index: int):
                async with semaphore:
                    content = await self.read_document_async(file_path)
                    results[file_path] = content

                    # Report progress
                    if progress_callback:
                        progress = ((index + 1) / total_files) * 100
                        await asyncio.to_thread(
                            progress_callback, progress, f"Read {file_path.name}"
                        )

            # Create tasks for all files
            tasks = [
                read_with_semaphore(file_path, i)
                for i, file_path in enumerate(file_paths)
            ]

            # Execute all tasks concurrently
            await asyncio.gather(*tasks, return_exceptions=True)

            logger.info("Successfully processed %d documents", len(results))
            return results

        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.exception("Batch document reading failed: %s", e)
            return results

    async def cleanup_temp_files_async(
        self, temp_dir: Path, max_age_hours: int = 24
    ) -> int:
        """Asynchronously clean up old temporary files.

        Args:
            temp_dir: Directory containing temporary files
            max_age_hours: Maximum age of files to keep

        Returns:
            Number of files cleaned up

        """
        try:
            if not temp_dir.exists():
                return 0

            import time

            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            cleaned_count = 0

            # Process files asynchronously
            for file_path in temp_dir.rglob("*"):
                if file_path.is_file():
                    try:
                        file_age = current_time - file_path.stat().st_mtime

                        if file_age > max_age_seconds:
                            await asyncio.to_thread(file_path.unlink)
                            cleaned_count += 1
                    except OSError as e:
                        logger.warning("Failed to delete %s: %s", file_path, e)

            logger.info("Cleaned up %d temporary files", cleaned_count)
            return cleaned_count

        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.exception("Temp file cleanup failed: %s", e)
            return 0


# Global async file handler instance
# Global async file handler instance
# Global async file handler instance
async_file_handler = AsyncFileHandler()
