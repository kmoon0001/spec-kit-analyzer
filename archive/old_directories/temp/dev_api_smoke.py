import json
import os
import sys
import time

import requests

BASE = "http://127.0.0.1:8001"
USERNAME = os.environ.get("API_USERNAME", "admin")
PASSWORD = os.environ.get("API_PASSWORD", "admin123")


def get_token() -> str:
    # Try OAuth2 password grant first
    try:
        data = {"username": USERNAME, "password": PASSWORD}
        r = requests.post(f"{BASE}/auth/token", data=data, timeout=10)
        if r.ok and "access_token" in r.json():
            return r.json()["access_token"]
    except (requests.RequestException, ValueError, KeyError):
        pass
    # Fallback to dev-token
    r = requests.get(f"{BASE}/auth/dev-token", timeout=10)
    r.raise_for_status()
    return r.json()["access_token"]


def main() -> int:
    try:
        token = get_token()
        headers = {"Authorization": f"Bearer {token}"}
        print("TOKEN OK")

        # Rubrics
        r = requests.get(f"{BASE}/rubrics", headers=headers, timeout=10)
        r.raise_for_status()
        print("RUBRICS:")
        print(json.dumps(r.json(), indent=2))

        # Analysis submit
        file_path = os.path.join(os.path.dirname(__file__), "..", "test_data", "good_note_1.txt")
        file_path = os.path.abspath(file_path)
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "text/plain")}
            data = {"discipline": "pt", "analysis_mode": "rubric"}
            r = requests.post(f"{BASE}/analysis/submit", headers=headers, files=files, data=data, timeout=30)
            r.raise_for_status()
            submit_payload = r.json()
            print("ANALYSIS SUBMIT:")
            print(json.dumps(submit_payload, indent=2))
            task_id = submit_payload.get("task_id")
        if not task_id:
            print("ERROR: No task_id returned from submit")
            return 1

        # Poll status
        max_polls = int(os.environ.get("POLL_MAX", "15"))
        delay = float(os.environ.get("POLL_DELAY", "1.0"))
        print("POLLING STATUS:")
        for _ in range(max_polls):
            time.sleep(delay)
            r = requests.get(f"{BASE}/analysis/status/{task_id}", headers=headers, timeout=10)
            if not r.ok:
                print(f"Status error: {r.status_code} {r.text}")
                continue
            payload = r.json()
            print(json.dumps(payload, indent=2))
            if payload.get("status") == "completed":
                break

        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
