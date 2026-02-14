"""
Create Admin User Script
Run this to create an admin user for the admin panel
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
print("SMART PARKING - CREATE ADMIN USER")
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

# Get admin details
print("\nEnter admin details:")
email = input("Email (default: admin): ").strip() or "admin"
password = input("Password (default: admin321): ").strip() or "admin321"
name = input("Name (default: Admin): ").strip() or "Admin"
phone = input("Phone (default: 9999999999): ").strip() or "9999999999"

# Check if admin already exists
existing_admin = db.users.find_one({'email': email.lower()})
if existing_admin:
    print(f"\n⚠️  User with email {email} already exists!")
    update = input("Do you want to update this user to admin role? (yes/no): ").strip().lower()
    
    if update == 'yes':
        # Update existing user
        db.users.update_one(
            {'email': email.lower()},
            {
                '$set': {
                    'role': 'admin',
                    'password_hash': generate_password_hash(password),
                    'is_active': True,
                    'is_verified': True,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        print("\n✅ User updated to admin successfully!")
    else:
        print("\nOperation cancelled.")
        sys.exit(0)
else:
    # Create new admin user
    admin_data = {
        'email': email.lower(),
        'password_hash': generate_password_hash(password),
        'name': name,
        'phone': phone,
        'role': 'admin',
        'is_verified': True,
        'is_active': True,
        'profile_image': None,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    db.users.insert_one(admin_data)
    print("\n✅ Admin user created successfully!")

    # Create wallet for admin
    wallet_data = {
        'user_id': admin_data['_id'] if '_id' in admin_data else None,
        'balance': 0.0,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    try:
        db.wallets.insert_one(wallet_data)
        print("✅ Wallet created for admin")
    except Exception as e:
        print(f"⚠️  Wallet creation warning: {e}")

print("\n" + "=" * 60)
print("ADMIN CREDENTIALS")
print("=" * 60)
print(f"Email: {email}")
print(f"Password: {password}")
print(f"\nLogin at: http://localhost:5000/secret-admin-panel")
print("=" * 60)
