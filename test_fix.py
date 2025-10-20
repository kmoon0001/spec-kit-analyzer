#!/usr/bin/env python3
"""Test script to verify the 5% progress fix."""

import time
import requests
import json
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

def test_backend_health():
    """Test if backend is running."""
    try:
        response = requests.get("http://127.0.0.1:8001/health", timeout=5)
        if response.status_code == 200:
            print("SUCCESS: Backend is running and healthy")
            return True
        else:
            print(f"ERROR: Backend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Backend not accessible: {e}")
        return False

def test_analysis_progress():
    """Test the analysis progress to see if it gets stuck at 5%."""
    print("\nTesting analysis progress...")
    
    # Create a simple test document
    test_content = """
    Patient: John Doe
    Date: 2024-01-15
    
    Physical Therapy Progress Note
    
    Patient demonstrates improved range of motion in left shoulder.
    Pain level decreased from 7/10 to 4/10.
    Patient able to perform ADLs with minimal assistance.
    
    Goals:
    - Increase ROM to 90% of normal
    - Reduce pain to 3/10 or less
    - Independent ADL performance
    
    Treatment provided:
    - Passive ROM exercises
    - Heat therapy
    - Patient education
    
    Next session scheduled for 2024-01-17.
    """
    
    try:
        # Start analysis
        files = {'file': ('test_note.txt', test_content, 'text/plain')}
        data = {'discipline': 'pt', 'strictness': 'standard'}
        
        print("Starting analysis...")
        response = requests.post(
            "http://127.0.0.1:8001/analysis/analyze",
            files=files,
            data=data,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"ERROR: Analysis start failed: {response.status_code}")
            print(response.text)
            return False
            
        result = response.json()
        task_id = result.get('task_id')
        
        if not task_id:
            print("ERROR: No task_id returned")
            return False
            
        print(f"SUCCESS: Analysis started with task_id: {task_id}")
        
        # Monitor progress
        progress_history = []
        max_wait_time = 30  # 30 seconds max
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                status_response = requests.get(
                    f"http://127.0.0.1:8001/analysis/status/{task_id}",
                    timeout=5
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    progress = status_data.get('progress', 0)
                    status = status_data.get('status', 'unknown')
                    message = status_data.get('status_message', '')
                    
                    progress_history.append(progress)
                    print(f"Progress: {progress}% | Status: {status} | {message}")
                    
                    if status == 'completed':
                        print("SUCCESS: Analysis completed successfully!")
                        print(f"Progress flow: {' -> '.join(map(str, progress_history))}")
                        
                        # Check if it got stuck at 5%
                        if len(progress_history) > 1 and progress_history[1] == 5 and len(set(progress_history[1:])) == 1:
                            print("ERROR: ANALYSIS STUCK AT 5% - FIX NOT WORKING")
                            return False
                        else:
                            print("SUCCESS: Progress flowed smoothly - FIX IS WORKING!")
                            return True
                            
                    elif status == 'failed':
                        print(f"ERROR: Analysis failed: {status_data.get('error', 'Unknown error')}")
                        return False
                        
                else:
                    print(f"ERROR: Status check failed: {status_response.status_code}")
                    return False
                    
            except requests.exceptions.RequestException as e:
                print(f"ERROR: Status check error: {e}")
                return False
                
            time.sleep(1)
            
        print("ERROR: Analysis timed out - may still be stuck")
        return False
        
    except Exception as e:
        print(f"ERROR: Test failed with exception: {e}")
        return False

def main():
    """Run the test."""
    print("Testing the 5% progress fix...")
    print("=" * 50)
    
    # Wait for backend to start
    print("Waiting for backend to start...")
    for i in range(10):
        if test_backend_health():
            break
        time.sleep(2)
        print(f"Attempt {i+1}/10...")
    else:
        print("ERROR: Backend failed to start")
        return False
    
    # Test analysis progress
    success = test_analysis_progress()
    
    print("\n" + "=" * 50)
    if success:
        print("SUCCESS: The 5% progress fix is working!")
        print("Analysis progresses smoothly from 0% to 100%")
    else:
        print("FAILURE: The 5% progress issue persists")
        print("Analysis still gets stuck at 5%")
    
    return success

if __name__ == "__main__":
    main()
