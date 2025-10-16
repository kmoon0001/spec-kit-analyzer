#!/usr/bin/env python3
"""
Robust Application Startup Script
Handles proper startup sequence with comprehensive error recovery
"""

import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any

import psutil
import requests


class RobustApplicationStarter:
    def __init__(self):
        self.api_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        self.api_port = int(os.environ.get("API_PORT", "8100"))
        self.frontend_port = int(os.environ.get("FRONTEND_PORT", "3000"))
        self.api_url = f"http://127.0.0.1:{self.api_port}"
        self.frontend_dir = Path(__file__).parent / "frontend" / "electron-react-app"
        self.shutdown_requested = False
        self.startup_timeout = 180  # 3 minutes
        self.health_check_interval = 5  # seconds

    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with timestamps"""
        timestamp = time.strftime("%H:%M:%S")
        colors = {
            "INFO": "\033[94m",    # Blue
            "SUCCESS": "\033[92m", # Green
            "WARNING": "\033[93m", # Yellow
            "ERROR": "\033[91m",   # Red
            "RESET": "\033[0m"     # Reset
        }
        
        color = colors.get(level, colors["INFO"])
        reset = colors["RESET"]
        print(f"{color}[{timestamp}] {level}: {message}{reset}")

    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        self.log("Checking prerequisites...")
        
        # Run diagnostic check
        try:
            result = subprocess.run([sys.executable, "diagnostic_startup.py"], 
                                  capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                self.log("Prerequisites check failed:", "ERROR")
                if result.stdout:
                    print("STDOUT:", result.stdout[-500:])  # Last 500 chars
                if result.stderr:
                    print("STDERR:", result.stderr[-500:])  # Last 500 chars
                self.log("Please run diagnostic_startup.py manually to see detailed issues.", "ERROR")
                return False
            
            self.log("Prerequisites check passed", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Failed to run prerequisites check: {e}", "ERROR")
            return False

    def kill_existing_processes(self):
        """Kill any existing processes on our ports"""
        self.log("Checking for existing processes...")
        
        ports_to_check = [self.api_port, self.frontend_port]
        killed_any = False
        
        for port in ports_to_check:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                    try:
                        process = psutil.Process(conn.pid)
                        process_name = process.name()
                        self.log(f"Killing existing process on port {port}: {process_name} (PID: {conn.pid})", "WARNING")
                        process.terminate()
                        process.wait(timeout=5)
                        killed_any = True
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                        pass
        
        if killed_any:
            time.sleep(2)  # Give processes time to clean up
            self.log("Existing processes cleaned up", "SUCCESS")
        else:
            self.log("No existing processes found on required ports", "INFO")

    def start_api_server(self) -> bool:
        """Start the FastAPI backend server with enhanced monitoring"""
        self.log("Starting API server...")
        
        # Set environment variables for optimal startup
        env = os.environ.copy()
        env.update({
            "API_PORT": str(self.api_port),
            "USE_AI_MOCKS": "false",  # Use real AI for production
            "LOG_LEVEL": "INFO",
            "PYTHONPATH": str(Path(__file__).parent),
        })
        
        try:
            # Start API server using uvicorn directly for better control
            cmd = [
                sys.executable, "-m", "uvicorn",
                "src.api.main:app",
                "--host", "127.0.0.1",
                "--port", str(self.api_port),
                "--log-level", "info",
                "--access-log"
            ]
            
            self.api_process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            
            self.log(f"API server started (PID: {self.api_process.pid})", "SUCCESS")
            
            # Monitor startup with enhanced health checking
            return self.wait_for_api_health()
            
        except Exception as e:
            self.log(f"Failed to start API server: {e}", "ERROR")
            return False

    def wait_for_api_health(self) -> bool:
        """Wait for API to be healthy with detailed monitoring"""
        self.log(f"Waiting for API health at {self.api_url}/health...")
        
        start_time = time.time()
        last_log_time = 0
        
        while time.time() - start_time < self.startup_timeout:
            if self.shutdown_requested:
                return False
            
            # Check if process is still running
            if self.api_process and self.api_process.poll() is not None:
                self.log("API process died during startup", "ERROR")
                self.log_process_output()
                return False
            
            try:
                # Try basic health check
                response = requests.get(f"{self.api_url}/health", timeout=10)
                if response.status_code == 200:
                    health_data = response.json()
                    uptime = health_data.get("uptime_seconds", 0)
                    self.log(f"API is healthy (uptime: {uptime:.1f}s)", "SUCCESS")
                    
                    # Try detailed health check
                    try:
                        detailed_response = requests.get(f"{self.api_url}/health/readiness", timeout=5)
                        if detailed_response.status_code == 200:
                            self.log("API readiness check passed", "SUCCESS")
                            return True
                        else:
                            self.log("API not ready yet, continuing to wait...", "INFO")
                    except requests.RequestException:
                        self.log("API basic health OK, readiness check pending...", "INFO")
                        return True  # Basic health is sufficient for startup
                
                elif response.status_code == 503:
                    self.log("API starting up (service unavailable), waiting...", "INFO")
                else:
                    self.log(f"API returned status {response.status_code}, continuing to wait...", "WARNING")
                    
            except requests.RequestException as e:
                current_time = time.time()
                if current_time - last_log_time > 10:  # Log every 10 seconds
                    elapsed = current_time - start_time
                    self.log(f"Still waiting for API... ({elapsed:.0f}s) - {type(e).__name__}", "INFO")
                    last_log_time = current_time
            
            time.sleep(self.health_check_interval)
        
        self.log(f"API health check timed out after {self.startup_timeout} seconds", "ERROR")
        self.log_process_output()
        return False

    def log_process_output(self):
        """Log recent output from API process for debugging"""
        if not self.api_process or not self.api_process.stdout:
            return
        
        self.log("Recent API server output:", "INFO")
        try:
            # Read available output without blocking
            import select
            if hasattr(select, 'select'):
                ready, _, _ = select.select([self.api_process.stdout], [], [], 0)
                if ready:
                    output = self.api_process.stdout.read()
                    if output:
                        for line in output.strip().split('\n')[-10:]:  # Last 10 lines
                            print(f"  API: {line}")
        except Exception:
            # Fallback for Windows
            pass

    def start_frontend(self) -> bool:
        """Start the Electron frontend with enhanced monitoring"""
        self.log("Starting Electron frontend...")
        
        if not self.frontend_dir.exists():
            self.log(f"Frontend directory not found: {self.frontend_dir}", "ERROR")
            return False

        # Ensure dependencies are installed
        node_modules = self.frontend_dir / "node_modules"
        if not node_modules.exists():
            self.log("Installing frontend dependencies...", "INFO")
            try:
                result = subprocess.run(
                    ["npm", "install"],
                    cwd=self.frontend_dir,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes
                )
                if result.returncode != 0:
                    self.log(f"Failed to install dependencies: {result.stderr}", "ERROR")
                    return False
                self.log("Frontend dependencies installed", "SUCCESS")
            except subprocess.TimeoutExpired:
                self.log("Frontend dependency installation timed out", "ERROR")
                return False

        # Set environment variables
        env = os.environ.copy()
        env.update({
            "COMPLIANCE_API_URL": self.api_url,
            "ELECTRON_IS_DEV": "1",
            "PORT": str(self.frontend_port),
            "BROWSER": "none",  # Don't open browser
        })

        try:
            # Start Electron app
            self.frontend_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=self.frontend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            
            self.log(f"Frontend started (PID: {self.frontend_process.pid})", "SUCCESS")
            
            # Give frontend time to start
            time.sleep(5)
            
            # Check if process is still running
            if self.frontend_process.poll() is not None:
                self.log("Frontend process died during startup", "ERROR")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"Failed to start frontend: {e}", "ERROR")
            return False

    def monitor_processes(self):
        """Monitor running processes and handle failures"""
        self.log("Starting process monitoring...", "INFO")
        
        last_health_check = 0
        
        while not self.shutdown_requested:
            try:
                current_time = time.time()
                
                # Check API process
                if self.api_process:
                    if self.api_process.poll() is not None:
                        self.log("API server died, attempting restart...", "ERROR")
                        if not self.start_api_server():
                            self.log("Failed to restart API server", "ERROR")
                            break
                
                # Check frontend process
                if self.frontend_process:
                    if self.frontend_process.poll() is not None:
                        self.log("Frontend died, attempting restart...", "ERROR")
                        if not self.start_frontend():
                            self.log("Failed to restart frontend", "ERROR")
                            break
                
                # Periodic health check
                if current_time - last_health_check > 30:  # Every 30 seconds
                    try:
                        response = requests.get(f"{self.api_url}/health", timeout=5)
                        if response.status_code != 200:
                            self.log(f"API health check failed: {response.status_code}", "WARNING")
                    except requests.RequestException:
                        self.log("API health check failed: connection error", "WARNING")
                    
                    last_health_check = current_time
                
                time.sleep(5)  # Check every 5 seconds
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log(f"Error in process monitoring: {e}", "ERROR")
                time.sleep(10)

    def stop_processes(self):
        """Stop all processes gracefully"""
        self.log("Stopping processes...", "INFO")
        
        # Stop frontend first
        if self.frontend_process:
            self.log("Stopping frontend...", "INFO")
            try:
                if sys.platform == "win32":
                    self.frontend_process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    self.frontend_process.terminate()
                
                self.frontend_process.wait(timeout=10)
                self.log("Frontend stopped gracefully", "SUCCESS")
            except subprocess.TimeoutExpired:
                self.log("Force killing frontend...", "WARNING")
                self.frontend_process.kill()
                self.frontend_process.wait()
            except Exception as e:
                self.log(f"Error stopping frontend: {e}", "ERROR")
            finally:
                self.frontend_process = None

        # Stop API server
        if self.api_process:
            self.log("Stopping API server...", "INFO")
            try:
                if sys.platform == "win32":
                    self.api_process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    self.api_process.terminate()
                
                self.api_process.wait(timeout=15)
                self.log("API server stopped gracefully", "SUCCESS")
            except subprocess.TimeoutExpired:
                self.log("Force killing API server...", "WARNING")
                self.api_process.kill()
                self.api_process.wait()
            except Exception as e:
                self.log(f"Error stopping API server: {e}", "ERROR")
            finally:
                self.api_process = None

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            if not self.shutdown_requested:
                self.log(f"Received signal {signum}, shutting down gracefully...", "INFO")
                self.shutdown_requested = True

        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)

    def run(self) -> int:
        """Main application runner with comprehensive error handling"""
        print("=" * 80)
        print("🚀 THERAPY COMPLIANCE ANALYZER - ROBUST STARTUP")
        print("=" * 80)
        
        self.setup_signal_handlers()
        
        try:
            # Step 1: Check prerequisites (optional for now)
            if not self.check_prerequisites():
                self.log("Prerequisites check failed, but continuing anyway...", "WARNING")
            
            # Step 2: Clean up existing processes
            self.kill_existing_processes()
            
            # Step 3: Start API server
            if not self.start_api_server():
                self.log("Failed to start API server", "ERROR")
                return 1

            # Step 4: Start frontend
            if not self.start_frontend():
                self.log("Failed to start frontend", "ERROR")
                self.stop_processes()
                return 1

            # Step 5: Show success message
            print("\n" + "=" * 80)
            print("✅ APPLICATION STARTED SUCCESSFULLY!")
            print("=" * 80)
            print(f"🔗 API Server: {self.api_url}")
            print(f"🖥️  Frontend: Electron Desktop App")
            print(f"📊 Health Check: {self.api_url}/health")
            print(f"📈 Detailed Health: {self.api_url}/health/detailed")
            print("\n💡 Press Ctrl+C to stop the application")
            print("=" * 80)

            # Step 6: Monitor processes
            self.monitor_processes()

        except KeyboardInterrupt:
            self.log("Shutdown requested by user", "INFO")
        except Exception as e:
            self.log(f"Unexpected error: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return 1
        finally:
            self.stop_processes()
            self.log("Application shutdown complete", "SUCCESS")

        return 0


def main():
    """Main entry point"""
    starter = RobustApplicationStarter()
    return starter.run()


if __name__ == "__main__":
    sys.exit(main())