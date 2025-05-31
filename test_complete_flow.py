#!/usr/bin/env python3
"""
Complete Flow Test for Vicino Backend
Tests the entire flow: Login -> WebSocket -> Order Creation -> Order Acceptance
"""

import asyncio
import httpx
import websockets
import json
import time

BASE_URL = "http://localhost:8000"


async def test_login_flow():
    """Test the login flow for both customer and delivery partner"""
    async with httpx.AsyncClient() as client:
        print("🔐 Testing Login Flow...")

        # Test delivery partner login
        print("\n1. Testing Delivery Partner Login:")

        # Send OTP
        otp_response = await client.post(f"{BASE_URL}/login/send_otp", json={
            "phone": "9442033333",
            "role": "delivery",
            "location": "Chennai"
        })

        print(f"   OTP Response: {otp_response.status_code}")
        otp_data = otp_response.json()
        print(f"   OTP: {otp_data.get('otp')}")

        if otp_response.status_code == 200:
            # Verify OTP
            verify_response = await client.post(f"{BASE_URL}/login/verify_otp", json={
                "phone": "9442033333",
                "otp": str(otp_data.get('otp'))
            })

            print(f"   Verify Response: {verify_response.status_code}")
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                print(f"   ✅ Login successful: {verify_data}")
                return verify_data.get('user_id')
            else:
                print(f"   ❌ Login failed: {verify_response.text}")
                return None
        else:
            print(f"   ❌ OTP failed: {otp_response.text}")
            return None


async def test_order_creation():
    """Test order creation"""
    async with httpx.AsyncClient() as client:
        print("\n📦 Testing Order Creation...")

        order_data = {
            "customer_id": "test-customer-123",
            "phone": "9876543210",
            "items": [
                {
                    "name": "Carrot",
                    "quantity": 2,
                    "unit": "kg",
                    "price": 10.0
                },
                {
                    "name": "Banana",
                    "quantity": 1,
                    "unit": "dozen",
                    "price": 5.0
                }
            ]
        }

        response = await client.post(f"{BASE_URL}/orders", json=order_data)
        print(f"   Order Response: {response.status_code}")

        if response.status_code == 200:
            order = response.json()
            print(f"   ✅ Order created: {order['id']}")
            print(f"   Total: ₹{order['total_amount']}")
            return order['id']
        else:
            print(f"   ❌ Order creation failed: {response.text}")
            return None


async def test_websocket_integration():
    """Test the complete WebSocket integration"""
    print("\n🔌 Testing WebSocket Integration...")

    delivery_partner_id = "test-partner-123"
    customer_id = "test-customer-456"

    async def delivery_partner_client():
        uri = f"ws://localhost:8000/ws/delivery/{delivery_partner_id}"
        try:
            async with websockets.connect(uri) as websocket:
                print("   ✅ Delivery partner connected")

                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        data = json.loads(message)

                        if data.get("type") == "new_order":
                            print(
                                f"   📦 New order received: {data['order']['id']}")
                            return data['order']['id']

                    except asyncio.TimeoutError:
                        await websocket.send(json.dumps({"type": "ping"}))

        except Exception as e:
            print(f"   ❌ Delivery partner WebSocket failed: {e}")
            return None

    async def customer_client():
        uri = f"ws://localhost:8000/ws/customer/{customer_id}"
        try:
            async with websockets.connect(uri) as websocket:
                print("   ✅ Customer connected")

                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(message)

                        if data.get("type") == "order_accepted":
                            print(
                                f"   🎉 Order accepted notification: {data['order_id']}")
                            return True

                    except asyncio.TimeoutError:
                        await websocket.send(json.dumps({"type": "ping"}))

        except Exception as e:
            print(f"   ❌ Customer WebSocket failed: {e}")
            return False

    # Start WebSocket clients
    delivery_task = asyncio.create_task(delivery_partner_client())
    customer_task = asyncio.create_task(customer_client())

    # Wait a bit for connections to establish
    await asyncio.sleep(1)

    # Create an order (this should trigger WebSocket notification)
    order_id = await test_order_creation()

    if order_id:
        # Wait for delivery partner to receive the order
        try:
            received_order_id = await asyncio.wait_for(delivery_task, timeout=3.0)
            if received_order_id == order_id:
                print("   ✅ WebSocket order notification working!")

                # Test order acceptance
                async with httpx.AsyncClient() as client:
                    accept_response = await client.post(
                        f"{BASE_URL}/orders/{order_id}/accept",
                        json={"delivery_partner_id": delivery_partner_id}
                    )

                    if accept_response.status_code == 200:
                        print("   ✅ Order accepted successfully")

                        # Wait for customer notification
                        try:
                            customer_notified = await asyncio.wait_for(customer_task, timeout=3.0)
                            if customer_notified:
                                print("   ✅ Customer notification working!")
                            else:
                                print("   ❌ Customer notification failed")
                        except asyncio.TimeoutError:
                            print("   ❌ Customer notification timeout")
                    else:
                        print(
                            f"   ❌ Order acceptance failed: {accept_response.text}")
            else:
                print("   ❌ Order ID mismatch in WebSocket")
        except asyncio.TimeoutError:
            print("   ❌ WebSocket notification timeout")

    # Cancel remaining tasks
    delivery_task.cancel()
    customer_task.cancel()


async def main():
    """Run all tests"""
    print("🚀 Starting Complete Flow Test for Vicino Backend")
    print("=" * 50)

    # Test login
    user_id = await test_login_flow()

    if user_id:
        print(f"\n✅ Login test passed for user: {user_id}")

        # Test WebSocket integration
        await test_websocket_integration()
    else:
        print("\n❌ Login test failed, skipping WebSocket tests")

    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
