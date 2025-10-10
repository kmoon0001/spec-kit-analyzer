"""AI Loader Worker for background initialization of AI models and services."""

import asyncio
import logging

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal as Signal

from src.core.analysis_service import AnalysisService
from src.core.compliance_service import ComplianceService
from src.core.database_maintenance_service import DatabaseMaintenanceService
from src.core.hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)


class AILoaderWorker(QObject):
    """Background worker for initializing AI models and services during application startup.

    Handles database maintenance, AI model loading, and service initialization
    in a separate thread to prevent UI blocking.
    """

    # Signals
    progress_updated = Signal(int)  # Progress percentage (0-100)
    status_updated = Signal(str)  # Status message for UI
    finished = Signal(object, bool, str, dict)  # service, success, message, health_map

    def __init__(self) -> None:
        """Initialize the AI loader worker."""
        super().__init__()
        self._analysis_service: AnalysisService | None = None
        self._compliance_service: ComplianceService | None = None

    def run(self) -> None:
        """Execute the AI loading workflow.

        Steps:
        1. Database maintenance and cleanup
        2. Initialize retrieval system
        3. Load AI models and services
        4. Perform health checks
        5. Emit completion signal
        """
        try:
            self._run_database_maintenance()
            self._initialize_retrieval_system()
            self._load_ai_services()
            health_map = self._perform_health_checks()

            self.status_updated.emit("AI Systems: Online")
            self.progress_updated.emit(100)
            self.finished.emit(
                self._compliance_service, True, "AI Systems: Online", health_map,
            )

        except (ImportError, AttributeError, RuntimeError) as e:
            logger.error("AI loader worker failed: %s", str(e), exc_info=True)
            self.status_updated.emit(f"AI Systems: Offline - {e}")
            self.finished.emit(None, False, f"AI Systems: Offline - {e}", {})

    def _run_database_maintenance(self) -> None:
        """Run database cleanup and maintenance tasks."""
        self.status_updated.emit("🔧 Running database maintenance...")
        self.progress_updated.emit(10)

        logger.info("Starting database maintenance")
        from src.config import get_settings
        settings = get_settings()
        maintenance_service = DatabaseMaintenanceService(db_path=settings.database.url)
        maintenance_service.purge_old_reports()
        logger.info("Database maintenance completed")

    def _initialize_retrieval_system(self) -> None:
        """Initialize the hybrid retrieval system."""
        self.status_updated.emit("🔍 Initializing retrieval system...")
        self.progress_updated.emit(30)

        logger.info("Initializing hybrid retriever")
        retriever = HybridRetriever()

        # Handle async initialization properly
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(retriever.initialize())
        finally:
            loop.close()

        self._retriever = retriever
        logger.info("Hybrid retriever initialized successfully")

    def _load_ai_services(self) -> None:
        """Load and initialize AI services."""
        self.status_updated.emit("🤖 Loading AI models...")
        self.progress_updated.emit(60)

        logger.info("Initializing analysis service")
        self._analysis_service = AnalysisService(retriever=self._retriever)

        logger.info("Initializing compliance service")
        self._compliance_service = ComplianceService(
            analysis_service=self._analysis_service,
        )

        self.progress_updated.emit(80)
        logger.info("AI services loaded successfully")

    def _perform_health_checks(self) -> dict[str, bool]:
        """Perform health checks on all AI components.

        Returns:
            Dictionary mapping component names to their health status

        """
        self.status_updated.emit("⚡ Performing health checks...")
        self.progress_updated.emit(90)

        health_map = {}

        if self._analysis_service:
            # Check LLM service
            llm_service = getattr(self._analysis_service, "llm_service", None)
            health_map["Generator"] = bool(
                llm_service and getattr(llm_service, "is_ready", lambda: False)(),
            )

            # Check fact checker (it's inside compliance_analyzer)
            compliance_analyzer = getattr(
                self._analysis_service, "compliance_analyzer", None,
            )
            fact_checker = (
                getattr(compliance_analyzer, "fact_checker_service", None)
                if compliance_analyzer
                else None
            )
            health_map["Fact Checker"] = bool(
                fact_checker and getattr(fact_checker, "pipeline", None),
            )

            # Check NER analyzer
            ner_analyzer = getattr(self._analysis_service, "ner_analyzer", None)
            health_map["NER"] = bool(
                ner_analyzer and hasattr(ner_analyzer, "ner_pipeline"),
            )

            # Check chat service
            chat_service = getattr(self._analysis_service, "chat_llm_service", None)
            health_map["Chat"] = bool(
                chat_service and getattr(chat_service, "is_ready", lambda: False)(),
            )
        else:
            # Default to False if analysis service not available
            health_map.update(
                {
                    "Generator": False,
                    "Fact Checker": False,
                    "NER": False,
                    "Chat": False,
                },
            )

        # These components are always available
        health_map.update(
            {
                "Retriever": True,
                "Checklist": True,
            },
        )

        logger.info("Health check completed: %s", health_map)
        return health_map
