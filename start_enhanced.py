#!/usr/bin/env python3
"""
Enhanced Startup Script for Therapy Compliance Analyzer
Uses service manager for proper port conflict resolution and process management
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.service_manager import create_default_services
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
        logger.info("Starting Therapy Compliance Analyzer with enhanced services...")

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

        # Create and start services
        logger.info("Creating service manager...")
        service_manager = create_default_services()

        # Start services with conflict resolution
        logger.info("Starting services...")
        results = await service_manager.start_all_services()

        # Report results
        for service_name, success in results.items():
            if success:
                logger.info("Service started successfully", service=service_name)
            else:
                logger.error("Failed to start service", service=service_name)

        # Check if all services started
        if not all(results.values()):
            logger.error("Some services failed to start")
            return False

        logger.info("All services started successfully!")

        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)

                # Cleanup zombie processes
                cleaned = service_manager.cleanup_zombie_processes()
                if cleaned > 0:
                    logger.info("Cleaned up zombie processes", count=cleaned)

        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")

        finally:
            # Graceful shutdown
            logger.info("Shutting down services...")
            await service_manager.stop_all_services()
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
