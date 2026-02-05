from flask import Blueprint, request, jsonify
from bson import ObjectId
from config.database import db
from routes.middleware import require_auth

bp = Blueprint('slots', __name__)

@bp.route('', methods=['GET'])
@require_auth
def get_all_slots(current_user):
    """Get all parking slots"""
    try:
        slots_collection = db.get_collection('parking_slots')
        
        if slots_collection is None:
            return jsonify({'message': 'Database not available'}), 503
        
        # Get query parameters
        slot_type = request.args.get('type')
        status = request.args.get('status')
        
        # Build query
        query = {}
        if slot_type:
            query['type'] = slot_type
        if status:
            query['status'] = status
        
        slots = list(slots_collection.find(query))
        
        # Convert ObjectId to string
        for slot in slots:
            slot['_id'] = str(slot['_id'])
        
        return jsonify(slots), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@bp.route('/<slot_id>', methods=['GET'])
@require_auth
def get_slot(current_user, slot_id):
    """Get specific slot"""
    try:
        slots_collection = db.get_collection('parking_slots')
        
        if slots_collection is None:
            return jsonify({'message': 'Database not available'}), 503
        
        slot = slots_collection.find_one({'_id': ObjectId(slot_id)})
        
        if not slot:
            return jsonify({'message': 'Slot not found'}), 404
        
        slot['_id'] = str(slot['_id'])
        
        return jsonify(slot), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@bp.route('/available', methods=['GET'])
@require_auth
def get_available_slots(current_user):
    """Get available slots"""
    try:
        slots_collection = db.get_collection('parking_slots')
        
        if slots_collection is None:
            return jsonify({'message': 'Database not available'}), 503
        
        slot_type = request.args.get('type')
        
        query = {'status': 'available'}
        if slot_type:
            query['type'] = slot_type
        
        slots = list(slots_collection.find(query))
        
        for slot in slots:
            slot['_id'] = str(slot['_id'])
        
        return jsonify(slots), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@bp.route('/<slot_id>/status', methods=['PUT'])
@require_auth
def update_slot_status(current_user, slot_id):
    """Update slot status (admin only)"""
    try:
        if current_user.get('role') != 'admin':
            return jsonify({'message': 'Unauthorized'}), 403
        
        data = request.json
        new_status = data.get('status')
        
        if new_status not in ['available', 'occupied', 'maintenance']:
            return jsonify({'message': 'Invalid status'}), 400
        
        slots_collection = db.get_collection('parking_slots')
        
        if slots_collection is None:
            return jsonify({'message': 'Database not available'}), 503
        
        result = slots_collection.update_one(
            {'_id': ObjectId(slot_id)},
            {'$set': {'status': new_status}}
        )
        
        if result.matched_count == 0:
            return jsonify({'message': 'Slot not found'}), 404
        
        return jsonify({'message': 'Status updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500
