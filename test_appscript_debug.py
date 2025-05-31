#!/usr/bin/env python3
"""
Debug script to test Apps Script OTP storage directly
"""

import asyncio
import httpx
import json

APP_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz8ccNA3R_9vfq6KvyuAHvsNb7FpoAV0nJi_pJuYHhZqNEBeedHfMTC5iLxvNdEQvm1/exec"


async def test_appscript_otp():
    """Test Apps Script OTP functionality directly"""
    print("🔍 Testing Apps Script OTP Storage")
    print("=" * 50)

    async with httpx.AsyncClient() as client:
        # Step 1: Send OTP
        print("1. Sending OTP via Apps Script...")
        send_response = await client.post(
            APP_SCRIPT_URL,
            params={"path": "send_otp"},
            json={
                "phone": "9998887771",
                "role": "delivery",
                "location": "Test Location"
            },
            timeout=30,
            follow_redirects=True
        )

        print(f"Send Status: {send_response.status_code}")
        print(f"Send Response: {send_response.text}")

        if send_response.status_code == 200:
            send_data = send_response.json()
            otp = send_data.get("otp")
            user_id = send_data.get("userId")

            print(f"✅ OTP Generated: {otp}")
            print(f"✅ User ID: {user_id}")

            # Step 2: Verify OTP immediately
            print("\n2. Verifying OTP via Apps Script...")
            verify_response = await client.post(
                APP_SCRIPT_URL,
                params={"path": "verify_otp"},
                json={
                    "phone": "9998887771",
                    "otp": otp  # Use the exact OTP returned
                },
                timeout=30,
                follow_redirects=True
            )

            print(f"Verify Status: {verify_response.status_code}")
            print(f"Verify Response: {verify_response.text}")

            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                if verify_data.get("success"):
                    print("✅ Apps Script OTP verification WORKING!")
                else:
                    print(
                        f"❌ Apps Script OTP verification failed: {verify_data.get('message')}")
            else:
                print("❌ Apps Script OTP verification request failed")
        else:
            print("❌ Apps Script OTP generation failed")

if __name__ == "__main__":
    asyncio.run(test_appscript_otp())
