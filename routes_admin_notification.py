from flask import Blueprint, request, jsonify
from database import db
from auth import token_required, admin_required
from bson import ObjectId
from datetime import datetime, timedelta
from utils import send_notification_to_user

admin_bp = Blueprint('admin', __name__)
notification_bp = Blueprint('notification', __name__)

# ========== ADMIN ROUTES ==========

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard_stats():
    """Get admin dashboard statistics"""
    try:
        total_users = db.db.users.count_documents({})
        total_drivers = db.db.users.count_documents({'role': 'driver'})
        total_hosts = db.db.users.count_documents({'role': 'host'})
        
        total_parking = db.db.parking_spaces.count_documents({})
        pending_parking = db.db.parking_spaces.count_documents({'status': 'pending'})
        approved_parking = db.db.parking_spaces.count_documents({'status': 'approved'})
        
        total_bookings = db.db.bookings.count_documents({})
        completed_bookings = db.db.bookings.count_documents({'status': 'completed'})
        active_bookings = db.db.bookings.count_documents({
            'status': {'$in': ['pending', 'confirmed']}
        })
        
        # Calculate revenue (total booking amounts)
        pipeline = [
            {'$match': {'payment_status': 'paid'}},
            {'$group': {'_id': None, 'total': {'$sum': '$total_amount'}}}
        ]
        revenue_result = list(db.db.bookings.aggregate(pipeline))
        total_revenue = revenue_result[0]['total'] if revenue_result else 0
        
        # Recent activity
        recent_bookings = list(db.db.bookings.find().sort('created_at', -1).limit(5))
        recent_parking = list(db.db.parking_spaces.find({'status': 'pending'}).sort('created_at', -1).limit(5))
        
        return jsonify({
            'users': {
                'total': total_users,
                'drivers': total_drivers,
                'hosts': total_hosts
            },
            'parking_spaces': {
                'total': total_parking,
                'pending': pending_parking,
                'approved': approved_parking
            },
            'bookings': {
                'total': total_bookings,
                'completed': completed_bookings,
                'active': active_bookings
            },
            'revenue': {
                'total': total_revenue
            },
            'recent_activity': {
                'bookings': len(recent_bookings),
                'pending_approvals': len(recent_parking)
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    """Get all users"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        skip = (page - 1) * per_page
        
        role_filter = request.args.get('role')
        query = {}
        if role_filter:
            query['role'] = role_filter
        
        users = list(db.db.users.find(query).skip(skip).limit(per_page))
        total = db.db.users.count_documents(query)
        
        results = []
        for user in users:
            wallet = db.db.wallets.find_one({'user_id': user['_id']})
            
            results.append({
                'id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'phone': user['phone'],
                'role': user['role'],
                'is_verified': user.get('is_verified', False),
                'wallet_balance': wallet['balance'] if wallet else 0.0,
                'created_at': user['created_at'].isoformat()
            })
        
        return jsonify({
            'users': results,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/parking/pending', methods=['GET'])
@admin_required
def get_pending_parking():
    """Get pending parking spaces for approval"""
    try:
        parking_spaces = list(db.db.parking_spaces.find({'status': 'pending'}).sort('created_at', -1))
        
        results = []
        for space in parking_spaces:
            owner = db.db.users.find_one({'_id': space['owner_id']})
            
            results.append({
                'id': str(space['_id']),
                'title': space['title'],
                'description': space['description'],
                'address': space['address'],
                'location': {
                    'latitude': space['location']['coordinates'][1],
                    'longitude': space['location']['coordinates'][0]
                },
                'vehicle_type': space['vehicle_type'],
                'price_per_hour': space['price_per_hour'],
                'total_hours': space['total_hours'],
                'images': space['images'],
                'owner': {
                    'id': str(owner['_id']),
                    'name': owner['name'],
                    'email': owner['email'],
                    'phone': owner['phone']
                },
                'created_at': space['created_at'].isoformat()
            })
        
        return jsonify({
            'parking_spaces': results,
            'total': len(results)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/parking/<parking_id>/approve', methods=['POST'])
@admin_required
def approve_parking(parking_id):
    """Approve parking space"""
    try:
        parking = db.db.parking_spaces.find_one({'_id': ObjectId(parking_id)})
        
        if not parking:
            return jsonify({'error': 'Parking space not found'}), 404
        
        db.db.parking_spaces.update_one(
            {'_id': ObjectId(parking_id)},
            {'$set': {'status': 'approved'}}
        )
        
        # Notify owner
        send_notification_to_user(
            str(parking['owner_id']),
            'Parking Space Approved',
            f'Your parking space "{parking["title"]}" has been approved',
            'booking'
        )
        
        return jsonify({'message': 'Parking space approved successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/parking/<parking_id>/reject', methods=['POST'])
@admin_required
def reject_parking(parking_id):
    """Reject parking space"""
    try:
        data = request.get_json()
        reason = data.get('reason', 'Does not meet requirements')
        
        parking = db.db.parking_spaces.find_one({'_id': ObjectId(parking_id)})
        
        if not parking:
            return jsonify({'error': 'Parking space not found'}), 404
        
        db.db.parking_spaces.update_one(
            {'_id': ObjectId(parking_id)},
            {'$set': {'status': 'rejected'}}
        )
        
        # Notify owner
        send_notification_to_user(
            str(parking['owner_id']),
            'Parking Space Rejected',
            f'Your parking space "{parking["title"]}" was rejected. Reason: {reason}',
            'booking'
        )
        
        return jsonify({'message': 'Parking space rejected'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/bookings', methods=['GET'])
@admin_required
def get_all_bookings():
    """Get all bookings"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        skip = (page - 1) * per_page
        
        status_filter = request.args.get('status')
        query = {}
        if status_filter:
            query['status'] = status_filter
        
        bookings = list(db.db.bookings.find(query).sort('created_at', -1).skip(skip).limit(per_page))
        total = db.db.bookings.count_documents(query)
        
        results = []
        for booking in bookings:
            parking = db.db.parking_spaces.find_one({'_id': booking['parking_id']})
            driver = db.db.users.find_one({'_id': booking['driver_id']})
            owner = db.db.users.find_one({'_id': parking['owner_id']})
            
            results.append({
                'id': str(booking['_id']),
                'parking_title': parking['title'],
                'driver_name': driver['name'],
                'owner_name': owner['name'],
                'hours': booking['hours'],
                'total_amount': booking['total_amount'],
                'status': booking['status'],
                'payment_status': booking['payment_status'],
                'created_at': booking['created_at'].isoformat()
            })
        
        return jsonify({
            'bookings': results,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/user/<user_id>/verify', methods=['POST'])
@admin_required
def verify_user(user_id):
    """Verify a user"""
    try:
        user = db.db.users.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        db.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'is_verified': True}}
        )
        
        send_notification_to_user(
            user_id,
            'Account Verified',
            'Your account has been verified',
            'booking'
        )
        
        return jsonify({'message': 'User verified successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========== NOTIFICATION ROUTES ==========

@notification_bp.route('/', methods=['GET'])
@token_required
def get_notifications():
    """Get user's notifications"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        skip = (page - 1) * per_page
        
        notifications = list(db.db.notifications.find({
            'user_id': ObjectId(request.user_id)
        }).sort('created_at', -1).skip(skip).limit(per_page))
        
        total = db.db.notifications.count_documents({'user_id': ObjectId(request.user_id)})
        unread = db.db.notifications.count_documents({
            'user_id': ObjectId(request.user_id),
            'is_read': False
        })
        
        results = []
        for notif in notifications:
            results.append({
                'id': str(notif['_id']),
                'title': notif['title'],
                'message': notif['message'],
                'notification_type': notif['notification_type'],
                'is_read': notif['is_read'],
                'created_at': notif['created_at'].isoformat()
            })
        
        return jsonify({
            'notifications': results,
            'total': total,
            'unread': unread,
            'page': page,
            'per_page': per_page
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/<notification_id>/read', methods=['POST'])
@token_required
def mark_as_read(notification_id):
    """Mark notification as read"""
    try:
        notification = db.db.notifications.find_one({'_id': ObjectId(notification_id)})
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        if str(notification['user_id']) != request.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        db.db.notifications.update_one(
            {'_id': ObjectId(notification_id)},
            {'$set': {'is_read': True}}
        )
        
        return jsonify({'message': 'Notification marked as read'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/mark-all-read', methods=['POST'])
@token_required
def mark_all_read():
    """Mark all notifications as read"""
    try:
        db.db.notifications.update_many(
            {'user_id': ObjectId(request.user_id), 'is_read': False},
            {'$set': {'is_read': True}}
        )
        
        return jsonify({'message': 'All notifications marked as read'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/unread-count', methods=['GET'])
@token_required
def get_unread_count():
    """Get unread notification count"""
    try:
        count = db.db.notifications.count_documents({
            'user_id': ObjectId(request.user_id),
            'is_read': False
        })
        
        return jsonify({'unread_count': count}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
