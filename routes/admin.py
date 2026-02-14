"""
Admin Routes
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.parking import ParkingSpace
from models.booking import Booking
from models.database import db as database
from bson.objectid import ObjectId
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def admin_required(fn):
    """Decorator to check if user is admin"""
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.get_by_id(database, user_id)
        
        if not user or user['role'] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return fn(*args, **kwargs)
    
    wrapper.__name__ = fn.__name__
    return wrapper

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard_stats():
    """Get admin dashboard statistics"""
    try:
        # Count users
        total_users = database.count_documents('users', {})
        
        # Count parking spaces by status
        total_parking = database.count_documents('parking_spaces', {})
        pending_parking = database.count_documents('parking_spaces', {'status': 'pending'})
        approved_parking = database.count_documents('parking_spaces', {'status': 'approved'})
        rejected_parking = database.count_documents('parking_spaces', {'status': 'rejected'})
        
        # Count bookings by status
        total_bookings = database.count_documents('bookings', {})
        pending_bookings = database.count_documents('bookings', {'status': 'pending'})
        confirmed_bookings = database.count_documents('bookings', {'status': 'confirmed'})
        completed_bookings = database.count_documents('bookings', {'status': 'completed'})
        cancelled_bookings = database.count_documents('bookings', {'status': 'cancelled'})
        
        # Calculate total revenue from completed bookings
        revenue_pipeline = [
            {'$match': {'status': 'completed'}},
            {'$group': {'_id': None, 'total': {'$sum': '$total_price'}}}
        ]
        revenue_result = database.aggregate('bookings', revenue_pipeline)
        total_revenue = revenue_result[0]['total'] if revenue_result else 0
        
        return jsonify({
            'users': {
                'total': total_users
            },
            'parking_spaces': {
                'total': total_parking,
                'pending': pending_parking,
                'approved': approved_parking,
                'rejected': rejected_parking
            },
            'bookings': {
                'total': total_bookings,
                'pending': pending_bookings,
                'confirmed': confirmed_bookings,
                'completed': completed_bookings,
                'cancelled': cancelled_bookings
            },
            'revenue': {
                'total': float(total_revenue)
            }
        }), 200
        
    except Exception as e:
        print(f"Dashboard stats error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get dashboard stats', 'details': str(e)}), 500

@admin_bp.route('/parking/pending', methods=['GET'])
@admin_required
def get_pending_parking():
    """Get all pending parking spaces"""
    try:
        parking_spaces = ParkingSpace.get_all_pending(database)
        
        # Get owner details for each parking space
        parking_with_owners = []
        for parking in parking_spaces:
            owner = User.get_by_id(database, str(parking['owner_id']))
            parking_dict = ParkingSpace.to_dict(parking)
            parking_dict['owner'] = {
                'id': str(owner['_id']),
                'name': owner['name'],
                'email': owner['email'],
                'phone': owner.get('phone')
            }
            parking_with_owners.append(parking_dict)
        
        return jsonify({
            'count': len(parking_with_owners),
            'parking_spaces': parking_with_owners
        }), 200
        
    except Exception as e:
        print(f"Get pending parking error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get pending parking', 'details': str(e)}), 500

@admin_bp.route('/parking/<parking_id>/approve', methods=['POST'])
@admin_required
def approve_parking(parking_id):
    """Approve a parking space"""
    try:
        parking = ParkingSpace.get_by_id(database, parking_id)
        if not parking:
            return jsonify({'error': 'Parking space not found'}), 404
        
        ParkingSpace.update_status(database, parking_id, 'approved')
        
        return jsonify({
            'message': 'Parking space approved successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to approve parking space', 'details': str(e)}), 500

@admin_bp.route('/parking/<parking_id>/reject', methods=['POST'])
@admin_required
def reject_parking(parking_id):
    """Reject a parking space"""
    try:
        data = request.get_json() or {}
        
        parking = ParkingSpace.get_by_id(database, parking_id)
        if not parking:
            return jsonify({'error': 'Parking space not found'}), 404
        
        ParkingSpace.update_status(database, parking_id, 'rejected')
        
        # Add rejection reason if provided
        if 'reason' in data:
            database.update_one(
                'parking_spaces',
                {'_id': ObjectId(parking_id)},
                {'$set': {'rejection_reason': data['reason'], 'rejected_at': datetime.utcnow()}}
            )
        
        return jsonify({
            'message': 'Parking space rejected'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to reject parking space', 'details': str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    """Get all users"""
    try:
        role = request.args.get('role')
        skip = int(request.args.get('skip', 0))
        limit = int(request.args.get('limit', 50))
        
        users = User.get_all_users(database, role, skip, limit)
        
        return jsonify({
            'count': len(users),
            'users': [User.to_dict(u) for u in users]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get users', 'details': str(e)}), 500

@admin_bp.route('/users/<user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """Activate or deactivate a user"""
    try:
        user = User.get_by_id(database, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        new_status = not user.get('is_active', True)
        
        User.update(database, user_id, {'is_active': new_status})
        
        return jsonify({
            'message': f'User {"activated" if new_status else "deactivated"} successfully',
            'is_active': new_status
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to toggle user status', 'details': str(e)}), 500

@admin_bp.route('/bookings', methods=['GET'])
@admin_required
def get_all_bookings():
    """Get all bookings"""
    try:
        status = request.args.get('status')
        skip = int(request.args.get('skip', 0))
        limit = int(request.args.get('limit', 50))
        
        query = {}
        if status:
            query['status'] = status
        
        bookings = database.find_many(
            'bookings',
            query,
            sort=[('created_at', -1)],
            limit=limit
        )
        
        # Get details for each booking
        bookings_with_details = []
        for booking in bookings:
            try:
                parking = ParkingSpace.get_by_id(database, str(booking['parking_id']))
                user = User.get_by_id(database, str(booking['user_id']))
                owner = User.get_by_id(database, str(booking['owner_id']))
                
                if not parking or not user or not owner:
                    continue
                
                booking_dict = Booking.to_dict(booking)
                booking_dict['parking'] = {
                    'id': str(parking['_id']),
                    'title': parking['title'],
                    'address': parking['address']
                }
                booking_dict['user'] = {
                    'id': str(user['_id']),
                    'name': user['name'],
                    'email': user['email']
                }
                booking_dict['owner'] = {
                    'id': str(owner['_id']),
                    'name': owner['name'],
                    'email': owner['email']
                }
                bookings_with_details.append(booking_dict)
            except Exception as e:
                print(f"Error processing booking: {e}")
                continue
        
        return jsonify({
            'count': len(bookings_with_details),
            'bookings': bookings_with_details
        }), 200
        
    except Exception as e:
        print(f"Get bookings error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get bookings', 'details': str(e)}), 500

@admin_bp.route('/resolve-issue', methods=['POST'])
@admin_required
def resolve_issue():
    """Resolve disputes or issues"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['booking_id', 'resolution', 'action']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        booking = Booking.get_by_id(database, data['booking_id'])
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Perform action based on resolution
        if data['action'] == 'refund':
            # Process refund
            from models.wallet import Wallet
            Wallet.add_balance(
                database,
                str(booking['user_id']),
                booking['total_price'],
                'refund',
                f"Admin refund: {data['resolution']}"
            )
        elif data['action'] == 'cancel':
            # Cancel booking
            Booking.cancel(database, data['booking_id'], 'admin')
        
        # Log the resolution
        resolution_data = {
            'booking_id': ObjectId(data['booking_id']),
            'resolution': data['resolution'],
            'action': data['action'],
            'resolved_by': get_jwt_identity(),
            'resolved_at': datetime.utcnow()
        }
        database.insert_one('issue_resolutions', resolution_data)
        
        return jsonify({
            'message': 'Issue resolved successfully'
        }), 200
        
    except Exception as e:
        print(f"Resolve issue error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to resolve issue', 'details': str(e)}), 500
