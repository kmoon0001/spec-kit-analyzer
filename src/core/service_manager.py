"""
Service Manager for Port Conflict Resolution and Process Management
Handles proper startup/shutdown of all services with conflict detection
"""

import asyncio
import logging
import socket
import subprocess
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from pathlib import Path

import psutil
import structlog

logger = structlog.get_logger(__name__)


class ServiceStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"


@dataclass
class ServiceConfig:
    name: str
    port: int
    command: List[str]
    working_dir: Optional[str] = None
    env_vars: Optional[Dict[str, str]] = None
    health_check_url: Optional[str] = None
    startup_timeout: int = 30
    shutdown_timeout: int = 10


class ServiceManager:
    """Manages multiple services with port conflict detection and resolution."""

    def __init__(self):
        self.services: Dict[str, ServiceConfig] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.status: Dict[str, ServiceStatus] = {}
        self._lock = asyncio.Lock()

    def register_service(self, config: ServiceConfig) -> None:
        """Register a service configuration."""
        self.services[config.name] = config
        self.status[config.name] = ServiceStatus.STOPPED
        logger.info("Registered service", service=config.name, port=config.port)

    async def start_service(self, service_name: str) -> bool:
        """Start a specific service with conflict resolution."""
        if service_name not in self.services:
            logger.error("Service not registered", service=service_name)
            return False

        config = self.services[service_name]

        async with self._lock:
            # Check if port is available
            if not await self._is_port_available(config.port):
                logger.warning("Port conflict detected", port=config.port, service=service_name)
                # Try to find alternative port
                alternative_port = await self._find_available_port(config.port)
                if alternative_port:
                    logger.info("Using alternative port",
                              original_port=config.port,
                              alternative_port=alternative_port,
                              service=service_name)
                    config.port = alternative_port
                else:
                    logger.error("No available ports found", service=service_name)
                    return False

            # Start the service
            try:
                self.status[service_name] = ServiceStatus.STARTING

                # Prepare environment
                env = config.env_vars or {}
                env.update({
                    'PORT': str(config.port),
                    'API_PORT': str(config.port),
                })

                # Start process
                process = subprocess.Popen(
                    config.command,
                    cwd=config.working_dir,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                self.processes[service_name] = process

                # Wait for startup
                if await self._wait_for_service_ready(service_name, config):
                    self.status[service_name] = ServiceStatus.RUNNING
                    logger.info("Service started successfully",
                              service=service_name,
                              port=config.port,
                              pid=process.pid)
                    return True
                else:
                    self.status[service_name] = ServiceStatus.FAILED
                    logger.error("Service failed to start", service=service_name)
                    return False

            except Exception as e:
                self.status[service_name] = ServiceStatus.FAILED
                logger.error("Failed to start service", service=service_name, error=str(e))
                return False

    async def stop_service(self, service_name: str) -> bool:
        """Stop a specific service gracefully."""
        if service_name not in self.processes:
            logger.warning("Service not running", service=service_name)
            return True

        async with self._lock:
            try:
                self.status[service_name] = ServiceStatus.STOPPING
                process = self.processes[service_name]

                # Try graceful shutdown first
                process.terminate()

                # Wait for graceful shutdown
                try:
                    process.wait(timeout=self.services[service_name].shutdown_timeout)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    logger.warning("Force killing service", service=service_name)
                    process.kill()
                    process.wait()

                del self.processes[service_name]
                self.status[service_name] = ServiceStatus.STOPPED
                logger.info("Service stopped", service=service_name)
                return True

            except Exception as e:
                logger.error("Failed to stop service", service=service_name, error=str(e))
                return False

    async def start_all_services(self) -> Dict[str, bool]:
        """Start all registered services."""
        results = {}
        for service_name in self.services:
            results[service_name] = await self.start_service(service_name)
        return results

    async def stop_all_services(self) -> Dict[str, bool]:
        """Stop all running services."""
        results = {}
        for service_name in list(self.processes.keys()):
            results[service_name] = await self.stop_service(service_name)
        return results

    async def restart_service(self, service_name: str) -> bool:
        """Restart a specific service."""
        await self.stop_service(service_name)
        await asyncio.sleep(1)  # Brief pause between stop and start
        return await self.start_service(service_name)

    def get_service_status(self, service_name: str) -> Optional[ServiceStatus]:
        """Get the current status of a service."""
        return self.status.get(service_name)

    def get_all_status(self) -> Dict[str, ServiceStatus]:
        """Get status of all services."""
        return self.status.copy()

    async def _is_port_available(self, port: int) -> bool:
        """Check if a port is available."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result != 0
        except Exception:
            return False

    async def _find_available_port(self, start_port: int, max_attempts: int = 10) -> Optional[int]:
        """Find an available port starting from start_port."""
        for port in range(start_port, start_port + max_attempts):
            if await self._is_port_available(port):
                return port
        return None

    async def _wait_for_service_ready(self, service_name: str, config: ServiceConfig) -> bool:
        """Wait for a service to be ready."""
        if config.health_check_url:
            # Use health check URL
            return await self._check_health_endpoint(config.health_check_url, config.startup_timeout)
        else:
            # Just wait for port to be available
            return await self._wait_for_port(config.port, config.startup_timeout)

    async def _check_health_endpoint(self, url: str, timeout: int) -> bool:
        """Check if a health endpoint is responding."""
        import aiohttp

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=2) as response:
                        if response.status == 200:
                            return True
            except Exception:
                pass
            await asyncio.sleep(1)
        return False

    async def _wait_for_port(self, port: int, timeout: int) -> bool:
        """Wait for a port to become available."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not await self._is_port_available(port):
                return True
            await asyncio.sleep(0.5)
        return False

    def cleanup_zombie_processes(self) -> int:
        """Clean up any zombie processes."""
        cleaned = 0
        for service_name, process in list(self.processes.items()):
            if process.poll() is not None:  # Process has terminated
                logger.info("Cleaning up zombie process", service=service_name, pid=process.pid)
                del self.processes[service_name]
                self.status[service_name] = ServiceStatus.STOPPED
                cleaned += 1
        return cleaned

    @asynccontextmanager
    async def managed_services(self):
        """Context manager for automatic service lifecycle management."""
        try:
            await self.start_all_services()
            yield self
        finally:
            await self.stop_all_services()


# Global service manager instance
service_manager = ServiceManager()


def create_default_services() -> ServiceManager:
    """Create default service configurations."""
    manager = ServiceManager()

    # API Service
    manager.register_service(ServiceConfig(
        name="api",
        port=8001,
        command=["python", "-m", "uvicorn", "src.api.main:app", "--host", "127.0.0.1", "--port", "8001"],
        working_dir=str(Path(__file__).parent.parent.parent),
        health_check_url="http://127.0.0.1:8001/health",
        startup_timeout=30
    ))

    # Frontend Service
    manager.register_service(ServiceConfig(
        name="frontend",
        port=3001,
        command=["cmd", "/c", "npm", "run", "start:renderer"],
        working_dir=str(Path(__file__).parent.parent.parent / "frontend" / "electron-react-app"),
        env_vars={"PORT": "3001", "BROWSER": "none"},
        startup_timeout=60
    ))

    return manager
