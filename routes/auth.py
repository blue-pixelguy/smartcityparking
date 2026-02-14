"""
Authentication Routes
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.user import User
from models.database import db as database

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'name', 'phone']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Default role to 'user' if not provided (unified registration)
        role = data.get('role', 'user')
        
        # Validate role
        if role not in User.ROLES:
            return jsonify({'error': f'Invalid role. Must be one of {User.ROLES}'}), 400
        
        # Create user
        user_id = User.create(
            database,
            email=data['email'],
            password=data['password'],
            name=data['name'],
            phone=data['phone'],
            role=role
        )
        
        # Get created user
        user = User.get_by_id(database, str(user_id))
        
        # Create access token
        access_token = create_access_token(identity=str(user_id))
        
        return jsonify({
            'message': 'User registered successfully',
            'user': User.to_dict(user),
            'access_token': access_token
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Registration failed', 'details': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Authenticate user
        user = User.authenticate(
            database,
            email=data['email'],
            password=data['password']
        )
        
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Create access token
        access_token = create_access_token(identity=str(user['_id']))
        
        return jsonify({
            'message': 'Login successful',
            'user': User.to_dict(user),
            'access_token': access_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        user_id = get_jwt_identity()
        user = User.get_by_id(database, user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': User.to_dict(user)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get profile', 'details': str(e)}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Remove fields that shouldn't be updated directly
        data.pop('email', None)
        data.pop('password', None)
        data.pop('role', None)
        data.pop('_id', None)
        
        # Update user
        User.update(database, user_id, data)
        
        # Get updated user
        user = User.get_by_id(database, user_id)
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': User.to_dict(user)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to update profile', 'details': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if 'old_password' not in data or 'new_password' not in data:
            return jsonify({'error': 'Old password and new password are required'}), 400
        
        # Get user
        user = User.get_by_id(database, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify old password
        authenticated = User.authenticate(
            database,
            email=user['email'],
            password=data['old_password']
        )
        
        if not authenticated:
            return jsonify({'error': 'Invalid old password'}), 401
        
        # Update password
        User.update_password(database, user_id, data['new_password'])
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to change password', 'details': str(e)}), 500
