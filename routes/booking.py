"""
Booking Routes
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.booking import Booking
from models.parking import ParkingSpace
from models.user import User
from models.review import Review
from models.wallet import Wallet
from models.database import db as database
from datetime import datetime

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/create', methods=['POST'])
@jwt_required()
def create_booking():
    """Create a new booking request (pending owner approval)"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['parking_id', 'start_time', 'end_time', 'vehicle_type', 'vehicle_number', 'user_name', 'user_phone']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate payment method
        payment_method = data.get('payment_method', 'cash')
        if payment_method not in ['cash', 'upi']:
            return jsonify({'error': 'Payment method must be cash or upi'}), 400
        
        # Get parking details to calculate platform fee
        parking = ParkingSpace.get_by_id(database, data['parking_id'])
        if not parking:
            return jsonify({'error': 'Parking space not found'}), 404
        
        # Calculate booking amount
        from datetime import datetime as dt
        start_time = dt.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        end_time = dt.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        
        # EXACT duration (not rounded)
        duration_hours = (end_time - start_time).total_seconds() / 3600
        
        # Calculate amounts and round to whole numbers
        booking_amount = round(duration_hours * parking['price_per_hour'])  # Rounded
        platform_fee = round(booking_amount * 0.01)  # 1% platform fee, rounded
        
        # Check wallet balance for platform fee
        wallet = Wallet.get_by_user_id(database, user_id)
        if not wallet:
            Wallet.create(database, user_id)
            wallet = Wallet.get_by_user_id(database, user_id)
        
        wallet_balance = wallet.get('balance', 0)
        if wallet_balance < platform_fee:
            return jsonify({
                'error': f'Insufficient wallet balance. Platform fee: ₹{platform_fee}. Your balance: ₹{wallet_balance}. Please add money to your wallet.'
            }), 400
        
        # Deduct platform fee from wallet
        new_balance = Wallet.deduct_balance(
            database,
            user_id,
            platform_fee,
            'platform_fee',
            f'Platform fee for booking (1% of ₹{booking_amount})'
        )
        
        # Add platform fee and booking amount to booking data
        data['platform_fee'] = platform_fee
        data['booking_amount'] = booking_amount
        
        # Create booking request (status: pending - waiting for owner approval)
        booking_id = Booking.create(
            database,
            user_id,
            data['parking_id'],
            data
        )
        
        # Get created booking
        booking = Booking.get_by_id(database, str(booking_id))
        
        return jsonify({
            'message': f'Booking request sent! Platform fee ₹{platform_fee} deducted from wallet. Parking fee ₹{booking_amount} will be paid to owner.',
            'booking': Booking.to_dict(booking),
            'platform_fee': platform_fee,
            'booking_amount': booking_amount,
            'new_wallet_balance': new_balance
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to create booking', 'details': str(e)}), 500

@booking_bp.route('/my-bookings', methods=['GET'])
@jwt_required()
def get_my_bookings():
    """Get user's bookings"""
    try:
        user_id = get_jwt_identity()
        status = request.args.get('status')
        
        bookings = Booking.get_by_user(database, user_id, status)
        
        # Get parking details for each booking
        bookings_with_details = []
        for booking in bookings:
            parking = ParkingSpace.get_by_id(database, str(booking['parking_id']))
            booking_dict = Booking.to_dict(booking)
            # Include UPI ID only for confirmed bookings (so user can pay)
            include_upi = booking['status'] == 'confirmed'
            booking_dict['parking'] = ParkingSpace.to_dict(parking, include_sensitive=include_upi)
            bookings_with_details.append(booking_dict)
        
        return jsonify({
            'count': len(bookings_with_details),
            'bookings': bookings_with_details
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get bookings', 'details': str(e)}), 500

@booking_bp.route('/received-bookings', methods=['GET'])
@jwt_required()
def get_received_bookings():
    """Get bookings for host's parking spaces"""
    try:
        user_id = get_jwt_identity()
        status = request.args.get('status')
        
        bookings = Booking.get_by_owner(database, user_id, status)
        
        # Get details for each booking
        bookings_with_details = []
        for booking in bookings:
            parking = ParkingSpace.get_by_id(database, str(booking['parking_id']))
            user = User.get_by_id(database, str(booking['user_id']))
            booking_dict = Booking.to_dict(booking)
            booking_dict['parking'] = ParkingSpace.to_dict(parking)
            booking_dict['user'] = {
                'id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'phone': user['phone']
            }
            bookings_with_details.append(booking_dict)
        
        return jsonify({
            'count': len(bookings_with_details),
            'bookings': bookings_with_details
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get bookings', 'details': str(e)}), 500

@booking_bp.route('/<booking_id>', methods=['GET'])
@jwt_required()
def get_booking_details(booking_id):
    """Get booking details"""
    try:
        user_id = get_jwt_identity()
        
        booking = Booking.get_by_id(database, booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Check if user has access to this booking
        if str(booking['user_id']) != user_id and str(booking['owner_id']) != user_id:
            return jsonify({'error': 'You do not have permission to view this booking'}), 403
        
        # Get parking and user details
        parking = ParkingSpace.get_by_id(database, str(booking['parking_id']))
        renter = User.get_by_id(database, str(booking['user_id']))
        owner = User.get_by_id(database, str(booking['owner_id']))
        
        booking_dict = Booking.to_dict(booking)
        booking_dict['parking'] = ParkingSpace.to_dict(parking)
        booking_dict['renter'] = User.to_dict(renter)
        booking_dict['owner'] = User.to_dict(owner)
        
        return jsonify({
            'booking': booking_dict
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get booking details', 'details': str(e)}), 500

@booking_bp.route('/<booking_id>/confirm', methods=['POST'])
@jwt_required()
def confirm_booking(booking_id):
    """Confirm/Accept booking request by owner"""
    try:
        user_id = get_jwt_identity()
        
        print(f"🔍 Confirming booking: {booking_id} by user: {user_id}")
        
        booking = Booking.get_by_id(database, booking_id)
        if not booking:
            print(f"❌ Booking not found: {booking_id}")
            return jsonify({'error': 'Booking not found'}), 404
        
        print(f"✅ Booking found: {booking['_id']}, Status: {booking['status']}, Owner: {booking.get('owner_id')}")
        
        # Check if user is the owner
        if str(booking['owner_id']) != user_id:
            print(f"❌ User {user_id} is not the owner {booking['owner_id']}")
            return jsonify({'error': 'Only the parking owner can confirm bookings'}), 403
        
        # Check if booking is pending
        if booking['status'] != 'pending':
            print(f"❌ Booking status is {booking['status']}, not pending")
            return jsonify({'error': 'Only pending bookings can be confirmed'}), 400
        
        # Confirm booking (owner accepts the request)
        print(f"📝 Accepting booking {booking_id}...")
        result = Booking.accept_by_owner(database, booking_id)
        
        if result:
            print(f"✅ Booking {booking_id} accepted successfully!")
            return jsonify({
                'message': 'Booking request accepted successfully! User can now park and pay.'
            }), 200
        else:
            print(f"❌ Failed to accept booking {booking_id}")
            return jsonify({'error': 'Failed to update booking'}), 500
        
    except ValueError as e:
        print(f"❌ ValueError: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to confirm booking', 'details': str(e)}), 500

@booking_bp.route('/<booking_id>/mark-paid', methods=['POST'])
@jwt_required()
def mark_paid(booking_id):
    """Mark booking as paid (by owner after receiving cash/UPI)"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        booking = Booking.get_by_id(database, booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Check if user is the owner
        if str(booking['owner_id']) != user_id:
            return jsonify({'error': 'Only the parking owner can mark payment as received'}), 403
        
        # Check if booking is confirmed
        if booking['status'] != 'confirmed':
            return jsonify({'error': 'Booking must be confirmed first'}), 400
        
        # Mark payment as completed
        payment_method = booking.get('payment_method', 'cash')
        payment_reference = data.get('payment_reference', f'{payment_method.upper()}-{datetime.now().strftime("%Y%m%d%H%M%S")}')
        
        Booking.mark_payment_completed(database, booking_id, payment_reference, payment_method)
        
        return jsonify({
            'message': f'Payment marked as received ({payment_method.upper()}). Booking is now active!'
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to mark payment', 'details': str(e)}), 500

@booking_bp.route('/<booking_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_booking(booking_id):
    """Cancel a booking"""
    try:
        user_id = get_jwt_identity()
        
        booking = Booking.get_by_id(database, booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Check if user has permission to cancel
        if str(booking['user_id']) != user_id and str(booking['owner_id']) != user_id:
            return jsonify({'error': 'You do not have permission to cancel this booking'}), 403
        
        # Determine who cancelled
        cancelled_by = 'owner' if str(booking['owner_id']) == user_id else 'user'
        
        # Cancel booking
        Booking.cancel(database, booking_id, cancelled_by)
        
        return jsonify({
            'message': 'Booking cancelled successfully. Refund will be processed to your wallet.'
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to cancel booking', 'details': str(e)}), 500

@booking_bp.route('/<booking_id>/review', methods=['POST'])
@jwt_required()
def add_review(booking_id):
    """Add review for completed booking"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if 'rating' not in data:
            return jsonify({'error': 'Rating is required'}), 400
        
        booking = Booking.get_by_id(database, booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Check if user made this booking
        if str(booking['user_id']) != user_id:
            return jsonify({'error': 'You can only review your own bookings'}), 403
        
        # Create review
        review_id = Review.create(
            database,
            user_id,
            str(booking['parking_id']),
            booking_id,
            data['rating'],
            data.get('comment', '')
        )
        
        # Get created review
        review = database.find_one('reviews', {'_id': review_id})
        
        return jsonify({
            'message': 'Review added successfully',
            'review': Review.to_dict(review)
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to add review', 'details': str(e)}), 500

@booking_bp.route('/update-statuses', methods=['POST'])
def update_booking_statuses():
    """Background job to update booking statuses"""
    try:
        Booking.check_active_bookings(database)
        return jsonify({
            'message': 'Booking statuses updated successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to update booking statuses', 'details': str(e)}), 500
