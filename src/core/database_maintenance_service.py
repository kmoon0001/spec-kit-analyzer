import logging
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import crud
from ..config import get_settings
from ..database.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class DatabaseMaintenanceService:
    """
    A service to handle background database maintenance tasks, such as purging old records.
    """

    def purge_old_reports(self, retention_days: int):
        """
        Synchronous entry point for purging old reports.
        This can be called from a synchronous context like a scheduler.
        """
        logger.info("Scheduler triggered: Kicking off database maintenance task for reports older than %d days.", retention_days)
        try:
            # Use asyncio.run() to execute the async method
            asyncio.run(self._purge_old_reports_async(retention_days))
            logger.info("Database maintenance task finished.")
        except Exception as e:
            logger.error(
                "An unexpected error occurred while running the database maintenance task: %s",
                e,
                exc_info=True,
            )

    async def _purge_old_reports_async(self, retention_days: int):
        """
        Asynchronously connects to the database and purges old reports.
        """
        if retention_days <= 0:
            logger.info("Database purging is disabled (retention_days <= 0).")
            return

        logger.info(
            "Starting database maintenance job: Purging reports older than %d days.",
            retention_days,
        )

        async with AsyncSessionLocal() as db:
            try:
                num_deleted = await crud.delete_reports_older_than(db, days=retention_days)
                if num_deleted > 0:
                    logger.info(
                        "Successfully purged %d old reports from the database.", num_deleted
                    )
                else:
                    logger.info("No old reports found to purge.")
            except Exception as e:
                logger.error(
                    "An error occurred during the database purge operation: %s",
                    e,
                    exc_info=True,
                )