"""
Service Manager for Port Conflict Resolution and Process Management
Handles proper startup/shutdown of all services with conflict detection
"""

import asyncio
import logging
import os
import socket
import subprocess
import sys
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

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

    def _prepare_command_with_port(self, command: List[str], port: int) -> List[str]:
        """Return a command list with the desired port substituted when possible."""
        patched: List[str] = []
        i = 0
        length = len(command)
        command_set = False
        while i < length:
            token = command[i]
            if token in {"--port", "-p"}:
                patched.append(token)
                if i + 1 < length:
                    patched.append(str(port))
                    i += 2
                else:
                    i += 1
                command_set = True
                continue
            if token.startswith("--port="):
                patched.append(f"--port={port}")
                command_set = True
            else:
                patched.append(token)
            i += 1
        if not command_set:
            return command.copy()
        return patched

    def _log_port_conflicts(self, port: int, service_name: str) -> None:
        """Log processes that currently occupy the requested port."""
        try:
            connections = psutil.net_connections(kind="inet")
        except (psutil.AccessDenied, psutil.ZombieProcess):
            logger.warning(
                "Insufficient permissions to inspect port %s usage. On Windows, run PowerShell as Administrator to gather details.",
                port,
            )
            return
        except NotImplementedError:
            logger.warning(
                "Platform does not support port inspection; skipping diagnostics for port %s",
                port,
            )
            return

        conflicts: list[str] = []
        for conn in connections:
            if not conn.laddr or conn.laddr.port != port:
                continue
            pid = conn.pid
            if pid is None:
                continue
            try:
                proc = psutil.Process(pid)
                conflicts.append(f"pid={pid} name={proc.name()} exe={proc.exe()}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                conflicts.append(f"pid={pid}")
        if conflicts:
            logger.warning(
                "Detected existing process(es) using port %s before starting service %s: %s",
                port,
                service_name,
                "; ".join(conflicts),
            )

    async def _cleanup_failed_process(
        self, service_name: str, process: subprocess.Popen
    ) -> tuple[str, str]:
        """Terminate a failed child process and return its captured output."""
        stdout_text = ""
        stderr_text = ""
        if process.poll() is None:
            await asyncio.to_thread(self._terminate_process_tree, process, 5.0)
        try:
            stdout_bytes, stderr_bytes = process.communicate(timeout=0.5)
            if stdout_bytes:
                stdout_text = (
                    stdout_bytes.decode(errors="ignore")
                    if isinstance(stdout_bytes, (bytes, bytearray))
                    else stdout_bytes
                )
            if stderr_bytes:
                stderr_text = (
                    stderr_bytes.decode(errors="ignore")
                    if isinstance(stderr_bytes, (bytes, bytearray))
                    else stderr_bytes
                )
        except Exception:
            pass
        self.processes.pop(service_name, None)
        self.status[service_name] = ServiceStatus.FAILED
        return stdout_text, stderr_text

    def _terminate_process_tree(
        self, process: subprocess.Popen, timeout: float
    ) -> None:
        """Terminate a process tree safely."""
        if process.poll() is not None:
            return
        try:
            proc = psutil.Process(process.pid)
        except psutil.NoSuchProcess:
            return

        children = proc.children(recursive=True)
        for child in children:
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                continue

        try:
            proc.terminate()
        except psutil.NoSuchProcess:
            return

        _, alive = psutil.wait_procs([proc, *children], timeout=timeout)
        for remaining in alive:
            try:
                remaining.kill()
            except psutil.NoSuchProcess:
                continue
        psutil.wait_procs(alive, timeout=timeout)

    def _handle_start_failure(
        self, service_name: str, port: int, stderr_output: str
    ) -> None:
        """Emit contextual logs for common startup failures."""
        stderr_lower = (stderr_output or "").lower()
        if "10013" in stderr_lower or (
            "permission" in stderr_lower and "denied" in stderr_lower
        ):
            logger.error(
                "Service %s was blocked from binding to port %s (WinError 10013 / permission denied)."
                " Try closing security software that reserves the port or launch this shell as Administrator.",
                service_name,
                port,
            )
        elif "eaddrinuse" in stderr_lower or "already in use" in stderr_lower:
            logger.error(
                "Service %s could not bind to port %s because it is already in use. Close the application using that port"
                " or update the configured port in config.yaml.",
                service_name,
                port,
            )
        elif "used by another process" in stderr_lower:
            logger.error(
                "Service %s encountered a file lock while starting. Close any running Electron/Node instances before retrying.",
                service_name,
            )
        elif stderr_output:
            logger.error(
                "Service %s failed to start. stderr: %s",
                service_name,
                stderr_output.strip(),
            )
        else:
            logger.error(
                "Service %s failed to reach ready state. Check logs for more details.",
                service_name,
            )

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
            command = list(config.command)
            actual_port = config.port

            if not await self._is_port_available(config.port):
                logger.warning(
                    "Port conflict detected", port=config.port, service=service_name
                )
                self._log_port_conflicts(config.port, service_name)
                alternative_port = await self._find_available_port(config.port)
                if alternative_port:
                    logger.info(
                        "Using alternative port",
                        original_port=config.port,
                        alternative_port=alternative_port,
                        service=service_name,
                    )
                    actual_port = alternative_port
                else:
                    logger.error("No available ports found", service=service_name)
                    return False

            try:
                self.status[service_name] = ServiceStatus.STARTING

                env = os.environ.copy()
                if config.env_vars:
                    env.update(config.env_vars)

                if actual_port:
                    env["PORT"] = str(actual_port)
                    env["API_PORT"] = str(actual_port)
                    env.setdefault("UVICORN_PORT", str(actual_port))
                    env.setdefault("FASTAPI_PORT", str(actual_port))

                if service_name == "frontend":
                    api_config = self.services.get("api")
                    if api_config and api_config.port:
                        env["REACT_APP_API_URL"] = (
                            f"http://127.0.0.1:{api_config.port}"
                        )

                prepared_command = self._prepare_command_with_port(command, actual_port)

                process = subprocess.Popen(
                    prepared_command,
                    cwd=config.working_dir,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                self.processes[service_name] = process
                config.port = actual_port

                if await self._wait_for_service_ready(service_name, config):
                    self.status[service_name] = ServiceStatus.RUNNING
                    logger.info(
                        "Service started successfully",
                        service=service_name,
                        port=actual_port,
                        pid=process.pid,
                    )
                    return True

                stdout_text, stderr_text = await self._cleanup_failed_process(
                    service_name, process
                )
                self._handle_start_failure(service_name, actual_port, stderr_text)
                return False

            except Exception as e:
                self.status[service_name] = ServiceStatus.FAILED
                logger.error(
                    "Failed to start service", service=service_name, error=str(e)
                )
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
                await asyncio.to_thread(
                    self._terminate_process_tree,
                    process,
                    self.services[service_name].shutdown_timeout,
                )

                del self.processes[service_name]
                self.status[service_name] = ServiceStatus.STOPPED
                logger.info("Service stopped", service=service_name)
                return True

            except Exception as e:
                logger.error(
                    "Failed to stop service", service=service_name, error=str(e)
                )
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
                result = sock.connect_ex(("localhost", port))
                return result != 0
        except Exception:
            return False

    async def _find_available_port(
        self, start_port: int, max_attempts: int = 10
    ) -> Optional[int]:
        """Find an available port starting from start_port."""
        for port in range(start_port, start_port + max_attempts):
            if await self._is_port_available(port):
                return port
        return None

    async def _wait_for_service_ready(
        self, service_name: str, config: ServiceConfig
    ) -> bool:
        """Wait for a service to be ready."""
        if config.health_check_url:
            # Use health check URL
            return await self._check_health_endpoint(
                config.health_check_url, config.startup_timeout
            )
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
                logger.info(
                    "Cleaning up zombie process", service=service_name, pid=process.pid
                )
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
    manager.register_service(
        ServiceConfig(
            name="api",
            port=8001,
            command=[
                sys.executable,
                "-m",
                "uvicorn",
                "src.api.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8001",
            ],
            working_dir=str(Path(__file__).parent.parent.parent),
            health_check_url="http://127.0.0.1:8001/health",
            startup_timeout=30,
        )
    )

    # Frontend Service
    manager.register_service(
        ServiceConfig(
            name="frontend",
            port=3001,
            command=[
                "cmd",
                "/c",
                "npm",
                "run",
                "start:renderer",
            ]
            if sys.platform.startswith("win")
            else ["npm", "run", "start:renderer"],
            working_dir=str(
                Path(__file__).parent.parent.parent / "frontend" / "electron-react-app"
            ),
            env_vars={
                "PORT": "3001",
                "BROWSER": "none",
                "REACT_APP_API_URL": "http://127.0.0.1:8001",
            },
            startup_timeout=60,
        )
    )

    return manager
