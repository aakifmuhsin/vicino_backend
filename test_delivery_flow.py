import httpx
import time

# Base URL of your FastAPI server
BASE_URL = "http://localhost:8000"

def test_delivery_flow():
    # Delivery Partner sends OTP
    partner_phone = "+1987654321"
    send_otp_response = httpx.post(
        f"{BASE_URL}/login/send_otp",
        json={"phone": partner_phone, "role": "delivery"}
    )
    assert send_otp_response.status_code == 200
    partner_id = send_otp_response.json()["user_id"]
    otp = send_otp_response.json()["otp"]

    # Verify OTP
    verify_response = httpx.post(
        f"{BASE_URL}/login/verify_otp",
        json={"phone": partner_phone, "otp": otp}
    )
    assert verify_response.status_code == 200
    assert verify_response.json()["role"] == "delivery"

    # Get Available Orders
    orders_response = httpx.get(f"{BASE_URL}/orders/available")
    assert orders_response.status_code == 200
    orders = orders_response.json()["orders"]
    assert len(orders) > 0
    order_id = orders[0]["id"]

    # Accept Order
    accept_response = httpx.post(
        f"{BASE_URL}/orders/{order_id}/accept",
        json={"delivery_partner_id": partner_id}
    )
    assert accept_response.status_code == 200
    delivery_otp = accept_response.json()["otp"]
    print(f"Delivery OTP: {delivery_otp}")

    # Close Order with OTP
    close_response = httpx.post(
        f"{BASE_URL}/orders/{order_id}/verify_otp",
        json={"otp": delivery_otp}
    )
    assert close_response.status_code == 200
    print("Order Closed Successfully:", close_response.json())

if __name__ == "__main__":
    test_delivery_flow()