from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid

app = FastAPI()

# Simulating a simple in-memory store to keep track of bookings
bookings = {}
partners = ["Partner1", "Partner2", "Partner3", "Partner4", "Partner5",
            "Partner6", "Partner7", "Partner8", "Partner9", "Partner10"]

class Booking(BaseModel):
    user_id: str
    service_name: str
    service_details: str

@app.post("/book_service/")
async def book_service(booking: Booking):
    # Generate a unique booking ID
    booking_id = str(uuid.uuid4())
    
    # Save the booking and notify all partners
    bookings[booking_id] = {
        "service": booking,
        "partners": {partner: "pending" for partner in partners}
    }
    
    # Print the booking ID
    print(f"Booking ID: {booking_id} created for service '{booking.service_name}' by user '{booking.user_id}'")
    
    # Notify all partners
    notify_partners(booking_id)
    
    return {"message": "Booking created and sent to partners", "booking_id": booking_id}

@app.post("/partner_pickup/{booking_id}/{partner_name}")
async def partner_pickup(booking_id: str, partner_name: str):
    # Check if the booking exists
    if booking_id not in bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check if the partner is valid
    if partner_name not in partners:
        raise HTTPException(status_code=400, detail="Invalid partner")
    
    # If the partner has not already picked the service, update the status
    if bookings[booking_id]["partners"][partner_name] == "picked":
        raise HTTPException(status_code=400, detail="Service already picked by another partner")
    
    # Update the partner's status to 'picked'
    bookings[booking_id]["partners"][partner_name] = "picked"
    
    # Remove the booking from the remaining partners
    for partner in partners:
        if partner != partner_name:
            bookings[booking_id]["partners"][partner] = "removed"
    
    # Print which partner picked the service and the remaining partners' requests
    print(f"Partner '{partner_name}' picked the service with Booking ID: {booking_id}")
    print("Remaining partners whose requests got cancelled:")
    for partner, status in bookings[booking_id]["partners"].items():
        if status == "removed":
            print(f"- {partner}")

    return {"message": f"Service picked by {partner_name}", "booking_id": booking_id, "partner": partner_name}

@app.get("/get_booking/{booking_id}")
async def get_booking(booking_id: str):
    # Check if the booking exists
    if booking_id not in bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return bookings[booking_id]

def notify_partners(booking_id: str):
    # Here you would send data to the partners via a webhook or some other mechanism
    # For now, just simulate the notification (print the booking data for each partner)
    booking = bookings[booking_id]["service"]
    for partner in partners:
        print(f"Notifying {partner} about the new service booking: {booking.service_name}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("webhook:app", host="0.0.0.0", port=8000, reload=True)