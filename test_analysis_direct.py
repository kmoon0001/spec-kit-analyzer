"""Direct test of analysis endpoint to diagnose the freezing issue."""
import requests
import time
import json

API_URL = "http://127.0.0.1:8001"

# Login
print("1. Logging in...")
login_response = requests.post(
    f"{API_URL}/auth/login",
    data={"username": "admin", "password": "admin123"}
)
if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"✓ Logged in successfully")

# Create a test document
print("\n2. Creating test document...")
test_content = """
PHYSICAL THERAPY PROGRESS NOTE

Patient: John Doe
Date: 2024-01-15

SUBJECTIVE: Patient reports decreased pain in right shoulder.

OBJECTIVE: ROM improved to 140 degrees flexion.

ASSESSMENT: Patient making good progress toward goals.

PLAN: Continue current treatment plan.
"""

# Upload and analyze
print("\n3. Starting analysis...")
files = {"file": ("test_note.txt", test_content.encode(), "text/plain")}
data = {
    "discipline": "pt",
    "analysis_mode": "rubric",
    "strictness": "standard"
}

analyze_response = requests.post(
    f"{API_URL}/analysis/analyze",
    files=files,
    data=data,
    headers=headers
)

if analyze_response.status_code != 202:
    print(f"Analysis start failed: {analyze_response.status_code}")
    print(analyze_response.text)
    exit(1)

task_id = analyze_response.json()["task_id"]
print(f"✓ Analysis started: {task_id}")

# Poll for status
print("\n4. Monitoring progress...")
print("-" * 60)
last_progress = -1
start_time = time.time()
max_wait = 120  # 2 minutes

while True:
    if time.time() - start_time > max_wait:
        print("\n✗ TIMEOUT: Analysis took too long")
        break

    status_response = requests.get(
        f"{API_URL}/analysis/status/{task_id}",
        headers=headers
    )

    if status_response.status_code != 200:
        print(f"\n✗ Status check failed: {status_response.status_code}")
        break

    status_data = status_response.json()
    status = status_data.get("status", "unknown")
    progress = status_data.get("progress", 0)
    message = status_data.get("status_message", "")

    # Only print when progress changes
    if progress != last_progress:
        elapsed = time.time() - start_time
        print(f"[{elapsed:5.1f}s] {progress:3d}% | {status:12s} | {message}")
        last_progress = progress

    if status == "completed":
        print("-" * 60)
        print("✓ ANALYSIS COMPLETED SUCCESSFULLY")

        # Show results
        if "analysis" in status_data:
            analysis = status_data["analysis"]
            score = analysis.get("compliance_score", "N/A")
            findings_count = len(analysis.get("findings", []))
            print(f"\nCompliance Score: {score}")
            print(f"Findings: {findings_count}")

        break

    if status == "failed":
        print("-" * 60)
        print(f"✗ ANALYSIS FAILED: {status_data.get('error', 'Unknown error')}")
        break

    time.sleep(1.5)  # Poll every 1.5 seconds

print("\nTest complete!")
