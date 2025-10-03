import requests
import time
import os
import json

API_URL = "http://127.0.0.1:8004"
USERNAME = "admin"
PASSWORD = "password"


def get_auth_token():
    """Authenticate and retrieve a JWT token."""
    print("Authenticating...")
    response = requests.post(
        f"{API_URL}/auth/token",
        data={"username": USERNAME, "password": PASSWORD},
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    print("Authentication successful.")
    return token


def analyze_document(token: str, file_path: str):
    """Upload a document for analysis and get the task ID."""
    print(f"Uploading '{file_path}' for analysis...")
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "text/plain")}
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{API_URL}/analysis/analyze",
            files=files,
            headers=headers,
            data={"discipline": "pt", "analysis_mode": "rubric"},
        )
    response.raise_for_status()
    task_id = response.json()["task_id"]
    print(f"Analysis task started with ID: {task_id}")
    return task_id


def get_analysis_result(token: str, task_id: str):
    """Poll for the analysis result until it's complete."""
    print("Polling for analysis result...")
    headers = {"Authorization": f"Bearer {token}"}
    while True:
        response = requests.get(f"{API_URL}/analysis/status/{task_id}", headers=headers)
        response.raise_for_status()
        data = response.json()
        status = data.get("status")

        if status == "completed":
            print("Analysis complete.")
            return data
        elif status == "failed":
            print("Analysis failed.")
            print(data)
            return None
        else:
            print("Analysis in progress, waiting 2 seconds...")
            time.sleep(2)


def main():
    """Run the full end-to-end API test."""
    # Create a dummy file to upload
    dummy_file_path = "dummy_document.txt"
    with open(dummy_file_path, "w") as f:
        f.write("This is a test document for analysis.")

    try:
        token = get_auth_token()
        task_id = analyze_document(token, dummy_file_path)
        result = get_analysis_result(token, task_id)

        if result:
            print("\n--- Analysis Result ---")
            print(json.dumps(result, indent=2))
            print("\n--- Verification Successful ---")
            print("Mock data was received, confirming the end-to-end flow is working.")
        else:
            print("\n--- Verification Failed ---")

    except requests.exceptions.RequestException as e:
        print(f"\nAn API error occurred: {e}")
        if e.response:
            print(f"Response: {e.response.text}")
    finally:
        # Clean up the dummy file
        if os.path.exists(dummy_file_path):
            os.remove(dummy_file_path)


if __name__ == "__main__":
    main()
