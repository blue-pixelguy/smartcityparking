#!/usr/bin/env python3
"""
Setup script for Parking Management System
Initializes database collections and creates indexes
"""

import sys
from pymongo import ASCENDING, DESCENDING
from config.database import db

def create_collections():
    """Create collections with proper schemas"""
    database = db.get_db()
    
    if database is None:
        print("✗ Database not connected. Please start MongoDB first.")
        return False
    
    collections = {
        'users': [
            ('email', ASCENDING, True),  # unique
            ('username', ASCENDING, True)  # unique
        ],
        'parking_slots': [
            ('slot_number', ASCENDING, True),  # unique
            ('status', ASCENDING, False)
        ],
        'bookings': [
            ('user_id', ASCENDING, False),
            ('slot_id', ASCENDING, False),
            ('status', ASCENDING, False),
            ('start_time', DESCENDING, False)
        ],
        'payments': [
            ('booking_id', ASCENDING, False),
            ('user_id', ASCENDING, False),
            ('payment_date', DESCENDING, False)
        ]
    }
    
    print("\n🔧 Setting up database collections...")
    
    for collection_name, indexes in collections.items():
        # Create collection if it doesn't exist
        if collection_name not in database.list_collection_names():
            database.create_collection(collection_name)
            print(f"  ✓ Created collection: {collection_name}")
        else:
            print(f"  → Collection exists: {collection_name}")
        
        # Create indexes
        collection = database[collection_name]
        for index_field, order, unique in indexes:
            try:
                collection.create_index(
                    [(index_field, order)],
                    unique=unique,
                    background=True
                )
                unique_str = " (unique)" if unique else ""
                print(f"    ✓ Index: {index_field}{unique_str}")
            except Exception as e:
                print(f"    ⚠ Index {index_field}: {str(e)}")
    
    return True

def create_default_slots():
    """Create default parking slots"""
    database = db.get_db()
    
    if database is None:
        return False
    
    slots_collection = database['parking_slots']
    
    # Check if slots already exist
    if slots_collection.count_documents({}) > 0:
        print("\n✓ Parking slots already initialized")
        return True
    
    print("\n🚗 Creating default parking slots...")
    
    # Create 50 parking slots
    slots = []
    for i in range(1, 51):
        slot = {
            'slot_number': f'A{i:02d}',
            'status': 'available',  # available, occupied, maintenance
            'floor': 1 if i <= 25 else 2,
            'type': 'regular',  # regular, handicapped, vip
            'hourly_rate': 50.0
        }
        slots.append(slot)
    
    # Add some VIP slots
    for i in range(51, 56):
        slot = {
            'slot_number': f'V{i-50:02d}',
            'status': 'available',
            'floor': 1,
            'type': 'vip',
            'hourly_rate': 100.0
        }
        slots.append(slot)
    
    # Add handicapped slots
    for i in range(56, 61):
        slot = {
            'slot_number': f'H{i-55:02d}',
            'status': 'available',
            'floor': 1,
            'type': 'handicapped',
            'hourly_rate': 40.0
        }
        slots.append(slot)
    
    try:
        result = slots_collection.insert_many(slots)
        print(f"  ✓ Created {len(result.inserted_ids)} parking slots")
        return True
    except Exception as e:
        print(f"  ✗ Error creating slots: {e}")
        return False

def create_test_user():
    """Create a test user account"""
    import bcrypt
    
    database = db.get_db()
    
    if database is None:
        return False
    
    users_collection = database['users']
    
    # Check if test user exists
    if users_collection.find_one({'email': 'test@parking.com'}):
        print("\n✓ Test user already exists")
        return True
    
    print("\n👤 Creating test user...")
    
    test_user = {
        'username': 'testuser',
        'email': 'test@parking.com',
        'password': bcrypt.hashpw('test123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        'full_name': 'Test User',
        'phone': '+1234567890',
        'vehicle_number': 'TN01AB1234',
        'role': 'user',
        'created_at': None
    }
    
    try:
        from datetime import datetime
        test_user['created_at'] = datetime.utcnow()
        users_collection.insert_one(test_user)
        print("  ✓ Test user created:")
        print("    Email: test@parking.com")
        print("    Password: test123")
        return True
    except Exception as e:
        print(f"  ✗ Error creating test user: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("  PARKING MANAGEMENT SYSTEM - DATABASE SETUP")
    print("=" * 60)
    
    # Try to connect to database
    if not db.connect():
        print("\n❌ Setup failed: Could not connect to MongoDB")
        print("\nPlease ensure MongoDB is running:")
        print("  - Install: sudo apt install mongodb")
        print("  - Start: sudo systemctl start mongodb")
        print("  - Status: sudo systemctl status mongodb")
        return 1
    
    # Create collections and indexes
    if not create_collections():
        print("\n❌ Setup failed: Could not create collections")
        return 1
    
    # Create default parking slots
    if not create_default_slots():
        print("\n⚠ Warning: Could not create default slots")
    
    # Create test user
    if not create_test_user():
        print("\n⚠ Warning: Could not create test user")
    
    print("\n" + "=" * 60)
    print("  ✅ SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nYou can now start the application:")
    print("  python app.py")
    print("\nAccess the web interface at:")
    print("  http://localhost:5000")
    print()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
