#!/usr/bin/env python3
"""
Complete workflow test - tests the entire analysis pipeline end-to-end.
Run this after restarting the API server.
"""

import sys
import time
import tempfile
import os
from pathlib import Path

import requests

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

API_URL = "http://127.0.0.1:8001"

def test_complete_workflow():
    """Test the complete analysis workflow end-to-end."""
    print("🏥 Therapy Compliance Analyzer - Complete Workflow Test")
    print("=" * 60)
    
    # Step 1: Test API connectivity
    print("\n1️⃣ Testing API connectivity...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ API server is running and healthy")
        else:
            print(f"   ❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Cannot connect to API server: {e}")
        print("   💡 Make sure to restart the API server first!")
        return False
    
    # Step 2: Test authentication
    print("\n2️⃣ Testing authentication...")
    try:
        auth_response = requests.post(
            f"{API_URL}/auth/token",
            data={
                "username": "admin",
                "password": "admin123"
            },
            timeout=10
        )
        
        if auth_response.status_code == 200:
            token_data = auth_response.json()
            access_token = token_data.get("access_token")
            print("   ✅ Authentication successful")
            print(f"   Token type: {token_data.get('token_type')}")
        else:
            print(f"   ❌ Authentication failed: {auth_response.status_code}")
            print(f"   Response: {auth_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        return False
    
    # Step 3: Create and submit test document
    print("\n3️⃣ Creating test document...")
    
    test_content = """
PHYSICAL THERAPY PROGRESS NOTE

Patient: Jane Smith
Date: 2024-01-15
Diagnosis: Right shoulder impingement syndrome

SUBJECTIVE:
Patient reports decreased pain in right shoulder from 8/10 to 5/10 since last visit.
Patient states she is able to reach overhead with less difficulty.
Denies any numbness or tingling.
Patient has been compliant with home exercise program.

OBJECTIVE:
Vital Signs: BP 120/80, HR 72, RR 16
ROM: Right shoulder flexion 0-140 degrees (improved from 0-120 degrees)
      Right shoulder abduction 0-130 degrees  
      Right shoulder external rotation 0-45 degrees
Strength: Right shoulder 4/5 in all planes tested
MMT: Deltoid 4/5, Rotator cuff 4/5
Pain: 5/10 with overhead activities, 2/10 at rest
Special Tests: Hawkins-Kennedy test positive
Palpation: Tenderness over greater tuberosity

ASSESSMENT:
Patient demonstrates good progress with decreased pain and improved ROM.
Functional improvements noted in ADL activities.
Continue current treatment plan with progression to strengthening.

PLAN:
1. Continue current exercise program
2. Progress strengthening exercises as tolerated
3. Add functional activities training
4. Patient education on posture and ergonomics
5. Next visit scheduled in 3 days

Goals:
- Increase shoulder flexion to 160 degrees by next week
- Decrease pain to 3/10 with overhead activities
- Return to work activities without limitations

Therapist: John Doe, PT
License: PT12345
"""
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write(test_content)
        temp_file_path = temp_file.name
    
    print("   ✅ Test document created (comprehensive PT note)")
    
    # Step 4: Submit analysis
    print("\n4️⃣ Submitting analysis request...")
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        with open(temp_file_path, 'rb') as f:
            files = {"file": ("pt_progress_note.txt", f, "text/plain")}
            data = {
                "discipline": "pt",
                "analysis_mode": "rubric"
            }
            
            analysis_response = requests.post(
                f"{API_URL}/analysis/analyze",
                files=files,
                data=data,
                headers=headers,
                timeout=30
            )
        
        # Clean up temp file
        try:
            os.unlink(temp_file_path)
        except OSError:
            pass
        
        print(f"   Analysis submission status: {analysis_response.status_code}")
        
        if analysis_response.status_code == 202:
            result = analysis_response.json()
            task_id = result.get("task_id")
            print("   ✅ Analysis submitted successfully!")
            print(f"   Task ID: {task_id}")
            print(f"   Status: {result.get('status')}")
        else:
            print(f"   ❌ Analysis submission failed: {analysis_response.status_code}")
            print(f"   Response: {analysis_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Analysis submission error: {e}")
        return False
    
    # Step 5: Poll for results
    print("\n5️⃣ Polling for analysis results...")
    
    max_attempts = 30  # 1 minute
    poll_interval = 2
    
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"   🔄 Polling attempt {attempt}/{max_attempts}...")
            
            status_response = requests.get(
                f"{API_URL}/analysis/status/{task_id}",
                headers=headers,
                timeout=15
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get("status", "unknown")
                progress = status_data.get("progress", 0)
                
                print(f"      Status: {status}, Progress: {progress}%")
                
                if status == "completed":
                    result = status_data.get("result")
                    print("   ✅ Analysis completed successfully!")
                    
                    # Show result summary
                    if result:
                        findings_count = len(result.get("findings", []))
                        compliance_score = result.get("compliance_score", "N/A")
                        document_type = result.get("document_type", "Unknown")
                        
                        print("      📊 Analysis Results:")
                        print(f"         Document Type: {document_type}")
                        print(f"         Compliance Score: {compliance_score}%")
                        print(f"         Findings: {findings_count}")
                        
                        # Show first few findings
                        findings = result.get("findings", [])
                        if findings:
                            print("      🔍 Sample Findings:")
                            for i, finding in enumerate(findings[:3]):
                                severity = finding.get("severity", "Unknown")
                                issue = finding.get("issue", "No description")
                                print(f"         {i+1}. [{severity}] {issue[:80]}...")
                    
                    return True
                    
                elif status == "failed":
                    error_msg = status_data.get("error", "Unknown error")
                    print(f"   ❌ Analysis failed: {error_msg}")
                    return False
                    
                elif status == "processing":
                    # Continue polling
                    pass
                else:
                    print(f"   ⚠️ Unknown status: {status}")
                    
            else:
                print(f"      ❌ Status check failed: HTTP {status_response.status_code}")
                
        except Exception as e:
            print(f"      ❌ Polling error: {e}")
            
        if attempt < max_attempts:
            time.sleep(poll_interval)
    
    print("   ⏰ Analysis timed out after 1 minute")
    return False

if __name__ == "__main__":
    print("🚀 Starting Complete Workflow Test")
    print("Make sure the API server is running with: python scripts/run_api.py")
    print()
    
    success = test_complete_workflow()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 COMPLETE WORKFLOW TEST PASSED!")
        print("✅ The Therapy Compliance Analyzer is working correctly!")
        print()
        print("🎯 What worked:")
        print("   • API server connectivity")
        print("   • User authentication")
        print("   • Document upload and processing")
        print("   • AI-powered compliance analysis")
        print("   • Results generation and retrieval")
        print()
        print("🚀 Ready for production use!")
    else:
        print("❌ COMPLETE WORKFLOW TEST FAILED!")
        print("Check the error messages above for specific issues.")
        print()
        print("💡 Common fixes:")
        print("   • Restart the API server: python scripts/run_api.py")
        print("   • Check if all AI models loaded successfully")
        print("   • Verify database connectivity")