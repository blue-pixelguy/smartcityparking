#!/usr/bin/env python3
"""
Comprehensive diagnostic script for P2P Parking System
Run this to identify deployment issues
"""
import sys
import os

print("=" * 80)
print("P2P PARKING - DIAGNOSTIC CHECK")
print("=" * 80)

# Test 1: Python version
print("\n1. Python Version Check...")
print(f"   Version: {sys.version}")
if sys.version_info >= (3, 9):
    print("   ✅ Python version OK")
else:
    print("   ⚠️  Python 3.9+ recommended")

# Test 2: Critical imports
print("\n2. Testing Critical Imports...")
imports = {
    'flask': 'Flask==3.0.0',
    'bcrypt': 'bcrypt==4.1.2',
    'pymongo': 'pymongo==4.6.1',
    'jwt': 'PyJWT==2.8.0',
    'dotenv': 'python-dotenv==1.0.0'
}

failed = []
for module, package in imports.items():
    try:
        __import__(module)
        print(f"   ✅ {module} OK")
    except Exception as e:
        print(f"   ❌ {module} FAILED: {e}")
        failed.append(package)

if failed:
    print(f"\n   ❌ Install missing: pip install {' '.join(failed)}")
    sys.exit(1)

# Test 3: Environment variables
print("\n3. Environment Variables...")
from dotenv import load_dotenv
load_dotenv()

vars_check = {
    'SECRET_KEY': os.getenv('SECRET_KEY'),
    'JWT_SECRET': os.getenv('JWT_SECRET'),
    'MONGO_URI': os.getenv('MONGO_URI'),
    'DB_NAME': os.getenv('DB_NAME'),
}

for var, val in vars_check.items():
    if val:
        print(f"   ✅ {var} is set")
    else:
        print(f"   ⚠️  {var} NOT set")

# Test 4: Application modules
print("\n4. Application Modules...")
modules = [
    ('models', 'User'),
    ('auth', 'create_token'),
    ('database', 'db'),
]

for mod_name, obj_name in modules:
    try:
        mod = __import__(mod_name)
        getattr(mod, obj_name)
        print(f"   ✅ {mod_name}.{obj_name} OK")
    except Exception as e:
        print(f"   ❌ {mod_name} FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Test 5: Flask app
print("\n5. Flask Application...")
try:
    from app import app
    print(f"   ✅ App created ({len(app.blueprints)} blueprints)")
except Exception as e:
    print(f"   ❌ App creation FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Database
print("\n6. Database Connection...")
try:
    from database import db
    db.client.server_info()
    print("   ✅ Database connected")
except Exception as e:
    print(f"   ⚠️  Database failed: {e}")
    print("   (OK if MONGO_URI not set yet)")

print("\n" + "=" * 80)
print("✅ DIAGNOSTIC COMPLETE")
print("=" * 80)
print("\nTo start: python app.py")
print("=" * 80)