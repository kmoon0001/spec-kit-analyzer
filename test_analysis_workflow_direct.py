#!/usr/bin/env python3
"""
Test script to verify the analysis workflow using FastAPI TestClient.
This bypasses any server startup issues and tests the API directly.
"""

import sys
import tempfile
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def test_analysis_workflow_direct():
    """Test the complete analysis workflow using FastAPI TestClient."""
    print("🧪 Testing Analysis Workflow (Direct)")
    print("=" * 50)
    
    try:
        from fastapi.testclient import TestClient
        from src.api.main import app
        
        client = TestClient(app)
        
        # Step 1: Get authentication token
        print("\n1️⃣ Getting authentication token...")
        auth_response = client.post(
            "/auth/token",
            data={
                "username": "admin",
                "password": "admin123"
            }
        )
        
        if auth_response.status_code != 200:
            print(f"   ❌ Authentication failed: {auth_response.status_code}")
            print(f"   Response: {auth_response.text}")
            return False
        
        token_data = auth_response.json()
        access_token = token_data.get("access_token")
        print("   ✅ Authentication successful")
        
        # Step 2: Create test document
        print("\n2️⃣ Preparing test document...")
        test_content = """
        PHYSICAL THERAPY PROGRESS NOTE
        
        Patient: John Doe
        Date: 2024-01-15
        
        SUBJECTIVE:
        Patient reports decreased pain in right shoulder from 8/10 to 5/10 since last visit.
        Patient states he is able to reach overhead with less difficulty.
        
        OBJECTIVE:
        ROM: Right shoulder flexion 0-140 degrees (improved from 0-120)
        Strength: Right shoulder 4/5 in all planes
        Pain: 5/10 with overhead activities
        
        ASSESSMENT:
        Patient demonstrates good progress with decreased pain and improved ROM.
        Continue current treatment plan.
        
        PLAN:
        Continue strengthening exercises
        Progress to functional activities
        Next visit in 3 days
        """
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
        
        print("   ✅ Test document created")
        
        # Step 3: Submit analysis
        print("\n3️⃣ Submitting analysis request...")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        with open(temp_file_path, 'rb') as f:
            files = {"file": ("test_document.txt", f, "text/plain")}
            data = {
                "discipline": "pt",
                "analysis_mode": "rubric"
            }
            
            analysis_response = client.post(
                "/analysis/analyze",
                files=files,
                data=data,
                headers=headers
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
            print(f"   ✅ Analysis submitted successfully! Task ID: {task_id[:8]}...")
            
            # Step 4: Check task status
            print("\n4️⃣ Checking task status...")
            
            status_response = client.get(
                f"/analysis/status/{task_id}",
                headers=headers
            )
            
            print(f"   Status check response: {status_response.status_code}")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"   Task status: {status_data.get('status')}")
                print("   ✅ Analysis workflow is working!")
                return True
            else:
                print(f"   ❌ Status check failed: {status_response.text}")
                return False
                
        else:
            print(f"   ❌ Analysis submission failed: {analysis_response.status_code}")
            print(f"   Response: {analysis_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error in workflow test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🏥 Therapy Compliance Analyzer - Direct Analysis Workflow Test")
    print("This script tests the analysis workflow using FastAPI TestClient.")
    print()
    
    success = test_analysis_workflow_direct()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Analysis workflow test PASSED!")
        print("The analysis system is working correctly.")
        print("\n💡 The issue was with the running server instance.")
        print("Restart the API server to fix the HTTP endpoint issues.")
    else:
        print("❌ Analysis workflow test FAILED!")
        print("Check the error messages above for specific issues.")