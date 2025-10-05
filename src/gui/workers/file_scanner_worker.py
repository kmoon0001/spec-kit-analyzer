"""
Worker for scanning directories for files with specific extensions.
"""

from PySide6.QtCore import QObject, Signal, Slot
from pathlib import Path
from typing import List

class FileScannerWorker(QObject):
    """Scans a directory for files with given extensions."""
    
    file_found = Signal(str)  # Emits the path of each file found
    finished = Signal(list)    # Emits the list of all file paths when done
    error = Signal(str)

    def __init__(self, folder_path: str, extensions: List[str]):
        super().__init__()
        self.folder_path = Path(folder_path)
        self.extensions = [ext.lower() for ext in extensions]
        self._is_running = True

    @Slot()
    def run(self):
        """Scan the directory for supported files."""
        try:
            if not self.folder_path.is_dir():
                self.error.emit(f"Invalid folder path: {self.folder_path}")
                return

            found_files = []
            for file_path in self.folder_path.rglob("*"):
                if not self._is_running:
                    break
                if file_path.is_file() and file_path.suffix.lower() in self.extensions:
                    found_files.append(str(file_path))
                    self.file_found.emit(file_path.name)
            
            if self._is_running:
                self.finished.emit(found_files)

        except Exception as e:
            self.error.emit(f"An error occurred while scanning the folder: {e}")

    def stop(self):
        self._is_running = False
