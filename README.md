# Parking Management System

A complete web-based parking management system with real-time slot booking, user authentication, and payment tracking.

## Features

- 🚗 Real-time parking slot availability
- 👤 User authentication & profile management
- 📅 Online booking system
- 💳 Payment tracking
- 📊 Dashboard with statistics
- 📱 Responsive design (mobile-friendly)
- 🔒 Secure JWT authentication

## Tech Stack

- **Backend:** Flask (Python)
- **Database:** MongoDB
- **Frontend:** HTML, CSS, JavaScript
- **Authentication:** JWT (JSON Web Tokens)
- **Password Hashing:** bcrypt

## Prerequisites

- Python 3.8 or higher
- MongoDB (local or Atlas)
- pip (Python package manager)

## Installation

### 1. Install MongoDB (Ubuntu/Debian)

```bash
# Install MongoDB
sudo apt update
sudo apt install -y mongodb

# Start MongoDB service
sudo systemctl start mongodb
sudo systemctl enable mongodb

# Check status
sudo systemctl status mongodb
```

### 2. Clone/Setup Project

```bash
cd parking-system
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or install packages individually:

```bash
pip install Flask==3.0.0 pymongo==4.6.0 python-dotenv==1.0.0 Flask-CORS==4.0.0 bcrypt==4.1.2 PyJWT==2.8.0 dnspython==2.4.2
```

### 4. Configure Environment Variables

The `.env` file is already created with default settings. For production, update:

```env
SECRET_KEY=your-production-secret-key-here
MONGODB_URI=mongodb://localhost:27017/
DB_NAME=parking_db
```

### 5. Initialize Database

Run the setup script to create collections and default data:

```bash
python setup.py
```

This will:
- Create database collections
- Add indexes for performance
- Create 60 parking slots (Regular, VIP, Handicapped)
- Create a test user account

**Test User Credentials:**
- Email: test@parking.com
- Password: test123

### 6. Start the Application

```bash
python app.py
```

The server will start on: http://localhost:5000

## Usage

### Access the Website

1. **Homepage:** http://localhost:5000
   - View features, pricing, and contact information
   - Register for a new account
   - Login to existing account

2. **Dashboard:** http://localhost:5000/dashboard (after login)
   - View parking statistics
   - Book parking slots
   - Manage bookings
   - Update profile

### API Endpoints

#### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/verify` - Verify JWT token

#### Parking Slots
- `GET /api/slots` - Get all slots
- `GET /api/slots/<id>` - Get specific slot
- `GET /api/slots/available` - Get available slots
- `PUT /api/slots/<id>/status` - Update slot status (admin)

#### Bookings
- `POST /api/bookings` - Create new booking
- `GET /api/bookings/my` - Get user's bookings
- `GET /api/bookings/<id>` - Get specific booking
- `PUT /api/bookings/<id>/cancel` - Cancel booking

#### Users
- `GET /api/users/profile` - Get user profile
- `PUT /api/users/profile` - Update user profile
- `GET /api/users` - Get all users (admin)

### API Testing

Check API status:
```bash
curl http://localhost:5000/api/status
```

## Project Structure

```
parking-system/
├── app.py                  # Main Flask application
├── setup.py               # Database setup script
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── config/
│   └── database.py        # Database configuration
├── routes/
│   ├── auth.py           # Authentication routes
│   ├── slots.py          # Parking slots routes
│   ├── bookings.py       # Bookings routes
│   ├── users.py          # Users routes
│   └── middleware.py     # Authentication middleware
├── static/
│   ├── css/
│   │   ├── style.css     # Main stylesheet
│   │   └── dashboard.css # Dashboard stylesheet
│   └── js/
│       ├── main.js       # Homepage JavaScript
│       └── dashboard.js  # Dashboard JavaScript
└── templates/
    ├── index.html        # Homepage
    └── dashboard.html    # Dashboard page
```

## Default Parking Slots

The system creates 60 parking slots by default:

- **Regular Slots (A01-A50):** ₹50/hour
  - 25 slots on Floor 1
  - 25 slots on Floor 2

- **VIP Slots (V01-V05):** ₹100/hour
  - Premium covered parking
  - Located on Floor 1

- **Handicapped Slots (H01-H05):** ₹40/hour
  - Accessible parking
  - Near entrance (Floor 1)

## Troubleshooting

### MongoDB Connection Error

If you get "MongoDB connection failed":

1. Check if MongoDB is running:
   ```bash
   sudo systemctl status mongodb
   ```

2. Start MongoDB:
   ```bash
   sudo systemctl start mongodb
   ```

3. Check MongoDB logs:
   ```bash
   sudo journalctl -u mongodb
   ```

### Port Already in Use

If port 5000 is already in use, change it in `.env`:
```env
PORT=8080
```

### Database Setup Issues

If setup fails, you can manually check MongoDB:

```bash
# Connect to MongoDB
mongosh

# Switch to parking_db
use parking_db

# Check collections
show collections

# Count documents
db.parking_slots.count()
db.users.count()
```

## Development

### Running in Development Mode

The application runs in debug mode by default (set in `.env`):
```env
DEBUG=True
FLASK_ENV=development
```

### Creating Admin User

To create an admin user, manually update a user in MongoDB:

```bash
mongosh
use parking_db
db.users.updateOne(
  {email: "admin@parking.com"},
  {$set: {role: "admin"}}
)
```

## Production Deployment

For production:

1. Set `DEBUG=False` in `.env`
2. Use a strong `SECRET_KEY`
3. Use MongoDB Atlas or secure MongoDB instance
4. Use a production WSGI server (gunicorn, uwsgi)
5. Set up HTTPS/SSL
6. Configure CORS properly

## License

MIT License

## Support

For issues or questions, please contact: support@parkease.com
