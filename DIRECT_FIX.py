"""
DIRECT ADMIN FIX - Run this NOW
This will create/update admin in your database immediately
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from pymongo import MongoClient
    from werkzeug.security import generate_password_hash
    from datetime import datetime
except ImportError:
    print("❌ Missing required packages!")
    print("Run: pip install pymongo werkzeug python-dotenv")
    sys.exit(1)

# Try to load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

print("=" * 70)
print("DIRECT ADMIN FIX - RUNNING NOW")
print("=" * 70)

# Get MongoDB URI
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/smartparking')
print(f"\nMongoDB URI: {MONGO_URI}")

# Connect
print("\nConnecting to MongoDB...")
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client.get_database()
    print(f"✅ Connected to: {db.name}")
except Exception as e:
    print(f"❌ FAILED: {e}")
    print("\n🔧 POSSIBLE FIXES:")
    print("1. Start MongoDB: mongod")
    print("2. Check .env file has correct MONGO_URI")
    print(f"3. Current URI: {MONGO_URI}")
    sys.exit(1)

# Admin credentials
USERNAME = "admin"
PASSWORD = "admin321"

print(f"\n🗑️  Removing old admin accounts...")
result = db.users.delete_many({'role': 'admin'})
print(f"   Deleted {result.deleted_count} old admin(s)")

print(f"\n➕ Creating NEW admin account...")
print(f"   Username: {USERNAME}")
print(f"   Password: {PASSWORD}")

# Create admin
admin_data = {
    'email': USERNAME,
    'password_hash': generate_password_hash(PASSWORD),
    'name': 'Administrator',
    'phone': '9999999999',
    'role': 'admin',
    'is_verified': True,
    'is_active': True,
    'profile_image': None,
    'created_at': datetime.utcnow(),
    'updated_at': datetime.utcnow()
}

try:
    result = db.users.insert_one(admin_data)
    print(f"✅ Admin created! ID: {result.inserted_id}")
except Exception as e:
    print(f"❌ Failed to create admin: {e}")
    sys.exit(1)

# Create wallet
print(f"\n💰 Creating admin wallet...")
wallet_data = {
    'user_id': result.inserted_id,
    'balance': 1000.0,
    'created_at': datetime.utcnow(),
    'updated_at': datetime.utcnow()
}

try:
    db.wallets.insert_one(wallet_data)
    print(f"✅ Wallet created with ₹1000")
except Exception as e:
    print(f"⚠️  Wallet warning: {e}")

# Verify
print(f"\n🔍 Verifying admin account...")
admin = db.users.find_one({'email': USERNAME, 'role': 'admin'})

if admin:
    print("✅ VERIFICATION PASSED!")
    print(f"\n{'='*70}")
    print("🎉 ADMIN ACCOUNT READY!")
    print(f"{'='*70}")
    print(f"\n🔑 LOGIN CREDENTIALS:")
    print(f"   Username: {USERNAME}")
    print(f"   Password: {PASSWORD}")
    print(f"\n🌐 LOGIN URL:")
    print(f"   http://localhost:5000/secret-admin-panel")
    print(f"\n📋 ACCOUNT DETAILS:")
    print(f"   • Role: {admin['role']}")
    print(f"   • Active: {admin['is_active']}")
    print(f"   • Verified: {admin['is_verified']}")
    print(f"   • Created: {admin['created_at']}")
    print(f"\n{'='*70}")
    print("✅ NOW TRY LOGGING IN!")
    print(f"{'='*70}\n")
else:
    print("❌ VERIFICATION FAILED!")
    print("Something went wrong. Admin not found in database.")
    sys.exit(1)
