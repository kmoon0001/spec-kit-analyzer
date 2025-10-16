#!/usr/bin/env python3
"""
Simple Real-time Monitor (No Unicode)
Monitors API and system resources.
"""

import psutil
import requests
from datetime import datetime


def check_api_status():
    """Check API server status."""
    try:
        response = requests.get("http://127.0.0.1:8001/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {"status": "online", "response_time": response.elapsed.total_seconds(), "data": data}
        else:
            return {"status": "error", "code": response.status_code}
    except requests.exceptions.RequestException as e:
        return {"status": "offline", "error": str(e)}


def get_python_processes():
    """Get information about Python processes."""
    processes = []
    for proc in psutil.process_iter(["pid", "name", "memory_info", "cpu_percent"]):
        if "python" in proc.info["name"].lower():
            try:
                proc.cpu_percent()  # Initialize CPU monitoring
                processes.append(
                    {
                        "pid": proc.info["pid"],
                        "name": proc.info["name"],
                        "memory_mb": proc.info["memory_info"].rss / 1024**2,
                        "cpu_percent": proc.cpu_percent(),
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    return processes


def print_status():
    """Print current system status."""
    timestamp = datetime.now().strftime("%H:%M:%S")

    print(f"\n[{timestamp}] Application Status")
    print("-" * 50)

    # API Status
    api_status = check_api_status()
    if api_status["status"] == "online":
        print(f"API: [ONLINE] ({api_status['response_time']:.3f}s)")
        print(f"Database: {api_status['data'].get('database', 'unknown')}")
    else:
        print(f"API: [OFFLINE] - {api_status.get('error', api_status.get('status', 'unknown'))}")

    # Python Processes
    processes = get_python_processes()
    print(f"Python Processes: {len(processes)}")
    for proc in processes:
        print(f"  PID {proc['pid']}: {proc['memory_mb']:.1f}MB RAM, {proc['cpu_percent']:.1f}% CPU")

    # System Resources
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    print(f"System: CPU {cpu_percent:.1f}%, RAM {memory.percent:.1f}%")


if __name__ == "__main__":
    print_status()
