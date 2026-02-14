# Smart City Parking System 🚗

A comprehensive peer-to-peer parking marketplace platform for smart cities, built with Flask and MongoDB.

## 🌟 Features

### For Drivers (Users)
- 🔍 Search parking spaces by location, price, and availability
- 📱 Real-time booking system
- 💳 Multiple payment options (Razorpay INR & NOWPayments Crypto)
- 💰 Digital wallet for easy transactions
- 💬 In-app chat with parking owners
- ⭐ Rating and review system
- 📊 Booking history and management

### For Hosts (Parking Owners)
- 📝 List parking spaces with photos and details
- ⏰ Set availability schedules and pricing
- 💵 Receive payments directly to wallet
- ✅ Confirm/reject bookings
- 💬 Communicate with renters
- 📈 Track earnings and statistics

### For Admins
- 🛡️ Approve/reject parking listings
- 👥 User management
- 🔍 Monitor all bookings and transactions
- 🎯 Resolve disputes and issues
- 📊 Comprehensive dashboard with analytics

## 🏗️ Architecture

### Tech Stack
- **Backend**: Flask (Python)
- **Database**: MongoDB (with PyMongo)
- **Authentication**: JWT (Flask-JWT-Extended)
- **Payments**: Razorpay (INR) & NOWPayments (Crypto)
- **File Upload**: Local storage with Werkzeug

### Project Structure
```
smartcity-parking/
├── app.py                  # Main application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── models/
│   ├── database.py       # Database connection & helpers
│   ├── user.py           # User model
│   ├── parking.py        # Parking space model
│   ├── booking.py        # Booking model
│   ├── wallet.py         # Wallet & transactions
│   ├── review.py         # Review model
│   └── message.py        # Chat/messaging model
├── routes/
│   ├── auth.py           # Authentication endpoints
│   ├── parking.py        # Parking CRUD operations
│   ├── booking.py        # Booking management
│   ├── payment.py        # Payment processing
│   ├── wallet.py         # Wallet operations
│   ├── chat.py           # Messaging system
│   ├── admin.py          # Admin functions
│   └── user.py           # User profile & dashboard
└── static/
    └── uploads/          # Uploaded images
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- MongoDB Atlas account or local MongoDB
- Razorpay account (for INR payments)
- NOWPayments account (for crypto payments)

### Step 1: Clone & Setup
```bash
# Create project directory
mkdir smartcity-parking
cd smartcity-parking

# Copy all files to this directory

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Edit `.env` file with your credentials:
```env
# MongoDB - Update with your connection string
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster0

# Razorpay - Get from https://dashboard.razorpay.com/
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

# NOWPayments - Get from https://nowpayments.io/
NOWPAYMENTS_API_KEY=your_nowpayments_api_key

# Google Maps (optional) - Get from Google Cloud Console
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

### Step 3: Run the Application
```bash
# Development mode
python app.py

# Production mode with Gunicorn
gunicorn app:app --bind 0.0.0.0:5000
```

The API will be available at `http://localhost:5000`

## 📚 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "John Doe",
  "phone": "1234567890",
  "role": "driver"  // or "host" or "admin"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

#### Get Profile
```http
GET /api/auth/profile
Authorization: Bearer <jwt_token>
```

### Parking Endpoints

#### Create Parking Space
```http
POST /api/parking/create
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "title": "Secure Garage Parking",
  "description": "Covered parking near metro station",
  "address": "123 Main St, Mumbai",
  "latitude": 19.0760,
  "longitude": 72.8777,
  "vehicle_type": "both",  // "2-wheeler", "4-wheeler", or "both"
  "price_per_hour": 50,
  "total_hours": 10,
  "available_from": "2024-02-06T00:00:00Z",
  "available_to": "2024-02-16T23:59:59Z",
  "total_spaces": 1,
  "amenities": ["covered", "security", "cctv"],
  "instructions": "Call upon arrival"
}
```

#### Search Parking
```http
GET /api/parking/search?latitude=19.0760&longitude=72.8777&radius=5000&vehicle_type=4-wheeler&max_price=100
```

#### Get Parking Details
```http
GET /api/parking/<parking_id>
```

### Booking Endpoints

#### Create Booking
```http
POST /api/booking/create
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "parking_id": "parking_space_id",
  "start_time": "2024-02-06T10:00:00Z",
  "end_time": "2024-02-06T18:00:00Z",
  "vehicle_number": "MH02AB1234",
  "vehicle_type": "4-wheeler"
}
```

#### Get My Bookings
```http
GET /api/booking/my-bookings?status=confirmed
Authorization: Bearer <jwt_token>
```

#### Confirm Booking (Host)
```http
POST /api/booking/<booking_id>/confirm
Authorization: Bearer <jwt_token>
```

#### Cancel Booking
```http
POST /api/booking/<booking_id>/cancel
Authorization: Bearer <jwt_token>
```

### Payment Endpoints

#### Create Razorpay Order
```http
POST /api/payment/create-order
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "amount": 500,
  "booking_id": "booking_id_optional"
}
```

#### Verify Payment
```http
POST /api/payment/verify-payment
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "razorpay_order_id": "order_xxx",
  "razorpay_payment_id": "pay_xxx",
  "razorpay_signature": "signature_xxx",
  "booking_id": "booking_id_optional"
}
```

#### Pay with Wallet
```http
POST /api/payment/book-with-wallet
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "booking_id": "booking_id"
}
```

#### Create Crypto Payment
```http
POST /api/payment/crypto/create-payment
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "amount": 50,  // Amount in USD
  "currency": "btc",  // btc, eth, usdt, etc.
  "booking_id": "booking_id_optional"
}
```

### Wallet Endpoints

#### Get Balance
```http
GET /api/wallet/balance
Authorization: Bearer <jwt_token>
```

#### Get Wallet Details
```http
GET /api/wallet/details
Authorization: Bearer <jwt_token>
```

#### Get Transactions
```http
GET /api/wallet/transactions?limit=50
Authorization: Bearer <jwt_token>
```

#### Add Money (Testing)
```http
POST /api/wallet/add-money
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "amount": 1000,
  "description": "Wallet recharge"
}
```

### Chat Endpoints

#### Send Message
```http
POST /api/chat/send
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "booking_id": "booking_id",
  "content": "Hello, is the parking available?"
}
```

#### Get Booking Messages
```http
GET /api/chat/booking/<booking_id>
Authorization: Bearer <jwt_token>
```

#### Get All Conversations
```http
GET /api/chat/conversations
Authorization: Bearer <jwt_token>
```

### Admin Endpoints

#### Get Dashboard Stats
```http
GET /api/admin/dashboard
Authorization: Bearer <admin_jwt_token>
```

#### Get Pending Parking Approvals
```http
GET /api/admin/parking/pending
Authorization: Bearer <admin_jwt_token>
```

#### Approve Parking
```http
POST /api/admin/parking/<parking_id>/approve
Authorization: Bearer <admin_jwt_token>
```

#### Reject Parking
```http
POST /api/admin/parking/<parking_id>/reject
Authorization: Bearer <admin_jwt_token>
Content-Type: application/json

{
  "reason": "Incomplete information"
}
```

## 💡 Key Business Rules

### Minimum Rental Duration
- Renters must book at least **70% of the total available hours**
- Example: If a parking space is listed for 10 hours, minimum booking is 7 hours

### Payment Flow
1. User creates a booking (status: `pending`)
2. User pays via Razorpay/Crypto or Wallet (status: `pending` → payment_status: `completed`)
3. Host confirms the booking after receiving payment (status: `confirmed`)
4. Booking becomes active at start time (status: `active`)
5. Booking completes at end time (status: `completed`)
6. Payment transferred to host's wallet

### Refund Policy
- Bookings can be cancelled by either party
- Cancelled bookings trigger automatic refund to user's wallet
- Hosts receive payment only after booking completion

## 🔐 Security Features

- JWT-based authentication
- Password hashing with Werkzeug
- Role-based access control (Driver, Host, Admin)
- Payment signature verification
- Input validation and sanitization
- CORS protection

## 📊 Database Collections

### users
- User authentication and profiles
- Roles: driver, host, admin

### parking_spaces
- Parking space listings
- Location (GeoJSON for spatial queries)
- Status: pending, approved, rejected, inactive

### bookings
- Rental bookings
- Status: pending, confirmed, active, completed, cancelled
- Payment tracking

### wallets
- User wallet balances
- Credit/debit tracking

### wallet_transactions
- Transaction history
- Types: credit, debit, refund, earning, withdrawal

### messages
- In-app chat messages
- Linked to bookings

### reviews
- Parking space ratings
- User feedback

## 🚀 Deployment

### Render Deployment
1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Configure environment variables
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `gunicorn app:app`

### Railway Deployment
1. Create a new project on Railway
2. Connect your GitHub repository
3. Add environment variables
4. Railway will auto-detect Python and deploy

### Environment Variables to Set
- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `MONGO_URI`
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- `NOWPAYMENTS_API_KEY`
- `GOOGLE_MAPS_API_KEY`
- `MAIL_USERNAME` (optional)
- `MAIL_PASSWORD` (optional)

## 🧪 Testing

### Create Test Users
```bash
# Create admin user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin",
    "password": "admin321",
    "name": "Admin User",
    "phone": "9999999999",
    "role": "admin"
  }'

# Create host user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "host@test.com",
    "password": "host123",
    "name": "Parking Host",
    "phone": "8888888888",
    "role": "host"
  }'

# Create driver user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "driver@test.com",
    "password": "driver123",
    "name": "Driver User",
    "phone": "7777777777",
    "role": "driver"
  }'
```

## 📝 License

This project is licensed under the MIT License.

## 👥 Support

For issues and questions:
- Email: akash.bluee@gmail.com
- Create an issue on GitHub

## 🙏 Acknowledgments

- Flask framework
- MongoDB Atlas
- Razorpay for payment gateway
- NOWPayments for crypto payments
