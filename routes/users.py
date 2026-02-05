from flask import Blueprint, request, jsonify
from bson import ObjectId
from config.database import db
from routes.middleware import require_auth

bp = Blueprint('users', __name__)

@bp.route('/profile', methods=['GET'])
@require_auth
def get_profile(current_user):
    """Get current user profile"""
    try:
        users_collection = db.get_collection('users')
        
        if users_collection is None:
            return jsonify({'message': 'Database not available'}), 503
        
        user = users_collection.find_one({'_id': ObjectId(current_user['id'])})
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Remove sensitive data
        user.pop('password', None)
        user['_id'] = str(user['_id'])
        
        return jsonify(user), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile(current_user):
    """Update current user profile"""
    try:
        data = request.json
        
        users_collection = db.get_collection('users')
        
        if users_collection is None:
            return jsonify({'message': 'Database not available'}), 503
        
        # Fields that can be updated
        update_fields = {}
        allowed_fields = ['full_name', 'phone', 'vehicle_number']
        
        for field in allowed_fields:
            if field in data:
                update_fields[field] = data[field]
        
        if not update_fields:
            return jsonify({'message': 'No valid fields to update'}), 400
        
        result = users_collection.update_one(
            {'_id': ObjectId(current_user['id'])},
            {'$set': update_fields}
        )
        
        if result.matched_count == 0:
            return jsonify({'message': 'User not found'}), 404
        
        # Get updated user
        user = users_collection.find_one({'_id': ObjectId(current_user['id'])})
        user.pop('password', None)
        user['_id'] = str(user['_id'])
        
        return jsonify(user), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@bp.route('', methods=['GET'])
@require_auth
def get_all_users(current_user):
    """Get all users (admin only)"""
    try:
        if current_user.get('role') != 'admin':
            return jsonify({'message': 'Unauthorized'}), 403
        
        users_collection = db.get_collection('users')
        
        if users_collection is None:
            return jsonify({'message': 'Database not available'}), 503
        
        users = list(users_collection.find())
        
        for user in users:
            user.pop('password', None)
            user['_id'] = str(user['_id'])
        
        return jsonify(users), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500
