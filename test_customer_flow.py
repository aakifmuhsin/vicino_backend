from fastapi import HTTPException
import httpx
import time

# Base URL for Google Apps Script API
APP_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxJiaNe-MaSm3vXlDKb6PvHUyq5IxXIfkguKQMkfMr7Y5f9PMyhTOLPoq4IfUA8LHeK/exec"

# Function to send POST requests to Google Apps Script API


async def make_appscript_request(endpoint: str, payload: dict):
    try:
        # Prepare query parameters (path)
        params = {"path": endpoint}
        print(f"Sending request with params: {params}")

        # Send the POST request to the App Script endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                APP_SCRIPT_URL,
                params=params,  # Add the path as a query parameter
                json=payload,  # Send the data as JSON in the body
                timeout=30,
            )

            # If the response is a redirect (302), handle it manually
            if response.status_code == 302:
                # Redirect location is in the 'Location' header
                redirect_url = response.headers['Location']

                # Perform a GET request to follow the redirect
                response = await client.get(redirect_url)

            # Raise an exception for non-2xx responses
            response.raise_for_status()
            return response.json()  # Return the response as JSON

    except httpx.HTTPStatusError as e:
        print(
            f"HTTP error occurred: {e.response.status_code}, {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"AppScript API error: {e.response.text}"
        )
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500, detail="Unexpected error occurred")
# ---------------------- Customer Flow ----------------------

# 1. Customer registers and gets OTP


async def send_otp_customer(phone: str, location: str):
    payload = {
        "phone": phone,
        "role": "customer",
        "location": location
    }
    response = await make_appscript_request("send_otp", payload)
    if 'otp' in response:
        print(f"Customer OTP sent: {response['otp']}")
        return response['userId'], response['otp']
    return None, None

# 2. Customer verifies OTP


async def verify_otp_customer(phone: int, otp: int):
    payload = {
        "phone": phone,
        "otp": otp
    }
    response = await make_appscript_request("verify_otp", payload)
    if response.get('success'):
        print(f"Customer login successful")
    else:
        print("Invalid OTP or user not found")

# 3. Customer creates an order


async def create_order_customer(customer_id: str, phone: str, items: list):
    payload = {
        "customerId": customer_id,
        "phone": phone,
        "items": items
    }
    response = await make_appscript_request("create_order", payload)
    if 'orderId' in response:
        print(f"Order created with ID: {response['orderId']}")
        return response['orderId']
    return None

# 4. Customer verifies order OTP (after delivery)


async def verify_order_otp_customer(order_id: str, otp: str):
    payload = {
        "otp": otp
    }
    response = await make_appscript_request(f"close_order", {
        "orderId": order_id,
        "otp": otp
    })
    if response.get("success"):
        print(f"Order {order_id} closed successfully with OTP verification")
    else:
        print("Failed to verify OTP")

# ---------------------- Delivery Partner Flow ----------------------

# 1. Delivery Partner registers and gets OTP


async def send_otp_delivery(phone: str, location: str):
    payload = {
        "phone": phone,
        "role": "delivery",
        "location": location
    }
    response = await make_appscript_request("send_otp", payload)
    if 'otp' in response:
        print(f"Delivery Partner OTP sent: {response['otp']}")
        return response['userId'], response['otp']
    return None, None

# 2. Delivery partner accepts the order


async def accept_order_delivery(order_id: str, partner_id: str):
    payload = {
        "delivery_partner_id": partner_id
    }
    response = await make_appscript_request(f"assign_order", {
        "orderId": order_id,
        "partnerId": partner_id
    })
    if response.get('status') == "Accepted":
        print(f"Order {order_id} accepted by Delivery Partner {partner_id}")
        return response['otp']
    return None

# 3. Delivery Partner verifies OTP for order completion


async def verify_order_otp_delivery(order_id: str, otp: str):
    payload = {
        "otp": otp
    }
    print(type(order_id))
    print(order_id)
    print(type(otp))
    print(otp)
    response = await make_appscript_request(f"close_order", {
        "orderId": order_id,
        "otp": otp
    })
    if response.get("success"):
        print(f"Order {order_id} closed successfully with OTP verification")
    else:
        print("Failed to verify OTP")

# Example of customer and delivery partner flow


async def customer_flow():
    phone = 1234567890
    location = "Coimbatore"

    # 1. Send OTP to customer
    customer_id, customer_otp = await send_otp_customer(phone, location)
    print(customer_id)
    if customer_id:
        # 2. Verify OTP
        otpcus = int(customer_otp)
        print(phone)
        await verify_otp_customer(phone, otpcus)

        # 3. Customer places an order
        items = [{"name": "Carrot", "quantity": 3, "price": 10.0}]
        order_id = await create_order_customer(customer_id, phone, items)

        if order_id:
            # Simulate delivery partner accepting the order and OTP for delivery
            await delivery_partner_flow(order_id)


async def delivery_partner_flow(order_id):
    partner_phone = "9876543210"
    partner_location = "Delivery Area"

    # 1. Send OTP to delivery partner
    partner_id, partner_otp = await send_otp_delivery(partner_phone, partner_location)
    if partner_id:
        # 2. Delivery partner accepts order
        order_otp = await accept_order_delivery(order_id, partner_id)
        order_otp = int(order_otp)
        if order_otp:
            # 3. Delivery partner verifies OTP
            await verify_order_otp_delivery(order_id, order_otp)

# Run the full flow


async def main():
    await customer_flow()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
