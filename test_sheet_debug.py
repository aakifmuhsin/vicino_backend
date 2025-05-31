#!/usr/bin/env python3
"""
Debug script to check Google Sheets data
"""

import asyncio
import httpx
import json

APP_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxJiaNe-MaSm3vXlDKb6PvHUyq5IxXIfkguKQMkfMr7Y5f9PMyhTOLPoq4IfUA8LHeK/exec"


async def debug_sheets():
    """Debug what's stored in the sheets"""
    print("🔍 Google Sheets Debug")
    print("=" * 50)

    async with httpx.AsyncClient() as client:
        # First, send OTP to create user and OTP
        print("1. Creating user and OTP...")
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

            # Wait a moment for data to be written
            await asyncio.sleep(2)

            # Now try verification to see the detailed logs
            print(f"\n2. Attempting verification with OTP: {otp}")
            verify_response = await client.post(
                APP_SCRIPT_URL,
                params={"path": "verify_otp"},
                json={
                    "phone": "9998887771",
                    "otp": otp
                },
                timeout=30,
                follow_redirects=True
            )

            print(f"Verify Status: {verify_response.status_code}")
            print(f"Verify Response: {verify_response.text}")

            # The logs will show us what's happening in the sheets
            print("\n📋 Check the Google Apps Script logs to see:")
            print("   - What users are in the Users sheet")
            print("   - What OTPs are in the OTPS sheet")
            print("   - The exact comparison values")
            print("\n🔗 Apps Script Logs: https://script.google.com/home/executions")

if __name__ == "__main__":
    asyncio.run(debug_sheets())
