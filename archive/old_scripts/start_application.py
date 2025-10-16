#!/usr/bin/env python3
"""
Comprehensive Application Startup Script
Handles proper startup sequence for the Therapy Compliance Analyzer
"""

import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import psutil
import requests


class ApplicationStarter:
    def __init__(self):
        self.api_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        self.api_port = int(os.environ.get("API_PORT", "8100"))
        self.frontend_port = int(os.environ.get("FRONTEND_PORT", "3000"))
        self.api_url = f"http://127.0.0.1:{self.api_port}"
        self.frontend_dir = Path(__file__).parent / "frontend" / "electron-react-app"
        self.shutdown_requested = False

    def check_port_available(self, port: int) -> bool:
        """Check if a port is available."""
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                return False
        return True

    def kill_process_on_port(self, port: int) -> bool:
        """Kill any process using the specified port."""
        killed = False
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                try:
                    process = psutil.Process(conn.pid)
                    print(f"Killing process {conn.pid} ({process.name()}) on port {port}")
                    process.terminate()
                    process.wait(timeout=5)
                    killed = True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    pass
        return killed

    def wait_for_api_health(self, timeout: int = 120) -> bool:
        """Wait for API to be healthy."""
        print(f"Waiting for API health check at {self.api_url}/health...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.api_url}/health", timeout=10)
                if response.status_code == 200:
                    print("✓ API is healthy")
                    return True
                else:
                    print(f"\nAPI returned status {response.status_code}, continuing to wait...")
            except requests.RequestException as e:
                # Print more detailed error info occasionally
                elapsed = time.time() - start_time
                if int(elapsed) % 10 == 0:  # Every 10 seconds
                    print(f"\nStill waiting... ({int(elapsed)}s) - {type(e).__name__}")
            
            print(".", end="", flush=True)
            time.sleep(3)
        
        print(f"\n✗ API health check failed after {timeout} seconds")
        return False

    def start_api_server(self) -> bool:
        """Start the FastAPI backend server."""
        print("Starting API server...")
        
        # Check if port is available
        if not self.check_port_available(self.api_port):
            print(f"Port {self.api_port} is in use. Attempting to free it...")
            if not self.kill_process_on_port(self.api_port):
                print(f"✗ Failed to free port {self.api_port}")
                return False

        # Start API server
        api_script = Path(__file__).parent / "start_api.py"
        if not api_script.exists():
            print(f"✗ API script not found: {api_script}")
            return False

        try:
            env = os.environ.copy()
            env["API_PORT"] = str(self.api_port)
            
            self.api_process = subprocess.Popen(
                [sys.executable, str(api_script)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            
            print(f"✓ API server started (PID: {self.api_process.pid})")
            
            # Wait for API to be healthy
            if self.wait_for_api_health():
                return True
            else:
                self.stop_api_server()
                return False
                
        except Exception as e:
            print(f"✗ Failed to start API server: {e}")
            return False

    def start_frontend(self) -> bool:
        """Start the Electron frontend."""
        print("Starting Electron frontend...")
        
        if not self.frontend_dir.exists():
            print(f"✗ Frontend directory not found: {self.frontend_dir}")
            return False

        # Check if frontend port is available
        if not self.check_port_available(self.frontend_port):
            print(f"Port {self.frontend_port} is in use. Attempting to free it...")
            if not self.kill_process_on_port(self.frontend_port):
                print(f"✗ Failed to free port {self.frontend_port}")
                return False

        try:
            # Check if node_modules exists
            node_modules = self.frontend_dir / "node_modules"
            if not node_modules.exists():
                print("Installing frontend dependencies...")
                install_result = subprocess.run(
                    ["npm", "install"],
                    cwd=self.frontend_dir,
                    capture_output=True,
                    text=True
                )
                if install_result.returncode != 0:
                    print(f"✗ Failed to install dependencies: {install_result.stderr}")
                    return False

            # Set environment variables
            env = os.environ.copy()
            env["COMPLIANCE_API_URL"] = self.api_url
            env["ELECTRON_IS_DEV"] = "1"
            env["PORT"] = str(self.frontend_port)

            # Start Electron app
            self.frontend_process = subprocess.Popen(
                ["npm", "run", "start:electron"],
                cwd=self.frontend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            
            print(f"✓ Frontend started (PID: {self.frontend_process.pid})")
            return True
            
        except Exception as e:
            print(f"✗ Failed to start frontend: {e}")
            return False

    def stop_api_server(self):
        """Stop the API server."""
        if self.api_process:
            print("Stopping API server...")
            try:
                if sys.platform == "win32":
                    self.api_process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    self.api_process.terminate()
                
                self.api_process.wait(timeout=10)
                print("✓ API server stopped")
            except subprocess.TimeoutExpired:
                print("Force killing API server...")
                self.api_process.kill()
                self.api_process.wait()
            except Exception as e:
                print(f"Error stopping API server: {e}")
            finally:
                self.api_process = None

    def stop_frontend(self):
        """Stop the frontend."""
        if self.frontend_process:
            print("Stopping frontend...")
            try:
                if sys.platform == "win32":
                    self.frontend_process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    self.frontend_process.terminate()
                
                self.frontend_process.wait(timeout=10)
                print("✓ Frontend stopped")
            except subprocess.TimeoutExpired:
                print("Force killing frontend...")
                self.frontend_process.kill()
                self.frontend_process.wait()
            except Exception as e:
                print(f"Error stopping frontend: {e}")
            finally:
                self.frontend_process = None

    def cleanup(self):
        """Clean up all processes."""
        print("\nCleaning up...")
        self.stop_frontend()
        self.stop_api_server()
        print("✓ Cleanup complete")

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            if not self.shutdown_requested:
                print(f"\nReceived signal {signum}, shutting down...")
                self.shutdown_requested = True
                self.cleanup()
                sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)

    def monitor_processes(self):
        """Monitor running processes and restart if needed."""
        while not self.shutdown_requested:
            try:
                # Check API process
                if self.api_process and self.api_process.poll() is not None:
                    print("✗ API server died, restarting...")
                    if not self.start_api_server():
                        print("✗ Failed to restart API server")
                        break

                # Check frontend process
                if self.frontend_process and self.frontend_process.poll() is not None:
                    print("✗ Frontend died, restarting...")
                    if not self.start_frontend():
                        print("✗ Failed to restart frontend")
                        break

                time.sleep(5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error in process monitoring: {e}")
                time.sleep(5)

    def run(self):
        """Main application runner."""
        print("=" * 60)
        print("Therapy Compliance Analyzer - Application Starter")
        print("=" * 60)
        
        self.setup_signal_handlers()
        
        try:
            # Start API server first
            if not self.start_api_server():
                print("✗ Failed to start API server")
                return 1

            # Start frontend
            if not self.start_frontend():
                print("✗ Failed to start frontend")
                self.cleanup()
                return 1

            print("\n" + "=" * 60)
            print("✓ Application started successfully!")
            print(f"API Server: {self.api_url}")
            print(f"Frontend: Running in Electron")
            print("Press Ctrl+C to stop")
            print("=" * 60)

            # Monitor processes
            self.monitor_processes()

        except KeyboardInterrupt:
            print("\nShutdown requested by user")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            return 1
        finally:
            self.cleanup()

        return 0


def main():
    """Main entry point."""
    # Check dependencies
    try:
        import psutil
        import requests
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install: pip install psutil requests")
        return 1

    starter = ApplicationStarter()
    return starter.run()


if __name__ == "__main__":
    sys.exit(main())