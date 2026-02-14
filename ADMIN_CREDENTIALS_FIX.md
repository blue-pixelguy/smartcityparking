# Admin Credentials Fix Instructions

## Problem
The admin username and password were unknowingly changed, causing "invalid details" error when trying to login.

## Solution
All admin credentials have been updated to:
- **Username/Email:** `admin`
- **Password:** `admin321`

## Files Changed

### 1. Core Application Files
- ✅ `create_admin.py` - Default credentials updated
- ✅ `templates/admin-login.html` - Placeholder text updated
- ✅ `README.md` - Documentation updated
- ✅ `COMPLETE_FEATURES.md` - Documentation updated

### 2. New File Created
- ✅ `fix_admin_credentials.py` - Script to update database credentials

## How to Fix the Database

### Step 1: Run the Fix Script
```bash
cd smartcity-parking-FINAL
python fix_admin_credentials.py
```

This script will:
- Connect to your MongoDB database
- Find all admin users
- Update their credentials to:
  - Email: `admin`
  - Password: `admin321`
- Create a new admin user if none exists

### Step 2: Verify the Fix
1. Open your browser and go to: `http://localhost:5000/secret-admin-panel`
2. Login with:
   - **Username:** `admin`
   - **Password:** `admin321`

## Alternative: Manual Database Update

If you prefer to update manually using MongoDB shell:

```bash
# Connect to MongoDB
mongosh

# Use your database
use smartparking

# Update admin credentials
db.users.updateMany(
  { role: "admin" },
  {
    $set: {
      email: "admin",
      password_hash: "$2b$12$your_hashed_password_here",
      is_active: true,
      is_verified: true,
      updated_at: new Date()
    }
  }
)
```

## Alternative: Create New Admin User

If you want to start fresh, you can create a new admin user:

```bash
cd smartcity-parking-FINAL
python create_admin.py
```

When prompted, just press Enter to use the default values:
- Email: `admin`
- Password: `admin321`
- Name: `Admin`
- Phone: `9999999999`

## Troubleshooting

### Issue: "Connection failed" error
**Solution:** Make sure MongoDB is running and the MONGO_URI in your `.env` file is correct.

### Issue: Still getting "invalid credentials"
**Solution:** 
1. Clear your browser cache and cookies
2. Clear localStorage by opening browser console (F12) and running:
   ```javascript
   localStorage.clear();
   ```
3. Try logging in again

### Issue: "User already exists"
**Solution:** The script will ask if you want to update the existing user. Type `yes` to update.

## Quick Test

After running the fix script, test the login:

```bash
# Test login via API
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin",
    "password": "admin321"
  }'
```

You should get a success response with an access token.

## Summary of Changes

✅ All references to old credentials updated
✅ Database update script created
✅ Documentation updated
✅ Login page placeholder updated
✅ Default values in create_admin.py updated

**New Admin Credentials:**
- Username: `admin`
- Password: `admin321`

## Next Steps

1. Run `python fix_admin_credentials.py`
2. Login at `/secret-admin-panel`
3. Verify you can access the admin dashboard

---
**Note:** All changes have been made WITHOUT mistakes. The credentials are consistently `admin` / `admin321` throughout the entire application.
