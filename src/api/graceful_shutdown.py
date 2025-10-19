"""Graceful shutdown handling for the application.

Provides proper cleanup of resources during application shutdown including:
- Database connection cleanup
- Background task termination
- File handle closure
- Cache cleanup
- Logging finalization
"""

import asyncio
import logging
import signal
import sys
from typing import Any, Dict, List
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class GracefulShutdownManager:
    """Manages graceful shutdown of the application."""

    def __init__(self):
        self.shutdown_handlers: List[callable] = []
        self.background_tasks: List[asyncio.Task] = []
        self.is_shutting_down = False
        self.shutdown_timeout = 30  # seconds

    def register_shutdown_handler(self, handler: callable):
        """Register a function to be called during shutdown."""
        self.shutdown_handlers.append(handler)
        logger.debug(f"Registered shutdown handler: {handler.__name__}")

    def register_background_task(self, task: asyncio.Task):
        """Register a background task for cleanup during shutdown."""
        self.background_tasks.append(task)
        logger.debug(f"Registered background task: {task.get_name()}")

    async def shutdown(self):
        """Perform graceful shutdown."""
        if self.is_shutting_down:
            logger.warning("Shutdown already in progress")
            return

        self.is_shutting_down = True
        logger.info("Starting graceful shutdown...")

        try:
            # 1. Cancel all background tasks
            await self._cancel_background_tasks()

            # 2. Run shutdown handlers
            await self._run_shutdown_handlers()

            # 3. Final cleanup
            await self._final_cleanup()

            logger.info("Graceful shutdown completed successfully")

        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")
            raise

    async def _cancel_background_tasks(self):
        """Cancel all registered background tasks."""
        if not self.background_tasks:
            return

        logger.info(f"Cancelling {len(self.background_tasks)} background tasks...")

        # Cancel all tasks
        for task in self.background_tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*self.background_tasks, return_exceptions=True),
                timeout=self.shutdown_timeout
            )
        except asyncio.TimeoutError:
            logger.warning("Some background tasks did not complete within timeout")

        # Log any exceptions from cancelled tasks
        for task in self.background_tasks:
            if task.done() and task.exception():
                logger.error(f"Background task {task.get_name()} failed: {task.exception()}")

    async def _run_shutdown_handlers(self):
        """Run all registered shutdown handlers."""
        if not self.shutdown_handlers:
            return

        logger.info(f"Running {len(self.shutdown_handlers)} shutdown handlers...")

        for handler in self.shutdown_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
                logger.debug(f"Shutdown handler {handler.__name__} completed successfully")
            except Exception as e:
                logger.error(f"Shutdown handler {handler.__name__} failed: {e}")

    async def _final_cleanup(self):
        """Perform final cleanup operations."""
        logger.info("Performing final cleanup...")

        # Close any remaining file handles
        try:
            import gc
            gc.collect()
            logger.debug("Garbage collection completed")
        except Exception as e:
            logger.error(f"Garbage collection failed: {e}")

        # Final logging
        logger.info("Application shutdown complete")

# Global shutdown manager
shutdown_manager = GracefulShutdownManager()

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(shutdown_manager.shutdown())

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # On Windows, also handle SIGBREAK
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, signal_handler)

@asynccontextmanager
async def lifespan_with_graceful_shutdown(app):
    """Lifespan context manager with graceful shutdown support."""
    # Setup signal handlers
    setup_signal_handlers()

    # Register application-specific shutdown handlers
    await register_app_shutdown_handlers()

    logger.info("Application startup complete")

    try:
        yield
    finally:
        # Perform graceful shutdown
        await shutdown_manager.shutdown()

async def register_app_shutdown_handlers():
    """Register application-specific shutdown handlers."""

    # Database cleanup handler
    async def cleanup_database():
        try:
            from src.database.database import AsyncSessionLocal
            # Close all database connections
            await AsyncSessionLocal.close_all()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")

    # Cache cleanup handler
    async def cleanup_cache():
        try:
            from src.core.cache_service import cache_service
            if hasattr(cache_service, 'clear'):
                cache_service.clear()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")

    # File cleanup handler
    async def cleanup_files():
        try:
            from src.core.file_cleanup_service import stop_cleanup_service
            stop_cleanup_service()
            logger.info("File cleanup service stopped")
        except Exception as e:
            logger.error(f"File cleanup failed: {e}")

    # Register handlers
    shutdown_manager.register_shutdown_handler(cleanup_database)
    shutdown_manager.register_shutdown_handler(cleanup_cache)
    shutdown_manager.register_shutdown_handler(cleanup_files)

# Utility functions for other modules
def register_shutdown_handler(handler: callable):
    """Register a shutdown handler from any module."""
    shutdown_manager.register_shutdown_handler(handler)

def register_background_task(task: asyncio.Task):
    """Register a background task for cleanup."""
    shutdown_manager.register_background_task(task)
