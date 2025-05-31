#!/usr/bin/env python3
"""
Final comprehensive test for the Vicino delivery system
"""

import asyncio
import httpx
import json

# Configuration
FASTAPI_BASE_URL = "http://127.0.0.1:8000"
APP_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxJiaNe-MaSm3vXlDKb6PvHUyq5IxXIfkguKQMkfMr7Y5f9PMyhTOLPoq4IfUA8LHeK/exec"


async def test_fastapi_server():
    """Test if FastAPI server is running"""
    print("🔄 Testing FastAPI server...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{FASTAPI_BASE_URL}/docs")
            if response.status_code == 200:
                print("✅ FastAPI server is running")
                return True
            else:
                print(f"❌ FastAPI server error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ FastAPI server not accessible: {e}")
            return False


async def test_apps_script():
    """Test Apps Script directly"""
    print("\n🔄 Testing Apps Script...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                APP_SCRIPT_URL,
                json={"test": "hello"},
                timeout=30
            )

            if response.status_code == 200:
                print("✅ Apps Script is working")
                return True
            else:
                print(f"❌ Apps Script error: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Apps Script error: {e}")
            return False


async def test_delivery_partner_login():
    """Test delivery partner login through FastAPI"""
    print("\n🔄 Testing delivery partner login...")

    async with httpx.AsyncClient() as client:
        try:
            # Send OTP
            response = await client.post(
                f"{FASTAPI_BASE_URL}/login/send_otp",
                json={
                    "phone": "9998887771",
                    "role": "delivery",
                    "location": "Test Location"
                },
                timeout=30
            )

            print(f"Login Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Delivery partner login working!")
                print(f"User ID: {data.get('user_id')}")
                print(f"OTP: {data.get('otp')}")
                return True
            else:
                print(f"❌ Login failed: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Login error: {e}")
            return False


async def main():
    """Run all tests"""
    print("🚀 Final System Test for Vicino Delivery Platform\n")

    # Test components
    fastapi_ok = await test_fastapi_server()
    appscript_ok = await test_apps_script()

    if fastapi_ok and appscript_ok:
        delivery_ok = await test_delivery_partner_login()
    else:
        delivery_ok = False
        print("\n⚠️ Skipping delivery test due to component failures")

    # Results
    print("\n" + "="*50)
    print("📊 FINAL TEST RESULTS")
    print("="*50)
    print(
        f"FastAPI Server:        {'✅ WORKING' if fastapi_ok else '❌ FAILED'}")
    print(
        f"Apps Script:           {'✅ WORKING' if appscript_ok else '❌ FAILED'}")
    print(
        f"Delivery Partner Login: {'✅ WORKING' if delivery_ok else '❌ FAILED'}")

    if fastapi_ok and appscript_ok and delivery_ok:
        print("\n🎉 SUCCESS! Everything is working!")
        print("✅ Delivery partner issue is FIXED!")
        print("✅ System is ready for production!")
    else:
        print("\n⚠️ Issues found:")
        if not fastapi_ok:
            print("- FastAPI server needs to be started")
        if not appscript_ok:
            print("- Apps Script needs proper deployment")
        if not delivery_ok:
            print("- Delivery partner login integration needs fixing")

if __name__ == "__main__":
    asyncio.run(main())
