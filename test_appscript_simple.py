#!/usr/bin/env python3
"""
Simple test to check if the Apps Script is accessible
"""

import requests
import json

APP_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz8ccNA3R_9vfq6KvyuAHvsNb7FpoAV0nJi_pJuYHhZqNEBeedHfMTC5iLxvNdEQvm1/exec"


def test_basic_access():
    """Test basic access to the Apps Script"""
    print("🔄 Testing basic Apps Script access...")

    try:
        # Test simple GET request
        response = requests.get(APP_SCRIPT_URL, timeout=30)
        print(f"GET Status: {response.status_code}")
        print(f"GET Response length: {len(response.text)}")

        # Test POST request without parameters
        response = requests.post(APP_SCRIPT_URL, timeout=30)
        print(f"POST Status: {response.status_code}")
        print(f"POST Response length: {len(response.text)}")

        # Test POST with minimal data
        response = requests.post(
            APP_SCRIPT_URL,
            json={"test": "data"},
            timeout=30
        )
        print(f"POST with JSON Status: {response.status_code}")
        print(f"POST with JSON Response: {response.text[:200]}...")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_basic_access()
