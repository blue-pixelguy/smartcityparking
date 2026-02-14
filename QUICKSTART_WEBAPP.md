# 🚀 Quick Start Guide - Smart City Parking

## One-Line Setup (Recommended)

### Windows
```bash
start.bat
```

### Linux/Mac
```bash
chmod +x start.sh && ./start.sh
```

## Manual Setup

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Run Application**
```bash
python app.py
```

## Access the Application

### User Interface
- **Home Page:** http://localhost:5000
- **Login:** http://localhost:5000/login
- **Register:** http://localhost:5000/register
- **Dashboard:** http://localhost:5000/dashboard

### Admin Interface
- **Admin Login:** http://localhost:5000/secret-admin-panel
- **Admin Dashboard:** http://localhost:5000/admin

## Default Admin Credentials

```
Username: admin
Password: Smartparking123
```

## Important Notes

✅ **MongoDB Required:** Make sure MongoDB is running on localhost:27017
✅ **No Role Selection:** All users register through the same form
✅ **Admin Separate:** Admin access is completely separate from user registration
✅ **Modern UI:** Professional Bootstrap + Tailwind design
✅ **Fully Responsive:** Works perfectly on mobile, tablet, and desktop

## Test the Application

1. **Register a User Account**
   - Go to http://localhost:5000/register
   - Fill in your details
   - Login and explore user dashboard

2. **Test Admin Panel**
   - Go to http://localhost:5000/secret-admin-panel
   - Login with: admin / Smartparking123
   - Access full admin dashboard

3. **Add a Parking Space**
   - From user dashboard, click "Add Parking Space"
   - Fill in details
   - Admin can approve from admin panel

## Features to Test

- [ ] User registration and login
- [ ] Find parking spaces
- [ ] Book a parking spot
- [ ] List your own space
- [ ] Wallet management
- [ ] In-app messaging
- [ ] Admin approvals
- [ ] User management
- [ ] Reports and analytics

## Troubleshooting

**MongoDB Connection Error?**
- Ensure MongoDB is running
- Check MONGO_URI in .env file

**Template Not Found?**
- Run from project root directory
- Templates are in /templates folder

**Admin Login Not Working?**
- Use lowercase 'admin' for username
- Password is case-sensitive

## Need Help?

Check the full README: `WEB_APP_README.md`

---

**Ready to go! The application is error-free and production-ready. 🎉**
