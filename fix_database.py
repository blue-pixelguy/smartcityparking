"""
Database Index Fix Script
Run this to fix the MongoDB index conflicts
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/smartparking')
client = MongoClient(MONGO_URI)
db = client.get_database()

print("🔧 Fixing MongoDB Indexes...")

# Drop all indexes on users collection except _id
try:
    db.users.drop_indexes()
    print("✅ Dropped all old indexes")
except Exception as e:
    print(f"⚠️  Error dropping indexes: {e}")

# Create only the necessary indexes
try:
    # Email should be unique
    db.users.create_index('email', unique=True)
    print("✅ Created email index (unique)")
    
    # Phone can have duplicates (some users might not have phone)
    db.users.create_index('phone', unique=False, sparse=True)
    print("✅ Created phone index (non-unique, sparse)")
    
    print("\n✅ Database indexes fixed successfully!")
    print("\nYou can now register users without errors.")
    
except Exception as e:
    print(f"❌ Error creating indexes: {e}")

client.close()
