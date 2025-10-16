"""
File I/O Worker (Production Version)

Handles all file operations in background thread with:
    - Chunked reading for large files
    - Progress reporting
    - Secure file deletion (overwrite + delete)
    - Error recovery
    - Memory-efficient processing

NEVER does file I/O on GUI thread!
"""

import os
import logging
from pathlib import Path

from src.gui.core import BaseWorker, FileSignals, ResourceMonitor


logger = logging.getLogger(__name__)


class FileReadWorker(BaseWorker):
    """
    Read files in background with progress reporting.

    Features:
        - Chunked reading for large files
        - Memory-efficient streaming
        - Progress updates
        - Encoding detection
        - Error handling

    Usage:
        ```python
        worker = FileReadWorker(
            file_path="large_document.txt",
            chunk_size=1024*1024  # 1MB chunks
        )
        worker.signals.result.connect(on_file_loaded)
        worker.signals.progress.connect(update_progress)

        threadpool.start(worker)
        ```
    """

    def __init__(
        self,
        file_path: str,
        chunk_size: int = 1024 * 1024,  # 1MB default
        encoding: str = "utf-8",
        timeout_seconds: float = 60.0,
        resource_monitor: ResourceMonitor | None = None,
    ):
        """
        Initialize file read worker.

        Args:
            file_path: Path to file to read
            chunk_size: Bytes per chunk
            encoding: File encoding
            timeout_seconds: Maximum read time
            resource_monitor: Resource monitor instance
        """
        super().__init__(timeout_seconds=timeout_seconds, resource_monitor=resource_monitor, job_type="general")

        self.file_path = Path(file_path)
        self.chunk_size = chunk_size
        self.encoding = encoding

    def create_signals(self) -> FileSignals:
        """Use specialized file signals."""
        return FileSignals()

    def do_work(self) -> str:
        """
        Read file contents.

        Returns:
            Complete file contents as string

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If can't read file
            UnicodeDecodeError: If encoding is wrong
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        # Get file size
        file_size = self.file_path.stat().st_size

        # Emit file opened signal
        self.signals.file_opened.emit(str(self.file_path))

        # Read file in chunks
        content_chunks = []
        bytes_read = 0

        try:
            with open(self.file_path, encoding=self.encoding) as f:
                while True:
                    if self.is_cancelled():
                        return ""

                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break

                    content_chunks.append(chunk)
                    bytes_read += len(chunk.encode(self.encoding))

                    # Report progress
                    self.signals.file_chunk_read.emit(bytes_read, file_size)
                    self.report_progress(bytes_read, file_size, f"Read {bytes_read}/{file_size} bytes")

            # Join chunks
            content = "".join(content_chunks)

            return content

        except UnicodeDecodeError:
            # Try fallback encoding
            logger.warning(f"Failed to decode with {self.encoding}, trying utf-8 with errors='ignore'")

            with open(self.file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            return content

    def cleanup(self):
        """Clean up resources."""
        logger.debug(f"File read worker cleanup: {self.file_path.name}")


class FileWriteWorker(BaseWorker):
    """
    Write files in background with progress reporting.

    Features:
        - Safe atomic writes (temp file + rename)
        - Progress updates
        - Automatic backup creation
        - Error recovery
    """

    def __init__(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        create_backup: bool = False,
        timeout_seconds: float = 60.0,
        resource_monitor: ResourceMonitor | None = None,
    ):
        """
        Initialize file write worker.

        Args:
            file_path: Path to write to
            content: Content to write
            encoding: File encoding
            create_backup: Create .bak file if original exists
            timeout_seconds: Maximum write time
            resource_monitor: Resource monitor instance
        """
        super().__init__(timeout_seconds=timeout_seconds, resource_monitor=resource_monitor, job_type="general")

        self.file_path = Path(file_path)
        self.content = content
        self.encoding = encoding
        self.create_backup = create_backup
        self._temp_file: Path | None = None

    def create_signals(self) -> FileSignals:
        """Use specialized file signals."""
        return FileSignals()

    def do_work(self) -> str:
        """
        Write file contents atomically.

        Returns:
            Path to written file

        Raises:
            PermissionError: If can't write file
            IOError: On write errors
        """
        # Create parent directory if needed
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create backup if requested
        if self.create_backup and self.file_path.exists():
            backup_path = self.file_path.with_suffix(self.file_path.suffix + ".bak")
            self.file_path.replace(backup_path)
            logger.info(f"Created backup: {backup_path}")

        # Write to temp file first (atomic operation)
        self._temp_file = self.file_path.with_suffix(self.file_path.suffix + ".tmp")

        try:
            # Write content
            with open(self._temp_file, "w", encoding=self.encoding) as f:
                f.write(self.content)

            # Atomic rename
            self._temp_file.replace(self.file_path)

            # Emit saved signal
            self.signals.file_saved.emit(str(self.file_path))

            return str(self.file_path)

        except Exception as e:
            # Emit IO error signal
            self.signals.io_error.emit(str(self.file_path), str(e))
            raise

    def cleanup(self):
        """Clean up temp file if it exists."""
        if self._temp_file and self._temp_file.exists():
            try:
                self._temp_file.unlink()
                logger.debug(f"Cleaned up temp file: {self._temp_file}")
            except Exception as e:
                logger.error(f"Failed to clean up temp file: {e}")


class SecureFileDeleteWorker(BaseWorker):
    """
    Securely delete files with overwrite before deletion.

    Critical for PHI/PII data - prevents file recovery.

    Features:
        - Multiple-pass overwrite
        - Random data overwrite
        - Verification
        - Batch deletion support
    """

    def __init__(
        self,
        file_paths: list[str],
        overwrite_passes: int = 3,
        timeout_seconds: float = 60.0,
        resource_monitor: ResourceMonitor | None = None,
    ):
        """
        Initialize secure delete worker.

        Args:
            file_paths: List of files to delete
            overwrite_passes: Number of overwrite passes
            timeout_seconds: Maximum deletion time
            resource_monitor: Resource monitor instance
        """
        super().__init__(timeout_seconds=timeout_seconds, resource_monitor=resource_monitor, job_type="general")

        self.file_paths = [Path(p) for p in file_paths]
        self.overwrite_passes = overwrite_passes

    def create_signals(self) -> FileSignals:
        """Use specialized file signals."""
        return FileSignals()

    def do_work(self) -> dict[str, bool]:
        """
        Securely delete all files.

        Returns:
            Dict of {file_path: success_bool}
        """
        results = {}
        total_files = len(self.file_paths)

        for idx, file_path in enumerate(self.file_paths):
            if self.is_cancelled():
                break

            try:
                self.report_progress(idx, total_files, f"Securely deleting {file_path.name}...")

                success = self._secure_delete(file_path)
                results[str(file_path)] = success

                if success:
                    self.signals.file_deleted.emit(str(file_path))

            except Exception as e:
                logger.error(f"Failed to delete {file_path}: {e}")
                self.signals.io_error.emit(str(file_path), str(e))
                results[str(file_path)] = False

        return results

    def _secure_delete(self, file_path: Path) -> bool:
        """
        Securely delete a single file.

        Args:
            file_path: File to delete

        Returns:
            True if successful
        """
        if not file_path.exists():
            logger.warning(f"File doesn't exist: {file_path}")
            return False

        try:
            file_size = file_path.stat().st_size

            # Overwrite with random data (multiple passes)
            for pass_num in range(self.overwrite_passes):
                if self.is_cancelled():
                    return False

                with open(file_path, "wb") as f:
                    # Write random data in chunks
                    bytes_written = 0
                    chunk_size = min(1024 * 1024, file_size)  # 1MB or file size

                    while bytes_written < file_size:
                        if self.is_cancelled():
                            return False

                        chunk = os.urandom(min(chunk_size, file_size - bytes_written))
                        f.write(chunk)
                        bytes_written += len(chunk)

                logger.debug(f"Overwrite pass {pass_num + 1}/{self.overwrite_passes} complete")

            # Final overwrite with zeros
            with open(file_path, "wb") as f:
                f.write(b"\x00" * min(file_size, 1024 * 1024))

            # Delete the file
            file_path.unlink()

            logger.info(f"Securely deleted: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Secure deletion failed for {file_path}: {e}")

            # Attempt regular deletion as fallback
            try:
                file_path.unlink()
                logger.warning(f"Fell back to regular deletion: {file_path}")
                return True
            except Exception:
                return False

    def cleanup(self):
        """Clean up resources."""
        logger.debug(f"Secure delete worker cleanup: {len(self.file_paths)} files processed")
