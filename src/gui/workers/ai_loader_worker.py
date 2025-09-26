import logging
from PyQt6.QtCore import QObject, pyqtSignal as Signal
import asyncio

# Import the services this worker needs to run
from src.config import get_config
from src.core.analysis_service import AnalysisService
from src.core.database_maintenance_service import DatabaseMaintenanceService
from src.core.retriever import HybridRetriever

logger = logging.getLogger(__name__)


class AILoaderWorker(QObject):
    """
    A worker to handle all application startup tasks in the background,
    including database maintenance and loading AI models.
    """

    finished = Signal(object, bool, str)  # analyzer, is_healthy, status_message

    def run(self):
        """Runs startup tasks: database purge, then AI model loading."""
        try:
            # 1. Load configuration using the centralized function
            config = get_config()

            # 2. Run Database Maintenance
            maintenance_service = DatabaseMaintenanceService()
            retention_days = config.maintenance.purge_retention_days
            maintenance_service.purge_old_reports(retention_days)

            # 3. Initialize HybridRetriever and AnalysisService
            retriever = HybridRetriever(settings=config.retrieval_settings)
            asyncio.run(retriever.initialize())
            analyzer_service = AnalysisService(retriever=retriever)
            compliance_service = ComplianceService(analysis_service=analyzer_service)

            # 4. Emit the success signal with the initialized service
            self.finished.emit(compliance_service, True, "AI Systems: Online")

        except Exception as e:
            # If any part of the startup fails, emit a failure signal
            logger.error(f"Error during AI loader worker execution: {e}", exc_info=True)
            self.finished.emit(None, False, f"AI Systems: Offline - {e}")
