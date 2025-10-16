#!/usr/bin/env python3
"""
Electron Setup Verification Script
Verifies that the entire codebase is properly configured for Electron frontend
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class ElectronSetupVerifier:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.frontend_dir = self.root_dir / "frontend" / "electron-react-app"
        self.src_dir = self.root_dir / "src"
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def log(self, message: str, level: str = "INFO"):
        """Log with color coding"""
        colors = {
            "INFO": "\033[94m",
            "SUCCESS": "\033[92m",
            "WARNING": "\033[93m",
            "ERROR": "\033[91m",
            "RESET": "\033[0m"
        }
        
        color = colors.get(level, colors["INFO"])
        reset = colors["RESET"]
        print(f"{color}{level}: {message}{reset}")

    def check_file_exists(self, file_path: Path, description: str) -> bool:
        """Check if a file exists"""
        if file_path.exists():
            self.log(f"✓ {description}: {file_path}", "SUCCESS")
            return True
        else:
            self.log(f"✗ {description} missing: {file_path}", "ERROR")
            self.errors.append(f"Missing {description}: {file_path}")
            return False

    def check_directory_exists(self, dir_path: Path, description: str) -> bool:
        """Check if a directory exists"""
        if dir_path.exists() and dir_path.is_dir():
            self.log(f"✓ {description}: {dir_path}", "SUCCESS")
            return True
        else:
            self.log(f"✗ {description} missing: {dir_path}", "ERROR")
            self.errors.append(f"Missing {description}: {dir_path}")
            return False

    def check_python_dependencies(self) -> bool:
        """Check Python dependencies"""
        self.log("Checking Python dependencies...", "INFO")
        
        required_packages = [
            "fastapi", "uvicorn", "sqlalchemy", "pydantic", 
            "requests", "psutil", "structlog"
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package)
                self.log(f"✓ {package}", "SUCCESS")
            except ImportError:
                self.log(f"✗ {package}", "ERROR")
                missing.append(package)
        
        if missing:
            self.errors.append(f"Missing Python packages: {', '.join(missing)}")
            return False
        
        return True

    def check_node_environment(self) -> bool:
        """Check Node.js and npm"""
        self.log("Checking Node.js environment...", "INFO")
        
        try:
            # Check Node.js
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.log(f"✓ Node.js {result.stdout.strip()}", "SUCCESS")
            else:
                self.log("✗ Node.js not working", "ERROR")
                self.errors.append("Node.js not working")
                return False
        except FileNotFoundError:
            self.log("✗ Node.js not installed", "ERROR")
            self.errors.append("Node.js not installed")
            return False
        
        try:
            # Check npm
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.log(f"✓ npm {result.stdout.strip()}", "SUCCESS")
            else:
                self.log("✗ npm not working", "ERROR")
                self.errors.append("npm not working")
                return False
        except FileNotFoundError:
            self.log("✗ npm not installed", "ERROR")
            self.errors.append("npm not installed")
            return False
        
        return True

    def check_frontend_structure(self) -> bool:
        """Check frontend directory structure"""
        self.log("Checking frontend structure...", "INFO")
        
        success = True
        
        # Check main directories
        required_dirs = [
            (self.frontend_dir, "Frontend root directory"),
            (self.frontend_dir / "src", "Frontend source directory"),
            (self.frontend_dir / "electron", "Electron main process directory"),
            (self.frontend_dir / "public", "Public assets directory"),
        ]
        
        for dir_path, description in required_dirs:
            if not self.check_directory_exists(dir_path, description):
                success = False
        
        # Check main files
        required_files = [
            (self.frontend_dir / "package.json", "Package.json"),
            (self.frontend_dir / "electron" / "main.js", "Electron main process"),
            (self.frontend_dir / "electron" / "preload.js", "Electron preload script"),
            (self.frontend_dir / "src" / "index.tsx", "React entry point"),
            (self.frontend_dir / "src" / "app" / "App.tsx", "Main App component"),
            (self.frontend_dir / ".env", "Environment configuration"),
        ]
        
        for file_path, description in required_files:
            if not self.check_file_exists(file_path, description):
                success = False
        
        return success

    def check_package_json(self) -> bool:
        """Check package.json configuration"""
        self.log("Checking package.json configuration...", "INFO")
        
        package_json_path = self.frontend_dir / "package.json"
        if not package_json_path.exists():
            self.errors.append("package.json not found")
            return False
        
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            # Check main field
            if package_data.get("main") == "electron/main.js":
                self.log("✓ Main field correctly set", "SUCCESS")
            else:
                self.log("✗ Main field incorrect", "ERROR")
                self.errors.append("package.json main field should be 'electron/main.js'")
                return False
            
            # Check scripts
            scripts = package_data.get("scripts", {})
            required_scripts = ["dev", "start:electron", "electron:dev"]
            
            for script in required_scripts:
                if script in scripts:
                    self.log(f"✓ Script '{script}' found", "SUCCESS")
                else:
                    self.log(f"✗ Script '{script}' missing", "ERROR")
                    self.errors.append(f"Missing npm script: {script}")
            
            # Check dependencies
            deps = package_data.get("dependencies", {})
            dev_deps = package_data.get("devDependencies", {})
            all_deps = {**deps, **dev_deps}
            
            required_deps = [
                "electron", "react", "react-dom", "react-router-dom",
                "@tanstack/react-query", "concurrently", "wait-on"
            ]
            
            for dep in required_deps:
                if dep in all_deps:
                    self.log(f"✓ Dependency '{dep}' found", "SUCCESS")
                else:
                    self.log(f"✗ Dependency '{dep}' missing", "ERROR")
                    self.errors.append(f"Missing dependency: {dep}")
            
            return True
            
        except json.JSONDecodeError:
            self.log("✗ package.json is not valid JSON", "ERROR")
            self.errors.append("package.json is not valid JSON")
            return False
        except Exception as e:
            self.log(f"✗ Error reading package.json: {e}", "ERROR")
            self.errors.append(f"Error reading package.json: {e}")
            return False

    def check_api_configuration(self) -> bool:
        """Check API configuration for Electron support"""
        self.log("Checking API configuration...", "INFO")
        
        api_main_path = self.src_dir / "api" / "main.py"
        if not api_main_path.exists():
            self.errors.append("API main.py not found")
            return False
        
        try:
            with open(api_main_path, 'r') as f:
                content = f.read()
            
            # Check CORS configuration
            if "CORSMiddleware" in content:
                self.log("✓ CORS middleware found", "SUCCESS")
            else:
                self.log("✗ CORS middleware missing", "ERROR")
                self.errors.append("CORS middleware not configured")
                return False
            
            # Check for Electron-specific origins
            if "app://" in content or "file://" in content:
                self.log("✓ Electron origins configured", "SUCCESS")
            else:
                self.log("⚠ Electron origins may not be configured", "WARNING")
                self.warnings.append("Electron-specific CORS origins may be missing")
            
            return True
            
        except Exception as e:
            self.log(f"✗ Error reading API configuration: {e}", "ERROR")
            self.errors.append(f"Error reading API configuration: {e}")
            return False

    def check_environment_files(self) -> bool:
        """Check environment configuration files"""
        self.log("Checking environment configuration...", "INFO")
        
        success = True
        
        # Check .env file
        env_path = self.frontend_dir / ".env"
        if env_path.exists():
            self.log("✓ .env file found", "SUCCESS")
            
            try:
                with open(env_path, 'r') as f:
                    env_content = f.read()
                
                required_vars = [
                    "REACT_APP_API_URL", "COMPLIANCE_API_URL", 
                    "ELECTRON_IS_DEV", "PORT"
                ]
                
                for var in required_vars:
                    if var in env_content:
                        self.log(f"✓ Environment variable '{var}' found", "SUCCESS")
                    else:
                        self.log(f"✗ Environment variable '{var}' missing", "ERROR")
                        self.errors.append(f"Missing environment variable: {var}")
                        success = False
                        
            except Exception as e:
                self.log(f"✗ Error reading .env file: {e}", "ERROR")
                self.errors.append(f"Error reading .env file: {e}")
                success = False
        else:
            self.log("✗ .env file missing", "ERROR")
            self.errors.append(".env file missing")
            success = False
        
        return success

    def check_startup_scripts(self) -> bool:
        """Check startup scripts"""
        self.log("Checking startup scripts...", "INFO")
        
        startup_scripts = [
            (self.root_dir / "start_electron_app.py", "Electron startup script"),
            (self.root_dir / "robust_startup.py", "Robust startup script"),
        ]
        
        success = True
        for script_path, description in startup_scripts:
            if not self.check_file_exists(script_path, description):
                success = False
        
        return success

    def run_verification(self) -> bool:
        """Run complete verification"""
        print("=" * 80)
        print("🔍 ELECTRON SETUP VERIFICATION")
        print("=" * 80)
        
        checks = [
            ("Python Dependencies", self.check_python_dependencies),
            ("Node.js Environment", self.check_node_environment),
            ("Frontend Structure", self.check_frontend_structure),
            ("Package.json Configuration", self.check_package_json),
            ("API Configuration", self.check_api_configuration),
            ("Environment Files", self.check_environment_files),
            ("Startup Scripts", self.check_startup_scripts),
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            print(f"\n--- {check_name} ---")
            try:
                if not check_func():
                    all_passed = False
            except Exception as e:
                self.log(f"✗ Check failed with exception: {e}", "ERROR")
                self.errors.append(f"{check_name} failed: {e}")
                all_passed = False
        
        # Summary
        print("\n" + "=" * 80)
        if all_passed and not self.errors:
            self.log("✅ ALL CHECKS PASSED - ELECTRON SETUP IS COMPLETE!", "SUCCESS")
            if self.warnings:
                print("\nWarnings:")
                for warning in self.warnings:
                    self.log(f"⚠ {warning}", "WARNING")
        else:
            self.log("❌ SETUP VERIFICATION FAILED", "ERROR")
            if self.errors:
                print("\nErrors that need to be fixed:")
                for error in self.errors:
                    self.log(f"✗ {error}", "ERROR")
            if self.warnings:
                print("\nWarnings:")
                for warning in self.warnings:
                    self.log(f"⚠ {warning}", "WARNING")
        
        print("=" * 80)
        return all_passed and not self.errors


def main():
    """Main entry point"""
    verifier = ElectronSetupVerifier()
    success = verifier.run_verification()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())