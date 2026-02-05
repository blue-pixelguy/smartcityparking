import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class Database:
    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self.connect()

    def connect(self):
        """Connect to MongoDB"""
        try:
            mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
            db_name = os.getenv('DB_NAME', 'parking_db')
            
            self._client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self._client.server_info()
            self._db = self._client[db_name]
            print(f"✓ Connected to MongoDB: {db_name}")
            return True
        except Exception as e:
            print(f"✗ MongoDB connection failed: {e}")
            print("  Running without database (API test mode)")
            return False

    def get_db(self):
        """Get database instance"""
        return self._db

    def get_collection(self, collection_name):
        """Get a specific collection"""
        if self._db is None:
            return None
        return self._db[collection_name]

# Global database instance
db = Database()
