import shutil
import time
from pathlib import Path

import structlog

from src.config import get_settings

logger = structlog.get_logger(__name__)


class DataPurgingService:
    """A service for purging old and temporary data to conserve disk space and enhance security."""

    def __init__(self):
        self.settings = get_settings()
        self.cache_dir = Path(self.settings.paths.cache_dir)
        self.temp_upload_dir = Path(self.settings.paths.temp_upload_dir)
        self.retention_days = self.settings.maintenance.purge_retention_days

    def purge_all(self):
        """Run all data purging operations."""
        logger.info("Starting all data purging operations.")
        self.purge_disk_cache()
        self.purge_temp_uploads()
        logger.info("All data purging operations complete.")

    def purge_disk_cache(self):
        """Purges expired files from the disk cache based on the retention period."""
        if not self.cache_dir.exists():
            return

        logger.info("Purging disk cache with a retention period of %s days.", self.retention_days)
        cutoff_time = time.time() - (self.retention_days * 86400)
        purged_count = 0

        for file_path in self.cache_dir.glob("**/*"):
            if file_path.is_file():
                try:
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        purged_count += 1
                        logger.debug("Purged cached file: %s", file_path.name)
                except (OSError, FileNotFoundError):
                    logger.warning("Could not purge cache file %s: {e}", file_path)

        logger.info("Purged %s expired files from the disk cache.", purged_count)

    def purge_temp_uploads(self):
        """Clears all files from the temporary upload directory, regardless of age."""
        if not self.temp_upload_dir.exists():
            return

        logger.info("Clearing all temporary upload files.")
        purged_count = 0
        for item in self.temp_upload_dir.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                    purged_count += 1
                elif item.is_dir():
                    shutil.rmtree(item)
                    purged_count += 1
            except (OSError, FileNotFoundError):
                logger.warning("Could not remove temporary item %s: {e}", item)

        logger.info("Removed %s items from the temporary upload directory.", purged_count)
