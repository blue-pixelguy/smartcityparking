from pymongo import MongoClient, GEOSPHERE
from config import Config

class Database:
    def __init__(self):
        self.client = MongoClient(Config.MONGO_URI)
        self.db = self.client.parking_system
        
        # Collections
        self.users = self.db.users
        self.parkings = self.db.parkings
        self.bookings = self.db.bookings
        self.transactions = self.db.transactions
        self.messages = self.db.messages
        self.notifications = self.db.notifications
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        
        # Users indexes
        self.users.create_index('email', unique=True)
        self.users.create_index('phone', unique=True)
        self.users.create_index('role')
        
        # Parkings indexes
        self.parkings.create_index([('location', GEOSPHERE)])  # Geospatial index
        self.parkings.create_index('city')
        self.parkings.create_index('status')
        self.parkings.create_index('host_id')
        self.parkings.create_index('vehicle_type')
        self.parkings.create_index('is_available')
        self.parkings.create_index([
            ('city', 1),
            ('vehicle_type', 1),
            ('status', 1),
            ('is_available', 1)
        ])
        
        # Bookings indexes
        self.bookings.create_index('driver_id')
        self.bookings.create_index('host_id')
        self.bookings.create_index('parking_id')
        self.bookings.create_index('status')
        self.bookings.create_index('start_time')
        self.bookings.create_index('end_time')
        
        # Transactions indexes
        self.transactions.create_index('user_id')
        self.transactions.create_index('booking_id')
        self.transactions.create_index('status')
        self.transactions.create_index('type')
        
        # Messages indexes
        self.messages.create_index('booking_id')
        self.messages.create_index('sender_id')
        self.messages.create_index('created_at')
        
        # Notifications indexes
        self.notifications.create_index('user_id')
        self.notifications.create_index('is_read')
        self.notifications.create_index('created_at')
    
    def create_admin_user(self, email, password, name, phone):
        """Create an admin user"""
        from werkzeug.security import generate_password_hash
        from datetime import datetime
        
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
        
        try:
            result = self.users.insert_one(admin)
            print(f"Admin user created with ID: {result.inserted_id}")
            return result.inserted_id
        except Exception as e:
            print(f"Error creating admin user: {e}")
            return None

# Initialize database connection
db_instance = Database()