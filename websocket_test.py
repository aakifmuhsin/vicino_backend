#!/usr/bin/env python3
"""
WebSocket Test Client for Vicino Backend
This script demonstrates how to connect to the WebSocket endpoints
"""

import asyncio
import websockets
import json


async def test_delivery_partner_websocket():
    """Test WebSocket connection for delivery partner"""
    uri = "ws://localhost:8000/ws/delivery/test-partner-123"

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected as delivery partner")

            # Send a test message
            await websocket.send("Hello from delivery partner!")

            # Listen for messages
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    print(f"📦 Received: {data}")

                    if data.get("type") == "new_order":
                        print(f"🚚 New order available: {data['order']['id']}")
                        print(f"   Total: ₹{data['order']['total_amount']}")
                        print(f"   Items: {len(data['order']['items'])} items")

                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await websocket.send(json.dumps({"type": "ping"}))

    except Exception as e:
        print(f"❌ Connection failed: {e}")


async def test_customer_websocket():
    """Test WebSocket connection for customer"""
    uri = "ws://localhost:8000/ws/customer/test-customer-456"

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected as customer")

            # Send a test message
            await websocket.send("Hello from customer!")

            # Listen for messages
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    print(f"👤 Received: {data}")

                    if data.get("type") == "order_accepted":
                        print(f"🎉 Order {data['order_id']} accepted!")
                        print(
                            f"   Delivery partner: {data['delivery_partner_id']}")

                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await websocket.send(json.dumps({"type": "ping"}))

    except Exception as e:
        print(f"❌ Connection failed: {e}")


async def main():
    """Run both WebSocket clients concurrently"""
    print("🚀 Starting WebSocket test clients...")
    print("📝 Make sure the FastAPI server is running on localhost:8000")
    print("🔄 Press Ctrl+C to stop\n")

    # Run both clients concurrently
    await asyncio.gather(
        test_delivery_partner_websocket(),
        test_customer_websocket()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 WebSocket test clients stopped")
