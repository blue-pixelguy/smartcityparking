# MongoDB Atlas Setup Guide

## 🔴 MongoDB Connection Error Fix

If you're seeing the error: "No connection could be made because the target machine actively refused it"

This means MongoDB Atlas is blocking your IP address. Follow these steps:

---

## ✅ Quick Fix Steps

### Step 1: Login to MongoDB Atlas
1. Go to https://cloud.mongodb.com
2. Login with your account
3. Select your cluster

### Step 2: Whitelist Your IP Address

**Method 1: Allow Access from Anywhere (Easy for Development)**
1. Click "Network Access" in the left sidebar
2. Click "Add IP Address"
3. Click "Allow Access from Anywhere"
4. Click "Confirm"
5. Wait 1-2 minutes for changes to apply

**Method 2: Add Your Specific IP (More Secure)**
1. Find your IP address: Go to https://whatismyipaddress.com
2. Click "Network Access" in MongoDB Atlas
3. Click "Add IP Address"
4. Enter your IP address
5. Click "Confirm"

### Step 3: Verify Database User
1. Click "Database Access" in the left sidebar
2. Make sure you have a user with password
3. User should have "Read and write to any database" permission
4. If not, create a new user:
   - Username: `akashbluee_db_user`
   - Password: `w8il1Fr9pBovHYVg` (or create your own)
   - Built-in Role: "Atlas admin" or "Read and write to any database"

### Step 4: Get Correct Connection String
1. Click "Database" (or "Clusters")
2. Click "Connect" on your cluster
3. Select "Connect your application"
4. Copy the connection string
5. Replace `<password>` with your actual password
6. Update MONGO_URI in your `.env` file

Example:
```
MONGO_URI=mongodb+srv://akashbluee_db_user:w8il1Fr9pBovHYVg@cluster0.qmsfjl6.mongodb.net/parking_system?retryWrites=true&w=majority
```

### Step 5: Test Connection
```bash
python test_setup.py
```

If successful, you'll see: "✅ MongoDB connection successful!"

---

## 🔧 Alternative: Use Local MongoDB (For Testing)

If you want to test locally without MongoDB Atlas:

### Windows:
1. Download MongoDB Community Server: https://www.mongodb.com/try/download/community
2. Install with default settings
3. MongoDB will run on `localhost:27017`
4. Update `.env`:
   ```
   MONGO_URI=mongodb://localhost:27017/parking_system
   ```

### macOS:
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```
Update `.env`:
```
MONGO_URI=mongodb://localhost:27017/parking_system
```

### Linux:
```bash
sudo apt-get install mongodb
sudo systemctl start mongodb
```
Update `.env`:
```
MONGO_URI=mongodb://localhost:27017/parking_system
```

---

## 🧪 Quick Test Without Database

To verify the app works without database (for testing):

1. Comment out database operations in app.py
2. Run: `python app.py`
3. Visit: http://localhost:5000
4. You should see the API welcome message

---

## 🆘 Still Having Issues?

### Check 1: Verify MongoDB URI Format
Your URI should look like:
```
mongodb+srv://username:password@cluster.xxxxx.mongodb.net/database_name
```

### Check 2: Special Characters in Password
If your password has special characters like `@`, `#`, `%`, etc., they need to be URL encoded:
- `@` → `%40`
- `#` → `%23`
- `%` → `%25`

### Check 3: Network Firewall
Your firewall might be blocking MongoDB. Try:
- Disable firewall temporarily
- Add exception for MongoDB ports
- Try from a different network (mobile hotspot)

### Check 4: VPN Issues
If using VPN, try disconnecting it.

---

## ✅ Once Connected

After fixing MongoDB connection:

1. Run test setup:
   ```bash
   python test_setup.py
   ```

2. Start the app:
   ```bash
   python app.py
   ```

3. Test the API:
   ```bash
   curl http://localhost:5000/health
   ```

4. Register a user:
   ```bash
   curl -X POST http://localhost:5000/api/auth/register \
     -H "Content-Type: application/json" \
     -d "{\"email\":\"test@test.com\",\"password\":\"pass123\",\"name\":\"Test User\",\"phone\":\"9876543210\",\"role\":\"driver\"}"
   ```

---

## 📧 Need Help?

If still stuck, email: akash.bluee@gmail.com

Include:
- Error message screenshot
- Your MONGO_URI (hide password)
- Output of `python test_setup.py`
