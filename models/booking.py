"""
Booking Model
"""

from datetime import datetime, timedelta
from bson.objectid import ObjectId

class Booking:
    """Booking model for parking reservations"""
    
    STATUSES = ['pending', 'confirmed', 'active', 'completed', 'cancelled']
    
    @staticmethod
    def create(db, user_id, parking_id, data):
        """Create a new booking"""
        parking = db.find_one('parking_spaces', {'_id': ObjectId(parking_id)})
        if not parking:
            raise ValueError("Parking space not found")
        
        if parking['status'] != 'approved' or not parking['is_available']:
            raise ValueError("Parking space is not available")
        
        # Parse datetime strings - handle both local and ISO formats
        def parse_datetime(dt_string):
            """Parse datetime from various formats"""
            if not dt_string:
                raise ValueError("DateTime string is required")
            
            # Remove 'Z' if present and replace with +00:00
            dt_string = dt_string.replace('Z', '+00:00')
            
            # If no timezone info, treat as local datetime
            if '+' not in dt_string and '-' not in dt_string[-6:]:
                return datetime.fromisoformat(dt_string)
            else:
                return datetime.fromisoformat(dt_string)
        
        start_time = parse_datetime(data['start_time'])
        end_time = parse_datetime(data['end_time'])
        
        # Calculate duration in hours
        duration = (end_time - start_time).total_seconds() / 3600
        
        # Get number of spots (default to 1)
        number_of_spots = int(data.get('number_of_spots', 1))
        
        # Check if enough spots are available
        if number_of_spots > parking['available_spaces']:
            raise ValueError(f"Only {parking['available_spaces']} spot(s) available")
        
        # NO MINIMUM BOOKING DURATION - Users can book any duration they want
        
        # Check if parking is available for the requested time
        # Start time must be in the future (from NOW)
        current_time = datetime.utcnow()
        if start_time < current_time:
            raise ValueError("Booking start time cannot be in the past")
        
        # End time must be before parking expires
        if end_time > parking['available_to']:
            raise ValueError(f"Booking end time exceeds parking availability. Parking expires at {parking['available_to'].strftime('%Y-%m-%d %H:%M')}")
        
        # Calculate total price (per spot × number of spots)
        total_price = parking['price_per_hour'] * duration * number_of_spots
        
        booking_data = {
            'user_id': ObjectId(user_id),
            'parking_id': ObjectId(parking_id),
            'owner_id': parking['owner_id'],
            'start_time': start_time,
            'end_time': end_time,
            'duration_hours': duration,
            'price_per_hour': parking['price_per_hour'],
            'number_of_spots': number_of_spots,
            'total_price': total_price,
            'vehicle_number': data.get('vehicle_number', ''),
            'vehicle_type': data.get('vehicle_type', parking['vehicle_type']),
            'user_name': data.get('user_name', ''),
            'user_phone': data.get('user_phone', ''),
            'payment_method': data.get('payment_method', 'cash'),  # 'cash' or 'upi'
            'status': 'pending',
            'payment_status': 'pending',
            'payment_id': None,
            'is_confirmed_by_owner': False,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        booking_id = db.insert_one('bookings', booking_data)
        
        # Update parking availability - deduct number of spots booked
        from models.parking import ParkingSpace
        ParkingSpace.update_availability(db, parking_id, -number_of_spots)
        
        return booking_id
    
    @staticmethod
    def get_by_id(db, booking_id):
        """Get booking by ID"""
        try:
            return db.find_one('bookings', {'_id': ObjectId(booking_id)})
        except:
            return None
    
    @staticmethod
    def get_by_user(db, user_id, status=None):
        """Get all bookings for a user"""
        query = {'user_id': ObjectId(user_id)}
        if status:
            query['status'] = status
        
        return db.find_many('bookings', query, sort=[('created_at', -1)])
    
    @staticmethod
    def get_by_owner(db, owner_id, status=None):
        """Get all bookings for parking spaces owned by a user"""
        from datetime import datetime
        import pytz
        
        query = {'owner_id': ObjectId(owner_id)}
        
        # Filter by status if provided
        if status:
            query['status'] = status
        
        # For pending bookings, exclude expired ones (end_time in past)
        if status == 'pending':
            # Use IST timezone
            ist = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(ist)
            # Make naive for MongoDB comparison
            current_time_naive = current_time.replace(tzinfo=None)
            query['end_time'] = {'$gte': current_time_naive}
        
        return db.find_many('bookings', query, sort=[('created_at', -1)])
    
    @staticmethod
    def get_by_parking(db, parking_id, status=None):
        """Get all bookings for a specific parking space"""
        query = {'parking_id': ObjectId(parking_id)}
        if status:
            query['status'] = status
        
        return db.find_many('bookings', query, sort=[('start_time', -1)])
    
    @staticmethod
    def update_status(db, booking_id, status):
        """Update booking status"""
        if status not in Booking.STATUSES:
            raise ValueError(f"Invalid status. Must be one of {Booking.STATUSES}")
        
        return db.update_one(
            'bookings',
            {'_id': ObjectId(booking_id)},
            {'$set': {
                'status': status,
                'updated_at': datetime.utcnow()
            }}
        )
    
    @staticmethod
    def accept_by_owner(db, booking_id):
        """Accept booking request by owner (before payment)"""
        from bson.objectid import ObjectId
        from datetime import datetime
        
        print(f"🔍 accept_by_owner called with booking_id: {booking_id}")
        
        try:
            booking = Booking.get_by_id(db, booking_id)
            if not booking:
                print(f"❌ Booking not found: {booking_id}")
                raise ValueError("Booking not found")
            
            print(f"✅ Booking found: {booking.get('_id')}")
            print(f"   Status: {booking.get('status')}")
            print(f"   Owner ID: {booking.get('owner_id')}")
            print(f"   User ID: {booking.get('user_id')}")
            
            if booking['status'] != 'pending':
                print(f"❌ Status is not pending: {booking['status']}")
                raise ValueError(f"Only pending bookings can be accepted. Current status: {booking['status']}")
            
            # Update booking status directly using MongoDB
            print(f"📝 Updating booking status to confirmed...")
            
            from models.database import db as database_instance
            result = database_instance.db.bookings.update_one(
                {'_id': ObjectId(booking_id)},
                {
                    '$set': {
                        'is_confirmed_by_owner': True,
                        'status': 'confirmed',
                        'confirmed_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            print(f"   Matched: {result.matched_count}, Modified: {result.modified_count}")
            
            if result.matched_count > 0:
                print(f"✅ Booking {booking_id} accepted successfully!")
                return True
            else:
                print(f"❌ No booking matched for update")
                raise ValueError("Failed to update booking - booking not found")
                
        except Exception as e:
            print(f"❌ Exception in accept_by_owner: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    @staticmethod
    def mark_payment_completed(db, booking_id, payment_reference, payment_method='cash'):
        """Mark payment as completed after owner receives cash/UPI"""
        booking = Booking.get_by_id(db, booking_id)
        if not booking:
            return False
        
        if booking['status'] != 'confirmed':
            raise ValueError("Booking must be confirmed by owner first")
        
        now = datetime.utcnow()
        
        # Check if booking should be active now
        is_active = booking['start_time'] <= now <= booking['end_time']
        new_status = 'active' if is_active else 'confirmed'
        
        success = db.update_one(
            'bookings',
            {'_id': ObjectId(booking_id)},
            {'$set': {
                'payment_id': payment_reference,
                'payment_status': 'completed',
                'payment_method': payment_method,
                'status': new_status,
                'payment_completed_at': now,
                'updated_at': now
            }}
        )
        
        return success
    
    @staticmethod
    def update_payment_status(db, booking_id, payment_id, status='completed'):
        """Update payment status for a booking"""
        return db.update_one(
            'bookings',
            {'_id': ObjectId(booking_id)},
            {'$set': {
                'payment_id': payment_id,
                'payment_status': status,
                'updated_at': datetime.utcnow()
            }}
        )
    
    @staticmethod
    def cancel(db, booking_id, cancelled_by):
        """Cancel a booking"""
        booking = Booking.get_by_id(db, booking_id)
        if not booking:
            return False
        
        if booking['status'] in ['completed', 'cancelled']:
            raise ValueError("Cannot cancel completed or already cancelled booking")
        
        # Update booking status
        db.update_one(
            'bookings',
            {'_id': ObjectId(booking_id)},
            {'$set': {
                'status': 'cancelled',
                'cancelled_by': cancelled_by,
                'cancelled_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }}
        )
        
        # Restore parking availability - restore number of spots that were booked
        from models.parking import ParkingSpace
        number_of_spots = booking.get('number_of_spots', 1)
        ParkingSpace.update_availability(db, str(booking['parking_id']), number_of_spots)
        
        # Handle refund if payment was completed
        if booking['payment_status'] == 'completed':
            from models.wallet import Wallet
            # Refund to user wallet
            Wallet.add_balance(
                db,
                str(booking['user_id']),
                booking['total_price'],
                'refund',
                f"Refund for cancelled booking {booking_id}"
            )
        
        return True
    
    @staticmethod
    def complete(db, booking_id):
        """Mark booking as completed"""
        booking = Booking.get_by_id(db, booking_id)
        if not booking:
            return False
        
        # Update booking status
        db.update_one(
            'bookings',
            {'_id': ObjectId(booking_id)},
            {'$set': {
                'status': 'completed',
                'completed_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }}
        )
        
        # Transfer payment to owner's wallet
        from models.wallet import Wallet
        Wallet.add_balance(
            db,
            str(booking['owner_id']),
            booking['total_price'],
            'earning',
            f"Payment for booking {booking_id}"
        )
        
        # Update parking total bookings
        db.update_one(
            'parking_spaces',
            {'_id': booking['parking_id']},
            {'$inc': {'total_bookings': 1}}
        )
        
        return True
    
    @staticmethod
    def check_active_bookings(db):
        """Check and update status of active bookings"""
        import pytz
        
        # Use IST timezone
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        # Make naive for MongoDB comparison
        now_naive = now.replace(tzinfo=None)
        
        # Find bookings that should be active
        pending_active = db.find_many(
            'bookings',
            {
                'status': 'confirmed',
                'start_time': {'$lte': now_naive},
                'end_time': {'$gte': now_naive}
            }
        )
        
        for booking in pending_active:
            Booking.update_status(db, str(booking['_id']), 'active')
        
        # Find bookings that should be completed
        pending_complete = db.find_many(
            'bookings',
            {
                'status': {'$in': ['confirmed', 'active']},
                'end_time': {'$lt': now_naive}
            }
        )
        
        for booking in pending_complete:
            Booking.complete(db, str(booking['_id']))
    
    @staticmethod
    def to_dict(booking):
        """Convert booking document to dictionary"""
        if not booking:
            return None
        
        return {
            'id': str(booking['_id']),
            'user_id': str(booking['user_id']),
            'parking_id': str(booking['parking_id']),
            'owner_id': str(booking['owner_id']),
            'start_time': booking['start_time'].isoformat(),
            'end_time': booking['end_time'].isoformat(),
            'duration_hours': booking['duration_hours'],
            'price_per_hour': booking['price_per_hour'],
            'number_of_spots': booking.get('number_of_spots', 1),
            'total_price': booking['total_price'],
            'vehicle_number': booking.get('vehicle_number', ''),
            'vehicle_type': booking.get('vehicle_type', ''),
            'user_name': booking.get('user_name', ''),
            'user_phone': booking.get('user_phone', ''),
            'payment_method': booking.get('payment_method', 'cash'),
            'status': booking['status'],
            'payment_status': booking['payment_status'],
            'payment_id': booking.get('payment_id'),
            'is_confirmed_by_owner': booking.get('is_confirmed_by_owner', False),
            'cancelled_by': booking.get('cancelled_by'),
            'cancelled_at': booking['cancelled_at'].isoformat() if booking.get('cancelled_at') else None,
            'completed_at': booking['completed_at'].isoformat() if booking.get('completed_at') else None,
            'created_at': booking['created_at'].isoformat(),
            'updated_at': booking['updated_at'].isoformat()
        }
