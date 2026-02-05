from flask import Blueprint, request, jsonify
from database import db
from models import User, Wallet
from auth import create_token, token_required
from bson import ObjectId

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """User registration"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'password', 'role']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if user exists
        existing_user = db.db.users.find_one({'email': data['email']})
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 400
        
        # Validate role
        if data['role'] not in ['driver', 'host', 'admin']:
            return jsonify({'error': 'Invalid role'}), 400
        
        # Create user
        user = User(
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            password=data['password'],
            role=data['role']
        )
        
        if 'address' in data:
            user.address = data['address']
        
        result = db.db.users.insert_one(user.to_dict())
        user_id = str(result.inserted_id)
        
        # Create wallet for user
        wallet = Wallet(user_id=user_id, balance=0.0)
        db.db.wallets.insert_one(wallet.to_dict())
        
        # Create token
        token = create_token(user_id, data['role'])
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user_id,
            'token': token,
            'role': data['role']
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user
        user = db.db.users.find_one({'email': data['email']})
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Verify password
        if not User.verify_password(data['password'], user['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Create token
        token = create_token(str(user['_id']), user['role'])
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'phone': user['phone'],
                'role': user['role'],
                'is_verified': user.get('is_verified', False)
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    """Get user profile"""
    try:
        user = db.db.users.find_one({'_id': ObjectId(request.user_id)})
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get wallet balance
        wallet = db.db.wallets.find_one({'user_id': ObjectId(request.user_id)})
        
        return jsonify({
            'user': {
                'id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'phone': user['phone'],
                'role': user['role'],
                'is_verified': user.get('is_verified', False),
                'profile_image': user.get('profile_image'),
                'address': user.get('address'),
                'created_at': user['created_at'].isoformat()
            },
            'wallet_balance': wallet['balance'] if wallet else 0.0
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        
        update_fields = {}
        allowed_fields = ['name', 'phone', 'address']
        
        for field in allowed_fields:
            if field in data:
                update_fields[field] = data[field]
        
        if update_fields:
            db.db.users.update_one(
                {'_id': ObjectId(request.user_id)},
                {'$set': update_fields}
            )
        
        return jsonify({'message': 'Profile updated successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        
        if 'old_password' not in data or 'new_password' not in data:
            return jsonify({'error': 'Old and new passwords are required'}), 400
        
        user = db.db.users.find_one({'_id': ObjectId(request.user_id)})
        
        if not User.verify_password(data['old_password'], user['password']):
            return jsonify({'error': 'Invalid old password'}), 401
        
        new_password_hash = User.hash_password(data['new_password'])
        
        db.db.users.update_one(
            {'_id': ObjectId(request.user_id)},
            {'$set': {'password': new_password_hash}}
        )
        
        return jsonify({'message': 'Password changed successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
