
import time
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot


class FolderWatcherWorker(QObject):
    """Periodically scans a folder for new documents and emits a signal."""

    new_file_found = Signal(str)  # Emits the path of the new file
    error = Signal(str)
    finished = Signal()

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".json"}

    def __init__(self, folder_path: str, interval: int = 5):
        super().__init__()
        self.folder_path = Path(folder_path)
        self.interval = interval
        self._is_running = True
        self.seen_files: set[Path] = set()

    @Slot()
    def run(self):
        """Scan the directory periodically for new, supported files."""
        if not self.folder_path.is_dir():
            self.error.emit(f"Invalid folder path: {self.folder_path}")
            return

        # Initial scan to establish a baseline
        try:
            self.seen_files = {p for p in self.folder_path.rglob("*") if p.is_file()}
        except Exception as e:
            self.error.emit(f"Failed to perform initial scan: {e}")
            return

        while self._is_running:
            try:
                current_files = {p for p in self.folder_path.rglob("*") if p.is_file()}
                new_files = current_files - self.seen_files

                for file_path in new_files:
                    if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                        self.new_file_found.emit(str(file_path))

                self.seen_files = current_files

            except Exception as e:
                self.error.emit(f"Error during folder scan: {e}")
                # Continue running even if one scan fails

            # Wait for the next interval
            for _ in range(self.interval):
                if not self._is_running:
                    break
                time.sleep(1)

        self.finished.emit()

    def stop(self):
        """Stops the watcher loop."""
        self._is_running = False
