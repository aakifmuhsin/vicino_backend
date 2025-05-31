import pytest
from fastapi.testclient import TestClient
from main import app  # Import your FastAPI app here
import uuid

client = TestClient(app)

# Simulated in-memory store for bookings
bookings = {}

# Test to create a booking and ensure that all partners get notified
def test_book_service():
    # Create booking data
    booking_data = {
        "user_id": "user1",
        "service_name": "Pet Grooming",
        "service_details": "Full grooming session"
    }
    
    # Send POST request to /book_service/
    response = client.post("/book_service/", json=booking_data)
    
    # Check the response for success
    assert response.status_code == 200
    assert "booking_id" in response.json()
    
    # Print the booking ID and confirmation message
    booking_id = response.json()["booking_id"]
    print(f"Booking ID: {booking_id} created for service 'Pet Grooming' by user 'user1'")

    # Check if all partners received the booking notification
    print("Notifying all partners about the new service booking:")
    for partner in ["Partner1", "Partner2", "Partner3", "Partner4", "Partner5",
                    "Partner6", "Partner7", "Partner8", "Partner9", "Partner10"]:
        print(f"Notifying {partner} about the new service booking: Pet Grooming")

# Test when a partner picks up the service and the others get cancelled
def test_partner_pickup():
    # Simulate booking ID and partner name
    booking_id = str(uuid.uuid4())  # Simulated Booking ID
    partner_name = "Partner1"
    
    # Add a new booking to the system manually (for testing purposes)
    bookings[booking_id] = {
        "service": {
            "user_id": "user1",
            "service_name": "Pet Grooming",
            "service_details": "Full grooming session"
        },
        "partners": {partner: "pending" for partner in ["Partner1", "Partner2", "Partner3", "Partner4", "Partner5",
                                                      "Partner6", "Partner7", "Partner8", "Partner9", "Partner10"]}
    }
    
    # Simulate sending POST request to /partner_pickup/{booking_id}/{partner_name}
    response = client.post(f"/partner_pickup/{booking_id}/{partner_name}")
    
    # Check the response for success
    assert response.status_code == 200
    assert "message" in response.json()

    # Print the output when a partner picks up the service
    print(f"Partner '{partner_name}' picked the service with Booking ID: {booking_id}")
    
    # Print the remaining partners whose requests got cancelled
    print("Remaining partners whose requests got cancelled:")
    for partner, status in bookings[booking_id]["partners"].items():
        if status == "removed":
            print(f"- {partner}")

# Test to retrieve booking details and check partner statuses
def test_get_booking():
    booking_id = str(uuid.uuid4())  # Simulated Booking ID
    
    # Simulate adding a booking
    bookings[booking_id] = {
        "service": {
            "user_id": "user1",
            "service_name": "Pet Grooming",
            "service_details": "Full grooming session"
        },
        "partners": {partner: "pending" for partner in ["Partner1", "Partner2", "Partner3", "Partner4", "Partner5",
                                                      "Partner6", "Partner7", "Partner8", "Partner9", "Partner10"]}
    }
    
    # Retrieve the booking
    response = client.get(f"/get_booking/{booking_id}")
    
    # Check if the booking details are returned correctly
    assert response.status_code == 200
    assert "partners" in response.json()
    
    # Print booking and partner status
    print(f"Booking details for ID: {booking_id}")
    print(f"Service: {response.json()['service']['service_name']}")
    print("Partner statuses:")
    for partner, status in response.json()['partners'].items():
        print(f"- {partner}: {status}")
