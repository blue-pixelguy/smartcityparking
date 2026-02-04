#!/usr/bin/env python3
"""
Setup script for ParkEasy - Peer-to-Peer Parking System
This script initializes the database and creates an admin user
"""

from database import Database
from werkzeug.security import generate_password_hash
from datetime import datetime
import sys

def setup_database():
    """Initialize database with indexes and collections"""
    print("Initializing database...")
    
    db = Database()
    
    print("✓ Database connection established")
    print("✓ Collections created")
    print("✓ Indexes created")
    
    return db

def create_admin_user(db):
    """Create an admin user"""
    print("\n--- Create Admin User ---")
    
    name = input("Admin Name: ").strip()
    email = input("Admin Email: ").strip()
    phone = input("Admin Phone (10 digits): ").strip()
    password = input("Admin Password: ").strip()
    
    if not all([name, email, phone, password]):
        print("❌ All fields are required!")
        return False
    
    if len(phone) != 10 or not phone.isdigit():
        print("❌ Phone number must be 10 digits!")
        return False
    
    try:
        # Check if admin already exists
        existing = db.users.find_one({'email': email})
        if existing:
            print("❌ Email already exists!")
            return False
        
        existing = db.users.find_one({'phone': phone})
        if existing:
            print("❌ Phone number already exists!")
            return False
        
        # Create admin user
        admin = {
            'name': name,
            'email': email,
            'password': generate_password_hash(password),
            'phone': phone,
            'role': 'admin',
            'wallet_balance': 0,
            'created_at': datetime.utcnow(),
            'is_verified': True
        }
        
        result = db.users.insert_one(admin)
        print(f"✓ Admin user created successfully!")
        print(f"  ID: {result.inserted_id}")
        print(f"  Email: {email}")
        print(f"  Login with these credentials to access admin panel")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create admin user: {e}")
        return False

def add_sample_data(db):
    """Add sample parking data for testing"""
    print("\n--- Add Sample Data? ---")
    choice = input("Add sample parking locations for Trichy? (y/n): ").strip().lower()
    
    if choice != 'y':
        return
    
    # Sample parking locations in Trichy
    sample_parkings = [
        {
            'title': 'Secure Parking near Trichy Central Bus Stand',
            'description': 'Safe and secure parking space with CCTV surveillance',
            'address': 'Rockins Road, Near Central Bus Stand, Trichy',
            'city': 'trichy',
            'state': 'tamil nadu',
            'location': {
                'type': 'Point',
                'coordinates': [78.7047, 10.7905]
            },
            'vehicle_type': '2-wheeler',
            'price_per_hour': 10,
            'total_hours': 10,
            'min_rental_hours': 7,
            'amenities': ['CCTV', 'Security Guard', 'Covered'],
            'status': 'approved',
            'is_available': True,
            'created_at': datetime.utcnow(),
            'ratings': [],
            'average_rating': 0,
            'images': []
        },
        {
            'title': 'Open Parking - Junction Main Road',
            'description': 'Large parking area suitable for 4-wheelers',
            'address': 'Junction Main Road, Trichy',
            'city': 'trichy',
            'state': 'tamil nadu',
            'location': {
                'type': 'Point',
                'coordinates': [78.6869, 10.8155]
            },
            'vehicle_type': '4-wheeler',
            'price_per_hour': 20,
            'total_hours': 8,
            'min_rental_hours': 6,
            'amenities': ['Open Area', 'Well-lit'],
            'status': 'approved',
            'is_available': True,
            'created_at': datetime.utcnow(),
            'ratings': [],
            'average_rating': 0,
            'images': []
        },
        {
            'title': 'Covered Parking - Srirangam Temple Area',
            'description': 'Covered parking near famous temple, very safe',
            'address': 'Srirangam, Trichy',
            'city': 'trichy',
            'state': 'tamil nadu',
            'location': {
                'type': 'Point',
                'coordinates': [78.6956, 10.8624]
            },
            'vehicle_type': '2-wheeler',
            'price_per_hour': 15,
            'total_hours': 12,
            'min_rental_hours': 8,
            'amenities': ['Covered', 'CCTV', 'Near Temple'],
            'status': 'approved',
            'is_available': True,
            'created_at': datetime.utcnow(),
            'ratings': [],
            'average_rating': 0,
            'images': []
        }
    ]
    
    try:
        # Create a sample host user
        host = {
            'name': 'Sample Host',
            'email': 'host@parkeasy.com',
            'password': generate_password_hash('password123'),
            'phone': '9876543210',
            'role': 'host',
            'wallet_balance': 0,
            'created_at': datetime.utcnow(),
            'is_verified': True
        }
        
        host_result = db.users.insert_one(host)
        
        # Add host_id to parking samples
        for parking in sample_parkings:
            parking['host_id'] = host_result.inserted_id
            parking['host_name'] = 'Sample Host'
            parking['host_phone'] = '9876543210'
            parking['available_from'] = datetime.utcnow()
            parking['available_to'] = datetime.utcnow().replace(hour=23, minute=59)
        
        db.parkings.insert_many(sample_parkings)
        
        print(f"✓ Sample data added successfully!")
        print(f"  Created {len(sample_parkings)} parking locations")
        print(f"  Sample Host credentials:")
        print(f"    Email: host@parkeasy.com")
        print(f"    Password: password123")
        
    except Exception as e:
        print(f"❌ Failed to add sample data: {e}")

def main():
    print("=" * 50)
    print("ParkEasy - Setup Script")
    print("=" * 50)
    
    try:
        # Initialize database
        db = setup_database()
        
        # Create admin user
        if create_admin_user(db):
            # Optionally add sample data
            add_sample_data(db)
        
        print("\n" + "=" * 50)
        print("Setup completed successfully!")
        print("=" * 50)
        print("\nNext steps:")
        print("1. Update .env file with your API keys")
        print("2. Run: python app.py")
        print("3. Open: http://localhost:5000")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()