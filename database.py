from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import CollectionInvalid
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class Database:
    def __init__(self):
        self.client = MongoClient(os.getenv('MONGO_URI'))
        self.db = self.client[os.getenv('DB_NAME')]
        self.initialize_collections()
    
    def initialize_collections(self):
        """Initialize collections and create indexes"""
        
        # Users Collection
        try:
            self.db.create_collection('users')
        except CollectionInvalid:
            pass
        
        self.db.users.create_index([('email', ASCENDING)], unique=True)
        self.db.users.create_index([('phone', ASCENDING)])
        
        # Parking Spaces Collection
        try:
            self.db.create_collection('parking_spaces')
        except CollectionInvalid:
            pass
        
        self.db.parking_spaces.create_index([('location', '2dsphere')])
        self.db.parking_spaces.create_index([('owner_id', ASCENDING)])
        self.db.parking_spaces.create_index([('status', ASCENDING)])
        
        # Bookings Collection
        try:
            self.db.create_collection('bookings')
        except CollectionInvalid:
            pass
        
        self.db.bookings.create_index([('driver_id', ASCENDING)])
        self.db.bookings.create_index([('parking_id', ASCENDING)])
        self.db.bookings.create_index([('status', ASCENDING)])
        self.db.bookings.create_index([('start_time', ASCENDING)])
        
        # Wallets Collection
        try:
            self.db.create_collection('wallets')
        except CollectionInvalid:
            pass
        
        self.db.wallets.create_index([('user_id', ASCENDING)], unique=True)
        
        # Transactions Collection
        try:
            self.db.create_collection('transactions')
        except CollectionInvalid:
            pass
        
        self.db.transactions.create_index([('user_id', ASCENDING)])
        self.db.transactions.create_index([('created_at', DESCENDING)])
        
        # Messages Collection
        try:
            self.db.create_collection('messages')
        except CollectionInvalid:
            pass
        
        self.db.messages.create_index([('sender_id', ASCENDING)])
        self.db.messages.create_index([('receiver_id', ASCENDING)])
        self.db.messages.create_index([('booking_id', ASCENDING)])
        
        # Reviews Collection
        try:
            self.db.create_collection('reviews')
        except CollectionInvalid:
            pass
        
        self.db.reviews.create_index([('parking_id', ASCENDING)])
        self.db.reviews.create_index([('reviewer_id', ASCENDING)])
        
        # Notifications Collection
        try:
            self.db.create_collection('notifications')
        except CollectionInvalid:
            pass
        
        self.db.notifications.create_index([('user_id', ASCENDING)])
        self.db.notifications.create_index([('created_at', DESCENDING)])
        
        print("Database initialized successfully!")
    
    def get_collection(self, name):
        return self.db[name]

# Initialize database instance
db = Database()
