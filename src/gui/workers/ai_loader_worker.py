import logging
from PyQt6.QtCore import QObject, pyqtSignal as Signal
import asyncio

# Import the services this worker needs to run
from src.config import get_settings
from src.core.analysis_service import AnalysisService
from src.core.database_maintenance_service import DatabaseMaintenanceService
from src.core.retriever import HybridRetriever
from src.core.compliance_service import ComplianceService

logger = logging.getLogger(__name__)


class AILoaderWorker(QObject):
    """
    A worker to handle all application startup tasks in the background,
    including database maintenance and loading AI models.
    """

    finished = Signal(object, bool, str, dict)  # analyzer, is_healthy, status_message

    def run(self):
        """Runs startup tasks: database purge, then AI model loading."""
        try:
            # 1. Load configuration using the centralized function
            config = get_settings()

            # 2. Run Database Maintenance
            maintenance_service = DatabaseMaintenanceService()
            retention_days = config.maintenance.purge_retention_days
            maintenance_service.purge_old_reports(retention_days)

            # 3. Initialize HybridRetriever and AnalysisService
            retriever = HybridRetriever()
            asyncio.run(retriever.initialize())
            analyzer_service = AnalysisService(retriever=retriever)
            compliance_service = ComplianceService(analysis_service=analyzer_service)

            chat_llm = getattr(analyzer_service, "chat_llm_service", None)
            chat_ready = bool(getattr(chat_llm, "is_ready", lambda: False)()) if chat_llm else False

            health_map = {
                "Generator": bool(getattr(analyzer_service.llm_service, "is_ready", lambda: False)()),
                "Retriever": True,
                "Fact Checker": bool(getattr(analyzer_service.fact_checker, "pipeline", None)),
                "NER": bool(getattr(analyzer_service.ner_pipeline, "pipelines", [])),
                "Checklist": True,
                "Chat": chat_ready,
            }

            # 4. Emit the success signal with the initialized service
            self.finished.emit(compliance_service, True, "AI Systems: Online", health_map)

        except Exception as e:
            # If any part of the startup fails, emit a failure signal
            logger.error(f"Error during AI loader worker execution: {e}", exc_info=True)
            self.finished.emit(None, False, f"AI Systems: Offline - {e}", {})
