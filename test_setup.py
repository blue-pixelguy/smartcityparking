"""
Test Script - Verify Installation
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all imports work correctly"""
    print("Testing imports...")
    
    try:
        from flask import Flask
        print("✓ Flask imported successfully")
    except ImportError as e:
        print(f"✗ Flask import failed: {e}")
        return False
    
    try:
        from pymongo import MongoClient
        print("✓ PyMongo imported successfully")
    except ImportError as e:
        print(f"✗ PyMongo import failed: {e}")
        return False
    
    try:
        from flask_jwt_extended import JWTManager
        print("✓ Flask-JWT-Extended imported successfully")
    except ImportError as e:
        print(f"✗ Flask-JWT-Extended import failed: {e}")
        return False
    
    try:
        import razorpay
        print("✓ Razorpay imported successfully")
    except ImportError as e:
        print(f"✗ Razorpay import failed: {e}")
        return False
    
    return True

def test_modules():
    """Test if all custom modules can be imported"""
    print("\nTesting custom modules...")
    
    try:
        from models.user import User
        from models.parking import ParkingSpace
        from models.booking import Booking
        from models.wallet import Wallet
        from models.review import Review
        from models.message import Message
        from models.database import db
        print("✓ All models imported successfully")
    except ImportError as e:
        print(f"✗ Model import failed: {e}")
        return False
    
    try:
        from routes.auth import auth_bp
        from routes.parking import parking_bp
        from routes.booking import booking_bp
        from routes.payment import payment_bp
        from routes.wallet import wallet_bp
        from routes.chat import chat_bp
        from routes.admin import admin_bp
        from routes.user import user_bp
        print("✓ All routes imported successfully")
    except ImportError as e:
        print(f"✗ Route import failed: {e}")
        return False
    
    return True

def test_config():
    """Test if configuration loads correctly"""
    print("\nTesting configuration...")
    
    try:
        from config import Config
        print("✓ Config imported successfully")
        
        # Check if essential config values exist
        if hasattr(Config, 'SECRET_KEY'):
            print("✓ SECRET_KEY configured")
        else:
            print("✗ SECRET_KEY not configured")
            
        if hasattr(Config, 'MONGO_URI'):
            print("✓ MONGO_URI configured")
        else:
            print("✗ MONGO_URI not configured")
            
        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False

def test_app_creation():
    """Test if app can be created"""
    print("\nTesting app creation...")
    
    try:
        from app import create_app
        app = create_app()
        print("✓ App created successfully")
        
        # Check if blueprints are registered
        print(f"✓ Registered blueprints: {list(app.blueprints.keys())}")
        
        return True
    except Exception as e:
        print(f"✗ App creation failed: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("Smart City Parking System - Installation Test")
    print("=" * 50)
    
    all_passed = True
    
    if not test_imports():
        all_passed = False
        print("\n⚠️  Some dependencies are missing. Please run: pip install -r requirements.txt")
    
    if not test_modules():
        all_passed = False
    
    if not test_config():
        all_passed = False
    
    if not test_app_creation():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All tests passed! Application is ready to run.")
        print("Run: python app.py")
    else:
        print("❌ Some tests failed. Please fix the errors above.")
    print("=" * 50)
