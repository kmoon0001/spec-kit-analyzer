"""
Quick test to verify API endpoints are working.
"""

import requests
import json

API_URL = "http://127.0.0.1:8001"

def test_health_endpoint():
    """Test the health endpoint."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        print(f"Health endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            return True
    except Exception as e:
        print(f"Health endpoint failed: {e}")
    return False

def test_analysis_submit_endpoint():
    """Test the analysis submit endpoint."""
    try:
        # Test with minimal payload
        test_payload = {
            "discipline": "medicare_benefits_policy_manual_ch15",
            "analysis_mode": "rubric"
        }
        
        # Create a test file
        test_file_content = "This is a test therapy note for compliance analysis."
        
        files = {"file": ("test_note.txt", test_file_content, "text/plain")}
        data = {"data": json.dumps(test_payload)}
        
        response = requests.post(f"{API_URL}/analysis/submit", files=files, data=data, timeout=30)
        print(f"Analysis submit endpoint: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Task ID: {result.get('task_id', 'No task ID')}")
            return result.get('task_id')
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Analysis submit failed: {e}")
    return None

def test_task_status_endpoint(task_id):
    """Test the task status endpoint."""
    if not task_id:
        print("No task ID to test")
        return
    
    try:
        response = requests.get(f"{API_URL}/tasks/{task_id}", timeout=10)
        print(f"Task status endpoint: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Task status: {result.get('status', 'unknown')}")
            print(f"Progress: {result.get('progress', 0)}%")
            return result
        else:
            print(f"Task status error: {response.text}")
            
    except Exception as e:
        print(f"Task status check failed: {e}")
    return None

if __name__ == "__main__":
    print("🔍 Testing API Endpoints")
    print("=" * 40)
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    health_ok = test_health_endpoint()
    
    if not health_ok:
        print("❌ Health check failed - API server may not be running")
        print("Start the API server with: python scripts/run_api.py")
        exit(1)
    
    # Test 2: Analysis submission
    print("\n2. Testing analysis submission...")
    task_id = test_analysis_submit_endpoint()
    
    if not task_id:
        print("❌ Analysis submission failed")
        exit(1)
    
    # Test 3: Task status checking
    print("\n3. Testing task status...")
    status_result = test_task_status_endpoint(task_id)
    
    if status_result:
        print("✅ All API endpoints are working!")
    else:
        print("❌ Task status endpoint failed")
    
    print("\n" + "=" * 40)
    print("API endpoint testing complete")