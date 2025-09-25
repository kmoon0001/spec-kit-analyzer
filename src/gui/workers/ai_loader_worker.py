import os
import yaml
import logging
from PyQt6.QtCore import QObject, Signal

# Import the services this worker needs to run
from src.core.analysis_service import AnalysisService
from src.core.database_maintenance_service import DatabaseMaintenanceService

logger = logging.getLogger(__name__)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

class AILoaderWorker(QObject):
    """
    A worker to handle all application startup tasks in the background,
    including database maintenance and loading AI models.
    """
    finished = Signal(object, bool, str)  # analyzer, is_healthy, status_message

    def run(self):
        """
        Runs startup tasks: database purge, then AI model loading.
        """
        try:
            # 1. Load configuration
            config_path = os.path.join(ROOT_DIR, "config.yaml")
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            # 2. Run Database Maintenance (New Step)
            maintenance_service = DatabaseMaintenanceService()
            retention_days = config.get('purge_retention_days', 0)
            maintenance_service.purge_old_reports(retention_days)

            # 3. Initialize the main AnalysisService (which loads all AI models)
            # This is the heavy step.
            analyzer_service = AnalysisService()

            # 4. Emit the success signal with the initialized service
            self.finished.emit(analyzer_service, True, "AI Systems: Online")

        except Exception as e:
            # If any part of the startup fails, emit a failure signal
            logger.error(f"Error during AI loader worker execution: {e}", exc_info=True)
            self.finished.emit(None, False, f"AI Systems: Offline - {e}")
