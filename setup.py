#!/usr/bin/env python3
"""
Setup script for P2P Parking System
This script initializes the database and creates sample data for testing
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db
from models import User, ParkingSpace, Wallet

def create_admin_user():
    """Create admin user"""
    print("Creating admin user...")
    
    # Check if admin exists
    existing_admin = db.db.users.find_one({'email': 'admin@parking.com'})
    if existing_admin:
        print("Admin user already exists!")
        return
    
    admin = User(
        name="Admin User",
        email="admin@parking.com",
        phone="9999999999",
        password="admin123",
        role="admin"
    )
    admin.is_verified = True
    
    result = db.db.users.insert_one(admin.to_dict())
    
    # Create wallet for admin
    wallet = Wallet(user_id=str(result.inserted_id), balance=10000.0)
    db.db.wallets.insert_one(wallet.to_dict())
    
    print(f"✅ Admin created: admin@parking.com / admin123")
    print(f"   User ID: {result.inserted_id}")

def create_sample_users():
    """Create sample users"""
    print("\nCreating sample users...")
    
    users = [
        {
            'name': 'Rajesh Kumar',
            'email': 'rajesh@example.com',
            'phone': '9876543210',
            'password': 'password123',
            'role': 'host'
        },
        {
            'name': 'Priya Sharma',
            'email': 'priya@example.com',
            'phone': '9876543211',
            'password': 'password123',
            'role': 'driver'
        },
        {
            'name': 'Arun Venkat',
            'email': 'arun@example.com',
            'phone': '9876543212',
            'password': 'password123',
            'role': 'host'
        },
        {
            'name': 'Lakshmi Devi',
            'email': 'lakshmi@example.com',
            'phone': '9876543213',
            'password': 'password123',
            'role': 'driver'
        }
    ]
    
    created_users = []
    
    for user_data in users:
        # Check if user exists
        existing = db.db.users.find_one({'email': user_data['email']})
        if existing:
            print(f"   User {user_data['email']} already exists, skipping...")
            created_users.append(str(existing['_id']))
            continue
        
        user = User(
            name=user_data['name'],
            email=user_data['email'],
            phone=user_data['phone'],
            password=user_data['password'],
            role=user_data['role']
        )
        user.is_verified = True
        
        result = db.db.users.insert_one(user.to_dict())
        user_id = str(result.inserted_id)
        created_users.append(user_id)
        
        # Create wallet
        wallet = Wallet(user_id=user_id, balance=5000.0)
        db.db.wallets.insert_one(wallet.to_dict())
        
        print(f"✅ Created: {user_data['name']} ({user_data['email']}) - {user_data['role']}")
    
    return created_users

def create_sample_parking(user_ids):
    """Create sample parking spaces"""
    print("\nCreating sample parking spaces...")
    
    # Trichy locations
    parking_data = [
        {
            'title': 'Secure 2-Wheeler Parking near Srirangam Temple',
            'description': 'Covered parking space for 2-wheelers. Located near the famous Srirangam Temple. Safe and secure with 24/7 CCTV surveillance.',
            'address': 'Near Srirangam Temple, Srirangam, Trichy',
            'latitude': 10.8650,
            'longitude': 78.6936,
            'vehicle_type': '2-wheeler',
            'price_per_hour': 10.0,
            'total_hours': 10,
            'features': ['CCTV', 'Covered', '24/7 Access']
        },
        {
            'title': 'Car Parking at Thillai Nagar Main Road',
            'description': 'Spacious parking for cars near Thillai Nagar shopping area. Easy access to main road.',
            'address': 'Thillai Nagar Main Road, Trichy',
            'latitude': 10.8055,
            'longitude': 78.6856,
            'vehicle_type': '4-wheeler',
            'price_per_hour': 30.0,
            'total_hours': 12,
            'features': ['Spacious', 'Main Road', 'Well-lit']
        },
        {
            'title': 'Multi-Vehicle Parking near Railway Station',
            'description': 'Large parking area for both 2-wheelers and 4-wheelers. Very close to Trichy Junction railway station.',
            'address': 'Near Trichy Junction, Cantonment, Trichy',
            'latitude': 10.8225,
            'longitude': 78.6867,
            'vehicle_type': 'both',
            'price_per_hour': 20.0,
            'total_hours': 24,
            'features': ['Near Station', 'Security', 'Large Space']
        },
        {
            'title': 'Bike Parking at K.K. Nagar Market',
            'description': 'Convenient parking for bikes near K.K. Nagar market area. Ideal for shopping trips.',
            'address': 'K.K. Nagar Market, Trichy',
            'latitude': 10.7671,
            'longitude': 78.7005,
            'vehicle_type': '2-wheeler',
            'price_per_hour': 8.0,
            'total_hours': 8,
            'features': ['Market Area', 'Convenient', 'Affordable']
        }
    ]
    
    # Get host users
    host_users = list(db.db.users.find({'role': 'host'}))
    
    if not host_users:
        print("No host users found! Please create host users first.")
        return
    
    for i, data in enumerate(parking_data):
        # Use different hosts
        owner_id = str(host_users[i % len(host_users)]['_id'])
        
        parking = ParkingSpace(
            owner_id=owner_id,
            title=data['title'],
            description=data['description'],
            address=data['address'],
            location={
                'type': 'Point',
                'coordinates': [data['longitude'], data['latitude']]
            },
            vehicle_type=data['vehicle_type'],
            price_per_hour=data['price_per_hour'],
            total_hours=data['total_hours']
        )
        parking.features = data['features']
        parking.status = 'approved'  # Pre-approve for testing
        parking.availability_start = datetime.utcnow()
        parking.availability_end = datetime.utcnow() + timedelta(days=30)
        
        result = db.db.parking_spaces.insert_one(parking.to_dict())
        print(f"✅ Created: {data['title']}")
        print(f"   Location: {data['address']}")
        print(f"   Price: ₹{data['price_per_hour']}/hour")

def display_summary():
    """Display setup summary"""
    print("\n" + "="*60)
    print("SETUP COMPLETE!")
    print("="*60)
    
    # Count documents
    users = db.db.users.count_documents({})
    parking = db.db.parking_spaces.count_documents({})
    
    print(f"\n📊 Database Summary:")
    print(f"   Total Users: {users}")
    print(f"   Total Parking Spaces: {parking}")
    
    print(f"\n🔐 Test Accounts:")
    print(f"   Admin: admin@parking.com / admin123")
    print(f"   Host: rajesh@example.com / password123")
    print(f"   Driver: priya@example.com / password123")
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Run: python app.py")
    print(f"   2. Open: http://localhost:5000")
    print(f"   3. Test the API using the frontend or Postman")
    
    print(f"\n📝 Documentation:")
    print(f"   See README.md for API documentation")
    print("="*60)

def main():
    """Main setup function"""
    print("\n" + "="*60)
    print("P2P PARKING SYSTEM - SETUP")
    print("="*60)
    
    try:
        # Test database connection
        print("\nTesting database connection...")
        db.client.server_info()
        print("✅ Database connected successfully!")
        
        # Create admin
        create_admin_user()
        
        # Create sample users
        user_ids = create_sample_users()
        
        # Create sample parking spaces
        create_sample_parking(user_ids)
        
        # Display summary
        display_summary()
        
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        print("\nPlease ensure MongoDB is running:")
        print("   sudo systemctl start mongodb")
        sys.exit(1)

if __name__ == '__main__':
    main()
