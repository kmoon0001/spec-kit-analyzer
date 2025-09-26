import logging
import asyncio
from ..database import AsyncSessionLocal
from .. import crud

logger = logging.getLogger(__name__)

class DatabaseMaintenanceService:
    """
    A service to handle periodic database maintenance tasks, like purging old data.
    This service runs synchronously within a background thread managed by APScheduler.
    """

    @staticmethod
    def _purge_old_reports_sync(retention_days: int):
        """
        Synchronous wrapper to run the async purge logic.
        """
        async def purge():
            if retention_days <= 0:
                logger.info("Database purging is disabled (retention_days <= 0).")
                return

            async with AsyncSessionLocal() as db:
                try:
                    logger.info(f"Running database maintenance: Purging reports older than {retention_days} days...")
                    # Note: crud.delete_reports_older_than needs to be async
                    num_deleted = await crud.delete_reports_older_than(db, days=retention_days)
                    if num_deleted > 0:
                        logger.info(f"Successfully purged {num_deleted} old reports from the database.")
                    else:
                        logger.info("No old reports found to purge.")
                except Exception as e:
                    logger.error(f"An error occurred during database maintenance: {e}", exc_info=True)

        # Run the async function in a new event loop
        asyncio.run(purge())

    def purge_old_reports(self, retention_days: int):
        """
        Public method to trigger the synchronous purge.
        """
        self._purge_old_reports_sync(retention_days)
