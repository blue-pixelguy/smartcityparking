from functools import wraps
from flask import request, jsonify
import jwt
import os
from bson import ObjectId
from config.database import db

def require_auth(f):
    """Middleware to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            
            if not auth_header:
                return jsonify({'message': 'Authorization token is required'}), 401
            
            # Extract token (format: "Bearer <token>")
            parts = auth_header.split()
            
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return jsonify({'message': 'Invalid authorization header format'}), 401
            
            token = parts[1]
            
            # Decode token
            try:
                payload = jwt.decode(
                    token,
                    os.getenv('SECRET_KEY'),
                    algorithms=['HS256']
                )
            except jwt.ExpiredSignatureError:
                return jsonify({'message': 'Token has expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'message': 'Invalid token'}), 401
            
            # Get user from database
            users_collection = db.get_collection('users')
            
            if users_collection is None:
                return jsonify({'message': 'Database not available'}), 503
            
            user = users_collection.find_one({'_id': ObjectId(payload['user_id'])})
            
            if not user:
                return jsonify({'message': 'User not found'}), 401
            
            # Create current_user object (without password)
            current_user = {
                'id': str(user['_id']),
                'email': user['email'],
                'full_name': user.get('full_name'),
                'role': user.get('role', 'user')
            }
            
            # Call the actual function with current_user
            return f(current_user, *args, **kwargs)
            
        except Exception as e:
            return jsonify({'message': f'Authentication error: {str(e)}'}), 401
    
    return decorated_function
