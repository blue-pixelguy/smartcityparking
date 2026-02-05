#!/usr/bin/env python3
"""
Simple diagnostic script to test if the app can start
Run this on Render shell to see what's failing
"""
import sys

print("=" * 60)
print("DIAGNOSTIC CHECK")
print("=" * 60)

# Test 1: Basic imports
print("\n1. Testing basic imports...")
try:
    import flask
    print("✅ Flask imported")
except Exception as e:
    print(f"❌ Flask failed: {e}")
    sys.exit(1)

try:
    import bcrypt
    print("✅ bcrypt imported")
except Exception as e:
    print(f"❌ bcrypt failed: {e}")
    print("   Fix: Add bcrypt==4.1.2 to requirements.txt")
    sys.exit(1)

try:
    import pymongo
    print("✅ pymongo imported")
except Exception as e:
    print(f"❌ pymongo failed: {e}")
    sys.exit(1)

# Test 2: Environment variables
print("\n2. Checking environment variables...")
import os
from dotenv import load_dotenv
load_dotenv()

critical_vars = {
    'SECRET_KEY': os.getenv('SECRET_KEY'),
    'JWT_SECRET': os.getenv('JWT_SECRET'),
    'MONGO_URI': os.getenv('MONGO_URI'),
    'DB_NAME': os.getenv('DB_NAME')
}

for var, value in critical_vars.items():
    if value:
        print(f"✅ {var} is set")
    else:
        print(f"⚠️  {var} is NOT set (will use default)")

# Test 3: Try importing app modules
print("\n3. Testing app modules...")
try:
    from models import User
    print("✅ models.py imported")
except Exception as e:
    print(f"❌ models.py failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from auth import create_token
    print("✅ auth.py imported")
except Exception as e:
    print(f"❌ auth.py failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from database import db
    print("✅ database.py imported")
except Exception as e:
    print(f"❌ database.py failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Try creating Flask app
print("\n4. Testing Flask app creation...")
try:
    from app import app
    print("✅ Flask app created successfully")
    print(f"   Blueprints: {len(app.blueprints)}")
except Exception as e:
    print(f"❌ Flask app failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Database connection
print("\n5. Testing database connection...")
try:
    db.client.server_info()
    print("✅ Database connected")
except Exception as e:
    print(f"⚠️  Database connection failed: {e}")
    print("   This is OK if you haven't set MONGO_URI yet")

print("\n" + "=" * 60)
print("✅ ALL CRITICAL CHECKS PASSED!")
print("=" * 60)
print("\nYour app should be able to start.")
print("If it still fails, check the Render logs for details.")
print("=" * 60)