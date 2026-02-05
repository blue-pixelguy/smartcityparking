from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime, timedelta
from config.database import db
from routes.middleware import require_auth

bp = Blueprint('bookings', __name__)

@bp.route('', methods=['POST'])
@require_auth
def create_booking(current_user):
    """Create new booking"""
    try:
        data = request.json
        
        # Validate required fields
        if 'slot_id' not in data or 'duration_hours' not in data:
            return jsonify({'message': 'slot_id and duration_hours are required'}), 400
        
        slot_id = data['slot_id']
        duration_hours = int(data['duration_hours'])
        
        if duration_hours < 1 or duration_hours > 24:
            return jsonify({'message': 'Duration must be between 1 and 24 hours'}), 400
        
        slots_collection = db.get_collection('parking_slots')
        bookings_collection = db.get_collection('bookings')
        
        if slots_collection is None or bookings_collection is None:
            return jsonify({'message': 'Database not available'}), 503
        
        # Check if slot is available
        slot = slots_collection.find_one({'_id': ObjectId(slot_id)})
        
        if not slot:
            return jsonify({'message': 'Slot not found'}), 404
        
        if slot['status'] != 'available':
            return jsonify({'message': 'Slot is not available'}), 400
        
        # Calculate total amount
        total_amount = slot['hourly_rate'] * duration_hours
        
        # Create booking
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=duration_hours)
        
        booking = {
            'user_id': ObjectId(current_user['id']),
            'slot_id': ObjectId(slot_id),
            'slot_number': slot['slot_number'],
            'start_time': start_time,
            'end_time': end_time,
            'duration_hours': duration_hours,
            'hourly_rate': slot['hourly_rate'],
            'total_amount': total_amount,
            'status': 'active',
            'created_at': datetime.utcnow()
        }
        
        result = bookings_collection.insert_one(booking)
        
        # Update slot status
        slots_collection.update_one(
            {'_id': ObjectId(slot_id)},
            {'$set': {'status': 'occupied'}}
        )
        
        return jsonify({
            'message': 'Booking created successfully',
            'booking_id': str(result.inserted_id),
            'total_amount': total_amount
        }), 201
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@bp.route('/my', methods=['GET'])
@require_auth
def get_my_bookings(current_user):
    """Get current user's bookings"""
    try:
        bookings_collection = db.get_collection('bookings')
        
        if bookings_collection is None:
            return jsonify({'message': 'Database not available'}), 503
        
        bookings = list(bookings_collection.find(
            {'user_id': ObjectId(current_user['id'])}
        ).sort('created_at', -1))
        
        for booking in bookings:
            booking['_id'] = str(booking['_id'])
            booking['user_id'] = str(booking['user_id'])
            booking['slot_id'] = str(booking['slot_id'])
            booking['start_time'] = booking['start_time'].isoformat()
            if booking.get('end_time'):
                booking['end_time'] = booking['end_time'].isoformat()
            if booking.get('created_at'):
                booking['created_at'] = booking['created_at'].isoformat()
        
        return jsonify(bookings), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@bp.route('/<booking_id>', methods=['GET'])
@require_auth
def get_booking(current_user, booking_id):
    """Get specific booking"""
    try:
        bookings_collection = db.get_collection('bookings')
        
        if bookings_collection is None:
            return jsonify({'message': 'Database not available'}), 503
        
        booking = bookings_collection.find_one({'_id': ObjectId(booking_id)})
        
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404
        
        # Check if user owns this booking or is admin
        if str(booking['user_id']) != current_user['id'] and current_user.get('role') != 'admin':
            return jsonify({'message': 'Unauthorized'}), 403
        
        booking['_id'] = str(booking['_id'])
        booking['user_id'] = str(booking['user_id'])
        booking['slot_id'] = str(booking['slot_id'])
        booking['start_time'] = booking['start_time'].isoformat()
        if booking.get('end_time'):
            booking['end_time'] = booking['end_time'].isoformat()
        
        return jsonify(booking), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@bp.route('/<booking_id>/cancel', methods=['PUT'])
@require_auth
def cancel_booking(current_user, booking_id):
    """Cancel booking"""
    try:
        bookings_collection = db.get_collection('bookings')
        slots_collection = db.get_collection('parking_slots')
        
        if bookings_collection is None or slots_collection is None:
            return jsonify({'message': 'Database not available'}), 503
        
        booking = bookings_collection.find_one({'_id': ObjectId(booking_id)})
        
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404
        
        # Check if user owns this booking
        if str(booking['user_id']) != current_user['id']:
            return jsonify({'message': 'Unauthorized'}), 403
        
        if booking['status'] != 'active':
            return jsonify({'message': 'Booking cannot be cancelled'}), 400
        
        # Update booking status
        bookings_collection.update_one(
            {'_id': ObjectId(booking_id)},
            {'$set': {'status': 'cancelled'}}
        )
        
        # Free up the slot
        slots_collection.update_one(
            {'_id': booking['slot_id']},
            {'$set': {'status': 'available'}}
        )
        
        return jsonify({'message': 'Booking cancelled successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@bp.route('', methods=['GET'])
@require_auth
def get_all_bookings(current_user):
    """Get all bookings (admin only)"""
    try:
        if current_user.get('role') != 'admin':
            return jsonify({'message': 'Unauthorized'}), 403
        
        bookings_collection = db.get_collection('bookings')
        
        if bookings_collection is None:
            return jsonify({'message': 'Database not available'}), 503
        
        bookings = list(bookings_collection.find().sort('created_at', -1))
        
        for booking in bookings:
            booking['_id'] = str(booking['_id'])
            booking['user_id'] = str(booking['user_id'])
            booking['slot_id'] = str(booking['slot_id'])
            booking['start_time'] = booking['start_time'].isoformat()
            if booking.get('end_time'):
                booking['end_time'] = booking['end_time'].isoformat()
        
        return jsonify(bookings), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500
