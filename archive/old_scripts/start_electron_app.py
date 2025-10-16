#!/usr/bin/env python3
"""
Complete Electron Application Startup Script
Ensures the entire codebase is properly configured for Electron frontend
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


class ElectronAppStarter:
    def __init__(self):
        self.api_process: Optional[subprocess.Popen] = None
        self.electron_process: Optional[subprocess.Popen] = None
        self.api_port = int(os.environ.get("API_PORT", "8100"))
        self.react_port = int(os.environ.get("REACT_PORT", "3000"))
        self.api_url = f"http://127.0.0.1:{self.api_port}"
        self.frontend_dir = Path(__file__).parent / "frontend" / "electron-react-app"
        self.shutdown_requested = False
        self.startup_timeout = 120  # 2 minutes

    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with timestamps and colors"""
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
        """Check if all prerequisites are met for Electron app"""
        self.log("Checking Electron prerequisites...")
        
        # Check Python dependencies
        try:
            import fastapi
            import uvicorn
            import sqlalchemy
            self.log("✓ Python dependencies available", "SUCCESS")
        except ImportError as e:
            self.log(f"✗ Missing Python dependency: {e}", "ERROR")
            return False
        
        # Check Node.js and npm
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.log(f"✓ Node.js {result.stdout.strip()}", "SUCCESS")
            else:
                self.log("✗ Node.js not found", "ERROR")
                return False
        except FileNotFoundError:
            self.log("✗ Node.js not installed", "ERROR")
            return False
        
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.log(f"✓ npm {result.stdout.strip()}", "SUCCESS")
            else:
                self.log("✗ npm not found", "ERROR")
                return False
        except FileNotFoundError:
            self.log("✗ npm not installed", "ERROR")
            return False
        
        # Check frontend directory
        if not self.frontend_dir.exists():
            self.log(f"✗ Frontend directory not found: {self.frontend_dir}", "ERROR")
            return False
        
        self.log("✓ Frontend directory exists", "SUCCESS")
        
        # Check package.json
        package_json = self.frontend_dir / "package.json"
        if not package_json.exists():
            self.log("✗ package.json not found", "ERROR")
            return False
        
        self.log("✓ package.json exists", "SUCCESS")
        return True

    def kill_existing_processes(self):
        """Kill any existing processes on our ports"""
        self.log("Checking for existing processes...")
        
        ports_to_check = [self.api_port, self.react_port]
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
            time.sleep(2)
            self.log("Existing processes cleaned up", "SUCCESS")
        else:
            self.log("No existing processes found on required ports", "INFO")

    def setup_environment(self):
        """Set up environment variables for Electron app"""
        self.log("Setting up environment variables...")
        
        # API environment
        os.environ.update({
            "API_PORT": str(self.api_port),
            "USE_AI_MOCKS": "false",
            "LOG_LEVEL": "INFO",
            "PYTHONPATH": str(Path(__file__).parent),
            "COMPLIANCE_API_URL": self.api_url,
        })
        
        # Electron environment
        os.environ.update({
            "ELECTRON_IS_DEV": "1",
            "REACT_APP_API_URL": self.api_url,
            "PORT": str(self.react_port),
            "BROWSER": "none",
            "ELECTRON_RENDERER_URL": f"http://localhost:{self.react_port}",
        })
        
        self.log("Environment variables configured", "SUCCESS")

    def install_frontend_dependencies(self) -> bool:
        """Install frontend dependencies if needed"""
        node_modules = self.frontend_dir / "node_modules"
        
        if node_modules.exists():
            self.log("Frontend dependencies already installed", "INFO")
            return True
        
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
            
            self.log("Frontend dependencies installed successfully", "SUCCESS")
            return True
            
        except subprocess.TimeoutExpired:
            self.log("Frontend dependency installation timed out", "ERROR")
            return False
        except Exception as e:
            self.log(f"Error installing dependencies: {e}", "ERROR")
            return False

    def start_api_server(self) -> bool:
        """Start the FastAPI backend server"""
        self.log("Starting FastAPI backend server...")
        
        try:
            cmd = [
                sys.executable, "-m", "uvicorn",
                "src.api.main:app",
                "--host", "127.0.0.1",
                "--port", str(self.api_port),
                "--log-level", "info",
                "--reload"  # Enable hot reload for development
            ]
            
            self.api_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            
            self.log(f"API server started (PID: {self.api_process.pid})", "SUCCESS")
            return self.wait_for_api_health()
            
        except Exception as e:
            self.log(f"Failed to start API server: {e}", "ERROR")
            return False

    def wait_for_api_health(self) -> bool:
        """Wait for API to be healthy"""
        self.log(f"Waiting for API health at {self.api_url}/health...")
        
        start_time = time.time()
        
        while time.time() - start_time < self.startup_timeout:
            if self.shutdown_requested:
                return False
            
            # Check if process is still running
            if self.api_process and self.api_process.poll() is not None:
                self.log("API process died during startup", "ERROR")
                return False
            
            try:
                response = requests.get(f"{self.api_url}/health", timeout=5)
                if response.status_code == 200:
                    health_data = response.json()
                    uptime = health_data.get("uptime_seconds", 0)
                    self.log(f"API is healthy (uptime: {uptime:.1f}s)", "SUCCESS")
                    return True
                    
            except requests.RequestException:
                pass
            
            time.sleep(2)
        
        self.log(f"API health check timed out after {self.startup_timeout} seconds", "ERROR")
        return False

    def start_electron_app(self) -> bool:
        """Start the Electron React application"""
        self.log("Starting Electron React application...")
        
        try:
            # Use the dev script which starts both React and Electron
            cmd = ["npm", "run", "dev"]
            
            self.electron_process = subprocess.Popen(
                cmd,
                cwd=self.frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            
            self.log(f"Electron app started (PID: {self.electron_process.pid})", "SUCCESS")
            
            # Give it time to start
            time.sleep(5)
            
            # Check if process is still running
            if self.electron_process.poll() is not None:
                self.log("Electron process died during startup", "ERROR")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"Failed to start Electron app: {e}", "ERROR")
            return False

    def monitor_processes(self):
        """Monitor running processes"""
        self.log("Starting process monitoring...", "INFO")
        
        while not self.shutdown_requested:
            try:
                # Check API process
                if self.api_process and self.api_process.poll() is not None:
                    self.log("API server died, restarting...", "ERROR")
                    if not self.start_api_server():
                        self.log("Failed to restart API server", "ERROR")
                        break
                
                # Check Electron process
                if self.electron_process and self.electron_process.poll() is not None:
                    self.log("Electron app died, restarting...", "ERROR")
                    if not self.start_electron_app():
                        self.log("Failed to restart Electron app", "ERROR")
                        break
                
                time.sleep(5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log(f"Error in process monitoring: {e}", "ERROR")
                time.sleep(10)

    def stop_processes(self):
        """Stop all processes gracefully"""
        self.log("Stopping processes...", "INFO")
        
        # Stop Electron first
        if self.electron_process:
            self.log("Stopping Electron app...", "INFO")
            try:
                if sys.platform == "win32":
                    self.electron_process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    self.electron_process.terminate()
                
                self.electron_process.wait(timeout=10)
                self.log("Electron app stopped gracefully", "SUCCESS")
            except subprocess.TimeoutExpired:
                self.log("Force killing Electron app...", "WARNING")
                self.electron_process.kill()
                self.electron_process.wait()
            except Exception as e:
                self.log(f"Error stopping Electron app: {e}", "ERROR")
            finally:
                self.electron_process = None

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
        """Main application runner"""
        print("=" * 80)
        print("🚀 THERAPY COMPLIANCE ANALYZER - ELECTRON FRONTEND")
        print("=" * 80)
        
        self.setup_signal_handlers()
        
        try:
            # Step 1: Check prerequisites
            if not self.check_prerequisites():
                self.log("Prerequisites check failed", "ERROR")
                return 1
            
            # Step 2: Setup environment
            self.setup_environment()
            
            # Step 3: Clean up existing processes
            self.kill_existing_processes()
            
            # Step 4: Install frontend dependencies
            if not self.install_frontend_dependencies():
                self.log("Failed to install frontend dependencies", "ERROR")
                return 1
            
            # Step 5: Start API server
            if not self.start_api_server():
                self.log("Failed to start API server", "ERROR")
                return 1

            # Step 6: Start Electron app
            if not self.start_electron_app():
                self.log("Failed to start Electron app", "ERROR")
                self.stop_processes()
                return 1

            # Step 7: Show success message
            print("\n" + "=" * 80)
            print("✅ ELECTRON APPLICATION STARTED SUCCESSFULLY!")
            print("=" * 80)
            print(f"🔗 API Server: {self.api_url}")
            print(f"🖥️  Electron App: Desktop Application")
            print(f"📊 Health Check: {self.api_url}/health")
            print(f"📈 API Docs: {self.api_url}/docs")
            print("\n💡 Press Ctrl+C to stop the application")
            print("=" * 80)

            # Step 8: Monitor processes
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
    starter = ElectronAppStarter()
    return starter.run()


if __name__ == "__main__":
    sys.exit(main())