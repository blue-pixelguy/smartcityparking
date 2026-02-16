"""
Admin Login Verification Script
Test if the admin credentials work correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient
from werkzeug.security import check_password_hash

print("=" * 70)
print(" " * 20 + "ADMIN LOGIN VERIFICATION")
print("=" * 70)

# Test credentials
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin321"

# Connect to MongoDB
try:
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/smartparking')
    print(f"\n[1/3] Connecting to database...")
    
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client.get_database()
    print(f"      ✅ Connected: {db.name}")
except Exception as e:
    print(f"      ❌ Failed: {e}")
    sys.exit(1)

print(f"\n[2/3] Looking for admin user with username: '{TEST_USERNAME}'")

# Find admin user
admin_user = db.users.find_one({'email': TEST_USERNAME, 'role': 'admin'})

if not admin_user:
    print(f"      ❌ Admin user not found!")
    print(f"\n💡 Run this command to create admin:")
    print(f"   python setup_admin.py")
    sys.exit(1)

print(f"      ✅ Admin user found!")
print(f"      • Name: {admin_user.get('name', 'N/A')}")
print(f"      • Email/Username: {admin_user.get('email', 'N/A')}")
print(f"      • Role: {admin_user.get('role', 'N/A')}")
print(f"      • Active: {admin_user.get('is_active', False)}")
print(f"      • Verified: {admin_user.get('is_verified', False)}")

print(f"\n[3/3] Testing password authentication...")

# Check password
password_hash = admin_user.get('password_hash')
if not password_hash:
    print(f"      ❌ No password hash found!")
    sys.exit(1)

password_valid = check_password_hash(password_hash, TEST_PASSWORD)

if password_valid:
    print(f"      ✅ Password is correct!")
else:
    print(f"      ❌ Password is incorrect!")
    print(f"\n💡 Reset password by running:")
    print(f"   python setup_admin.py")
    sys.exit(1)

# Check if admin is active
if not admin_user.get('is_active', False):
    print(f"\n⚠️  WARNING: Admin account is INACTIVE!")
    sys.exit(1)

print("\n" + "=" * 70)
print(" " * 15 + "✅ ALL CHECKS PASSED!")
print("=" * 70)

print("\n🎉 Admin login credentials are working correctly!")
print(f"\n🔑 Login with:")
print(f"   Username: {TEST_USERNAME}")
print(f"   Password: {TEST_PASSWORD}")
print(f"\n🌐 Admin Panel: http://localhost:5000/secret-admin-panel")

# Test API login
print(f"\n📡 API Test Command:")
print(f"""
curl -X POST http://localhost:5000/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{{"email": "{TEST_USERNAME}", "password": "{TEST_PASSWORD}"}}'
""")

print("=" * 70 + "\n")
