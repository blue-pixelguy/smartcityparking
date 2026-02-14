"""
User Routes
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.wallet import Wallet
from models.booking import Booking
from models.parking import ParkingSpace

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile/<user_id>', methods=['GET'])
def get_user_profile(user_id):
    """Get public user profile"""
    try:
        user = User.get_by_id(current_app.db, user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user stats
        if user['role'] == 'host':
            # Get host stats
            total_listings = current_app.db.count_documents(
                'parking_spaces',
                {'owner_id': user['_id']}
            )
            active_listings = current_app.db.count_documents(
                'parking_spaces',
                {'owner_id': user['_id'], 'status': 'approved'}
            )
            total_bookings = current_app.db.count_documents(
                'bookings',
                {'owner_id': user['_id'], 'status': 'completed'}
            )
            
            # Calculate average rating from parking spaces
            parking_spaces = ParkingSpace.get_by_owner(current_app.db, user_id)
            total_rating = sum(p.get('rating', 0) for p in parking_spaces)
            avg_rating = total_rating / len(parking_spaces) if parking_spaces else 0
            
            stats = {
                'total_listings': total_listings,
                'active_listings': active_listings,
                'total_bookings': total_bookings,
                'average_rating': round(avg_rating, 2)
            }
        else:
            # Get driver stats
            total_bookings = current_app.db.count_documents(
                'bookings',
                {'user_id': user['_id']}
            )
            completed_bookings = current_app.db.count_documents(
                'bookings',
                {'user_id': user['_id'], 'status': 'completed'}
            )
            
            stats = {
                'total_bookings': total_bookings,
                'completed_bookings': completed_bookings
            }
        
        profile = User.to_dict(user)
        profile['stats'] = stats
        
        return jsonify({
            'profile': profile
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get user profile', 'details': str(e)}), 500

@user_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_user_dashboard():
    """Get user dashboard data"""
    try:
        user_id = get_jwt_identity()
        user = User.get_by_id(current_app.db, user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get wallet balance
        wallet = Wallet.get_by_user_id(current_app.db, user_id)
        
        # Get recent bookings
        recent_bookings = Booking.get_by_user(current_app.db, user_id)[:5]
        bookings_with_details = []
        for booking in recent_bookings:
            parking = ParkingSpace.get_by_id(current_app.db, str(booking['parking_id']))
            booking_dict = Booking.to_dict(booking)
            booking_dict['parking'] = {
                'id': str(parking['_id']),
                'title': parking['title'],
                'address': parking['address'],
                'images': parking.get('images', [])
            }
            bookings_with_details.append(booking_dict)
        
        dashboard_data = {
            'user': User.to_dict(user),
            'wallet': Wallet.to_dict(wallet) if wallet else None,
            'recent_bookings': bookings_with_details
        }
        
        # If user is a host, add host-specific data
        if user['role'] in ['host', 'admin']:
            # Get host listings
            listings = ParkingSpace.get_by_owner(current_app.db, user_id)[:5]
            
            # Get received bookings
            received_bookings = Booking.get_by_owner(current_app.db, user_id)[:5]
            received_with_details = []
            for booking in received_bookings:
                parking = ParkingSpace.get_by_id(current_app.db, str(booking['parking_id']))
                renter = User.get_by_id(current_app.db, str(booking['user_id']))
                booking_dict = Booking.to_dict(booking)
                booking_dict['parking'] = {
                    'id': str(parking['_id']),
                    'title': parking['title']
                }
                booking_dict['renter'] = {
                    'id': str(renter['_id']),
                    'name': renter['name']
                }
                received_with_details.append(booking_dict)
            
            dashboard_data['my_listings'] = [ParkingSpace.to_dict(p) for p in listings]
            dashboard_data['received_bookings'] = received_with_details
        
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get dashboard data', 'details': str(e)}), 500

@user_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get user notifications"""
    try:
        user_id = get_jwt_identity()
        
        # In a real system, you would have a notifications collection
        # For now, return based on bookings and messages
        from models.message import Message
        
        unread_messages = Message.get_unread_count(current_app.db, user_id)
        
        # Get pending booking confirmations (for hosts)
        pending_confirmations = current_app.db.count_documents(
            'bookings',
            {
                'owner_id': current_app.db.find_one('users', {'_id': current_app.db.db['users'].find_one({'_id': user_id})})['_id'],
                'status': 'pending',
                'payment_status': 'completed',
                'is_confirmed_by_owner': False
            }
        )
        
        notifications = {
            'unread_messages': unread_messages,
            'pending_confirmations': pending_confirmations
        }
        
        return jsonify(notifications), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get notifications', 'details': str(e)}), 500

@user_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    """Get detailed user statistics"""
    try:
        user_id = get_jwt_identity()
        user = User.get_by_id(current_app.db, user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        stats = {}
        
        # Common stats
        wallet = Wallet.get_by_user_id(current_app.db, user_id)
        stats['wallet_balance'] = wallet['balance'] if wallet else 0
        
        # Booking stats
        total_bookings = current_app.db.count_documents(
            'bookings',
            {'user_id': user['_id']}
        )
        completed_bookings = current_app.db.count_documents(
            'bookings',
            {'user_id': user['_id'], 'status': 'completed'}
        )
        active_bookings = current_app.db.count_documents(
            'bookings',
            {'user_id': user['_id'], 'status': {'$in': ['confirmed', 'active']}}
        )
        
        stats['bookings'] = {
            'total': total_bookings,
            'completed': completed_bookings,
            'active': active_bookings
        }
        
        # Host-specific stats
        if user['role'] in ['host', 'admin']:
            total_listings = current_app.db.count_documents(
                'parking_spaces',
                {'owner_id': user['_id']}
            )
            active_listings = current_app.db.count_documents(
                'parking_spaces',
                {'owner_id': user['_id'], 'status': 'approved', 'is_available': True}
            )
            
            # Calculate total earnings
            earnings_pipeline = [
                {'$match': {'owner_id': user['_id'], 'status': 'completed'}},
                {'$group': {'_id': None, 'total': {'$sum': '$total_price'}}}
            ]
            earnings_result = current_app.db.aggregate('bookings', earnings_pipeline)
            total_earnings = earnings_result[0]['total'] if earnings_result else 0
            
            stats['hosting'] = {
                'total_listings': total_listings,
                'active_listings': active_listings,
                'total_earnings': total_earnings
            }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get user stats', 'details': str(e)}), 500
