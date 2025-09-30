import logging
from typing import Any, Dict

from ..config import get_settings
from ..core.mock_analysis_service import MockAnalysisService

# Configure logger
logger = logging.getLogger(__name__)

# This dictionary will hold our singleton instances
app_state: Dict[str, Any] = {}


def get_analysis_service() -> Any:
    """
    Dependency to get the singleton AnalysisService instance.
    The instance will be either a real or a mock service.
    """
    return app_state.get("analysis_service")


async def get_retriever() -> Any:
    """
    Dependency to get the singleton HybridRetriever instance.
    Initializes the retriever on the first call.
    """
    if "retriever" not in app_state:
        logger.info("Retriever instance not found, creating a new one.")
        # Conditional import to avoid ModuleNotFoundError in mock mode
        from ..core.hybrid_retriever import HybridRetriever

        retriever_instance = HybridRetriever()
        await retriever_instance.initialize()
        app_state["retriever"] = retriever_instance
        logger.info("New retriever instance created and initialized.")
    return app_state["retriever"]


async def startup_event():
    """Application startup event handler. Initializes singleton services."""
    logger.info("Application starting up...")
    settings = get_settings()

    if settings.use_ai_mocks:
        logger.warning("AI mocks are enabled. Using MockAnalysisService.")
        app_state["analysis_service"] = MockAnalysisService()
    else:
        logger.info("AI mocks are disabled. Initializing real AnalysisService.")
        # Conditionally import the real service only when needed
        from ..core.analysis_service import AnalysisService

        # 1. Initialize the retriever, which is a dependency for other services.
        retriever = await get_retriever()

        # 2. Initialize the analysis service, injecting the retriever.
        analysis_service = AnalysisService(retriever=retriever)
        app_state["analysis_service"] = analysis_service

    logger.info("Application startup complete. Services are initialized.")


async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Application shutting down...")
