from flask import Blueprint, request, jsonify
from database import db
from models import Booking
from auth import token_required
from bson import ObjectId
from datetime import datetime, timedelta
from utils import generate_confirmation_code, send_notification_to_user
from payments import WalletPayment

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/create', methods=['POST'])
@token_required
def create_booking():
    """Create a new booking"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['parking_id', 'start_time', 'hours', 'payment_method']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        parking_id = data['parking_id']
        hours = int(data['hours'])
        
        # Get parking space
        parking = db.db.parking_spaces.find_one({'_id': ObjectId(parking_id)})
        
        if not parking:
            return jsonify({'error': 'Parking space not found'}), 404
        
        if parking['status'] != 'approved':
            return jsonify({'error': 'Parking space not available'}), 400
        
        # Validate minimum hours
        if hours < parking['min_hours']:
            return jsonify({
                'error': f'Minimum booking is {parking["min_hours"]} hours'
            }), 400
        
        if hours > parking['total_hours']:
            return jsonify({
                'error': f'Maximum booking is {parking["total_hours"]} hours'
            }), 400
        
        # Calculate total amount
        total_amount = parking['price_per_hour'] * hours
        
        # Parse start time
        start_time = datetime.fromisoformat(data['start_time'])
        end_time = start_time + timedelta(hours=hours)
        
        # Check for overlapping bookings
        overlapping = db.db.bookings.find_one({
            'parking_id': ObjectId(parking_id),
            'status': {'$in': ['pending', 'confirmed']},
            '$or': [
                {
                    'start_time': {'$lte': start_time},
                    'end_time': {'$gt': start_time}
                },
                {
                    'start_time': {'$lt': end_time},
                    'end_time': {'$gte': end_time}
                },
                {
                    'start_time': {'$gte': start_time},
                    'end_time': {'$lte': end_time}
                }
            ]
        })
        
        if overlapping:
            return jsonify({'error': 'Parking space not available for selected time'}), 400
        
        # Create booking
        booking = Booking(
            driver_id=request.user_id,
            parking_id=parking_id,
            start_time=start_time,
            end_time=end_time,
            hours=hours,
            total_amount=total_amount
        )
        booking.payment_method = data['payment_method']
        
        # Process payment based on method
        if data['payment_method'] == 'wallet':
            payment_result = WalletPayment.process_payment(
                user_id=request.user_id,
                amount=total_amount,
                description=f"Parking booking - {parking['title']}"
            )
            
            if not payment_result['success']:
                return jsonify({'error': payment_result['error']}), 400
            
            booking.payment_status = 'paid'
            booking.status = 'pending'  # Pending host confirmation
        
        elif data['payment_method'] in ['razorpay', 'crypto']:
            # Payment will be processed on frontend, mark as pending
            booking.payment_status = 'pending'
            booking.status = 'pending'
        
        else:
            return jsonify({'error': 'Invalid payment method'}), 400
        
        result = db.db.bookings.insert_one(booking.to_dict())
        booking_id = str(result.inserted_id)
        
        # Update parking status
        db.db.parking_spaces.update_one(
            {'_id': ObjectId(parking_id)},
            {'$set': {'status': 'booked'}}
        )
        
        # Send notification to host
        owner_id = str(parking['owner_id'])
        send_notification_to_user(
            owner_id,
            'New Booking Request',
            f'You have a new booking request for {parking["title"]}',
            'booking'
        )
        
        return jsonify({
            'message': 'Booking created successfully',
            'booking_id': booking_id,
            'total_amount': total_amount,
            'payment_status': booking.payment_status
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@booking_bp.route('/confirm/<booking_id>', methods=['POST'])
@token_required
def confirm_booking(booking_id):
    """Host confirms booking after receiving payment"""
    try:
        booking = db.db.bookings.find_one({'_id': ObjectId(booking_id)})
        
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Get parking to verify ownership
        parking = db.db.parking_spaces.find_one({'_id': booking['parking_id']})
        
        if str(parking['owner_id']) != request.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if booking['payment_status'] != 'paid':
            return jsonify({'error': 'Payment not received'}), 400
        
        # Generate confirmation code
        confirmation_code = generate_confirmation_code()
        
        # Update booking
        db.db.bookings.update_one(
            {'_id': ObjectId(booking_id)},
            {
                '$set': {
                    'status': 'confirmed',
                    'confirmation_code': confirmation_code
                }
            }
        )
        
        # Update parking status to approved
        db.db.parking_spaces.update_one(
            {'_id': booking['parking_id']},
            {'$set': {'status': 'approved'}}
        )
        
        # Send notification to driver
        send_notification_to_user(
            str(booking['driver_id']),
            'Booking Confirmed',
            f'Your booking has been confirmed. Confirmation code: {confirmation_code}',
            'booking'
        )
        
        return jsonify({
            'message': 'Booking confirmed successfully',
            'confirmation_code': confirmation_code
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@booking_bp.route('/my-bookings', methods=['GET'])
@token_required
def get_my_bookings():
    """Get user's bookings"""
    try:
        status_filter = request.args.get('status')
        
        query = {'driver_id': ObjectId(request.user_id)}
        
        if status_filter:
            query['status'] = status_filter
        
        bookings = list(db.db.bookings.find(query).sort('created_at', -1))
        
        results = []
        for booking in bookings:
            parking = db.db.parking_spaces.find_one({'_id': booking['parking_id']})
            owner = db.db.users.find_one({'_id': parking['owner_id']})
            
            results.append({
                'id': str(booking['_id']),
                'parking': {
                    'id': str(parking['_id']),
                    'title': parking['title'],
                    'address': parking['address'],
                    'images': parking['images']
                },
                'owner': {
                    'name': owner['name'],
                    'phone': owner['phone']
                },
                'start_time': booking['start_time'].isoformat(),
                'end_time': booking['end_time'].isoformat(),
                'hours': booking['hours'],
                'total_amount': booking['total_amount'],
                'status': booking['status'],
                'payment_status': booking['payment_status'],
                'confirmation_code': booking.get('confirmation_code'),
                'created_at': booking['created_at'].isoformat()
            })
        
        return jsonify({
            'bookings': results,
            'total': len(results)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@booking_bp.route('/host/bookings', methods=['GET'])
@token_required
def get_host_bookings():
    """Get bookings for host's parking spaces"""
    try:
        # Get all parking spaces owned by host
        parking_spaces = list(db.db.parking_spaces.find({'owner_id': ObjectId(request.user_id)}))
        parking_ids = [space['_id'] for space in parking_spaces]
        
        # Get bookings for these parking spaces
        bookings = list(db.db.bookings.find({
            'parking_id': {'$in': parking_ids}
        }).sort('created_at', -1))
        
        results = []
        for booking in bookings:
            parking = db.db.parking_spaces.find_one({'_id': booking['parking_id']})
            driver = db.db.users.find_one({'_id': booking['driver_id']})
            
            results.append({
                'id': str(booking['_id']),
                'parking': {
                    'id': str(parking['_id']),
                    'title': parking['title'],
                    'address': parking['address']
                },
                'driver': {
                    'name': driver['name'],
                    'phone': driver['phone'],
                    'email': driver['email']
                },
                'start_time': booking['start_time'].isoformat(),
                'end_time': booking['end_time'].isoformat(),
                'hours': booking['hours'],
                'total_amount': booking['total_amount'],
                'status': booking['status'],
                'payment_status': booking['payment_status'],
                'payment_method': booking.get('payment_method'),
                'created_at': booking['created_at'].isoformat()
            })
        
        return jsonify({
            'bookings': results,
            'total': len(results)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@booking_bp.route('/<booking_id>', methods=['GET'])
@token_required
def get_booking_details(booking_id):
    """Get booking details"""
    try:
        booking = db.db.bookings.find_one({'_id': ObjectId(booking_id)})
        
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Verify user has access to this booking
        parking = db.db.parking_spaces.find_one({'_id': booking['parking_id']})
        
        if (str(booking['driver_id']) != request.user_id and 
            str(parking['owner_id']) != request.user_id and 
            request.user_role != 'admin'):
            return jsonify({'error': 'Unauthorized'}), 403
        
        driver = db.db.users.find_one({'_id': booking['driver_id']})
        owner = db.db.users.find_one({'_id': parking['owner_id']})
        
        return jsonify({
            'id': str(booking['_id']),
            'parking': {
                'id': str(parking['_id']),
                'title': parking['title'],
                'description': parking['description'],
                'address': parking['address'],
                'images': parking['images'],
                'price_per_hour': parking['price_per_hour']
            },
            'driver': {
                'id': str(driver['_id']),
                'name': driver['name'],
                'phone': driver['phone'],
                'email': driver['email']
            },
            'owner': {
                'id': str(owner['_id']),
                'name': owner['name'],
                'phone': owner['phone'],
                'email': owner['email']
            },
            'start_time': booking['start_time'].isoformat(),
            'end_time': booking['end_time'].isoformat(),
            'hours': booking['hours'],
            'total_amount': booking['total_amount'],
            'status': booking['status'],
            'payment_status': booking['payment_status'],
            'payment_method': booking.get('payment_method'),
            'confirmation_code': booking.get('confirmation_code'),
            'created_at': booking['created_at'].isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@booking_bp.route('/<booking_id>/cancel', methods=['POST'])
@token_required
def cancel_booking(booking_id):
    """Cancel booking"""
    try:
        booking = db.db.bookings.find_one({'_id': ObjectId(booking_id)})
        
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        if str(booking['driver_id']) != request.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if booking['status'] == 'completed':
            return jsonify({'error': 'Cannot cancel completed booking'}), 400
        
        # Refund if payment was made
        if booking['payment_status'] == 'paid':
            # Add funds back to wallet
            from payments import WalletPayment
            WalletPayment.add_funds(
                user_id=request.user_id,
                amount=booking['total_amount'],
                payment_method='refund',
                payment_id=f"refund_{booking_id}"
            )
        
        # Update booking status
        db.db.bookings.update_one(
            {'_id': ObjectId(booking_id)},
            {
                '$set': {
                    'status': 'cancelled',
                    'payment_status': 'refunded'
                }
            }
        )
        
        # Update parking status
        db.db.parking_spaces.update_one(
            {'_id': booking['parking_id']},
            {'$set': {'status': 'approved'}}
        )
        
        # Notify host
        parking = db.db.parking_spaces.find_one({'_id': booking['parking_id']})
        send_notification_to_user(
            str(parking['owner_id']),
            'Booking Cancelled',
            f'A booking for {parking["title"]} has been cancelled',
            'booking'
        )
        
        return jsonify({'message': 'Booking cancelled successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@booking_bp.route('/<booking_id>/complete', methods=['POST'])
@token_required
def complete_booking(booking_id):
    """Mark booking as completed"""
    try:
        booking = db.db.bookings.find_one({'_id': ObjectId(booking_id)})
        
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        parking = db.db.parking_spaces.find_one({'_id': booking['parking_id']})
        
        # Only host can mark as completed
        if str(parking['owner_id']) != request.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if booking['status'] != 'confirmed':
            return jsonify({'error': 'Only confirmed bookings can be completed'}), 400
        
        # Update booking
        db.db.bookings.update_one(
            {'_id': ObjectId(booking_id)},
            {'$set': {'status': 'completed'}}
        )
        
        # Update parking status back to available
        db.db.parking_spaces.update_one(
            {'_id': booking['parking_id']},
            {'$set': {'status': 'approved'}}
        )
        
        # Notify driver
        send_notification_to_user(
            str(booking['driver_id']),
            'Booking Completed',
            f'Your booking for {parking["title"]} has been completed',
            'booking'
        )
        
        return jsonify({'message': 'Booking completed successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
