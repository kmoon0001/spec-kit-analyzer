#!/usr/bin/env python3
"""
End-to-end test runner with consistent console output for CI and local use.
"""

import subprocess
import sys
import time
from pathlib import Path
import os

import requests

# Ensure project root is importable when the script is launched directly
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("USE_AI_MOCKS", "1")


STATUS_LABELS = {
    "PASSED": "[OK]",
    "FAILED": "[FAIL]",
    "TIMEOUT": "[TIMEOUT]",
    "ERROR": "[ERROR]",
}


def check_api_server(max_attempts: int = 5, delay: int = 2) -> bool:
    """Poll the FastAPI health endpoint until it responds or we time out."""
    print("[INFO] Checking API server availability...")

    for attempt in range(max_attempts):
        try:
            response = requests.get("http://127.0.0.1:8001/health", timeout=5)
            if response.status_code == 200:
                print("[OK] API server is running and accessible!")
                return True
        except requests.exceptions.RequestException as exc:
            print(f"   Attempt {attempt + 1}/{max_attempts}: API not ready ({exc})")

        if attempt < max_attempts - 1:
            time.sleep(delay)

    print("[FAIL] API server is not accessible")
    return False


def run_e2e_tests() -> bool:
    """Run the complete E2E suite and summarise the results."""
    print("[RUN] Starting End-to-End Test Suite")
    print("=" * 50)

    if not check_api_server():
        print("\n[FAIL] Prerequisites not met. Please start the API server first:")
        print("   python scripts/run_api.py")
        return False

    print("\n[RUN] Running E2E Tests...")

    test_commands = [
        ["pytest", "tests/e2e/test_document_analysis_workflow.py", "-v", "--tb=short"],
        ["pytest", "tests/e2e/test_plugin_system_workflow.py", "-v", "--tb=short"],
    ]

    results: list[tuple[str, str, str]] = []

    for index, cmd in enumerate(test_commands, 1):
        test_name = cmd[1].split("/")[-1].replace(".py", "")
        print(f"\n[RUN] Running Test Suite {index}/{len(test_commands)}: {test_name}")
        print("-" * 40)

        try:
            completed = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        except subprocess.TimeoutExpired:
            print(f"[TIMEOUT] {test_name}: TIMEOUT")
            results.append((test_name, "TIMEOUT", "Test suite timed out after 10 minutes"))
            continue
        except Exception as exc:  # pragma: no cover - protects subprocess invocation
            print(f"[ERROR] {test_name}: ERROR - {exc}")
            results.append((test_name, "ERROR", str(exc)))
            continue

        if completed.returncode == 0:
            print(f"[OK] {test_name}: PASSED")
            results.append((test_name, "PASSED", completed.stdout))
        else:
            print(f"[FAIL] {test_name}: FAILED")
            print("STDOUT:", completed.stdout)
            print("STDERR:", completed.stderr)
            results.append((test_name, "FAILED", completed.stderr))

    print("\n" + "=" * 50)
    print("[SUMMARY] E2E Test Results Summary")
    print("=" * 50)

    passed = sum(1 for _, status, _ in results if status == "PASSED")
    total = len(results)

    for test_name, status, _details in results:
        label = STATUS_LABELS.get(status, "[INFO]")
        print(f"{label} {test_name}: {status}")

    print(f"\n[SUMMARY] Overall Results: {passed}/{total} test suites passed")

    if passed == total and total > 0:
        print("[SUCCESS] ALL E2E TESTS PASSED! System is ready for production.")
        return True

    print(f"[FAIL] {total - passed} test suite(s) failed. Review issues above.")
    return False


def run_quick_e2e_tests() -> bool:
    """Run the most critical workflow test for a quick health check."""
    print("[RUN] Running Quick E2E Test Suite")
    print("=" * 40)

    if not check_api_server():
        print("[WARN] API server not available")
        return False

    cmd = [
        "pytest",
        "tests/e2e/test_document_analysis_workflow.py::TestDocumentAnalysisWorkflow::test_complete_analysis_workflow",
        "-v",
    ]

    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] Quick E2E test timed out after 5 minutes")
        return False
    except Exception as exc:  # pragma: no cover - protects subprocess invocation
        print(f"[ERROR] Quick E2E test errored: {exc}")
        return False

    if completed.returncode == 0:
        print("[OK] Quick E2E test PASSED!")
        return True

    print("[FAIL] Quick E2E test FAILED!")
    print("STDOUT:", completed.stdout)
    print("STDERR:", completed.stderr)
    return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run E2E tests for Therapy Compliance Analyzer")
    parser.add_argument("--quick", action="store_true", help="Run quick E2E tests only")
    parser.add_argument("--check-server", action="store_true", help="Only check if API server is running")

    arguments = parser.parse_args()

    if arguments.check_server:
        success = check_api_server()
        sys.exit(0 if success else 1)
    if arguments.quick:
        success = run_quick_e2e_tests()
        sys.exit(0 if success else 1)

    success = run_e2e_tests()
    sys.exit(0 if success else 1)
