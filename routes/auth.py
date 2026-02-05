from flask import Blueprint, request, jsonify
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from config.database import db

bp = Blueprint('auth', __name__)

def generate_token(user_id):
    """Generate JWT token"""
    payload = {
        'user_id': str(user_id),
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    token = jwt.encode(payload, os.getenv('SECRET_KEY'), algorithm='HS256')
    return token

@bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['email', 'password', 'full_name', 'phone', 'vehicle_number']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'{field} is required'}), 400
        
        users_collection = db.get_collection('users')
        
        if users_collection is None:
            return jsonify({'message': 'Database not available'}), 503
        
        # Check if user already exists
        if users_collection.find_one({'email': data['email']}):
            return jsonify({'message': 'Email already registered'}), 400
        
        # Hash password
        hashed_password = bcrypt.hashpw(
            data['password'].encode('utf-8'),
            bcrypt.gensalt()
        )
        
        # Create user document
        user = {
            'email': data['email'],
            'password': hashed_password.decode('utf-8'),
            'full_name': data['full_name'],
            'phone': data['phone'],
            'vehicle_number': data['vehicle_number'],
            'role': 'user',
            'created_at': datetime.utcnow()
        }
        
        result = users_collection.insert_one(user)
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@bp.route('/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.json
        
        # Validate required fields
        if 'email' not in data or 'password' not in data:
            return jsonify({'message': 'Email and password are required'}), 400
        
        users_collection = db.get_collection('users')
        
        if users_collection is None:
            return jsonify({'message': 'Database not available'}), 503
        
        # Find user
        user = users_collection.find_one({'email': data['email']})
        
        if not user:
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Verify password
        if not bcrypt.checkpw(
            data['password'].encode('utf-8'),
            user['password'].encode('utf-8')
        ):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Generate token
        token = generate_token(user['_id'])
        
        # Return user data (without password)
        user_data = {
            'id': str(user['_id']),
            'email': user['email'],
            'full_name': user.get('full_name'),
            'phone': user.get('phone'),
            'vehicle_number': user.get('vehicle_number'),
            'role': user.get('role', 'user')
        }
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': user_data
        }), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@bp.route('/verify', methods=['GET'])
def verify_token():
    """Verify JWT token"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'message': 'Token is required'}), 401
        
        payload = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=['HS256'])
        
        return jsonify({
            'message': 'Token is valid',
            'user_id': payload['user_id']
        }), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'message': str(e)}), 500
