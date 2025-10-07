#!/usr/bin/env python3
"""
Quick test to check if server is responding
"""

import requests

try:
    print("Testing basic connectivity...")
    response = requests.get("http://127.0.0.1:8001/", timeout=5)
    print(f"Root endpoint: {response.status_code} - {response.json()}")
    
    print("\nTesting health endpoint...")
    response = requests.get("http://127.0.0.1:8001/health", timeout=5)
    print(f"Health endpoint: {response.status_code} - {response.json()}")
    
    print("\nTesting NEW rubrics endpoint...")
    response = requests.get("http://127.0.0.1:8001/rubrics", timeout=5)
    print(f"Rubrics endpoint: {response.status_code} - {response.json()}")
    
except Exception as e:
    print(f"Error: {e}")