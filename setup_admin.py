"""
COMPREHENSIVE Admin Credentials Fix Script
This script properly sets up admin with username 'admin' and password 'admin321'
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime

print("=" * 70)
print(" " * 15 + "SMART PARKING - ADMIN FIX TOOL")
print("=" * 70)

# Admin credentials
NEW_USERNAME = "admin"
NEW_PASSWORD = "admin321"

# Connect to MongoDB
try:
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/smartparking')
    print(f"\n[1/5] Connecting to MongoDB...")
    print(f"      URI: {MONGO_URI}")
    
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client.get_database()
    print(f"      ✅ Connected to database: {db.name}")
except Exception as e:
    print(f"      ❌ Connection failed: {e}")
    print("\n💡 TIP: Make sure MongoDB is running!")
    print("   Start MongoDB: mongod --dbpath <your-db-path>")
    sys.exit(1)

print(f"\n[2/5] Searching for existing admin users...")

# Find all admin users
admin_users = list(db.users.find({'role': 'admin'}))

if admin_users:
    print(f"      ✅ Found {len(admin_users)} admin user(s)")
    
    # Delete all existing admin users to avoid conflicts
    print(f"\n[3/5] Cleaning up old admin accounts...")
    for admin in admin_users:
        old_email = admin.get('email', 'unknown')
        print(f"      🗑️  Removing old admin: {old_email}")
        
        # Delete the admin user
        db.users.delete_one({'_id': admin['_id']})
        
        # Delete their wallet if exists
        db.wallets.delete_one({'user_id': admin['_id']})
    
    print(f"      ✅ Old admin accounts removed")
else:
    print(f"      ℹ️  No existing admin users found")

print(f"\n[4/5] Creating new admin user...")
print(f"      Username: {NEW_USERNAME}")
print(f"      Password: {NEW_PASSWORD}")

# Create new admin user
admin_data = {
    'email': NEW_USERNAME,  # Using 'admin' as username (not an email format)
    'password_hash': generate_password_hash(NEW_PASSWORD),
    'name': 'System Administrator',
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
    admin_id = result.inserted_id
    print(f"      ✅ Admin user created successfully!")
    print(f"      ID: {admin_id}")
except Exception as e:
    print(f"      ❌ Failed to create admin: {e}")
    sys.exit(1)

# Create wallet for admin
print(f"\n[5/5] Setting up admin wallet...")
wallet_data = {
    'user_id': admin_id,
    'balance': 1000.0,  # Give admin some initial balance
    'created_at': datetime.utcnow(),
    'updated_at': datetime.utcnow()
}

try:
    db.wallets.insert_one(wallet_data)
    print(f"      ✅ Admin wallet created (Balance: ₹1000.00)")
except Exception as e:
    print(f"      ⚠️  Wallet creation warning: {e}")

# Verify the admin was created correctly
verify_admin = db.users.find_one({'email': NEW_USERNAME, 'role': 'admin'})

print("\n" + "=" * 70)
print(" " * 20 + "✅ ADMIN SETUP COMPLETE!")
print("=" * 70)

if verify_admin:
    print("\n📋 Admin Account Details:")
    print(f"   • Username: {NEW_USERNAME}")
    print(f"   • Password: {NEW_PASSWORD}")
    print(f"   • Role: admin")
    print(f"   • Status: Active & Verified")
    print(f"   • Created: {verify_admin['created_at']}")
    
    print("\n🌐 Login URLs:")
    print(f"   • Admin Panel: http://localhost:5000/secret-admin-panel")
    print(f"   • Alternative: http://127.0.0.1:5000/secret-admin-panel")
    
    print("\n🔑 Login Credentials:")
    print(f"   Username: {NEW_USERNAME}")
    print(f"   Password: {NEW_PASSWORD}")
    
    print("\n📝 Important Notes:")
    print("   1. The input field accepts plain text (not email format)")
    print("   2. Just type 'admin' without @domain.com")
    print("   3. Password is case-sensitive")
    print("   4. Clear browser cache/localStorage if you have issues")
    
    print("\n💡 Troubleshooting:")
    print("   • Clear browser cache: Ctrl+Shift+Delete")
    print("   • Clear localStorage: Press F12 > Console > type: localStorage.clear()")
    print("   • Make sure Flask app is running on port 5000")
    
else:
    print("\n⚠️  WARNING: Admin verification failed!")
    print("Please run this script again or contact support.")

print("\n" + "=" * 70)
print("🚀 You can now login to the admin panel!")
print("=" * 70 + "\n")
