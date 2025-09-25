import logging
from ..database import SessionLocal
from .. import crud

logger = logging.getLogger(__name__)

class DatabaseMaintenanceService:
    """
    A service to handle periodic database maintenance tasks, like purging old data.
    """
    def purge_old_reports(self, retention_days: int):
        """
        Connects to the database and purges reports older than the retention period.

        Args:
            retention_days: The maximum age of reports to keep, in days.
        """
        if retention_days <= 0:
            logger.info("Database purging is disabled (retention_days <= 0).")
            return

        db = None
        try:
            db = SessionLocal()
            logger.info(f"Running database maintenance: Purging reports older than {retention_days} days...")
            num_deleted = crud.delete_reports_older_than(db, days=retention_days)
            if num_deleted > 0:
                logger.info(f"Successfully purged {num_deleted} old reports from the database.")
            else:
                logger.info("No old reports found to purge.")
        except Exception as e:
            logger.error(f"An error occurred during database maintenance: {e}", exc_info=True)
        finally:
            if db:
                db.close()
