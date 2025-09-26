import logging
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.analysis_service import AnalysisService
from ..core.retriever import HybridRetriever # Assuming this is the new location
from ..database import get_async_db, AsyncSessionLocal

# Configure logger
logger = logging.getLogger(__name__)

# This dictionary will hold our singleton instances
app_state = {}

def get_analysis_service() -> AnalysisService:
    """Dependency to get the singleton AnalysisService instance."""
    return app_state.get('analysis_service')

async def get_retriever() -> HybridRetriever:
    """
    Dependency to get the singleton HybridRetriever instance.
    Initializes the retriever on the first call.
    """
    # Use a lock or other mechanism here in a multi-worker setup
    if "retriever" not in app_state:
        logger.info("Retriever instance not found, creating a new one.")
        # The retriever will create its own session for the one-time loading process.
        # This is safe because initialization happens only once.
        retriever_instance = HybridRetriever()
        await retriever_instance.initialize()
        app_state["retriever"] = retriever_instance
        logger.info("New retriever instance created and initialized.")
    return app_state["retriever"]

async def startup_event():
    """
    Application startup event handler. Initializes singleton services.
    """
    logger.info("Application starting up...")
    # 1. Initialize the retriever, which is a dependency for other services.
    retriever = await get_retriever()

    # 2. Initialize the analysis service, injecting the retriever.
    analysis_service = AnalysisService(retriever=retriever)
    app_state['analysis_service'] = analysis_service

    logger.info("Application startup complete. Services are initialized.")

async def shutdown_event():
    """
    Application shutdown event handler.
    """
    logger.info("Application shutting down...")
    # Clean up resources if needed
    pass