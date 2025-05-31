#!/usr/bin/env python3
"""
Simple test to verify Apps Script POST functionality
"""

import requests
import json

APP_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxJiaNe-MaSm3vXlDKb6PvHUyq5IxXIfkguKQMkfMr7Y5f9PMyhTOLPoq4IfUA8LHeK/exec"


def test_simple_post():
    """Test simple POST request to Apps Script"""
    print("🔄 Testing simple POST to Apps Script...")

    try:
        # Test with minimal payload
        payload = {"test": "hello"}

        response = requests.post(
            APP_SCRIPT_URL,
            json=payload,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")

        if response.status_code == 200:
            print("✅ Apps Script is responding to POST requests!")
        else:
            print("❌ Apps Script is not handling POST requests correctly")

    except Exception as e:
        print(f"❌ Error: {e}")


def test_with_path_parameter():
    """Test POST with path parameter"""
    print("\n🔄 Testing POST with path parameter...")

    try:
        payload = {"phone": "1234567890", "role": "delivery"}

        response = requests.post(
            f"{APP_SCRIPT_URL}?path=send_otp",
            json=payload,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")

        if response.status_code == 200:
            print("✅ Apps Script is handling path parameters!")
        else:
            print("❌ Apps Script path parameter handling failed")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_simple_post()
    test_with_path_parameter()
