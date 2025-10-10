#!/usr/bin/env python3
"""
E2E Test Runner

Comprehensive end-to-end test execution with proper setup and teardown.
"""

import sys
import subprocess
import time
import requests
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def check_api_server(max_attempts=5, delay=2):
    """Check if the API server is running."""
    print("Checking API server availability...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://127.0.0.1:8001/health", timeout=5)
            if response.status_code == 200:
                print("✅ API server is running and accessible!")
                return True
        except requests.exceptions.RequestException as e:
            print(f"   Attempt {attempt + 1}/{max_attempts}: API not ready ({e})")
        
        if attempt < max_attempts - 1:
            time.sleep(delay)
    
    print("❌ API server is not accessible")
    return False


def run_e2e_tests():
    """Run the complete E2E test suite."""
    print("🧪 Starting End-to-End Test Suite")
    print("=" * 50)
    
    # Check prerequisites
    if not check_api_server():
        print("\n❌ Prerequisites not met. Please start the API server first:")
        print("   python scripts/run_api.py")
        return False
    
    # Run E2E tests
    print("\n🚀 Running E2E Tests...")
    
    test_commands = [
        # Core workflow tests (Priority 1)
        ["pytest", "tests/e2e/test_document_analysis_workflow.py", "-v", "--tb=short"],
        
        # Enterprise feature tests (Priority 2)
        ["pytest", "tests/e2e/test_enterprise_copilot_workflow.py", "-v", "--tb=short"],
        
        # Plugin system tests (Priority 3)
        ["pytest", "tests/e2e/test_plugin_system_workflow.py", "-v", "--tb=short"],
    ]
    
    results = []
    
    for i, cmd in enumerate(test_commands, 1):
        test_name = cmd[1].split('/')[-1].replace('.py', '')
        print(f"\n📋 Running Test Suite {i}/{len(test_commands)}: {test_name}")
        print("-" * 40)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                print(f"✅ {test_name}: PASSED")
                results.append((test_name, "PASSED", result.stdout))
            else:
                print(f"❌ {test_name}: FAILED")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                results.append((test_name, "FAILED", result.stderr))
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_name}: TIMEOUT")
            results.append((test_name, "TIMEOUT", "Test suite timed out after 10 minutes"))
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
            results.append((test_name, "ERROR", str(e)))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 E2E Test Results Summary")
    print("=" * 50)
    
    passed = sum(1 for _, status, _ in results if status == "PASSED")
    total = len(results)
    
    for test_name, status, details in results:
        status_emoji = {
            "PASSED": "✅",
            "FAILED": "❌", 
            "TIMEOUT": "⏰",
            "ERROR": "💥"
        }
        print(f"{status_emoji.get(status, '❓')} {test_name}: {status}")
    
    print(f"\n📈 Overall Results: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 ALL E2E TESTS PASSED! System is ready for production.")
        return True
    else:
        print(f"⚠️  {total - passed} test suite(s) failed. Review issues above.")
        return False


def run_quick_e2e_tests():
    """Run a quick subset of E2E tests for rapid validation."""
    print("⚡ Running Quick E2E Test Suite")
    print("=" * 40)
    
    if not check_api_server():
        print("❌ API server not available")
        return False
    
    # Run only the most critical test
    cmd = ["pytest", "tests/e2e/test_document_analysis_workflow.py::TestDocumentAnalysisWorkflow::test_complete_analysis_workflow", "-v"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Quick E2E test PASSED!")
            return True
        else:
            print("❌ Quick E2E test FAILED!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Quick E2E test TIMEOUT!")
        return False
    except Exception as e:
        print(f"💥 Quick E2E test ERROR: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run E2E tests for Therapy Compliance Analyzer")
    parser.add_argument("--quick", action="store_true", help="Run quick E2E tests only")
    parser.add_argument("--check-server", action="store_true", help="Only check if API server is running")
    
    args = parser.parse_args()
    
    if args.check_server:
        success = check_api_server()
        sys.exit(0 if success else 1)
    elif args.quick:
        success = run_quick_e2e_tests()
        sys.exit(0 if success else 1)
    else:
        success = run_e2e_tests()
        sys.exit(0 if success else 1)