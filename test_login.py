#!/usr/bin/env python3
"""
Test script to diagnose the login issue without needing the server to be running.
This will help us understand where the "Invalid role provided" error is coming from.
"""

import asyncio
import httpx
import json

# Test the Apps Script directly
APP_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxJiaNe-MaSm3vXlDKb6PvHUyq5IxXIfkguKQMkfMr7Y5f9PMyhTOLPoq4IfUA8LHeK/exec"


async def test_appscript_directly():
    """Test the Apps Script directly to see if it's working"""
    print("🔄 Testing Apps Script directly...")

    async with httpx.AsyncClient() as client:
        try:
            # Test send OTP
            print("\n1. Testing send_otp...")
            send_otp_payload = {
                "phone": "9998887771",
                "role": "delivery",
                "location": "Test Location"
            }

            response = await client.post(
                APP_SCRIPT_URL,
                params={"path": "send_otp"},
                json=send_otp_payload,
                timeout=30,
                follow_redirects=True
            )

            print(f"Send OTP Status: {response.status_code}")
            print(f"Send OTP Response: {response.text}")

            if response.status_code == 200:
                otp_response = response.json()
                otp = otp_response.get("otp")
                user_id = otp_response.get("userId")

                print(f"✅ OTP received: {otp}")
                print(f"✅ User ID: {user_id}")

                # Test verify OTP
                print("\n2. Testing verify_otp...")
                verify_payload = {
                    "phone": "9998887771",
                    "otp": otp
                }

                verify_response = await client.post(
                    APP_SCRIPT_URL,
                    params={"path": "verify_otp"},
                    json=verify_payload,
                    timeout=30,
                    follow_redirects=True
                )

                print(f"Verify OTP Status: {verify_response.status_code}")
                print(f"Verify OTP Response: {verify_response.text}")

                if verify_response.status_code == 200:
                    verify_result = verify_response.json()
                    print(f"✅ Verification successful!")
                    print(f"Role: {verify_result.get('role')}")
                    print(f"User ID: {verify_result.get('userId')}")
                else:
                    print(f"❌ Verification failed")
            else:
                print(f"❌ Send OTP failed")

        except Exception as e:
            print(f"❌ Error: {e}")


def test_role_validation():
    """Test role validation logic"""
    print("\n🔄 Testing role validation...")

    # Test valid roles
    valid_roles = ["customer", "delivery", "admin"]
    test_role = "delivery"

    print(f"Testing role: '{test_role}'")
    print(f"Valid roles: {valid_roles}")
    print(f"Is valid: {test_role in valid_roles}")

    # Test case sensitivity
    print(f"Case sensitive test: {'delivery' == 'Delivery'}")
    print(f"Lowercase test: {'delivery' == 'delivery'.lower()}")


if __name__ == "__main__":
    print("🚀 Starting login diagnosis...")

    # Test role validation first
    test_role_validation()

    # Test Apps Script
    asyncio.run(test_appscript_directly())

    print("\n✅ Diagnosis complete!")
