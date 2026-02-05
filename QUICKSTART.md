# QUICK START GUIDE

## 🚀 Get Started in 3 Steps

### Step 1: Run the Installer
```bash
cd parking-system
./install.sh
```

This will:
- Install MongoDB (if not installed)
- Install Python dependencies
- Setup database with default data
- Create test user account

### Step 2: Start the Server
```bash
python3 app.py
```

### Step 3: Access the Website
Open your browser and go to: **http://localhost:5000**

---

## 🔐 Test User Login

- **Email:** test@parking.com
- **Password:** test123

---

## ✨ Features

### For Users:
1. **Register/Login** - Create account or login
2. **Browse Slots** - See available parking spots in real-time
3. **Book Parking** - Reserve slots by the hour
4. **Manage Bookings** - View, track, and cancel bookings
5. **Update Profile** - Manage your account details

### Slot Types:
- **Regular** (A01-A50): ₹50/hour - Standard parking
- **VIP** (V01-V05): ₹100/hour - Premium covered parking
- **Handicapped** (H01-H05): ₹40/hour - Accessible parking

---

## 📱 Pages

### Homepage (/)
- Landing page with features
- Login/Register modals
- Pricing information
- Contact form

### Dashboard (/dashboard)
- Overview statistics
- Book new parking slot
- View/manage bookings
- Update profile

---

## 🔧 Troubleshooting

### MongoDB Not Starting?
```bash
sudo systemctl start mongodb
sudo systemctl status mongodb
```

### Port 5000 Already in Use?
Edit `.env` file and change:
```
PORT=8080
```

### Dependencies Not Installing?
```bash
pip3 install --break-system-packages Flask pymongo python-dotenv Flask-CORS bcrypt PyJWT dnspython
```

---

## 📂 What's Included

```
parking-system/
├── app.py              # Main application
├── setup.py            # Database setup
├── install.sh          # Auto-installer
├── requirements.txt    # Dependencies
├── README.md           # Full documentation
├── templates/          # HTML pages
│   ├── index.html
│   └── dashboard.html
├── static/             # CSS & JavaScript
│   ├── css/
│   └── js/
├── routes/             # API endpoints
│   ├── auth.py
│   ├── slots.py
│   ├── bookings.py
│   └── users.py
└── config/             # Configuration
    └── database.py
```

---

## 🎯 What You Can Do

1. ✅ Register new users
2. ✅ Login with authentication
3. ✅ View real-time slot availability
4. ✅ Book parking slots (hourly basis)
5. ✅ Cancel bookings
6. ✅ Track booking history
7. ✅ Update user profile
8. ✅ Different slot types (Regular, VIP, Handicapped)
9. ✅ Automatic payment calculation
10. ✅ Responsive design (works on mobile)

---

## 🌐 API Endpoints

All endpoints are at: http://localhost:5000/api

- **POST** `/auth/register` - Register
- **POST** `/auth/login` - Login
- **GET** `/slots` - Get all slots
- **GET** `/slots/available` - Get available slots
- **POST** `/bookings` - Create booking
- **GET** `/bookings/my` - My bookings
- **PUT** `/bookings/<id>/cancel` - Cancel booking
- **GET** `/users/profile` - Get profile
- **PUT** `/users/profile` - Update profile

---

## 💡 Tips

1. **First Time:** Use the test account to explore features
2. **Booking:** Select a slot type, choose duration, click book
3. **Cancellation:** Only active bookings can be cancelled
4. **Profile:** Update vehicle number to match your car
5. **Slots:** Green = Available, Red = Occupied

---

## 📞 Need Help?

Check the full README.md for detailed documentation and troubleshooting.

**Enjoy your parking management system! 🚗✨**
