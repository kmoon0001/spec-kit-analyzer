#!/usr/bin/env python3
"""
Therapy Compliance Analyzer - Debug Tools
Comprehensive debugging utilities for API and GUI components.
"""

import sys
import asyncio
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, List

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

class DebugManager:
    """Centralized debugging manager for the Therapy Compliance Analyzer."""
    
    def __init__(self):
        self.setup_logging()
        self.debug_info = {}
        
    def setup_logging(self):
        """Setup comprehensive logging for debugging."""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('debug.log', mode='w'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('debug')
        
    def debug_api_startup(self):
        """Debug API startup process step by step."""
        print("DEBUGGING API STARTUP")
        print("=" * 50)
        
        try:
            # Step 1: Import check
            print("1. Testing imports...")
            from fastapi import FastAPI
            print("   [OK] FastAPI imported")
            
            from src.api.main import app
            print("   [OK] API app imported")
            
            # Step 2: Configuration check
            print("2. Checking configuration...")
            from src.config import settings
            print(f"   ✓ Config loaded: {settings.get('app_name', 'Unknown')}")
            print(f"   ✓ Use AI Mocks: {settings.get('use_ai_mocks', 'Unknown')}")
            
            # Step 3: Database check
            print("3. Testing database...")
            from src.database.database import init_db
            print("   ✓ Database module imported")
            
            # Step 4: AI Services check
            print("4. Testing AI services...")
            from src.core.analysis_service import AnalysisService
            print("   ✓ AnalysisService imported")
            
            # Step 5: Lifespan test
            print("5. Testing lifespan events...")
            from src.api.main import lifespan
            print("   ✓ Lifespan function imported")
            
            print("\n✅ API startup components are ready!")
            return True
            
        except Exception as e:
            print(f"\n❌ API startup failed: {e}")
            traceback.print_exc()
            return False
    
    def debug_gui_startup(self):
        """Debug GUI startup process."""
        print("\n🖥️ DEBUGGING GUI STARTUP")
        print("=" * 50)
        
        try:
            # Step 1: PySide6 check
            print("1. Testing PySide6...")
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import QThread
            print("   ✓ PySide6 imported")
            
            # Step 2: GUI components check
            print("2. Testing GUI components...")
            from src.gui.main_window import MainWindow
            print("   ✓ MainWindow imported")
            
            from src.gui.components.analysis_tab_builder import AnalysisTabBuilder
            print("   ✓ AnalysisTabBuilder imported")
            
            # Step 3: Theme check
            print("3. Testing theme system...")
            from src.gui.widgets.pycharm_dark_theme import pycharm_theme
            print("   ✓ Theme system imported")
            
            # Step 4: Worker system check
            print("4. Testing worker system...")
            from src.gui.core.base_worker import BaseWorker
            print("   ✓ Worker system imported")
            
            print("\n✅ GUI startup components are ready!")
            return True
            
        except Exception as e:
            print(f"\n❌ GUI startup failed: {e}")
            traceback.print_exc()
            return False
    
    def debug_api_endpoints(self):
        """Debug API endpoints."""
        print("\n🌐 DEBUGGING API ENDPOINTS")
        print("=" * 50)
        
        try:
            from fastapi.testclient import TestClient
            from src.api.main import app
            
            client = TestClient(app)
            
            # Test health endpoint
            print("1. Testing health endpoint...")
            response = client.get("/health")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Response: {response.json()}")
                print("   ✓ Health endpoint working")
            else:
                print(f"   ❌ Health endpoint failed: {response.text}")
            
            # Test auth endpoint
            print("2. Testing auth endpoint...")
            response = client.post("/auth/token", data={"username": "admin", "password": "admin"})
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                token_data = response.json()
                print(f"   ✓ Auth working, token: {token_data.get('access_token', '')[:20]}...")
                return token_data.get('access_token')
            else:
                print(f"   ❌ Auth failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ API endpoint testing failed: {e}")
            traceback.print_exc()
            return None
    
    def debug_ai_models(self):
        """Debug AI model loading."""
        print("\n🤖 DEBUGGING AI MODELS")
        print("=" * 50)
        
        try:
            from src.core.analysis_service import AnalysisService
            from src.core.hybrid_retriever import HybridRetriever
            
            print("1. Testing retriever...")
            retriever = HybridRetriever()
            print("   ✓ Retriever created")
            
            print("2. Testing analysis service...")
            analysis_service = AnalysisService(retriever=retriever)
            print("   ✓ Analysis service created")
            
            print("3. Testing document classifier...")
            if analysis_service.document_classifier:
                result = analysis_service.document_classifier.classify_document("Test document")
                print(f"   ✓ Document classified as: {result}")
            else:
                print("   ⚠️ Document classifier not available")
            
            print("4. Testing NER service...")
            if analysis_service.clinical_ner_service:
                print("   ✓ NER service available")
            else:
                print("   ⚠️ NER service not available")
            
            print("\n✅ AI models are working!")
            return True
            
        except Exception as e:
            print(f"❌ AI model testing failed: {e}")
            traceback.print_exc()
            return False
    
    def debug_system_resources(self):
        """Debug system resource usage."""
        print("\n💻 DEBUGGING SYSTEM RESOURCES")
        print("=" * 50)
        
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            print(f"1. CPU Usage: {cpu_percent}%")
            
            # Memory usage
            memory = psutil.virtual_memory()
            print(f"2. RAM Usage: {memory.percent}% ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)")
            
            # Disk usage
            disk = psutil.disk_usage('.')
            print(f"3. Disk Usage: {disk.percent}% ({disk.free / 1024**3:.1f}GB free)")
            
            # Python processes
            python_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                if 'python' in proc.info['name'].lower():
                    python_processes.append(proc.info)
            
            print(f"4. Python Processes: {len(python_processes)}")
            for proc in python_processes:
                memory_mb = proc['memory_info'].rss / 1024**2
                print(f"   PID {proc['pid']}: {memory_mb:.1f}MB")
            
            return True
            
        except Exception as e:
            print(f"❌ System resource debugging failed: {e}")
            traceback.print_exc()
            return False
    
    def run_full_debug(self):
        """Run complete debugging suite."""
        print("THERAPY COMPLIANCE ANALYZER - FULL DEBUG")
        print("=" * 60)
        
        results = {
            'api_startup': self.debug_api_startup(),
            'gui_startup': self.debug_gui_startup(),
            'api_endpoints': self.debug_api_endpoints(),
            'ai_models': self.debug_ai_models(),
            'system_resources': self.debug_system_resources()
        }
        
        print("\n📊 DEBUG SUMMARY")
        print("=" * 50)
        for test, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test.replace('_', ' ').title()}: {status}")
        
        return results

def main():
    """Main debug function."""
    debug_manager = DebugManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "api":
            debug_manager.debug_api_startup()
        elif command == "gui":
            debug_manager.debug_gui_startup()
        elif command == "endpoints":
            debug_manager.debug_api_endpoints()
        elif command == "ai":
            debug_manager.debug_ai_models()
        elif command == "resources":
            debug_manager.debug_system_resources()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: api, gui, endpoints, ai, resources")
    else:
        debug_manager.run_full_debug()

if __name__ == "__main__":
    main()
