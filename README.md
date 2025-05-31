# Vicino Backend - FastAPI with WebSocket Support

A modern delivery platform backend built with FastAPI, featuring real-time WebSocket communication and Google Sheets integration.

## 🚀 Features

- **Real-time Communication**: WebSocket support for instant order notifications
- **OTP Authentication**: Secure login system for customers and delivery partners
- **Order Management**: Complete order lifecycle from creation to delivery
- **Google Sheets Integration**: Data persistence using Google Apps Script
- **Blockchain Simulation**: Transaction recording for transparency
- **CORS Support**: Ready for frontend integration

## 🏗️ Architecture

```
Dart/Flutter Frontend → FastAPI Backend → Google Apps Script → Google Sheets
                     ↕️ WebSocket
```

## 📋 Prerequisites

- Python 3.8+
- Google Apps Script project set up
- Google Sheets for data storage

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vicino_backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Update Google Apps Script URL**
   
   In `main.py`, update the `APP_SCRIPT_URL` with your Google Apps Script deployment URL:
   ```python
   APP_SCRIPT_URL = "https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec"
   ```

## 🚀 Running the Server

### Development
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production (Vercel)
The project is configured for Vercel deployment with `vercel.json`.

## 🧪 Testing

### 1. Test Login Flow
```bash
python test_complete_flow.py
```

### 2. Test WebSocket Connections
```bash
python websocket_test.py
```

### 3. Manual API Testing

**Send OTP:**
```bash
curl -X POST "http://localhost:8000/login/send_otp" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "9442033333",
    "role": "delivery",
    "location": "Chennai"
  }'
```

**Verify OTP:**
```bash
curl -X POST "http://localhost:8000/login/verify_otp" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "9442033333",
    "otp": "1234"
  }'
```

**Create Order:**
```bash
curl -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "test-customer-123",
    "phone": "9876543210",
    "items": [
      {
        "name": "Carrot",
        "quantity": 2,
        "unit": "kg",
        "price": 10.0
      }
    ]
  }'
```

## 🔌 WebSocket Endpoints

### Delivery Partner Connection
```
ws://localhost:8000/ws/delivery/{user_id}
```

**Receives:**
- New order notifications
- Order status updates

### Customer Connection
```
ws://localhost:8000/ws/customer/{user_id}
```

**Receives:**
- Order acceptance notifications
- Delivery updates

## 📡 API Endpoints

### Authentication
- `POST /login/send_otp` - Send OTP for login
- `POST /login/verify_otp` - Verify OTP and login

### Orders
- `POST /orders` - Create new order
- `GET /orders/available` - Get available orders for delivery
- `POST /orders/{order_id}/accept` - Accept an order
- `POST /orders/{order_id}/verify_otp` - Complete delivery with OTP
- `GET /orders/{order_id}` - Get order details

### Utility
- `GET /items/nearby` - Get nearby items
- `GET /orders/partner/status` - Check delivery partner status
- `GET /blockchain/transactions` - View transaction history

## 🔧 Configuration

### Environment Variables
- `APP_SCRIPT_URL`: Google Apps Script deployment URL

### Google Apps Script Setup
1. Create a new Google Apps Script project
2. Copy all files from `vicino_frontend/appscript/` to your project
3. Deploy as a web app with execute permissions for "Anyone"
4. Update the `APP_SCRIPT_URL` in `main.py`

## 🐛 Troubleshooting

### Common Issues

1. **"Invalid role provided" error**
   - Ensure the role is one of: "customer", "delivery", "admin"
   - Check Google Apps Script logs for detailed errors

2. **WebSocket connection fails**
   - Ensure the server is running on the correct port
   - Check firewall settings
   - Verify the WebSocket URL format

3. **Google Apps Script timeout**
   - Check the Apps Script execution time limits
   - Verify the script has proper permissions
   - Check Google Sheets access permissions

### Debug Mode
Enable debug logging by setting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Data Flow

1. **User Registration/Login**
   ```
   Frontend → FastAPI → Google Apps Script → Google Sheets (Users)
   ```

2. **Order Creation**
   ```
   Frontend → FastAPI → Google Apps Script → Google Sheets (Orders)
                    ↓
   WebSocket notification to delivery partners
   ```

3. **Order Acceptance**
   ```
   Delivery Partner → FastAPI → Google Apps Script → Google Sheets (Orders)
                             ↓
   WebSocket notification to customer
   ```

## 🚀 Deployment

### Vercel Deployment
1. Install Vercel CLI: `npm i -g vercel`
2. Run: `vercel`
3. Follow the prompts

### Environment Setup
Ensure your `vercel.json` includes the Google Apps Script URL:
```json
{
  "env": {
    "APP_SCRIPT_URL": "https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec"
  }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review Google Apps Script logs
3. Test with the provided test scripts
4. Create an issue with detailed error logs 