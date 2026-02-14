"""
User Model
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

class User:
    """User model for authentication and profile management"""
    
    ROLES = ['user', 'admin']
    
    @staticmethod
    def create(db, email, password, name, phone, role='user'):
        """Create a new user"""
        if role not in User.ROLES:
            raise ValueError(f"Invalid role. Must be one of {User.ROLES}")
        
        # Check if user already exists
        existing_user = db.find_one('users', {'email': email.lower()})
        if existing_user:
            raise ValueError("User with this email already exists")
        
        user_data = {
            'email': email.lower(),
            'password_hash': generate_password_hash(password),
            'name': name,
            'phone': phone,
            'role': role,
            'is_verified': False,
            'is_active': True,
            'profile_image': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        user_id = db.insert_one('users', user_data)
        
        # Create wallet for the user
        from models.wallet import Wallet
        Wallet.create(db, user_id)
        
        return user_id
    
    @staticmethod
    def authenticate(db, email, password):
        """Authenticate user with email and password"""
        user = db.find_one('users', {'email': email.lower()})
        
        if not user:
            return None
        
        if not check_password_hash(user['password_hash'], password):
            return None
        
        if not user.get('is_active', True):
            return None
        
        return user
    
    @staticmethod
    def get_by_id(db, user_id):
        """Get user by ID"""
        try:
            if not db or not hasattr(db, 'find_one'):
                raise ValueError("Invalid database object")
            return db.find_one('users', {'_id': ObjectId(user_id)})
        except Exception as e:
            # Log the error but still return None for not found
            print(f"[ERROR] User.get_by_id failed for {user_id}: {e}")
            return None
    
    @staticmethod
    def get_by_email(db, email):
        """Get user by email"""
        return db.find_one('users', {'email': email.lower()})
    
    @staticmethod
    def update(db, user_id, update_data):
        """Update user information"""
        update_data['updated_at'] = datetime.utcnow()
        return db.update_one(
            'users',
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )
    
    @staticmethod
    def update_password(db, user_id, new_password):
        """Update user password"""
        password_hash = generate_password_hash(new_password)
        return db.update_one(
            'users',
            {'_id': ObjectId(user_id)},
            {'$set': {
                'password_hash': password_hash,
                'updated_at': datetime.utcnow()
            }}
        )
    
    @staticmethod
    def get_all_users(db, role=None, skip=0, limit=50):
        """Get all users with optional role filter"""
        query = {}
        if role:
            query['role'] = role
        
        return db.find_many(
            'users',
            query,
            projection={'password_hash': 0},
            sort=[('created_at', -1)],
            limit=limit
        )
    
    @staticmethod
    def to_dict(user):
        """Convert user document to dictionary"""
        if not user:
            return None
        
        return {
            'id': str(user['_id']),
            'email': user['email'],
            'name': user['name'],
            'phone': user.get('phone'),
            'role': user['role'],
            'is_verified': user.get('is_verified', False),
            'is_active': user.get('is_active', True),
            'profile_image': user.get('profile_image'),
            'created_at': user['created_at'].isoformat() if user.get('created_at') else None,
            'updated_at': user['updated_at'].isoformat() if user.get('updated_at') else None
        }
