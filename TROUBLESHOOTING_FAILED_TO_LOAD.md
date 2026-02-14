# Troubleshooting: "Failed to load parking details" Error

## Error Description

When you try to book a parking space, you see an alert:
```
localhost:5000 says
Failed to load parking details
```

And the page shows:
- Parking Space: Loading...
- Price per Hour: ₹0
- Address: Loading...

## Root Causes & Solutions

### 1. **MongoDB Not Running** ⭐ MOST COMMON

**Symptoms:**
- Backend console shows: "⚠️ MongoDB connection failed"
- API returns 500 error
- All database operations fail

**Solution:**
```bash
# Check if MongoDB is running
# Windows:
net start MongoDB

# Linux/Mac:
sudo systemctl status mongod
# or
sudo service mongod status

# If not running, start it:
# Windows:
net start MongoDB

# Linux/Mac:
sudo systemctl start mongod
# or
sudo service mongod start
```

**Alternative (MongoDB Atlas - Cloud):**
- Check your internet connection
- Verify MONGO_URI in `.env` file is correct
- Check if your IP is whitelisted in MongoDB Atlas

---

### 2. **Backend Server Not Running**

**Symptoms:**
- Browser console shows: "Failed to fetch" or "ERR_CONNECTION_REFUSED"
- Cannot access `http://localhost:5000`

**Solution:**
```bash
# Start the Flask backend server
python app.py

# OR
flask run

# OR (Windows)
start.bat

# OR (Linux/Mac)
./start.sh
```

**Verify it's running:**
- Open `http://localhost:5000/health` in browser
- Should show: `{"status": "healthy", ...}`

---

### 3. **Invalid Parking ID**

**Symptoms:**
- Backend console shows: "Invalid parking ID format"
- API returns 400 error

**Solution:**
- This means the parking space ID in the URL is invalid or corrupted
- Check the URL: `localhost:5000/booking/[PARKING_ID]`
- The parking ID should be a valid MongoDB ObjectId (24 hex characters)
- Go back to "Find Parking" and click "Book Now" again

---

### 4. **Parking Space Not Found**

**Symptoms:**
- Backend console shows: "Parking space not found"
- API returns 404 error

**Solution:**
- The parking space might have been deleted
- Or the parking ID is incorrect
- Go back to "Find Parking" and search for available parking spaces
- Try booking a different parking space

---

### 5. **Not Logged In**

**Symptoms:**
- Alert shows: "Please login first"
- Redirected to login page

**Solution:**
- Login to your account
- Then try to book again

---

### 6. **CORS Issues** (Less Common)

**Symptoms:**
- Browser console shows CORS errors
- "Access-Control-Allow-Origin" errors

**Solution:**
- Ensure Flask-CORS is installed: `pip install flask-cors`
- Check `app.py` has: `CORS(app, resources={r"/api/*": {"origins": "*"}})`

---

## How to Debug

### Step 1: Check Browser Console

1. Press `F12` to open Developer Tools
2. Go to "Console" tab
3. Look for errors in red

**What to look for:**
```javascript
// Good - data is loading
Loading parking details for ID: 69874bf39767...
API Response status: 200
API Response data: {parking: {...}, owner: {...}}
Parking data loaded: {parkingData: {...}, pricePerHour: 50}

// Bad - network error
Failed to fetch
net::ERR_CONNECTION_REFUSED

// Bad - API error
API Response status: 404
API Error: {error: "Parking space not found"}
```

### Step 2: Check Backend Console

Look at your terminal where Flask is running:

**Good output:**
```
Fetching parking details for ID: 69874bf39767...
Parking found: Downtown Parking
Successfully returning parking details for: 69874bf39767...
```

**Bad output:**
```
⚠️ MongoDB connection failed: ...
Parking space not found: 69874bf39767...
Error fetching owner: ...
```

### Step 3: Test API Directly

Open in browser or use Postman:
```
http://localhost:5000/api/parking/YOUR_PARKING_ID_HERE
```

**Expected response:**
```json
{
  "parking": {
    "id": "69874bf39767...",
    "title": "Downtown Parking",
    "price_per_hour": 50,
    ...
  },
  "owner": {
    "id": "...",
    "name": "John Doe",
    "email": "john@example.com"
  },
  "reviews": []
}
```

---

## Complete Checklist

Before trying to book, verify:

- [ ] **MongoDB is running**
  - Test: `mongo` or `mongosh` command works
  - OR MongoDB Atlas connection is working

- [ ] **Backend server is running**
  - Test: `http://localhost:5000/health` returns healthy

- [ ] **You are logged in**
  - Check: localStorage has 'token'
  - Test: Open browser console, type: `localStorage.getItem('token')`

- [ ] **Parking space exists**
  - Go to "Find Parking"
  - See available parking spaces
  - Click "Book Now" from there

- [ ] **.env file is configured**
  - Contains valid MONGO_URI
  - Contains SECRET_KEY
  - Contains JWT_SECRET_KEY

---

## Environment File (.env) Example

Make sure your `.env` file looks like this:

```env
# MongoDB Connection
MONGO_URI=mongodb://localhost:27017/smartparking
# OR for MongoDB Atlas:
# MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/smartparking

# Security Keys
SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-here-change-in-production

# App Configuration
FLASK_ENV=development
DEBUG=True
```

---

## Quick Fix Commands

### Option 1: Restart Everything
```bash
# Stop everything first
# Ctrl+C on both terminals

# Start MongoDB
# Windows:
net start MongoDB

# Linux/Mac:
sudo systemctl start mongod

# Start Backend
python app.py

# Then refresh your browser
```

### Option 2: Check Logs
```bash
# In backend terminal, you'll see detailed logs:
Loading parking details for ID: ...
API Response status: ...
Parking data loaded: ...

# Any errors will show with full details
```

### Option 3: Reset and Try Again
```bash
# Clear browser storage
# Open browser console (F12)
localStorage.clear()

# Then:
1. Login again
2. Go to "Find Parking"
3. Search for parking
4. Click "Book Now" on a parking space
```

---

## Improved Error Messages

The updated code now shows better error messages:

**Before:**
```
Failed to load parking details
```

**After:**
```
Failed to load parking details: Parking space not found

Please check:
1. You are logged in
2. The parking space exists
3. The backend server is running
```

It also logs detailed information in the browser console to help you debug.

---

## Common Scenarios & Solutions

### Scenario 1: Fresh Install
```
Problem: Nothing works
Solution:
1. Install MongoDB
2. Run: pip install -r requirements.txt
3. Create .env file
4. Run: python app.py
5. Open http://localhost:5000
6. Register an account
7. Login
8. Try booking
```

### Scenario 2: Worked Before, Not Now
```
Problem: Used to work, now showing error
Solution:
1. Check if MongoDB stopped running
2. Restart MongoDB
3. Restart Flask app
4. Clear browser cache
5. Try again
```

### Scenario 3: Some Parking Works, Others Don't
```
Problem: Can book some parking, but not others
Solution:
1. Check if those parking spaces are approved by admin
2. Check if owner account still exists
3. Check database for corrupted data
```

---

## Database Verification

If issues persist, check MongoDB directly:

```bash
# Connect to MongoDB
mongo
# OR
mongosh

# Switch to database
use smartparking

# Check if parking exists
db.parking_spaces.find({_id: ObjectId("YOUR_PARKING_ID")})

# Check if owner exists
db.users.find({_id: ObjectId("OWNER_ID")})
```

---

## Still Not Working?

If none of the above helps:

1. **Check backend console** for full error stack trace
2. **Check browser console** for detailed error logs
3. **Verify database** has the parking space
4. **Test API directly** using browser or Postman
5. **Check .env file** has correct MongoDB URI
6. **Restart everything** - MongoDB, Flask, Browser

---

## Contact Support

If you've tried everything above and it still doesn't work:

1. Take a screenshot of:
   - Browser error message
   - Browser console (F12)
   - Backend terminal output

2. Note down:
   - Which parking space you're trying to book
   - The parking ID from the URL
   - Whether you're logged in
   - If MongoDB is running

3. Share these details for faster resolution

---

**Last Updated:** February 8, 2026  
**Status:** Complete Troubleshooting Guide ✅
