#!/usr/bin/env python3
"""
Robust Startup Script for Therapy Compliance Analyzer
Handles port conflicts and process management automatically
"""

import asyncio
import logging
import sys
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.persistent_task_registry import persistent_task_registry
from src.core.enhanced_worker_manager import enhanced_worker_manager
from src.database import init_db
from src.core.vector_store import get_vector_store
from src.logging_config import configure_logging
from src.config import get_settings

import structlog
import psutil

logger = structlog.get_logger(__name__)


def find_available_port(start_port: int, max_attempts: int = 10) -> Optional[int]:
    """Find an available port starting from start_port."""
    import socket

    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                if result != 0:  # Port is available
                    return port
        except Exception:
            continue
    return None


def _terminate_process_tree(pid: int, timeout: float = 5.0) -> bool:
    """Terminate a process tree safely."""
    try:
        process = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return True

    children = process.children(recursive=True)
    for child in children:
        try:
            child.terminate()
        except psutil.NoSuchProcess:
            continue

    try:
        process.terminate()
    except psutil.NoSuchProcess:
        return True

    gone, alive = psutil.wait_procs([process, *children], timeout=timeout)
    for proc in alive:
        try:
            proc.kill()
        except psutil.NoSuchProcess:
            continue

    psutil.wait_procs(alive, timeout=timeout)
    return True


def kill_process_on_port(port: int) -> bool:
    """Kill any process using the specified port."""
    try:
        killed = False
        for conn in psutil.net_connections(kind="inet"):
            if not conn.laddr or conn.laddr.port != port:
                continue
            if conn.pid is None:
                continue
            if _terminate_process_tree(conn.pid):
                logger.info("Killed process on port", port=port, pid=conn.pid)
                killed = True
        if killed:
            time.sleep(1)
        return killed
    except (psutil.AccessDenied, psutil.ZombieProcess, NotImplementedError) as e:
        logger.warning("Failed to inspect processes on port", port=port, error=str(e))
        return False
    except Exception as e:
        logger.error("Failed to kill process on port", port=port, error=str(e))
        return False


async def start_api_server(port: int = 8001) -> Tuple[subprocess.Popen, int]:
    """Start the API server on the specified port."""
    # Kill any existing process on the port
    kill_process_on_port(port)

    # Find available port if needed
    available_port = find_available_port(port)
    if available_port != port:
        logger.info(f"Port {port} busy, using port {available_port}")
        port = available_port

    if port is None:
        raise RuntimeError(f"No available ports found starting from {port}")

    # Start the API server
    cmd = [
        sys.executable, "-m", "uvicorn",
        "src.api.main:app",
        "--host", "127.0.0.1",
        "--port", str(port),
    ]

    logger.info(f"Starting API server on port {port}")
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for server to start
    max_wait = 30
    for i in range(max_wait):
        try:
            import requests
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            if response.status_code == 200:
                logger.info(f"API server started successfully on port {port}")
                return process, port
        except Exception:
            pass

        if process.poll() is not None:
            # Process has terminated
            stdout, stderr = process.communicate()
            logger.error(f"API server failed to start: {stderr}")
            raise RuntimeError(f"API server failed: {stderr}")

        time.sleep(1)

    raise RuntimeError(f"API server failed to start within {max_wait} seconds")


def start_frontend_server(port: int = 3001, api_port: int = 8001) -> Tuple[subprocess.Popen, int]:
    """Start the frontend server on the specified port."""
    # Kill any existing process on the port
    kill_process_on_port(port)

    # Find available port if needed
    available_port = find_available_port(port)
    if available_port != port:
        logger.info(f"Port {port} busy, using port {available_port}")
        port = available_port

    if port is None:
        raise RuntimeError(f"No available ports found starting from {port}")

    # Change to frontend directory
    frontend_dir = Path(__file__).parent / "frontend" / "electron-react-app"

    # Start the frontend server
    if sys.platform.startswith("win"):
        cmd = ["cmd", "/c", "npm", "run", "start:renderer"]
    else:
        cmd = ["npm", "run", "start:renderer"]

    env = {
        "PORT": str(port),
        "BROWSER": "none",
        "REACT_APP_API_URL": f"http://127.0.0.1:{api_port}",
    }

    logger.info(f"Starting frontend server on port {port}")
    process = subprocess.Popen(
        cmd,
        cwd=frontend_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for server to start
    max_wait = 60
    for i in range(max_wait):
        try:
            import requests
            response = requests.get(f"http://localhost:{port}", timeout=2)
            if response.status_code == 200:
                logger.info(f"Frontend server started successfully on port {port}")
                return process, port
        except Exception:
            pass

        if process.poll() is not None:
            # Process has terminated
            stdout, stderr = process.communicate()
            logger.error(f"Frontend server failed to start: {stderr}")
            raise RuntimeError(f"Frontend server failed: {stderr}")

        time.sleep(1)

    raise RuntimeError(f"Frontend server failed to start within {max_wait} seconds")


async def main():
    """Main startup function."""
    try:
        # Configure logging
        settings = get_settings()
        configure_logging(settings.log_level)
        logger.info("Starting Therapy Compliance Analyzer with robust startup...")

        # Initialize database
        logger.info("Initializing database...")
        await init_db()

        # Initialize vector store
        logger.info("Initializing vector store...")
        vector_store = get_vector_store()

        # Initialize persistent task registry
        # NOTE: Blocking await is correct here - this is a standalone script
        # that needs services fully started before proceeding
        logger.info("Initializing persistent task registry...")
        await persistent_task_registry.cleanup_old_tasks(days_old=7)

        # Initialize enhanced worker manager
        # NOTE: Blocking await is correct here - not a web server startup
        logger.info("Starting enhanced worker manager...")
        await enhanced_worker_manager.start()

        logger.info("Enhanced core services started successfully!")

        # Start API server
        api_process, api_port = await start_api_server(8001)

        # Start frontend server
        frontend_process, frontend_port = start_frontend_server(3001, api_port=api_port)

        logger.info("All services started successfully!")
        logger.info("API Server: http://localhost:%s", api_port)
        logger.info("Frontend Server: http://localhost:%s", frontend_port)
        logger.info("API Documentation: http://localhost:%s/docs", api_port)

        # Keep running until interrupted
        try:
            while True:
                # Check if processes are still running
                if api_process.poll() is not None:
                    logger.error("API server stopped unexpectedly")
                    break

                if frontend_process.poll() is not None:
                    logger.error("Frontend server stopped unexpectedly")
                    break

                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")

        finally:
            # Graceful shutdown
            logger.info("Shutting down services...")

            if api_process.poll() is None:
                _terminate_process_tree(api_process.pid, timeout=10.0)

            if frontend_process.poll() is None:
                _terminate_process_tree(frontend_process.pid, timeout=10.0)

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
