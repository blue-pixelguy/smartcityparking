"""
Database Fix Script
Fixes common issues with the SmartParking database
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient
from bson.objectid import ObjectId

print("=" * 60)
print("SMART PARKING - DATABASE FIX SCRIPT")
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

# Fix 1: Ensure all users have a role field
print("\n1. Checking user roles...")
users_without_role = list(db.users.find({'role': {'$exists': False}}))

if users_without_role:
    print(f"   Found {len(users_without_role)} users without role field")
    print(f"   Setting role='user' for these users...")
    
    for user in users_without_role:
        db.users.update_one(
            {'_id': user['_id']},
            {'$set': {'role': 'user'}}
        )
        print(f"   - Updated user: {user.get('email', user['_id'])}")
    
    print(f"   ✅ Fixed {len(users_without_role)} users")
else:
    print(f"   ✅ All users have role field")

# Fix 2: Normalize invalid roles
print("\n2. Checking for invalid roles...")
all_users = list(db.users.find({}))
fixed_count = 0

for user in all_users:
    role = user.get('role')
    if role not in ['user', 'admin']:
        print(f"   Found invalid role '{role}' for user: {user.get('email')}")
        
        # If role is 'host', convert to 'user'
        if role == 'host':
            db.users.update_one(
                {'_id': user['_id']},
                {'$set': {'role': 'user'}}
            )
            print(f"   - Converted 'host' to 'user'")
            fixed_count += 1
        else:
            print(f"   - WARNING: Unknown role '{role}', setting to 'user'")
            db.users.update_one(
                {'_id': user['_id']},
                {'$set': {'role': 'user'}}
            )
            fixed_count += 1

if fixed_count > 0:
    print(f"   ✅ Fixed {fixed_count} users with invalid roles")
else:
    print(f"   ✅ All users have valid roles")

# Fix 3: Ensure all users have required fields
print("\n3. Checking for missing required fields...")
required_fields = ['email', 'name', 'is_active', 'is_verified', 'created_at']

for user in all_users:
    updates = {}
    
    if 'is_active' not in user:
        updates['is_active'] = True
    
    if 'is_verified' not in user:
        updates['is_verified'] = False
    
    if 'created_at' not in user:
        from datetime import datetime
        updates['created_at'] = datetime.utcnow()
    
    if 'updated_at' not in user:
        from datetime import datetime
        updates['updated_at'] = datetime.utcnow()
    
    if updates:
        db.users.update_one(
            {'_id': user['_id']},
            {'$set': updates}
        )
        print(f"   - Updated user {user.get('email')}: added {list(updates.keys())}")

print(f"   ✅ All users have required fields")

# Summary
print("\n" + "=" * 60)
print("FIX COMPLETE!")
print("=" * 60)

user_count = db.users.count_documents({})
print(f"\nTotal users in database: {user_count}")

if user_count > 0:
    # Show role distribution
    roles = db.users.aggregate([
        {'$group': {'_id': '$role', 'count': {'$sum': 1}}}
    ])
    print("\nRole distribution:")
    for role_stat in roles:
        print(f"  - {role_stat['_id']}: {role_stat['count']}")

print("\nYou can now start the application!")
print("Run: python app.py")
