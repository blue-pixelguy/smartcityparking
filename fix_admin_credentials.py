"""
Fix Admin Credentials Script
This script updates the admin username and password in the database
Username: admin
Password: admin321
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime

print("=" * 60)
print("SMART PARKING - FIX ADMIN CREDENTIALS")
print("=" * 60)

# Connect to MongoDB
try:
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/smartparking')
    print(f"\nConnecting to MongoDB...")
    
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client.get_database()
    print(f"✅ Connected to database: {db.name}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

# New admin credentials
new_email = "admin"
new_password = "admin321"

print(f"\nSearching for admin users...")

# Find all users with admin role
admin_users = list(db.users.find({'role': 'admin'}))

if not admin_users:
    print("\n⚠️  No admin users found in database!")
    print("Creating new admin user...")
    
    # Create new admin user
    admin_data = {
        'email': new_email,  # Using 'admin' as username
        'password_hash': generate_password_hash(new_password),
        'name': 'Admin',
        'phone': '9999999999',
        'role': 'admin',
        'is_verified': True,
        'is_active': True,
        'profile_image': None,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    result = db.users.insert_one(admin_data)
    print(f"✅ New admin user created with ID: {result.inserted_id}")
    
    # Create wallet for admin
    wallet_data = {
        'user_id': result.inserted_id,
        'balance': 0.0,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    try:
        db.wallets.insert_one(wallet_data)
        print("✅ Wallet created for admin")
    except Exception as e:
        print(f"⚠️  Wallet creation warning: {e}")
else:
    print(f"\n✅ Found {len(admin_users)} admin user(s)")
    
    # Update all admin users to new credentials
    for admin in admin_users:
        old_email = admin.get('email', 'unknown')
        print(f"\nUpdating admin user: {old_email}")
        
        update_result = db.users.update_one(
            {'_id': admin['_id']},
            {
                '$set': {
                    'email': new_email,  # Using 'admin' as username/email
                    'password_hash': generate_password_hash(new_password),
                    'is_active': True,
                    'is_verified': True,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if update_result.modified_count > 0:
            print(f"✅ Admin credentials updated successfully")
        else:
            print(f"⚠️  No changes made (credentials may already be correct)")

print("\n" + "=" * 60)
print("ADMIN CREDENTIALS - UPDATED")
print("=" * 60)
print(f"Email/Username: {new_email}")
print(f"Password: {new_password}")
print(f"\nLogin at: http://localhost:5000/secret-admin-panel")
print("=" * 60)
print("\n✅ Admin credentials fix completed!")
print("\nYou can now login with:")
print(f"   Username: {new_email}")
print(f"   Password: {new_password}")
print("=" * 60)
