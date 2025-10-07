#!/usr/bin/env python3
"""
Test script to verify the analysis workflow is working properly.
This script tests the analysis workflow without the GUI to isolate issues.
"""

import sys
import time
from pathlib import Path

import requests

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.analysis_diagnostics import diagnostics
from src.core.analysis_status_tracker import AnalysisState, status_tracker
from src.core.analysis_workflow_logger import workflow_logger

API_URL = "http://127.0.0.1:8001"


def get_auth_token() -> str | None:
    """Get authentication token for API requests."""
    try:
        # Try to login with default test credentials
        response = requests.post(
            f"{API_URL}/auth/token",
            data={"username": "admin", "password": "admin123"},
            timeout=10,
        )

        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            print(f"   ❌ Authentication failed: {response.status_code}")
            return None

    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        return None


def _run_system_diagnostics() -> bool:
    """Run system diagnostics and return True if all pass."""
    print("\n1️⃣ Running system diagnostics...")
    diagnostic_results = diagnostics.run_full_diagnostic()

    for component, result in diagnostic_results.items():
        status_icon = (
            "✅"
            if result.status.value == "healthy"
            else "⚠️"
            if result.status.value == "warning"
            else "❌"
        )
        print(f"   {status_icon} {component}: {result.message}")

    # Check for critical issues
    critical_issues = [
        r for r in diagnostic_results.values() if r.status.value == "error"
    ]
    if critical_issues:
        print(f"\n❌ Critical issues found: {len(critical_issues)}")
        for issue in critical_issues:
            print(f"   • {issue.component}: {issue.message}")
        return False

    print("✅ All diagnostics passed!")
    return True


def _find_valid_test_file() -> str | None:
    """Find a valid test file for analysis."""
    print("\n3️⃣ Testing file validation...")
    test_files = [
        "test_data/sample_document.txt",
        "README.md",  # Should exist
        "nonexistent_file.txt",  # Should not exist
    ]

    for test_file in test_files:
        if Path(test_file).exists():
            validation_result = diagnostics.validate_file_format(test_file)
            status_icon = (
                "✅"
                if validation_result.status.value == "healthy"
                else "⚠️"
                if validation_result.status.value == "warning"
                else "❌"
            )
            print(f"   {status_icon} {test_file}: {validation_result.message}")

            if validation_result.status.value in ["healthy", "warning"]:
                return test_file

    print("❌ No valid test file found")
    return None


def _submit_analysis_request(valid_file: str, auth_token: str) -> str | None:
    """Submit analysis request and return task_id if successful."""
    print(f"\n4️⃣ Testing analysis submission with file: {valid_file}")

    # Start workflow tracking
    session_id = workflow_logger.log_analysis_start(
        valid_file, "test_rubric", "test_user"
    )
    status_tracker.start_tracking(session_id, valid_file, "test_rubric")

    try:
        # Prepare test document content
        with open(valid_file, "r", encoding="utf-8") as f:
            content = f.read()[:1000]  # First 1000 chars

        # Submit analysis request
        print("   📤 Submitting analysis request...")
        workflow_logger.log_api_request("/analysis/analyze", "POST")

        # Create a temporary file for the request
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            headers = {"Authorization": f"Bearer {auth_token}"}
            with open(temp_file_path, "rb") as f:
                files = {"file": ("test_document.txt", f, "text/plain")}
                data = {"discipline": "pt", "analysis_mode": "rubric"}
                response = requests.post(
                    f"{API_URL}/analysis/analyze",
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=30,
                )
        finally:
            # Clean up temp file
            import os

            try:
                os.unlink(temp_file_path)
            except OSError:
                pass

        workflow_logger.log_api_response(
            response.status_code, response.json() if response.content else None
        )

        if response.status_code == 202:
            result = response.json()
            task_id = result.get("task_id")

            if task_id:
                print(
                    f"   ✅ Analysis submitted successfully! Task ID: {task_id[:8]}..."
                )
                status_tracker.set_task_id(task_id)
                status_tracker.update_status(
                    AnalysisState.PROCESSING, 20, "Analysis submitted"
                )
                return task_id

            print("   ❌ No task ID returned")
            return None

        print(f"   ❌ Analysis submission failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

    except requests.RequestException as e:
        print(f"   ❌ Analysis submission error: {e}")
        workflow_logger.log_workflow_completion(False, error=str(e))
        return None


def test_analysis_workflow() -> bool:
    """Test the complete analysis workflow."""
    print("🧪 Testing Analysis Workflow")
    print("=" * 50)

    # Step 1: Run diagnostics
    if not _run_system_diagnostics():
        return False

    # Step 2: Get authentication token
    print("\n2️⃣ Getting authentication token...")
    auth_token = get_auth_token()
    if not auth_token:
        print("❌ Failed to get authentication token")
        return False
    print("✅ Authentication successful")

    # Step 3: Find valid test file
    valid_file = _find_valid_test_file()
    if not valid_file:
        return False

    # Step 4: Submit analysis request
    task_id = _submit_analysis_request(valid_file, auth_token)
    if not task_id:
        return False

    # Step 5: Test polling
    print(f"\n5️⃣ Testing status polling for task: {task_id[:8]}...")
    return test_polling(task_id, auth_token)


def test_polling(task_id: str, auth_token: str) -> bool:
    """Test the polling mechanism."""
    max_attempts = 30  # 1 minute
    poll_interval = 2

    for attempt in range(1, max_attempts + 1):
        try:
            print(f"   🔄 Polling attempt {attempt}/{max_attempts}...")
            workflow_logger.log_polling_attempt(task_id, attempt)

            headers = {"Authorization": f"Bearer {auth_token}"}
            response = requests.get(
                f"{API_URL}/analysis/status/{task_id}", headers=headers, timeout=15
            )
            workflow_logger.log_api_response(
                response.status_code, response.json() if response.content else None
            )

            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get("status", "unknown")
                progress = status_data.get("progress", 0)

                print(f"      Status: {status}, Progress: {progress}%")

                if status == "completed":
                    result = status_data.get("result")
                    print("   ✅ Analysis completed successfully!")
                    workflow_logger.log_workflow_completion(True, result)
                    status_tracker.complete_analysis(result)

                    # Show result summary
                    if result:
                        findings_count = len(result.get("findings", []))
                        compliance_score = result.get("compliance_score", "N/A")
                        print(
                            f"      📊 Results: {findings_count} findings, "
                            f"{compliance_score}% compliance"
                        )

                    return True

                if status == "failed":
                    error_msg = status_data.get("error", "Unknown error")
                    print(f"   ❌ Analysis failed: {error_msg}")
                    workflow_logger.log_workflow_completion(False, error=error_msg)
                    status_tracker.set_error(error_msg)
                    return False

                if status == "processing":
                    status_tracker.update_status(
                        AnalysisState.PROCESSING, progress, f"Processing... {progress}%"
                    )

            else:
                print(f"      ❌ Polling failed: HTTP {response.status_code}")

        except requests.RequestException as e:
            print(f"      ❌ Polling error: {e}")

        if attempt < max_attempts:
            time.sleep(poll_interval)

    print("   ⏰ Analysis timed out")
    workflow_logger.log_workflow_timeout(max_attempts * poll_interval)
    status_tracker.update_status(AnalysisState.TIMEOUT, 100, "Timed out")
    return False


def main() -> None:
    """Main function to run the analysis workflow test."""
    print("🏥 Therapy Compliance Analyzer - Analysis Workflow Test")
    print("This script tests the analysis workflow to identify issues.")
    print()

    test_success = test_analysis_workflow()

    print("\n" + "=" * 50)
    if test_success:
        print("🎉 Analysis workflow test PASSED!")
        print("The analysis system is working correctly.")
    else:
        print("❌ Analysis workflow test FAILED!")
        print("Check the logs above for specific issues.")

        # Show status tracker summary
        summary = status_tracker.get_status_summary()
        print(f"\nFinal Status: {summary['state']}")
        if summary["error_message"]:
            print(f"Error: {summary['error_message']}")

    print("\n💡 Next steps:")
    if test_success:
        print("• The analysis workflow is working - the GUI issue may be elsewhere")
        print("• Check GUI event handling and result display")
    else:
        print("• Fix the identified issues in the analysis pipeline")
        print("• Check API server logs for more details")
        print("• Verify AI models are loaded correctly")


if __name__ == "__main__":
    main()
