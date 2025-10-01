import logging
import asyncio
from src.config import get_settings
from ..database import AsyncSessionLocal, crud

logger = logging.getLogger(__name__)


class DatabaseMaintenanceService:
    """
    A service to handle database maintenance tasks, such as purging old reports.
    """

    def __init__(self):
        self.settings = get_settings()

    async def _purge_old_reports_async(self):
        """
        Asynchronously connects to the database and purges old reports based on
        the retention policy defined in the application settings.
        """
        retention_days = self.settings.maintenance.purge_retention_days

        if retention_days <= 0:
            logger.info("Database purging is disabled (retention_days <= 0).")
            return

        logger.info(
            "Starting database maintenance job: Purging reports older than %d days.",
            retention_days,
        )

        async with AsyncSessionLocal() as db:
            try:
                num_deleted = await crud.delete_reports_older_than(
                    db, days=retention_days
                )
                if num_deleted > 0:
                    logger.info(
                        "Successfully purged %d old reports from the database.",
                        num_deleted,
                    )
                else:
                    logger.info("No old reports found to purge.")
            except Exception as e:
                logger.error(
                    "An error occurred during the database purge operation: %s",
                    e,
                    exc_info=True,
                )

    def purge_old_reports(self, retention_days: int = 0):
        """
        Synchronous entry point for the database maintenance task.

        This function is designed to be called by a synchronous scheduler (like APScheduler).
        It runs the core asynchronous purge logic in a new asyncio event loop.
        """
        logger.info("Scheduler triggered: Kicking off database maintenance task.")
        try:
            asyncio.run(self._purge_old_reports_async())
            logger.info("Database maintenance task finished.")
        except Exception as e:
            logger.error(
                "An unexpected error occurred while running the database maintenance task: %s",
                e,
                exc_info=True,
            )
