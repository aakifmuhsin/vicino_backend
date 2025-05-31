from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from enum import Enum
import uuid
import random
import time
import httpx
import json
import asyncio

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development purposes)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# WebSocket Connection Manager


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[Dict]] = {
            "delivery_partners": [],
            "customers": []
        }

    async def connect(self, websocket: WebSocket, client_type: str, user_id: str = None):
        await websocket.accept()
        if client_type not in self.active_connections:
            self.active_connections[client_type] = []

        connection_info = {
            "websocket": websocket,
            "user_id": user_id
        }
        self.active_connections[client_type].append(connection_info)
        print(f"Client {user_id} connected to {client_type}")

    def disconnect(self, websocket: WebSocket, client_type: str):
        connections = self.active_connections.get(client_type, [])
        self.active_connections[client_type] = [
            conn for conn in connections if conn["websocket"] != websocket
        ]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            pass

    async def broadcast_to_delivery_partners(self, message: str):
        connections = self.active_connections.get("delivery_partners", [])
        disconnected = []

        for connection in connections:
            try:
                await connection["websocket"].send_text(message)
            except:
                disconnected.append(connection)

        # Remove disconnected websockets
        for conn in disconnected:
            self.disconnect(conn["websocket"], "delivery_partners")

    async def notify_customer(self, customer_id: str, message: str):
        connections = self.active_connections.get("customers", [])
        for connection in connections:
            if connection["user_id"] == customer_id:
                try:
                    await connection["websocket"].send_text(message)
                except:
                    self.disconnect(connection["websocket"], "customers")


manager = ConnectionManager()

APP_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxJiaNe-MaSm3vXlDKb6PvHUyq5IxXIfkguKQMkfMr7Y5f9PMyhTOLPoq4IfUA8LHeK/exec"
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
# orders_db = {}            # {order_id: Order}.
# blockchain_ledger = []    # List of transaction records
# otp_db = {}                # {phone: otp}
# user_db = {}  # {user_id: user_info}


class LoginRequest(BaseModel):
    phone: str
    role: str  # Should be one of: "customer", "delivery", "admin"
    location: Optional[str] = None  # Required if role is "admin"

# Model for OTP verification


class OtpVerificationRequest(BaseModel):
    phone: str
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
    phone: str  # Add phone number here
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


async def make_appscript_request(endpoint: str, payload: dict):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                APP_SCRIPT_URL,
                params={"path": endpoint},
                json=payload,
                timeout=30,
                follow_redirects=True
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"AppScript API error: {e.response.text}"
            )


def generate_unique_id(role: str) -> str:
    """Generate a unique user ID based on role."""
    return str(uuid.uuid4())


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
# GOOOOOOOOOGLEEEEEEEEEEEE SSSSSSSCCCCCCCRRRRRRRIIIIIIIIIIIIPPPPPPPPPPTTTTTTTTTTT


@app.post("/login/send_otp")
async def send_otp(login_request: LoginRequest):
    # Standardize role name
    role = login_request.role.lower()
    if role == "deliverypartner":
        role = "delivery"

    response = await make_appscript_request("send_otp", {
        "phone": login_request.phone,
        "role": role,
        "location": login_request.location
    })

    return {
        "message": f"OTP sent to {login_request.phone}",
        "user_id": response.get("userId"),
        "otp": response.get("otp")  # Remove in production
    }


@app.post("/login/verify_otp")
async def verify_otp(otp_request: OtpVerificationRequest):
    try:
        otp_request_otp = int(otp_request.otp)
        response = await make_appscript_request("verify_otp", {
            "phone": otp_request.phone,
            "otp": otp_request_otp
        })

        if not response.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.get("message", "Invalid OTP or user not found")
            )

        return {
            "message": f"{response.get('role')} login successful",
            "role": response.get("role"),
            "user_id": response.get("userId")
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@app.post("/orders", response_model=Order)
async def create_order(order_data: OrderCreate):
    # Calculate total first
    total = calculate_order_total(order_data.items)
    # Prepare items for serialization
    items_serialized = [item.dict() for item in order_data.items]

    response = await make_appscript_request("create_order", {
        "customerId": order_data.customer_id,
        "phone": order_data.phone,
        "items": items_serialized,
        "totalAmount": total
    })

    order = Order(
        id=response["orderId"],
        customer_id=order_data.customer_id,
        items=order_data.items,
        total_amount=total,
        status=OrderStatus.PENDING
    )

    # Broadcast new order to all delivery partners
    order_notification = {
        "type": "new_order",
        "order": {
            "id": order.id,
            "customer_id": order.customer_id,
            "items": [item.dict() for item in order.items],
            "total_amount": order.total_amount,
            "status": order.status.value
        }
    }

    await manager.broadcast_to_delivery_partners(json.dumps(order_notification))

    return order


@app.get("/orders/available", response_model=List[Order])
async def get_available_orders():
    response = await make_appscript_request("get_available_orders", {})

    orders = []
    for order_data in response["orders"]:
        orders.append(Order(
            id=order_data["id"],
            customer_id=order_data["customerId"],
            items=[Item(**item) for item in order_data["items"]],
            total_amount=order_data["totalAmount"],
            status=OrderStatus(order_data["status"]),
            assigned_partner_id=order_data.get("assignedPartnerId"),
            otp=order_data.get("otp")
        ))

    return orders


@app.post("/orders/{order_id}/accept", response_model=Order)
async def accept_order(order_id: str, accept_req: AcceptOrderRequest):
    response = await make_appscript_request("assign_order", {
        "orderId": order_id,
        "partnerId": accept_req.delivery_partner_id
    })
    order = Order(
        id=order_id,
        customer_id=response["customerId"],
        items=[Item(**item) for item in response["items"]],
        total_amount=response["totalAmount"],
        status=OrderStatus.ACCEPTED,  # Change to ACCEPTED when delivery partner accepts
        assigned_partner_id=accept_req.delivery_partner_id,
        otp=response["otp"]  # OTP sent to the delivery partner
    )

    # Notify customer that order has been accepted
    customer_notification = {
        "type": "order_accepted",
        "order_id": order.id,
        "delivery_partner_id": order.assigned_partner_id,
        "message": "Your order has been accepted by a delivery partner"
    }

    await manager.notify_customer(order.customer_id, json.dumps(customer_notification))

    # Notify other delivery partners that this order is no longer available
    order_taken_notification = {
        "type": "order_taken",
        "order_id": order.id,
        "message": "This order has been taken by another delivery partner"
    }

    await manager.broadcast_to_delivery_partners(json.dumps(order_taken_notification))

    return order


@app.post("/orders/{order_id}/verify_otp", response_model=TransactionRecord)
async def verify_order_otp(order_id: str, verify_req: VerifyOTPRequest):
    response = await make_appscript_request("close_order", {
        "orderId": order_id,
        "otp": verify_req.otp
    })

    # Ensure the response contains details for blockchain transaction
    return TransactionRecord(
        order_id=order_id,
        customer_id=response["customerId"],
        delivery_partner_id=response["deliveryPartnerId"],
        order_total=response["orderTotal"],
        reward_bonus=response["rewardBonus"],
        partner_commission=response["partnerCommission"],
        platform_commission=response["platformCommission"]
    )


@app.post("/users/register")
async def register_user(register_data: LoginRequest):
    """
    Register a new user after successful OTP verification.
    The role and phone are required.
    """
    response = await make_appscript_request("register_user", {
        "phone": register_data.phone,
        "role": register_data.role,
        "location": register_data.location
    })
    return response


@app.get("/items/nearby", response_model=List[StoreItem])
async def get_nearby_items():
    response = await make_appscript_request("get_nearby_items", {})
    return response.get("items", [])


@app.get("/orders/partner/status")
async def check_partner_status(delivery_partner_id: str):
    """
    Check if a delivery partner is already assigned to an ongoing order.
    Returns true if the partner is free to accept new orders, false if they have an ongoing unverified order.
    """
    response = await make_appscript_request("check_partner_status", {
        "deliveryPartnerId": delivery_partner_id
    })
    return response


@app.get("/orders/{order_id}", response_model=Order)
async def get_order_details(order_id: str):
    """
    Retrieve details of a specific order.
    """
    response = await make_appscript_request("get_order_details", {"orderId": order_id})
    return Order(
        id=response["id"],
        customer_id=response["customerId"],
        items=[Item(**item) for item in response["items"]],
        total_amount=response["totalAmount"],
        status=OrderStatus(response["status"]),
        assigned_partner_id=response.get("assignedPartnerId"),
        otp=response.get("otp")
    )


@app.get("/blockchain/transactions", response_model=List[TransactionRecord])
async def get_blockchain_transactions():
    """
    View the list of blockchain transaction records (for demonstration purposes).
    """
    response = await make_appscript_request("get_blockchain_transactions", {})
    return response.get("transactions", [])

# SQLLLLLLLLLLLLLLLLLLLLLLLLLLLL

# @app.post("/login/send_otp")
# def send_otp(login_request: LoginRequest):
#     # Standardize the role name
#     if login_request.role.lower() == "deliverypartner":
#         login_request.role = "delivery"

#     user = next((user for user in user_db.values()
#                 if user["phone"] == login_request.phone), None)

#     if user:
#         # Find the user_id by matching the phone number
#         user_id = next(uid for uid, u in user_db.items()
#                        if u["phone"] == login_request.phone)
#     else:
#         user_id = generate_unique_id(login_request.role)
#         user_db[user_id] = {
#             "phone": login_request.phone,
#             "role": login_request.role,
#             "location": login_request.location
#         }

#     otp = str(random.randint(1000, 9999))
#     otp_db[login_request.phone] = {"otp": otp, "timestamp": time.time()}

#     return {"message": f"OTP sent to {login_request.phone}", "user_id": user_id, "otp": otp}


# @app.post("/login/verify_otp")
# def verify_otp(otp_request: OtpVerificationRequest):
#     if otp_request.phone not in otp_db:
#         raise HTTPException(
#             status_code=404, detail="OTP not found for the provided phone number")

#     stored_otp = otp_db[otp_request.phone]
#     if otp_request.otp != stored_otp["otp"]:
#         raise HTTPException(status_code=400, detail="Invalid OTP")

#     del otp_db[otp_request.phone]

#     # Find user by phone number
#     user_id = next((uid for uid, user in user_db.items()
#                    if user["phone"] == otp_request.phone), None)

#     if not user_id:
#         raise HTTPException(
#             status_code=404, detail="User not found. Please complete registration first.")

#     user = user_db[user_id]
#     return {"message": f"{user['role']} login successful",
#             "role": user["role"],
#             "user_id": user_id}


# @app.post("/orders", response_model=Order)
# def create_order(order_data: OrderCreate):
#     """
#     Customer creates an order with multiple items.
#     The total amount is calculated and the order status is set to Pending.
#     If the user does not exist, they are registered automatically.
#     """
#     if order_data.customer_id not in user_db:
#         # Register user if they don't exist in the database
#         user_db[order_data.customer_id] = {
#             "phone": order_data.phone,  # Store phone number from the order data
#             "role": "customer",  # Set role to customer by default
#         }
#     order_id = str(uuid.uuid4())
#     total = calculate_order_total(order_data.items)
#     order = Order(
#         id=order_id,
#         customer_id=order_data.customer_id,
#         items=order_data.items,
#         total_amount=total,
#         status=OrderStatus.PENDING
#     )
#     orders_db[order_id] = order
#     return order


# @app.get("/orders/available", response_model=List[Order])
# def get_available_orders():
#     """
#     Delivery partners fetch available orders.
#     Only orders with status 'Pending' are returned.
#     """
#     return [order for order in orders_db.values() if order.status == OrderStatus.PENDING]


# @app.post("/orders/{order_id}/accept", response_model=Order)
# def accept_order(order_id: str, accept_req: AcceptOrderRequest):
#     """
#     A delivery partner accepts an order.
#     The order status changes to Accepted, an OTP is generated (simulating sending to the customer),
#     and the partner's ID is recorded. The partner will be prevented from accepting another order until OTP is verified.
#     """
#     # Check if delivery partner exists
#     if accept_req.delivery_partner_id not in user_db:
#         raise HTTPException(
#             status_code=404, detail="Delivery partner not found")

#     # Check if partner's role is correct
#     if user_db[accept_req.delivery_partner_id]["role"] != "delivery":
#         raise HTTPException(
#             status_code=403, detail="Only delivery partners can accept orders")

#     # Check if partner has ongoing orders
#     ongoing_order = next((order for order in orders_db.values()
#                          if order.assigned_partner_id == accept_req.delivery_partner_id
#                          and order.status != OrderStatus.DELIVERED), None)
#     if ongoing_order:
#         raise HTTPException(
#             status_code=400, detail="You cannot accept a new order until the current one is delivered and OTP is verified")

#     if order_id not in orders_db:
#         raise HTTPException(status_code=404, detail="Order not found")

#     order = orders_db[order_id]
#     if order.status != OrderStatus.PENDING:
#         raise HTTPException(
#             status_code=400, detail="Order not available for acceptance")

#     order.assigned_partner_id = accept_req.delivery_partner_id
#     order.status = OrderStatus.ACCEPTED
#     # Generate a 4-digit OTP for the customer to verify delivery
#     order.otp = str(random.randint(1000, 9999))
#     orders_db[order_id] = order

#     # In a real app, the OTP would be sent via SMS or email.
#     return order


# @app.post("/orders/{order_id}/verify_otp", response_model=TransactionRecord)
# def verify_order_otp(order_id: str, verify_req: VerifyOTPRequest):
#     """
#     After receiving their items, the customer verifies the OTP.
#     If correct, the order is marked as Delivered, commissions and rewards are calculated,
#     and a blockchain transaction is recorded. The delivery partner is then freed up for new orders.
#     """
#     if order_id not in orders_db:
#         raise HTTPException(status_code=404, detail="Order not found")

#     order = orders_db[order_id]
#     if order.status != OrderStatus.ACCEPTED:
#         raise HTTPException(
#             status_code=400, detail="Order not in a verifiable state")
#     if order.otp != verify_req.otp:
#         raise HTTPException(status_code=400, detail="Invalid OTP provided")

#     # Mark order as delivered and close it
#     order.status = OrderStatus.DELIVERED
#     orders_db[order_id] = order

#     # Calculate reward bonus and commissions
#     reward_bonus = calculate_reward_bonus(order.total_amount)
#     partner_commission, platform_commission = calculate_commission(
#         order.total_amount)

#     transaction = TransactionRecord(
#         order_id=order.id,
#         customer_id=order.customer_id,
#         delivery_partner_id=order.assigned_partner_id,
#         order_total=order.total_amount,
#         reward_bonus=reward_bonus,
#         partner_commission=partner_commission,
#         platform_commission=platform_commission
#     )

#     # Record the transaction on our simulated blockchain ledger
#     record_blockchain_transaction(transaction)
#     return transaction

# @app.post("/users/register")
# def register_user(register_data: LoginRequest):
#     """
#     Register a new user after successful OTP verification.
#     The role and phone are required.
#     """
#     # Check if user exists by phone number
#     existing_user_id = next((uid for uid, user in user_db.items()
#                              if user["phone"] == register_data.phone), None)

#     if existing_user_id:
#         # Update existing user instead of creating new one
#         user_db[existing_user_id].update({
#             "role": register_data.role,
#             "location": register_data.location
#         })
#         return {"message": "User updated successfully", "user_id": existing_user_id}

#     # Only create new user if they don't exist
#     user_id = generate_unique_id(register_data.role)
#     user_db[user_id] = {
#         "phone": register_data.phone,
#         "role": register_data.role,
#         "location": register_data.location
#     }

#     return {"message": f"User registered successfully with user_id {user_id}", "user_id": user_id}


# @app.get("/items/nearby", response_model=List[StoreItem])
# def get_nearby_items():
#     return items_db

# @app.get("/orders/partner/status")
# def check_partner_status(delivery_partner_id: str):
#     """
#     Check if a delivery partner is already assigned to an ongoing order.
#     Returns true if the partner is free to accept new orders, false if they have an ongoing unverified order.
#     """
#     ongoing_order = next(
#         (order for order in orders_db.values() if order.assigned_partner_id ==
#          delivery_partner_id and order.status == OrderStatus.ACCEPTED),
#         None
#     )
#     if ongoing_order:
#         return {"status": "busy", "order_id": ongoing_order.id}
#     else:
#         return {"status": "free"}

# @app.get("/orders/{order_id}", response_model=Order)
# def get_order_details(order_id: str):
#     """Retrieve details of a specific order."""
#     if order_id not in orders_db:
#         raise HTTPException(status_code=404, detail="Order not found")
#     return orders_db[order_id]


# @app.get("/blockchain/transactions", response_model=List[TransactionRecord])
# def get_blockchain_transactions():
#     """View the list of blockchain transaction records (for demonstration purposes)."""
#     return blockchain_ledger

# WebSocket endpoints
@app.websocket("/ws/delivery/{user_id}")
async def websocket_delivery_partner(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, "delivery_partners", user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle ping/pong or other messages from delivery partners
            await manager.send_personal_message(f"Echo: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "delivery_partners")
        print(f"Delivery partner {user_id} disconnected")


@app.websocket("/ws/customer/{user_id}")
async def websocket_customer(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, "customers", user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle ping/pong or other messages from customers
            await manager.send_personal_message(f"Echo: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "customers")
        print(f"Customer {user_id} disconnected")

# Run the server using: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
