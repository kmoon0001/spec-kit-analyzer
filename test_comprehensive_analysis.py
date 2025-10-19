"""Comprehensive test to reproduce the 5% stuck issue."""
import requests
import time
import json
import threading
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.unicode_safe import safe_print, setup_unicode_safe_environment

# Setup Unicode-safe environment
setup_unicode_safe_environment()

API_URL = "http://127.0.0.1:8001"

def test_analysis_with_timeout(content, discipline="pt", analysis_mode="rubric", strictness="balanced", timeout=30, test_name="Test"):
    """Test analysis with timeout to detect hanging."""
    safe_print(f"\n=== {test_name} ===")

    # Login
    login_response = requests.post(
        f"{API_URL}/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    if login_response.status_code != 200:
        safe_print(f"Login failed: {login_response.status_code}")
        return False

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Start analysis
    files = {"file": ("test_note.txt", content.encode(), "text/plain")}
    data = {
        "discipline": discipline,
        "analysis_mode": analysis_mode,
        "strictness": strictness
    }

    analyze_response = requests.post(
        f"{API_URL}/analysis/analyze",
        files=files,
        data=data,
        headers=headers
    )

    if analyze_response.status_code != 202:
        safe_print(f"Analysis start failed: {analyze_response.status_code}")
        safe_print(analyze_response.text)
        return False

    task_id = analyze_response.json()["task_id"]
    safe_print(f"Analysis started: {task_id}")

    # Monitor with timeout
    start_time = time.time()
    last_progress = -1

    while time.time() - start_time < timeout:
        status_response = requests.get(
            f"{API_URL}/analysis/status/{task_id}",
            headers=headers
        )

        if status_response.status_code != 200:
            safe_print(f"Status check failed: {status_response.status_code}")
            break

        status_data = status_response.json()
        status = status_data.get("status", "unknown")
        progress = status_data.get("progress", 0)
        message = status_data.get("status_message", "")

        if progress != last_progress:
            elapsed = time.time() - start_time
            safe_print(f"[{elapsed:5.1f}s] {progress:3d}% | {status:12s} | {message}")
            last_progress = progress

        if status == "completed":
            safe_print("[OK] Analysis completed successfully")
            return True

        if status == "failed":
            safe_print(f"[FAIL] Analysis failed: {status_data.get('error', 'Unknown error')}")
            return False

        time.sleep(1)

    print(f"[TIMEOUT] Analysis timed out after {timeout} seconds")
    return False

# Test cases
test_cases = [
    {
        "name": "Short PT Note",
        "content": """PHYSICAL THERAPY PROGRESS NOTE
Patient: John Doe
Date: 2024-01-15
SUBJECTIVE: Patient reports decreased pain in right shoulder.
OBJECTIVE: ROM improved to 140 degrees flexion.
ASSESSMENT: Patient making good progress toward goals.
PLAN: Continue current treatment plan.""",
        "strictness": "ultra_fast"
    },
    {
        "name": "Medium PT Note",
        "content": """PHYSICAL THERAPY PROGRESS NOTE

Patient: Jane Smith
Date: 2024-01-15
Therapist: Dr. Johnson

SUBJECTIVE:
Patient reports significant improvement in left knee pain since last visit.
States she can now walk up stairs without severe discomfort.
Sleep quality has improved due to reduced pain levels.

OBJECTIVE:
- ROM: Left knee flexion 120 degrees (improved from 100 degrees)
- Strength: Quadriceps 4/5 (improved from 3/5)
- Gait: Normal heel-toe pattern maintained
- Balance: Single leg stance 15 seconds (improved from 8 seconds)

ASSESSMENT:
Patient demonstrates excellent progress toward established goals.
Pain levels have decreased significantly.
Functional mobility has improved substantially.

PLAN:
- Continue current exercise program
- Progress to advanced balance exercises
- Schedule follow-up in 2 weeks""",
        "strictness": "balanced"
    },
    {
        "name": "Long PT Note",
        "content": """PHYSICAL THERAPY PROGRESS NOTE

Patient: Robert Johnson
Date: 2024-01-15
Therapist: Dr. Sarah Williams
Clinic: Advanced Physical Therapy Center

SUBJECTIVE:
Patient reports continued improvement in lower back pain and mobility.
States he can now sit for extended periods without discomfort.
Sleep quality has improved significantly.
Patient expresses satisfaction with current treatment progress.

OBJECTIVE:
- ROM: Lumbar flexion 60 degrees (improved from 45 degrees)
- ROM: Lumbar extension 25 degrees (improved from 15 degrees)
- ROM: Lumbar lateral flexion 30 degrees bilaterally (improved from 20 degrees)
- Strength: Core muscles 4+/5 (improved from 3/5)
- Strength: Hip flexors 4/5 (improved from 3/5)
- Gait: Normal pattern with improved stride length
- Balance: Tandem walk 10 steps (improved from 5 steps)
- Functional: Can lift 25 lbs from floor (improved from 15 lbs)

ASSESSMENT:
Patient demonstrates excellent progress toward established goals.
Significant improvement in pain levels and functional mobility.
Core strength and stability have improved substantially.
Patient is ready for advanced strengthening exercises.

PLAN:
- Continue current exercise program with progression
- Add advanced core strengthening exercises
- Progress to functional lifting activities
- Schedule follow-up in 1 week
- Consider discharge planning if goals continue to be met""",
        "strictness": "thorough"
    }
]

print("Starting comprehensive analysis tests...")
print("=" * 60)

success_count = 0
total_tests = len(test_cases)

for i, test_case in enumerate(test_cases, 1):
    print(f"\nTest {i}/{total_tests}")
    if test_analysis_with_timeout(test_case["content"], test_case.get("discipline", "pt"), test_case.get("analysis_mode", "rubric"), test_case.get("strictness", "balanced"), 30, test_case["name"]):
        success_count += 1

print("\n" + "=" * 60)
print(f"Test Results: {success_count}/{total_tests} tests passed")
print(f"Success Rate: {(success_count/total_tests)*100:.1f}%")

if success_count == total_tests:
    print("[SUCCESS] All tests passed - no 5% stuck issue detected")
else:
    print("[WARNING] Some tests failed - 5% stuck issue may be present")
