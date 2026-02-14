# 🚀 Quick Start Guide

## ⚠️ IMPORTANT: MongoDB Connection Issue

You're seeing this error because **MongoDB Atlas is blocking your IP address**.

---

## ✅ Fix in 3 Steps

### 1️⃣ Allow Your IP in MongoDB Atlas

1. Go to https://cloud.mongodb.com
2. Click **"Network Access"** (left sidebar)
3. Click **"Add IP Address"**
4. Click **"Allow Access from Anywhere"** (easiest for testing)
5. Click **"Confirm"**
6. **Wait 1-2 minutes** for changes to apply ⏰

### 2️⃣ Verify Your Connection String

Open `.env` file and check your `MONGO_URI`:

```env
MONGO_URI=mongodb+srv://akashbluee_db_user:w8il1Fr9pBovHYVg@cluster0.qmsfjl6.mongodb.net/?appName=Cluster0
```

**Add the database name:**
```env
MONGO_URI=mongodb+srv://akashbluee_db_user:w8il1Fr9pBovHYVg@cluster0.qmsfjl6.mongodb.net/parking_system?retryWrites=true&w=majority
```

### 3️⃣ Run the App Again

**Windows:**
```bash
python app.py
```

**Mac/Linux:**
```bash
python3 app.py
```

Or use the startup scripts:
- Windows: Double-click `run.bat`
- Mac/Linux: `./run.sh`

---

## 🎯 Expected Output

When successful, you'll see:
```
✅ MongoDB connection successful!
 * Running on http://127.0.0.1:5000
```

Then open your browser: http://localhost:5000

You should see:
```json
{
  "message": "Smart City Parking API",
  "version": "1.0.0",
  "endpoints": { ... }
}
```

---

## 🧪 Test the API

### 1. Health Check
```bash
curl http://localhost:5000/health
```

### 2. Register a User
```bash
curl -X POST http://localhost:5000/api/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@test.com\",\"password\":\"password123\",\"name\":\"Test User\",\"phone\":\"9876543210\",\"role\":\"driver\"}"
```

*Note: On Mac/Linux, use `\` instead of `^` for line continuation*

### 3. Login
```bash
curl -X POST http://localhost:5000/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@test.com\",\"password\":\"password123\"}"
```

Copy the `access_token` from the response!

### 4. Get Profile
```bash
curl http://localhost:5000/api/auth/profile ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

---

## 📚 Full Documentation

- **API Reference**: See `README.md`
- **MongoDB Setup**: See `MONGODB_SETUP.md`
- **Deployment**: See `DEPLOYMENT.md`
- **Project Overview**: See `PROJECT_SUMMARY.md`

---

## 🆘 Still Not Working?

### Option 1: Use Local MongoDB (Easiest)

1. **Download MongoDB Community**: https://www.mongodb.com/try/download/community
2. Install with default settings
3. Update `.env`:
   ```env
   MONGO_URI=mongodb://localhost:27017/parking_system
   ```
4. Run `python app.py`

### Option 2: Check Network Access in MongoDB Atlas

Your MongoDB Atlas might need:
- ✅ IP Whitelisted (0.0.0.0/0 for testing)
- ✅ Database user created with password
- ✅ Correct connection string with database name

**Full guide:** See `MONGODB_SETUP.md`

---

## 💡 Pro Tips

1. **Use Postman or Thunder Client** (VS Code extension) to test APIs easily
2. Import `api-collection.json` into Postman for ready-made requests
3. Check `test_setup.py` to verify your installation
4. Always use `python test_setup.py` before running the app

---

## 📞 Need Help?

**Read the detailed setup guide:** `MONGODB_SETUP.md`

**Still stuck?** Email: akash.bluee@gmail.com with:
- Screenshot of error
- Output of `python test_setup.py`
- Your MongoDB Atlas Network Access settings

---

## ✅ Success Checklist

- [ ] MongoDB Atlas IP is whitelisted (0.0.0.0/0)
- [ ] Database user exists with correct password
- [ ] MONGO_URI includes database name (`parking_system`)
- [ ] Waited 1-2 minutes after changing MongoDB settings
- [ ] Ran `pip install -r requirements.txt`
- [ ] No firewall blocking port 5000
- [ ] Python 3.8+ installed

Once all checked, run: `python app.py` 🚀
