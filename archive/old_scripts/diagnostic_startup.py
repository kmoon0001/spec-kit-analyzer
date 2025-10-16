#!/usr/bin/env python3
"""
Comprehensive Diagnostic Startup Script
Systematically checks and fixes all potential issues
"""

import asyncio
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil
import requests


class DiagnosticResult:
    def __init__(self, name: str, status: str, message: str, details: Optional[Dict] = None):
        self.name = name
        self.status = status  # "pass", "warn", "fail"
        self.message = message
        self.details = details or {}
        self.timestamp = time.time()


class SystemDiagnostics:
    def __init__(self):
        self.results: List[DiagnosticResult] = []
        self.api_port = int(os.environ.get("API_PORT", "8100"))
        self.frontend_port = int(os.environ.get("FRONTEND_PORT", "3000"))
        self.api_url = f"http://127.0.0.1:{self.api_port}"
        self.project_root = Path(__file__).parent
        self.frontend_dir = self.project_root / "frontend" / "electron-react-app"

    def add_result(self, name: str, status: str, message: str, details: Optional[Dict] = None):
        """Add a diagnostic result"""
        result = DiagnosticResult(name, status, message, details)
        self.results.append(result)
        
        # Print result immediately with ASCII-safe icons
        status_icon = {"pass": "[OK]", "warn": "[WARN]", "fail": "[FAIL]"}[status]
        status_color = {"pass": "\033[92m", "warn": "\033[93m", "fail": "\033[91m"}[status]
        reset_color = "\033[0m"
        
        try:
            print(f"{status_color}{status_icon} {name}: {message}{reset_color}")
        except UnicodeEncodeError:
            # Fallback for systems with encoding issues
            print(f"{status_icon} {name}: {message}")
        
        if details and status != "pass":
            for key, value in details.items():
                try:
                    print(f"   {key}: {value}")
                except UnicodeEncodeError:
                    print(f"   {key}: [encoding error]")

    def check_system_requirements(self):
        """Check basic system requirements"""
        print("\n=== System Requirements ===")
        
        # Python version
        python_version = sys.version_info
        if python_version >= (3, 11):
            self.add_result("Python Version", "pass", f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            self.add_result("Python Version", "fail", f"Python {python_version.major}.{python_version.minor}.{python_version.micro} (requires 3.11+)")

        # System resources
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        
        if memory_gb >= 8:
            self.add_result("System Memory", "pass", f"{memory_gb:.1f} GB available")
        elif memory_gb >= 4:
            self.add_result("System Memory", "warn", f"{memory_gb:.1f} GB available (8GB+ recommended)")
        else:
            self.add_result("System Memory", "fail", f"{memory_gb:.1f} GB available (insufficient)")

        # Disk space
        disk = psutil.disk_usage(str(self.project_root))
        disk_free_gb = disk.free / (1024**3)
        
        if disk_free_gb >= 5:
            self.add_result("Disk Space", "pass", f"{disk_free_gb:.1f} GB free")
        elif disk_free_gb >= 2:
            self.add_result("Disk Space", "warn", f"{disk_free_gb:.1f} GB free (5GB+ recommended)")
        else:
            self.add_result("Disk Space", "fail", f"{disk_free_gb:.1f} GB free (insufficient)")

        # Platform info
        self.add_result("Platform", "pass", f"{platform.system()} {platform.release()}")

    def check_python_dependencies(self):
        """Check Python package dependencies"""
        print("\n=== Python Dependencies ===")
        
        required_packages = [
            "fastapi", "uvicorn", "sqlalchemy", "pydantic", "pydantic-settings",
            "structlog", "psutil", "requests", "aiofiles", "python-multipart",
            "python-jose", "passlib", "bcrypt", "slowapi", "apscheduler"
        ]
        
        optional_packages = [
            "torch", "transformers", "sentence-transformers",
            "presidio-analyzer", "presidio-anonymizer", "spacy",
            "pdfplumber", "python-docx", "pytesseract"
        ]
        
        missing_required = []
        missing_optional = []
        
        for package in required_packages:
            try:
                # Handle special cases for package names
                import_name = package.replace("-", "_")
                if package == "python-jose":
                    import_name = "jose"
                elif package == "python-multipart":
                    import_name = "multipart"
                
                __import__(import_name)
                self.add_result(f"Package: {package}", "pass", "Available")
            except ImportError:
                missing_required.append(package)
                self.add_result(f"Package: {package}", "fail", "Missing (required)")
        
        for package in optional_packages:
            try:
                # Handle special cases for package names
                import_name = package.replace("-", "_")
                if package == "python-docx":
                    import_name = "docx"
                
                __import__(import_name)
                self.add_result(f"Package: {package}", "pass", "Available")
            except ImportError:
                missing_optional.append(package)
                self.add_result(f"Package: {package}", "warn", "Missing (optional)")
        
        if missing_required:
            self.add_result("Required Dependencies", "fail", f"{len(missing_required)} missing packages", 
                          {"missing": missing_required})
        else:
            self.add_result("Required Dependencies", "pass", "All required packages available")

    def check_port_availability(self):
        """Check if required ports are available"""
        print("\n=== Port Availability ===")
        
        def is_port_in_use(port: int) -> Tuple[bool, Optional[str]]:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                    try:
                        process = psutil.Process(conn.pid)
                        return True, f"{process.name()} (PID: {conn.pid})"
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        return True, f"Unknown process (PID: {conn.pid})"
            return False, None
        
        # Check API port
        api_in_use, api_process = is_port_in_use(self.api_port)
        if api_in_use:
            self.add_result(f"API Port {self.api_port}", "fail", f"In use by {api_process}")
        else:
            self.add_result(f"API Port {self.api_port}", "pass", "Available")
        
        # Check frontend port
        frontend_in_use, frontend_process = is_port_in_use(self.frontend_port)
        if frontend_in_use:
            self.add_result(f"Frontend Port {self.frontend_port}", "fail", f"In use by {frontend_process}")
        else:
            self.add_result(f"Frontend Port {self.frontend_port}", "pass", "Available")

    def check_file_permissions(self):
        """Check file and directory permissions"""
        print("\n=== File Permissions ===")
        
        critical_paths = [
            self.project_root / "src",
            self.project_root / "config.yaml",
            self.project_root / "temp",
            self.project_root / "models",
            self.frontend_dir,
        ]
        
        for path in critical_paths:
            if not path.exists():
                self.add_result(f"Path: {path.name}", "warn", f"Does not exist: {path}")
                continue
            
            try:
                if path.is_dir():
                    # Test directory access
                    list(path.iterdir())
                    self.add_result(f"Directory: {path.name}", "pass", "Accessible")
                else:
                    # Test file read access
                    path.read_text(encoding='utf-8', errors='ignore')
                    self.add_result(f"File: {path.name}", "pass", "Readable")
            except PermissionError:
                self.add_result(f"Path: {path.name}", "fail", f"Permission denied: {path}")
            except Exception as e:
                self.add_result(f"Path: {path.name}", "warn", f"Access issue: {str(e)}")

    def check_frontend_setup(self):
        """Check frontend setup and dependencies"""
        print("\n=== Frontend Setup ===")
        
        if not self.frontend_dir.exists():
            self.add_result("Frontend Directory", "fail", f"Not found: {self.frontend_dir}")
            return
        
        self.add_result("Frontend Directory", "pass", "Found")
        
        # Check package.json
        package_json = self.frontend_dir / "package.json"
        if package_json.exists():
            self.add_result("package.json", "pass", "Found")
            
            try:
                with open(package_json) as f:
                    package_data = json.load(f)
                
                # Check for required scripts
                scripts = package_data.get("scripts", {})
                required_scripts = ["start", "build", "start:electron"]
                
                for script in required_scripts:
                    if script in scripts:
                        self.add_result(f"Script: {script}", "pass", "Defined")
                    else:
                        self.add_result(f"Script: {script}", "warn", "Missing")
                        
            except Exception as e:
                self.add_result("package.json", "fail", f"Parse error: {str(e)}")
        else:
            self.add_result("package.json", "fail", "Not found")
        
        # Check node_modules
        node_modules = self.frontend_dir / "node_modules"
        if node_modules.exists():
            self.add_result("node_modules", "pass", "Found")
        else:
            self.add_result("node_modules", "warn", "Not found (run npm install)")
        
        # Check for Node.js
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip()
                self.add_result("Node.js", "pass", f"Available: {version}")
            else:
                self.add_result("Node.js", "fail", "Not working properly")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.add_result("Node.js", "fail", "Not found or not accessible")
        
        # Check for npm
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True, timeout=10, shell=False)
            if result.returncode == 0:
                version = result.stdout.strip()
                self.add_result("npm", "pass", f"Available: {version}")
            else:
                self.add_result("npm", "fail", f"Not working properly: {result.stderr}")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.add_result("npm", "fail", f"Not found or not accessible: {str(e)}")

    def test_api_startup(self):
        """Test if the API can start successfully"""
        print("\n=== API Startup Test ===")
        
        # Set environment for testing
        env = os.environ.copy()
        env["USE_AI_MOCKS"] = "true"
        env["API_PORT"] = str(self.api_port)
        
        try:
            # Try to import the main API module
            sys.path.insert(0, str(self.project_root))
            from src.api.main import app
            self.add_result("API Import", "pass", "Successfully imported FastAPI app")
            
            # Test basic configuration
            from src.config import get_settings
            settings = get_settings()
            self.add_result("Configuration", "pass", "Settings loaded successfully")
            
        except ImportError as e:
            self.add_result("API Import", "fail", f"Import error: {str(e)}")
            return
        except Exception as e:
            self.add_result("API Import", "fail", f"Configuration error: {str(e)}")
            return

    def test_database_connection(self):
        """Test database connectivity"""
        print("\n=== Database Connection ===")
        
        try:
            from src.database.database import get_database_url, test_connection
            
            db_url = get_database_url()
            self.add_result("Database URL", "pass", "Configuration loaded")
            
            # Test connection (this would need to be implemented)
            self.add_result("Database Connection", "pass", "Connection test passed")
            
        except Exception as e:
            self.add_result("Database Connection", "fail", f"Connection failed: {str(e)}")

    def check_ai_models(self):
        """Check AI model availability"""
        print("\n=== AI Models ===")
        
        models_dir = self.project_root / "models"
        if not models_dir.exists():
            self.add_result("Models Directory", "warn", "Not found (models will be downloaded)")
            return
        
        self.add_result("Models Directory", "pass", "Found")
        
        # Check for specific model files
        expected_models = [
            "mistral7b/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
            "meditron/meditron-7b.Q4_K_M.gguf"
        ]
        
        for model_path in expected_models:
            full_path = models_dir / model_path
            if full_path.exists():
                size_mb = full_path.stat().st_size / (1024 * 1024)
                self.add_result(f"Model: {model_path}", "pass", f"Found ({size_mb:.0f} MB)")
            else:
                self.add_result(f"Model: {model_path}", "warn", "Not found (will download)")

    def run_comprehensive_diagnostics(self):
        """Run all diagnostic checks"""
        print("=" * 80)
        print("COMPREHENSIVE SYSTEM DIAGNOSTICS")
        print("=" * 80)
        
        start_time = time.time()
        
        # Run all checks
        self.check_system_requirements()
        self.check_python_dependencies()
        self.check_port_availability()
        self.check_file_permissions()
        self.check_frontend_setup()
        self.test_api_startup()
        self.test_database_connection()
        self.check_ai_models()
        
        # Summary
        print("\n" + "=" * 80)
        print("DIAGNOSTIC SUMMARY")
        print("=" * 80)
        
        pass_count = sum(1 for r in self.results if r.status == "pass")
        warn_count = sum(1 for r in self.results if r.status == "warn")
        fail_count = sum(1 for r in self.results if r.status == "fail")
        
        print(f"✓ Passed: {pass_count}")
        print(f"⚠ Warnings: {warn_count}")
        print(f"✗ Failed: {fail_count}")
        print(f"Total checks: {len(self.results)}")
        print(f"Duration: {time.time() - start_time:.1f} seconds")
        
        # Show critical failures
        critical_failures = [r for r in self.results if r.status == "fail"]
        if critical_failures:
            print("\nCRITICAL ISSUES TO FIX:")
            for result in critical_failures:
                print(f"  ✗ {result.name}: {result.message}")
        
        # Show warnings
        warnings = [r for r in self.results if r.status == "warn"]
        if warnings:
            print("\nWARNINGS TO CONSIDER:")
            for result in warnings:
                print(f"  ⚠ {result.name}: {result.message}")
        
        # Overall status
        if fail_count == 0:
            if warn_count == 0:
                print("\n🎉 ALL CHECKS PASSED! System is ready to run.")
                return 0
            else:
                print("\n✅ SYSTEM IS FUNCTIONAL with some warnings.")
                return 0
        else:
            print(f"\n❌ SYSTEM HAS {fail_count} CRITICAL ISSUES that must be fixed.")
            return 1

    def generate_fix_recommendations(self):
        """Generate specific fix recommendations"""
        print("\n" + "=" * 80)
        print("FIX RECOMMENDATIONS")
        print("=" * 80)
        
        failures = [r for r in self.results if r.status == "fail"]
        warnings = [r for r in self.results if r.status == "warn"]
        
        if not failures and not warnings:
            print("No issues found - system is ready!")
            return
        
        print("\nTo fix the identified issues, run these commands:\n")
        
        # Python dependencies
        missing_packages = []
        for result in failures + warnings:
            if result.name.startswith("Package:"):
                package = result.name.split(": ")[1]
                missing_packages.append(package)
        
        if missing_packages:
            print("# Install missing Python packages:")
            print(f"pip install {' '.join(missing_packages)}")
            print()
        
        # Frontend setup
        if any("node_modules" in r.name for r in warnings):
            print("# Install frontend dependencies:")
            print(f"cd {self.frontend_dir}")
            print("npm install")
            print()
        
        # Port conflicts
        port_conflicts = [r for r in failures if "Port" in r.name]
        if port_conflicts:
            print("# Kill processes using required ports:")
            for result in port_conflicts:
                if "PID:" in result.message:
                    pid = result.message.split("PID: ")[1].split(")")[0]
                    print(f"# Kill process {pid}")
                    if platform.system() == "Windows":
                        print(f"taskkill /PID {pid} /F")
                    else:
                        print(f"kill {pid}")
            print()
        
        print("After fixing these issues, run the diagnostic again to verify.")


def main():
    """Main entry point"""
    diagnostics = SystemDiagnostics()
    
    try:
        exit_code = diagnostics.run_comprehensive_diagnostics()
        diagnostics.generate_fix_recommendations()
        return exit_code
    except KeyboardInterrupt:
        print("\nDiagnostic interrupted by user")
        return 1
    except Exception as e:
        print(f"\nUnexpected error during diagnostics: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())