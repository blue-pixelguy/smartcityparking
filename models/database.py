"""
Database Connection and Helper Functions
"""

from flask import current_app
from pymongo import ASCENDING, DESCENDING
from datetime import datetime
from bson.objectid import ObjectId

class Database:
    """Database helper class for MongoDB operations"""
    
    def __init__(self):
        self.db = None
    
    def init_app(self, app):
        """Initialize database with Flask app"""
        if not hasattr(app, 'db') or app.db is None:
            print("⚠️  Skipping database initialization - MongoDB not connected")
            return
        self.db = app.db
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            # First, drop all indexes except _id to avoid conflicts
            try:
                self.db.users.drop_indexes()
            except:
                pass  # Ignore if no indexes exist
            
            # Users collection indexes
            self.db.users.create_index([('email', ASCENDING)], unique=True)
            # Phone index - NOT unique, sparse (allows missing values)
            self.db.users.create_index([('phone', ASCENDING)], unique=False, sparse=True)
            self.db.users.create_index([('role', ASCENDING)])
            
            # Parking spaces collection indexes
            self.db.parking_spaces.create_index([('owner_id', ASCENDING)])
            self.db.parking_spaces.create_index([('status', ASCENDING)])
            self.db.parking_spaces.create_index([('vehicle_type', ASCENDING)])
            try:
                self.db.parking_spaces.create_index([
                    ('location.coordinates', '2dsphere')
                ])
            except:
                pass  # Geospatial index might not be supported
            
            # Bookings collection indexes
            self.db.bookings.create_index([('user_id', ASCENDING)])
            self.db.bookings.create_index([('parking_id', ASCENDING)])
            self.db.bookings.create_index([('status', ASCENDING)])
            self.db.bookings.create_index([('start_time', DESCENDING)])
            
            # Payments collection indexes
            self.db.payments.create_index([('booking_id', ASCENDING)])
            self.db.payments.create_index([('user_id', ASCENDING)])
            self.db.payments.create_index([('status', ASCENDING)])
            
            # Wallets collection indexes
            self.db.wallets.create_index([('user_id', ASCENDING)], unique=True)
            
            # Wallet transactions collection indexes
            self.db.wallet_transactions.create_index([('user_id', ASCENDING)])
            self.db.wallet_transactions.create_index([('wallet_id', ASCENDING)])
            self.db.wallet_transactions.create_index([('created_at', DESCENDING)])
            
            # Reviews collection indexes
            self.db.reviews.create_index([('parking_id', ASCENDING)])
            self.db.reviews.create_index([('user_id', ASCENDING)])
            
            # Messages/Chat collection indexes
            self.db.messages.create_index([('booking_id', ASCENDING)])
            self.db.messages.create_index([('sender_id', ASCENDING)])
            self.db.messages.create_index([('created_at', DESCENDING)])
            
            print("✅ Database indexes created successfully")
        except Exception as e:
            print(f"⚠️  Index creation warning: {e}")
            print("App will continue to work, but performance may be affected")
    
    def get_collection(self, collection_name):
        """Get a MongoDB collection"""
        return self.db[collection_name]
    
    def insert_one(self, collection_name, document):
        """Insert a single document"""
        # Only add timestamps if they don't exist
        if 'created_at' not in document:
            document['created_at'] = datetime.utcnow()
        if 'updated_at' not in document:
            document['updated_at'] = datetime.utcnow()
        result = self.db[collection_name].insert_one(document)
        return result.inserted_id
    
    def find_one(self, collection_name, query, projection=None):
        """Find a single document"""
        return self.db[collection_name].find_one(query, projection)
    
    def find_many(self, collection_name, query, projection=None, sort=None, limit=0):
        """Find multiple documents"""
        cursor = self.db[collection_name].find(query, projection)
        if sort:
            cursor = cursor.sort(sort)
        if limit > 0:
            cursor = cursor.limit(limit)
        return list(cursor)
    
    def update_one(self, collection_name, query, update, upsert=False):
        """Update a single document"""
        update.setdefault('$set', {})['updated_at'] = datetime.utcnow()
        result = self.db[collection_name].update_one(query, update, upsert=upsert)
        # Return True if document was found (matched), even if no changes were made
        return result.matched_count > 0
    
    def delete_one(self, collection_name, query):
        """Delete a single document"""
        result = self.db[collection_name].delete_one(query)
        return result.deleted_count > 0
    
    def count_documents(self, collection_name, query):
        """Count documents matching query"""
        return self.db[collection_name].count_documents(query)
    
    def aggregate(self, collection_name, pipeline):
        """Run aggregation pipeline"""
        return list(self.db[collection_name].aggregate(pipeline))

# Global database instance
db = Database()
