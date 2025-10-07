#!/usr/bin/env python3
"""
Test script to verify the analysis workflow is working properly.
This script tests the analysis workflow without the GUI to isolate issues.
"""

import sys
import time
import requests
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.analysis_workflow_logger import workflow_logger
from src.core.analysis_status_tracker import status_tracker, AnalysisState
from src.core.analysis_diagnostics import diagnostics

API_URL = "http://127.0.0.1:8001"

def test_analysis_workflow():
    """Test the complete analysis workflow."""
    print("🧪 Testing Analysis Workflow")
    print("=" * 50)
    
    # Step 1: Run diagnostics
    print("\n1️⃣ Running system diagnostics...")
    diagnostic_results = diagnostics.run_full_diagnostic()
    
    for component, result in diagnostic_results.items():
        status_icon = "✅" if result.status.value == "healthy" else "⚠️" if result.status.value == "warning" else "❌"
        print(f"   {status_icon} {component}: {result.message}")
    
    # Check for critical issues
    critical_issues = [r for r in diagnostic_results.values() if r.status.value == "error"]
    if critical_issues:
        print(f"\n❌ Critical issues found: {len(critical_issues)}")
        for issue in critical_issues:
            print(f"   • {issue.component}: {issue.message}")
        return False
    
    print("✅ All diagnostics passed!")
    
    # Step 2: Test file validation
    print("\n2️⃣ Testing file validation...")
    test_files = [
        "test_data/sample_document.txt",
        "README.md",  # Should exist
        "nonexistent_file.txt"  # Should not exist
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            validation_result = diagnostics.validate_file_format(test_file)
            status_icon = "✅" if validation_result.status.value == "healthy" else "⚠️" if validation_result.status.value == "warning" else "❌"
            print(f"   {status_icon} {test_file}: {validation_result.message}")
            
            if validation_result.status.value in ["healthy", "warning"]:
                valid_file = test_file
                break
    else:
        print("❌ No valid test file found")
        return False
    
    # Step 3: Test analysis submission
    print(f"\n3️⃣ Testing analysis submission with file: {valid_file}")
    
    # Start workflow tracking
    session_id = workflow_logger.log_analysis_start(valid_file, "test_rubric", "test_user")
    status_tracker.start_tracking(session_id, valid_file, "test_rubric")
    
    try:
        # Prepare test document content
        with open(valid_file, 'r', encoding='utf-8') as f:
            content = f.read()[:1000]  # First 1000 chars
        
        # Submit analysis request
        print("   📤 Submitting analysis request...")
        workflow_logger.log_api_request("/analysis/submit", "POST")
        
        response = requests.post(
            f"{API_URL}/analysis/submit",
            json={
                "content": content,
                "discipline": "pt",
                "analysis_mode": "rubric",
                "session_id": session_id
            },
            timeout=30
        )
        
        workflow_logger.log_api_response(response.status_code, response.json() if response.content else None)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get("task_id")
            
            if task_id:
                print(f"   ✅ Analysis submitted successfully! Task ID: {task_id[:8]}...")
                status_tracker.set_task_id(task_id)
                status_tracker.update_status(AnalysisState.PROCESSING, 20, "Analysis submitted")
                
                # Step 4: Test polling
                print(f"\n4️⃣ Testing status polling for task: {task_id[:8]}...")
                return test_polling(task_id)
            else:
                print("   ❌ No task ID returned")
                return False
        else:
            print(f"   ❌ Analysis submission failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Analysis submission error: {e}")
        workflow_logger.log_workflow_completion(False, error=str(e))
        return False

def test_polling(task_id):
    """Test the polling mechanism."""
    max_attempts = 30  # 1 minute
    poll_interval = 2
    
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"   🔄 Polling attempt {attempt}/{max_attempts}...")
            workflow_logger.log_polling_attempt(task_id, attempt)
            
            response = requests.get(f"{API_URL}/tasks/{task_id}", timeout=15)
            workflow_logger.log_api_response(response.status_code, response.json() if response.content else None)
            
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
                        print(f"      📊 Results: {findings_count} findings, {compliance_score}% compliance")
                    
                    return True
                    
                elif status == "failed":
                    error_msg = status_data.get("error", "Unknown error")
                    print(f"   ❌ Analysis failed: {error_msg}")
                    workflow_logger.log_workflow_completion(False, error=error_msg)
                    status_tracker.set_error(error_msg)
                    return False
                    
                elif status == "processing":
                    status_tracker.update_status(AnalysisState.PROCESSING, progress, f"Processing... {progress}%")
                    
            else:
                print(f"      ❌ Polling failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ Polling error: {e}")
            
        if attempt < max_attempts:
            time.sleep(poll_interval)
    
    print("   ⏰ Analysis timed out")
    workflow_logger.log_workflow_timeout(max_attempts * poll_interval)
    status_tracker.update_status(AnalysisState.TIMEOUT, 100, "Timed out")
    return False

if __name__ == "__main__":
    print("🏥 Therapy Compliance Analyzer - Analysis Workflow Test")
    print("This script tests the analysis workflow to identify issues.")
    print()
    
    success = test_analysis_workflow()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Analysis workflow test PASSED!")
        print("The analysis system is working correctly.")
    else:
        print("❌ Analysis workflow test FAILED!")
        print("Check the logs above for specific issues.")
        
        # Show status tracker summary
        summary = status_tracker.get_status_summary()
        print(f"\nFinal Status: {summary['state']}")
        if summary['error_message']:
            print(f"Error: {summary['error_message']}")
    
    print("\n💡 Next steps:")
    if success:
        print("• The analysis workflow is working - the GUI issue may be elsewhere")
        print("• Check GUI event handling and result display")
    else:
        print("• Fix the identified issues in the analysis pipeline")
        print("• Check API server logs for more details")
        print("• Verify AI models are loaded correctly")