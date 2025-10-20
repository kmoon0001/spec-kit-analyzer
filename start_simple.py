#!/usr/bin/env python3
"""
Simple Startup Script for Therapy Compliance Analyzer
Bypasses Windows socket permission issues
"""

import asyncio
import logging
import sys
import subprocess
import time
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
        logger.info("")
        logger.info("=== MANUAL STARTUP INSTRUCTIONS ===")
        logger.info("Due to Windows socket permission issues, please start services manually:")
        logger.info("")
        logger.info("1. API Server (in a new terminal):")
        logger.info("   venv_fresh\\Scripts\\activate")
        logger.info("   python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8001")
        logger.info("")
        logger.info("2. Frontend Server (in another terminal):")
        logger.info("   cd frontend/electron-react-app")
        logger.info("   npm run start:renderer")
        logger.info("")
        logger.info("3. Electron Desktop App (in another terminal):")
        logger.info("   cd frontend/electron-react-app")
        logger.info("   npm run electron:dev")
        logger.info("")
        logger.info("=== ACCESS POINTS ===")
        logger.info("API Server: http://localhost:8001")
        logger.info("Frontend: http://localhost:3001")
        logger.info("API Docs: http://localhost:8001/docs")
        logger.info("")
        logger.info("Core enhanced services are running in the background.")
        logger.info("Press Ctrl+C to stop core services.")
        
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
