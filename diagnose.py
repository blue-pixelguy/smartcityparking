"""
Database Diagnostic Script
Run this to check if your database is set up correctly
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient
from models.database import Database
from models.user import User
from bson.objectid import ObjectId

print("=" * 60)
print("SMART PARKING - DATABASE DIAGNOSTIC")
print("=" * 60)

# Test 1: MongoDB Connection
print("\n1. Testing MongoDB Connection...")
try:
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/smartparking')
    print(f"   Connecting to: {MONGO_URI[:50]}...")
    
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db_raw = client.get_database()
    print(f"   ✅ Connected to database: {db_raw.name}")
except Exception as e:
    print(f"   ❌ Connection failed: {e}")
    print("\n   Please check your MONGO_URI in the .env file")
    sys.exit(1)

# Test 2: Check if users collection exists
print("\n2. Checking users collection...")
try:
    user_count = db_raw.users.count_documents({})
    print(f"   ✅ Users collection exists with {user_count} users")
    
    if user_count > 0:
        # Show first user (without password)
        sample_user = db_raw.users.find_one({}, {'password_hash': 0})
        print(f"\n   Sample user:")
        print(f"   - ID: {sample_user['_id']}")
        print(f"   - Email: {sample_user.get('email')}")
        print(f"   - Name: {sample_user.get('name')}")
        print(f"   - Role: {sample_user.get('role')}")
except Exception as e:
    print(f"   ❌ Error accessing users collection: {e}")

# Test 3: Test Database wrapper
print("\n3. Testing Database wrapper...")
try:
    db_wrapper = Database()
    
    # Simulate what happens in app.py
    class FakeApp:
        def __init__(self):
            self.db = db_raw
    
    fake_app = FakeApp()
    db_wrapper.init_app(fake_app)
    
    print(f"   ✅ Database wrapper initialized")
    print(f"   - wrapper.db is None: {db_wrapper.db is None}")
    
    # Test the find_one method
    if user_count > 0:
        test_user = db_wrapper.find_one('users', {})
        if test_user:
            print(f"   ✅ Database wrapper find_one works!")
            print(f"   - Found user: {test_user.get('email')}")
        else:
            print(f"   ❌ Database wrapper find_one returned None")
    
except Exception as e:
    print(f"   ❌ Database wrapper test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test User.get_by_id
print("\n4. Testing User.get_by_id...")
try:
    if user_count > 0:
        # Get a real user ID
        real_user = db_raw.users.find_one({})
        real_user_id = str(real_user['_id'])
        
        print(f"   Testing with user ID: {real_user_id}")
        
        # Test with wrapper
        found_user = User.get_by_id(db_wrapper, real_user_id)
        if found_user:
            print(f"   ✅ User.get_by_id works with wrapper!")
            print(f"   - Found: {found_user.get('email')}")
        else:
            print(f"   ❌ User.get_by_id returned None")
            
            # Try direct lookup for debugging
            print(f"\n   Debugging: Direct lookup...")
            direct_lookup = db_raw.users.find_one({'_id': ObjectId(real_user_id)})
            print(f"   - Direct lookup result: {direct_lookup is not None}")
            
    else:
        print(f"   ⚠️  No users in database to test with")
        print(f"\n   You need to register a user first!")
        
except Exception as e:
    print(f"   ❌ User.get_by_id test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Check for common issues
print("\n5. Checking for common issues...")

# Check if user has 'role' field
if user_count > 0:
    users_without_role = db_raw.users.count_documents({'role': {'$exists': False}})
    if users_without_role > 0:
        print(f"   ⚠️  WARNING: {users_without_role} users don't have a 'role' field!")
        print(f"   This could cause issues. Run the fix script to add roles.")
    else:
        print(f"   ✅ All users have roles")
    
    # Check role values
    user_roles = db_raw.users.distinct('role')
    print(f"   User roles in database: {user_roles}")
    
    invalid_roles = [r for r in user_roles if r not in ['user', 'admin']]
    if invalid_roles:
        print(f"   ⚠️  WARNING: Invalid roles found: {invalid_roles}")
        print(f"   Expected roles: ['user', 'admin']")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
