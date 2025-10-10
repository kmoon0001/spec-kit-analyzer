"""Dependency injection and singleton service management for FastAPI application."""

import logging
from typing import Any

from fastapi import Depends, HTTPException, status

from src.auth import get_current_active_user
from src.core.hybrid_retriever import HybridRetriever
from src.database import models

from ..core.analysis_service import AnalysisService

# Configure logger
logger = logging.getLogger(__name__)

# This dictionary will hold our singleton instances
app_state: dict[str, Any] = {}

def require_admin(current_user: models.User = Depends(get_current_active_user)):
    """Dependency that requires the current user to be an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have administrative privileges")
    return current_user

def get_analysis_service() -> Any:
    """Dependency to get the singleton AnalysisService instance.
    The instance will be either a real or a mock service.
    """
    return app_state.get("analysis_service")

async def get_retriever() -> Any:
    """Get retriever instance."""
    if "retriever" not in app_state:
        logger.info("Retriever instance not found, creating a new one.")

        retriever_instance = HybridRetriever()
        await retriever_instance.initialize()
        app_state["retriever"] = retriever_instance
        logger.info("New retriever instance created and initialized.")
    return app_state["retriever"]

async def startup_event():
    """Application startup event handler. Initializes singleton services."""
    logger.info("Application starting up...")

    # Force the use of the real AnalysisService for production readiness.
    logger.info("Initializing real AnalysisService.")

    # 1. Initialize the retriever, which is a dependency for other services.
    retriever = await get_retriever()

    # 2. Initialize the analysis service, injecting the retriever.
    analysis_service = AnalysisService(retriever=retriever)
    app_state["analysis_service"] = analysis_service

    logger.info("Application startup complete. Services are initialized.")

async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Application shutting down...")
