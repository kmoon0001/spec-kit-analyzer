#!/usr/bin/env python3
"""
Simplified Enhanced Startup Script for Therapy Compliance Analyzer
Focuses on the core improvements without complex service management
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.persistent_task_registry import persistent_task_registry
from src.core.enhanced_worker_manager import enhanced_worker_manager
from src.database import init_db
from src.core.vector_store import get_vector_store
from src.logging_config import configure_logging
from src.config import get_settings

import structlog

logger = structlog.get_logger(__name__)


async def main():
    """Main startup function."""
    try:
        # Configure logging
        settings = get_settings()
        configure_logging(settings.log_level)
        logger.info("Starting Therapy Compliance Analyzer with enhanced core services...")

        # Initialize database
        logger.info("Initializing database...")
        await init_db()

        # Initialize vector store
        logger.info("Initializing vector store...")
        vector_store = get_vector_store()

        # Initialize persistent task registry
        logger.info("Initializing persistent task registry...")
        await persistent_task_registry.cleanup_old_tasks(days_old=7)

        # Initialize enhanced worker manager
        logger.info("Starting enhanced worker manager...")
        await enhanced_worker_manager.start()

        logger.info("Enhanced core services started successfully!")
        logger.info("You can now start the API server with: python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8001 --reload")
        logger.info("And the frontend with: cd frontend/electron-react-app && npm run dev")

        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")

        finally:
            # Graceful shutdown
            logger.info("Shutting down enhanced services...")
            await enhanced_worker_manager.stop()
            await persistent_task_registry.close()
            logger.info("Shutdown complete")

        return True

    except Exception as e:
        logger.error("Startup failed", error=str(e))
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
