"""
Simple MongoDB Connection Test
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

print("=" * 60)
print("Testing MongoDB Connection")
print("=" * 60)

# Get MONGO_URI from environment
mongo_uri = os.getenv('MONGO_URI')

print(f"\n📋 Checking MONGO_URI...")
if not mongo_uri:
    print("❌ ERROR: MONGO_URI not found in .env file")
    exit(1)

# Hide password in output
safe_uri = mongo_uri.split('@')[1] if '@' in mongo_uri else mongo_uri
print(f"✅ MONGO_URI found: mongodb+srv://***@{safe_uri}")

# Check URI format
if not (mongo_uri.startswith('mongodb://') or mongo_uri.startswith('mongodb+srv://')):
    print("❌ ERROR: Invalid URI scheme")
    print("   URI must start with 'mongodb://' or 'mongodb+srv://'")
    exit(1)

print("✅ URI scheme is valid")

# Check if database name is included
if '?' in mongo_uri:
    uri_path = mongo_uri.split('?')[0]
    if '/' in uri_path.split('@')[1]:
        db_name = uri_path.split('@')[1].split('/')[1]
        if db_name:
            print(f"✅ Database name found: {db_name}")
        else:
            print("⚠️  WARNING: No database name specified in URI")
    else:
        print("⚠️  WARNING: No database name specified in URI")
else:
    print("⚠️  WARNING: No database name specified in URI")

# Try to connect
print("\n🔄 Attempting to connect to MongoDB...")
try:
    client = MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=5000
    )
    
    # Test connection
    client.admin.command('ping')
    print("✅ MongoDB connection successful!")
    
    # Get database
    db = client.get_database()
    print(f"✅ Connected to database: {db.name}")
    
    # List collections
    collections = db.list_collection_names()
    print(f"✅ Found {len(collections)} collections")
    if collections:
        print(f"   Collections: {', '.join(collections[:5])}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYou can now run: python app.py")
    
except Exception as e:
    print(f"\n❌ CONNECTION FAILED!")
    print(f"   Error: {e}")
    print("\n" + "=" * 60)
    print("🔧 TROUBLESHOOTING:")
    print("=" * 60)
    print("1. Check if your IP is whitelisted in MongoDB Atlas")
    print("   → Go to: https://cloud.mongodb.com")
    print("   → Network Access → Add IP Address")
    print("   → Use 0.0.0.0/0 for testing")
    print("\n2. Verify your connection string includes database name")
    print("   → Should be: mongodb+srv://user:pass@host/DATABASE_NAME?options")
    print("\n3. Check if database user exists and has correct password")
    print("   → Database Access in MongoDB Atlas")
    exit(1)
