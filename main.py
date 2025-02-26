from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from enum import Enum
import uuid
import random

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development purposes)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

items_db = [
    {
        "id": "1",
        "name": "Carrot",
        "price": 10.0,
        "store_name": "Local Grocery",
        "image_url": "https://via.placeholder.com/150?text=Carrot"
    },
    {
        "id": "2",
        "name": "Aspirin",
        "price": 50.0,
        "store_name": "Pharmacy",
        "image_url": "https://via.placeholder.com/150?text=Aspirin"
    },
    {
        "id": "3",
        "name": "Banana",
        "price": 5.0,
        "store_name": "Fruit Market",
        "image_url": "https://via.placeholder.com/150?text=Banana"
    },
]

# In‑memory "databases"
orders_db = {}            # {order_id: Order}.
blockchain_ledger = []    # List of transaction records
otp_db ={}                # {phone: otp}
class LoginRequest(BaseModel):
    phone: str
    role: str
    admin_value: Optional[str] = None  # Required if role is "admin"

# Model for OTP verification
class OtpVerificationRequest(BaseModel):
    phone: str
    role: str
    otp: str

class StoreItem(BaseModel):
    id: str
    name: str
    price: float
    store_name: str
    image_url: Optional[str] = None

class OrderStatus(str, Enum):
    PENDING = "Pending"      # Order created, waiting for delivery partner acceptance
    ACCEPTED = "Accepted"    # Order accepted by a delivery partner; OTP generated
    DELIVERED = "Delivered"  # Order delivered after OTP verification

# Model for an item in the order


class Item(BaseModel):
    name: str
    quantity: float   # e.g., 100 for 100g, 3 for 3 items
    unit: Optional[str] = "unit"  # e.g., g, mg, items
    price: float      # Price per unit

# Model for order creation by the customer


class OrderCreate(BaseModel):
    customer_id: str
    items: List[Item]

# Order model stored in our orders_db


class Order(BaseModel):
    id: str
    customer_id: str
    items: List[Item]
    total_amount: float
    status: OrderStatus
    assigned_partner_id: Optional[str] = None
    otp: Optional[str] = None

# Request model when a delivery partner accepts an order


class AcceptOrderRequest(BaseModel):
    delivery_partner_id: str

# Request model for OTP verification by the customer


class VerifyOTPRequest(BaseModel):
    otp: str

# Model representing a blockchain transaction record


class TransactionRecord(BaseModel):
    order_id: str
    customer_id: str
    delivery_partner_id: str
    order_total: float
    reward_bonus: float
    partner_commission: float
    platform_commission: float

# ------------------ Helper Functions ------------------


def calculate_order_total(items: List[Item]) -> float:
    """Calculate total order amount based on items, quantity, and unit price."""
    return sum(item.price * item.quantity for item in items)


def calculate_reward_bonus(total: float) -> float:
    """
    Calculate the reward bonus based on the order total:
    - ₹1 to ₹100: 20%
    - ₹100 to ₹500: 15%
    - Above ₹500: 10%
    """
    if total <= 100:
        return total * 0.20
    elif total <= 500:
        return total * 0.15
    else:
        return total * 0.10


def calculate_commission(total: float):
    """
    Calculate commissions.
    For example, for an order of ₹500:
      - Delivery partner gets 2% (₹10)
      - Platform gets 8% (₹40)
    These values are fixed percentages of the order total.
    """
    partner_commission = total * 0.02
    platform_commission = total * 0.08
    return partner_commission, platform_commission


def record_blockchain_transaction(record: TransactionRecord):
    """
    Simulate recording a transaction on the blockchain.
    In production, this function would interact with an actual blockchain network.
    """
    blockchain_ledger.append(record.dict())

# ------------------ API Endpoints ------------------
@app.post("/login/send_otp")
def send_otp(login_request: LoginRequest):
    # For admin role, ensure the additional field is correct
    if login_request.role == "admin":
        if login_request.admin_value != "adminotp":
            raise HTTPException(status_code=400, detail="Invalid admin credentials")
    
    # For demonstration, we always send the same OTP ("1234")
    otp = "1234"
    otp_db[login_request.phone] = otp
    
    # In production, you would integrate with an SMS service to send the OTP.
    return {
        "message": f"OTP sent to {login_request.phone}",
        "otp": otp  # Remove OTP from the response in a real app!
    }

@app.post("/login/verify_otp")
def verify_otp(otp_request: OtpVerificationRequest):
    # Check if the OTP was previously sent for this phone number
    if otp_request.phone not in otp_db:
        raise HTTPException(status_code=404, detail="OTP not found for the provided phone number")
    
    stored_otp = otp_db[otp_request.phone]
    if otp_request.otp != stored_otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Remove the OTP after successful verification to simulate one-time use
    del otp_db[otp_request.phone]
    
    # Return a role-based success response
    if otp_request.role == "admin":
        return {"message": "Admin login successful", "role": "admin"}
    elif otp_request.role == "customer":
        return {"message": "Customer login successful", "role": "customer"}
    elif otp_request.role == "deliveryPartner":
        return {"message": "Delivery Partner login successful", "role": "deliveryPartner"}
    else:
        raise HTTPException(status_code=400, detail="Invalid role provided")
@app.get("/items/nearby", response_model=List[StoreItem])
def get_nearby_items():
    return items_db

@app.post("/orders", response_model=Order)
def create_order(order_data: OrderCreate):
    """
    Customer creates an order with multiple items.
    The total amount is calculated and the order status is set to Pending.
    """
    order_id = str(uuid.uuid4())
    total = calculate_order_total(order_data.items)
    order = Order(
        id=order_id,
        customer_id=order_data.customer_id,
        items=order_data.items,
        total_amount=total,
        status=OrderStatus.PENDING
    )
    orders_db[order_id] = order
    return order


@app.get("/orders/available", response_model=List[Order])
def get_available_orders():
    """
    Delivery partners fetch available orders.
    Only orders with status 'Pending' are returned.
    """
    return [order for order in orders_db.values() if order.status == OrderStatus.PENDING]


@app.post("/orders/{order_id}/accept", response_model=Order)
def accept_order(order_id: str, accept_req: AcceptOrderRequest):
    """
    A delivery partner accepts an order.
    The order status changes to Accepted, an OTP is generated (simulating sending to the customer),
    and the partner's ID is recorded.
    """
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    order = orders_db[order_id]
    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=400, detail="Order not available for acceptance")

    order.assigned_partner_id = accept_req.delivery_partner_id
    order.status = OrderStatus.ACCEPTED
    # Generate a 4-digit OTP for the customer to verify delivery
    order.otp = str(random.randint(1000, 9999))
    orders_db[order_id] = order

    # In a real app, the OTP would be sent via SMS or email.
    return order


@app.post("/orders/{order_id}/verify_otp", response_model=TransactionRecord)
def verify_order_otp(order_id: str, verify_req: VerifyOTPRequest):
    """
    After receiving their items, the customer verifies the OTP.
    If correct, the order is marked as Delivered, commissions and rewards are calculated,
    and a blockchain transaction is recorded.
    """
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    order = orders_db[order_id]
    if order.status != OrderStatus.ACCEPTED:
        raise HTTPException(
            status_code=400, detail="Order not in a verifiable state")
    if order.otp != verify_req.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP provided")

    # Mark order as delivered
    order.status = OrderStatus.DELIVERED
    orders_db[order_id] = order

    # Calculate reward bonus and commissions
    reward_bonus = calculate_reward_bonus(order.total_amount)
    partner_commission, platform_commission = calculate_commission(
        order.total_amount)
    transaction = TransactionRecord(
        order_id=order.id,
        customer_id=order.customer_id,
        delivery_partner_id=order.assigned_partner_id,
        order_total=order.total_amount,
        reward_bonus=reward_bonus,
        partner_commission=partner_commission,
        platform_commission=platform_commission
    )
    # Record the transaction on our simulated blockchain ledger
    record_blockchain_transaction(transaction)
    return transaction


@app.get("/orders/{order_id}", response_model=Order)
def get_order_details(order_id: str):
    """Retrieve details of a specific order."""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders_db[order_id]


@app.get("/blockchain/transactions", response_model=List[TransactionRecord])
def get_blockchain_transactions():
    """View the list of blockchain transaction records (for demonstration purposes)."""
    return blockchain_ledger


# Run the server using: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
