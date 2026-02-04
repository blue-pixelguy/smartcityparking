from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from bson import ObjectId
import os
import jwt
from functools import wraps
import requests
from config import Config
from database import Database

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize Database
db = Database()

# File upload configuration
UPLOAD_FOLDER = 'static/uploads/parking'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# JWT Token decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            token = token.split(" ")[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = db.users.find_one({'_id': ObjectId(data['user_id'])})
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Admin only decorator
def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.get('role') != 'admin':
            return jsonify({'message': 'Admin access required!'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

# ==================== AUTH ROUTES ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['name', 'email', 'password', 'phone', 'role']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'{field} is required'}), 400
        
        # Check if user exists
        if db.users.find_one({'email': data['email']}):
            return jsonify({'message': 'Email already registered'}), 400
        
        if db.users.find_one({'phone': data['phone']}):
            return jsonify({'message': 'Phone number already registered'}), 400
        
        # Create user
        user = {
            'name': data['name'],
            'email': data['email'],
            'password': generate_password_hash(data['password']),
            'phone': data['phone'],
            'role': data['role'],  # 'host', 'driver', or 'admin'
            'wallet_balance': 0,
            'created_at': datetime.utcnow(),
            'is_verified': False
        }
        
        result = db.users.insert_one(user)
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        return jsonify({'message': 'Registration failed', 'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Email and password required'}), 400
        
        user = db.users.find_one({'email': data['email']})
        
        if not user or not check_password_hash(user['password'], data['password']):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': str(user['_id']),
            'exp': datetime.utcnow() + timedelta(days=7)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'role': user['role'],
                'wallet_balance': user['wallet_balance']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Login failed', 'error': str(e)}), 500

# ==================== WALLET ROUTES ====================

@app.route('/api/wallet/add-money/razorpay', methods=['POST'])
@token_required
def add_money_razorpay(current_user):
    try:
        data = request.json
        amount = data.get('amount')
        
        if not amount or amount <= 0:
            return jsonify({'message': 'Invalid amount'}), 400
        
        # Create Razorpay order
        razorpay_data = {
            'amount': int(amount * 100),  # Razorpay expects amount in paisa
            'currency': 'INR',
            'receipt': f"wallet_{str(current_user['_id'])}_{datetime.utcnow().timestamp()}"
        }
        
        # In production, use Razorpay SDK
        # For now, simulate the transaction
        transaction = {
            'user_id': current_user['_id'],
            'type': 'wallet_topup',
            'method': 'razorpay',
            'amount': amount,
            'status': 'pending',
            'created_at': datetime.utcnow()
        }
        
        result = db.transactions.insert_one(transaction)
        
        return jsonify({
            'message': 'Payment initiated',
            'transaction_id': str(result.inserted_id),
            'order_details': razorpay_data
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Transaction failed', 'error': str(e)}), 500

@app.route('/api/wallet/add-money/crypto', methods=['POST'])
@token_required
def add_money_crypto(current_user):
    try:
        data = request.json
        amount = data.get('amount')
        currency = data.get('currency', 'btc')  # btc, eth, usdt, etc.
        
        if not amount or amount <= 0:
            return jsonify({'message': 'Invalid amount'}), 400
        
        # Create NOWPayments invoice
        nowpayments_data = {
            'price_amount': amount,
            'price_currency': 'inr',
            'pay_currency': currency,
            'order_id': f"wallet_{str(current_user['_id'])}_{datetime.utcnow().timestamp()}",
            'order_description': 'Wallet top-up'
        }
        
        # In production, call NOWPayments API
        # headers = {'x-api-key': app.config['NOWPAYMENTS_API_KEY']}
        # response = requests.post('https://api.nowpayments.io/v1/invoice', json=nowpayments_data, headers=headers)
        
        transaction = {
            'user_id': current_user['_id'],
            'type': 'wallet_topup',
            'method': 'crypto',
            'amount': amount,
            'currency': currency,
            'status': 'pending',
            'created_at': datetime.utcnow()
        }
        
        result = db.transactions.insert_one(transaction)
        
        return jsonify({
            'message': 'Crypto payment initiated',
            'transaction_id': str(result.inserted_id),
            'payment_url': 'https://nowpayments.io/payment/...'  # Would be actual URL in production
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Transaction failed', 'error': str(e)}), 500

@app.route('/api/wallet/confirm-payment', methods=['POST'])
@token_required
def confirm_payment(current_user):
    try:
        data = request.json
        transaction_id = data.get('transaction_id')
        
        transaction = db.transactions.find_one({'_id': ObjectId(transaction_id)})
        
        if not transaction:
            return jsonify({'message': 'Transaction not found'}), 404
        
        if transaction['user_id'] != current_user['_id']:
            return jsonify({'message': 'Unauthorized'}), 403
        
        # Update transaction status
        db.transactions.update_one(
            {'_id': ObjectId(transaction_id)},
            {'$set': {'status': 'completed', 'completed_at': datetime.utcnow()}}
        )
        
        # Update user wallet
        db.users.update_one(
            {'_id': current_user['_id']},
            {'$inc': {'wallet_balance': transaction['amount']}}
        )
        
        return jsonify({
            'message': 'Payment confirmed',
            'new_balance': current_user['wallet_balance'] + transaction['amount']
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Confirmation failed', 'error': str(e)}), 500

@app.route('/api/wallet/balance', methods=['GET'])
@token_required
def get_wallet_balance(current_user):
    return jsonify({
        'balance': current_user['wallet_balance']
    }), 200

# ==================== PARKING LISTING ROUTES ====================

@app.route('/api/parking/create', methods=['POST'])
@token_required
def create_parking(current_user):
    try:
        if current_user['role'] not in ['host', 'admin']:
            return jsonify({'message': 'Only hosts can create parking listings'}), 403
        
        data = request.form.to_dict()
        
        # Validate required fields
        required_fields = ['title', 'description', 'address', 'city', 'latitude', 
                          'longitude', 'vehicle_type', 'price_per_hour', 'available_from', 
                          'available_to', 'total_hours']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'{field} is required'}), 400
        
        # Handle image uploads
        images = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"{datetime.utcnow().timestamp()}_{file.filename}")
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    images.append(f'/static/uploads/parking/{filename}')
        
        # Calculate minimum rental hours (70% of total hours)
        total_hours = int(data['total_hours'])
        min_rental_hours = int(total_hours * 0.7)
        
        parking = {
            'host_id': current_user['_id'],
            'host_name': current_user['name'],
            'host_phone': current_user['phone'],
            'title': data['title'],
            'description': data['description'],
            'address': data['address'],
            'city': data['city'].lower(),
            'state': 'tamil nadu',
            'location': {
                'type': 'Point',
                'coordinates': [float(data['longitude']), float(data['latitude'])]
            },
            'vehicle_type': data['vehicle_type'],  # '2-wheeler' or '4-wheeler'
            'price_per_hour': float(data['price_per_hour']),
            'available_from': datetime.fromisoformat(data['available_from']),
            'available_to': datetime.fromisoformat(data['available_to']),
            'total_hours': total_hours,
            'min_rental_hours': min_rental_hours,
            'images': images,
            'amenities': data.get('amenities', '').split(',') if data.get('amenities') else [],
            'status': 'pending',  # pending, approved, rejected
            'is_available': True,
            'created_at': datetime.utcnow(),
            'ratings': [],
            'average_rating': 0
        }
        
        result = db.parkings.insert_one(parking)
        
        return jsonify({
            'message': 'Parking listing created successfully',
            'parking_id': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        return jsonify({'message': 'Listing creation failed', 'error': str(e)}), 500

@app.route('/api/parking/search', methods=['GET'])
def search_parking():
    try:
        # Get query parameters
        city = request.args.get('city', 'trichy').lower()
        vehicle_type = request.args.get('vehicle_type')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        lat = request.args.get('latitude')
        lng = request.args.get('longitude')
        radius = float(request.args.get('radius', 5))  # km
        
        # Build query
        query = {
            'status': 'approved',
            'is_available': True,
            'city': city
        }
        
        if vehicle_type:
            query['vehicle_type'] = vehicle_type
        
        if start_time and end_time:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
            query['available_from'] = {'$lte': start}
            query['available_to'] = {'$gte': end}
        
        # Location-based search
        if lat and lng:
            query['location'] = {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': [float(lng), float(lat)]
                    },
                    '$maxDistance': radius * 1000  # Convert km to meters
                }
            }
        
        parkings = list(db.parkings.find(query).limit(50))
        
        # Convert ObjectId to string
        for parking in parkings:
            parking['_id'] = str(parking['_id'])
            parking['host_id'] = str(parking['host_id'])
            parking['available_from'] = parking['available_from'].isoformat()
            parking['available_to'] = parking['available_to'].isoformat()
            parking['created_at'] = parking['created_at'].isoformat()
        
        return jsonify({
            'count': len(parkings),
            'parkings': parkings
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Search failed', 'error': str(e)}), 500

@app.route('/api/parking/<parking_id>', methods=['GET'])
def get_parking_details(parking_id):
    try:
        parking = db.parkings.find_one({'_id': ObjectId(parking_id)})
        
        if not parking:
            return jsonify({'message': 'Parking not found'}), 404
        
        parking['_id'] = str(parking['_id'])
        parking['host_id'] = str(parking['host_id'])
        parking['available_from'] = parking['available_from'].isoformat()
        parking['available_to'] = parking['available_to'].isoformat()
        parking['created_at'] = parking['created_at'].isoformat()
        
        return jsonify(parking), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch parking', 'error': str(e)}), 500

@app.route('/api/parking/my-listings', methods=['GET'])
@token_required
def get_my_listings(current_user):
    try:
        parkings = list(db.parkings.find({'host_id': current_user['_id']}))
        
        for parking in parkings:
            parking['_id'] = str(parking['_id'])
            parking['host_id'] = str(parking['host_id'])
            parking['available_from'] = parking['available_from'].isoformat()
            parking['available_to'] = parking['available_to'].isoformat()
            parking['created_at'] = parking['created_at'].isoformat()
        
        return jsonify({
            'count': len(parkings),
            'parkings': parkings
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch listings', 'error': str(e)}), 500

# ==================== BOOKING ROUTES ====================

@app.route('/api/booking/create', methods=['POST'])
@token_required
def create_booking(current_user):
    try:
        if current_user['role'] not in ['driver', 'admin']:
            return jsonify({'message': 'Only drivers can create bookings'}), 403
        
        data = request.json
        parking_id = data.get('parking_id')
        start_time = datetime.fromisoformat(data.get('start_time'))
        rental_hours = int(data.get('rental_hours'))
        
        parking = db.parkings.find_one({'_id': ObjectId(parking_id)})
        
        if not parking:
            return jsonify({'message': 'Parking not found'}), 404
        
        # Validate minimum rental hours
        if rental_hours < parking['min_rental_hours']:
            return jsonify({
                'message': f'Minimum rental hours is {parking["min_rental_hours"]} (70% of {parking["total_hours"]} hours)'
            }), 400
        
        # Calculate total cost
        total_cost = parking['price_per_hour'] * rental_hours
        
        # Check wallet balance
        if current_user['wallet_balance'] < total_cost:
            return jsonify({
                'message': 'Insufficient wallet balance',
                'required': total_cost,
                'available': current_user['wallet_balance']
            }), 400
        
        # Create booking
        end_time = start_time + timedelta(hours=rental_hours)
        
        booking = {
            'parking_id': parking['_id'],
            'driver_id': current_user['_id'],
            'driver_name': current_user['name'],
            'driver_phone': current_user['phone'],
            'host_id': parking['host_id'],
            'start_time': start_time,
            'end_time': end_time,
            'rental_hours': rental_hours,
            'price_per_hour': parking['price_per_hour'],
            'total_cost': total_cost,
            'status': 'payment_pending',  # payment_pending, confirmed, completed, cancelled
            'payment_status': 'pending',
            'created_at': datetime.utcnow()
        }
        
        result = db.bookings.insert_one(booking)
        
        # Deduct from driver's wallet (hold the amount)
        db.users.update_one(
            {'_id': current_user['_id']},
            {'$inc': {'wallet_balance': -total_cost}}
        )
        
        # Create transaction
        transaction = {
            'booking_id': result.inserted_id,
            'from_user': current_user['_id'],
            'to_user': parking['host_id'],
            'amount': total_cost,
            'type': 'booking_payment',
            'status': 'held',
            'created_at': datetime.utcnow()
        }
        
        db.transactions.insert_one(transaction)
        
        return jsonify({
            'message': 'Booking created successfully. Waiting for host confirmation.',
            'booking_id': str(result.inserted_id),
            'total_cost': total_cost
        }), 201
        
    except Exception as e:
        return jsonify({'message': 'Booking failed', 'error': str(e)}), 500

@app.route('/api/booking/confirm/<booking_id>', methods=['POST'])
@token_required
def confirm_booking(current_user, booking_id):
    try:
        booking = db.bookings.find_one({'_id': ObjectId(booking_id)})
        
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404
        
        # Only host can confirm
        if booking['host_id'] != current_user['_id']:
            return jsonify({'message': 'Unauthorized'}), 403
        
        if booking['status'] != 'payment_pending':
            return jsonify({'message': 'Booking already processed'}), 400
        
        # Update booking status
        db.bookings.update_one(
            {'_id': ObjectId(booking_id)},
            {
                '$set': {
                    'status': 'confirmed',
                    'payment_status': 'completed',
                    'confirmed_at': datetime.utcnow()
                }
            }
        )
        
        # Transfer money to host
        db.users.update_one(
            {'_id': current_user['_id']},
            {'$inc': {'wallet_balance': booking['total_cost']}}
        )
        
        # Update transaction
        db.transactions.update_one(
            {'booking_id': booking['_id']},
            {'$set': {'status': 'completed', 'completed_at': datetime.utcnow()}}
        )
        
        # Create notification for driver
        notification = {
            'user_id': booking['driver_id'],
            'type': 'booking_confirmed',
            'message': f'Your booking has been confirmed by the host',
            'booking_id': booking['_id'],
            'created_at': datetime.utcnow(),
            'is_read': False
        }
        db.notifications.insert_one(notification)
        
        return jsonify({
            'message': 'Booking confirmed successfully',
            'amount_received': booking['total_cost']
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Confirmation failed', 'error': str(e)}), 500

@app.route('/api/booking/my-bookings', methods=['GET'])
@token_required
def get_my_bookings(current_user):
    try:
        role = current_user['role']
        
        if role == 'driver':
            bookings = list(db.bookings.find({'driver_id': current_user['_id']}))
        elif role == 'host':
            bookings = list(db.bookings.find({'host_id': current_user['_id']}))
        else:
            bookings = list(db.bookings.find({}))
        
        for booking in bookings:
            booking['_id'] = str(booking['_id'])
            booking['parking_id'] = str(booking['parking_id'])
            booking['driver_id'] = str(booking['driver_id'])
            booking['host_id'] = str(booking['host_id'])
            booking['start_time'] = booking['start_time'].isoformat()
            booking['end_time'] = booking['end_time'].isoformat()
            booking['created_at'] = booking['created_at'].isoformat()
            
            # Get parking details
            parking = db.parkings.find_one({'_id': ObjectId(booking['parking_id'])})
            if parking:
                booking['parking_title'] = parking['title']
                booking['parking_address'] = parking['address']
        
        return jsonify({
            'count': len(bookings),
            'bookings': bookings
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch bookings', 'error': str(e)}), 500

# ==================== RATING ROUTES ====================

@app.route('/api/rating/add', methods=['POST'])
@token_required
def add_rating(current_user):
    try:
        data = request.json
        booking_id = data.get('booking_id')
        rating = int(data.get('rating'))
        review = data.get('review', '')
        
        if rating < 1 or rating > 5:
            return jsonify({'message': 'Rating must be between 1 and 5'}), 400
        
        booking = db.bookings.find_one({'_id': ObjectId(booking_id)})
        
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404
        
        if booking['driver_id'] != current_user['_id']:
            return jsonify({'message': 'Unauthorized'}), 403
        
        if booking['status'] != 'completed':
            return jsonify({'message': 'Can only rate completed bookings'}), 400
        
        # Add rating to parking
        rating_obj = {
            'user_id': current_user['_id'],
            'user_name': current_user['name'],
            'booking_id': booking['_id'],
            'rating': rating,
            'review': review,
            'created_at': datetime.utcnow()
        }
        
        db.parkings.update_one(
            {'_id': booking['parking_id']},
            {'$push': {'ratings': rating_obj}}
        )
        
        # Update average rating
        parking = db.parkings.find_one({'_id': booking['parking_id']})
        ratings = parking.get('ratings', [])
        avg_rating = sum(r['rating'] for r in ratings) / len(ratings)
        
        db.parkings.update_one(
            {'_id': booking['parking_id']},
            {'$set': {'average_rating': avg_rating}}
        )
        
        return jsonify({
            'message': 'Rating added successfully',
            'average_rating': avg_rating
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Rating failed', 'error': str(e)}), 500

# ==================== CHAT ROUTES ====================

@app.route('/api/chat/send', methods=['POST'])
@token_required
def send_message(current_user):
    try:
        data = request.json
        booking_id = data.get('booking_id')
        message = data.get('message')
        
        booking = db.bookings.find_one({'_id': ObjectId(booking_id)})
        
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404
        
        # Verify user is part of this booking
        if current_user['_id'] not in [booking['driver_id'], booking['host_id']]:
            return jsonify({'message': 'Unauthorized'}), 403
        
        # Create message
        chat_message = {
            'booking_id': booking['_id'],
            'sender_id': current_user['_id'],
            'sender_name': current_user['name'],
            'message': message,
            'created_at': datetime.utcnow(),
            'is_read': False
        }
        
        result = db.messages.insert_one(chat_message)
        
        # Create notification for receiver
        receiver_id = booking['host_id'] if current_user['_id'] == booking['driver_id'] else booking['driver_id']
        
        notification = {
            'user_id': receiver_id,
            'type': 'new_message',
            'message': f'New message from {current_user["name"]}',
            'booking_id': booking['_id'],
            'created_at': datetime.utcnow(),
            'is_read': False
        }
        db.notifications.insert_one(notification)
        
        return jsonify({
            'message': 'Message sent successfully',
            'message_id': str(result.inserted_id)
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to send message', 'error': str(e)}), 500

@app.route('/api/chat/<booking_id>', methods=['GET'])
@token_required
def get_messages(current_user, booking_id):
    try:
        booking = db.bookings.find_one({'_id': ObjectId(booking_id)})
        
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404
        
        if current_user['_id'] not in [booking['driver_id'], booking['host_id']]:
            return jsonify({'message': 'Unauthorized'}), 403
        
        messages = list(db.messages.find({'booking_id': ObjectId(booking_id)}).sort('created_at', 1))
        
        for msg in messages:
            msg['_id'] = str(msg['_id'])
            msg['booking_id'] = str(msg['booking_id'])
            msg['sender_id'] = str(msg['sender_id'])
            msg['created_at'] = msg['created_at'].isoformat()
        
        # Mark messages as read
        db.messages.update_many(
            {
                'booking_id': ObjectId(booking_id),
                'sender_id': {'$ne': current_user['_id']}
            },
            {'$set': {'is_read': True}}
        )
        
        return jsonify({
            'count': len(messages),
            'messages': messages
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch messages', 'error': str(e)}), 500

# ==================== NOTIFICATION ROUTES ====================

@app.route('/api/notifications', methods=['GET'])
@token_required
def get_notifications(current_user):
    try:
        notifications = list(db.notifications.find({'user_id': current_user['_id']}).sort('created_at', -1).limit(50))
        
        for notif in notifications:
            notif['_id'] = str(notif['_id'])
            notif['user_id'] = str(notif['user_id'])
            if 'booking_id' in notif:
                notif['booking_id'] = str(notif['booking_id'])
            notif['created_at'] = notif['created_at'].isoformat()
        
        return jsonify({
            'count': len(notifications),
            'notifications': notifications
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch notifications', 'error': str(e)}), 500

@app.route('/api/notifications/mark-read/<notification_id>', methods=['PUT'])
@token_required
def mark_notification_read(current_user, notification_id):
    try:
        db.notifications.update_one(
            {'_id': ObjectId(notification_id), 'user_id': current_user['_id']},
            {'$set': {'is_read': True}}
        )
        
        return jsonify({'message': 'Notification marked as read'}), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to update notification', 'error': str(e)}), 500

# ==================== ADMIN ROUTES ====================

@app.route('/api/admin/pending-listings', methods=['GET'])
@token_required
@admin_required
def get_pending_listings(current_user):
    try:
        parkings = list(db.parkings.find({'status': 'pending'}))
        
        for parking in parkings:
            parking['_id'] = str(parking['_id'])
            parking['host_id'] = str(parking['host_id'])
            parking['available_from'] = parking['available_from'].isoformat()
            parking['available_to'] = parking['available_to'].isoformat()
            parking['created_at'] = parking['created_at'].isoformat()
        
        return jsonify({
            'count': len(parkings),
            'parkings': parkings
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch listings', 'error': str(e)}), 500

@app.route('/api/admin/approve-listing/<parking_id>', methods=['PUT'])
@token_required
@admin_required
def approve_listing(current_user, parking_id):
    try:
        result = db.parkings.update_one(
            {'_id': ObjectId(parking_id)},
            {'$set': {'status': 'approved', 'approved_at': datetime.utcnow(), 'approved_by': current_user['_id']}}
        )
        
        if result.modified_count == 0:
            return jsonify({'message': 'Parking not found'}), 404
        
        # Notify host
        parking = db.parkings.find_one({'_id': ObjectId(parking_id)})
        notification = {
            'user_id': parking['host_id'],
            'type': 'listing_approved',
            'message': f'Your parking listing "{parking["title"]}" has been approved',
            'created_at': datetime.utcnow(),
            'is_read': False
        }
        db.notifications.insert_one(notification)
        
        return jsonify({'message': 'Listing approved successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': 'Approval failed', 'error': str(e)}), 500

@app.route('/api/admin/reject-listing/<parking_id>', methods=['PUT'])
@token_required
@admin_required
def reject_listing(current_user, parking_id):
    try:
        data = request.json
        reason = data.get('reason', 'No reason provided')
        
        result = db.parkings.update_one(
            {'_id': ObjectId(parking_id)},
            {
                '$set': {
                    'status': 'rejected',
                    'rejected_at': datetime.utcnow(),
                    'rejected_by': current_user['_id'],
                    'rejection_reason': reason
                }
            }
        )
        
        if result.modified_count == 0:
            return jsonify({'message': 'Parking not found'}), 404
        
        # Notify host
        parking = db.parkings.find_one({'_id': ObjectId(parking_id)})
        notification = {
            'user_id': parking['host_id'],
            'type': 'listing_rejected',
            'message': f'Your parking listing "{parking["title"]}" has been rejected. Reason: {reason}',
            'created_at': datetime.utcnow(),
            'is_read': False
        }
        db.notifications.insert_one(notification)
        
        return jsonify({'message': 'Listing rejected successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': 'Rejection failed', 'error': str(e)}), 500

@app.route('/api/admin/dashboard', methods=['GET'])
@token_required
@admin_required
def admin_dashboard(current_user):
    try:
        stats = {
            'total_users': db.users.count_documents({}),
            'total_hosts': db.users.count_documents({'role': 'host'}),
            'total_drivers': db.users.count_documents({'role': 'driver'}),
            'total_parkings': db.parkings.count_documents({}),
            'pending_parkings': db.parkings.count_documents({'status': 'pending'}),
            'approved_parkings': db.parkings.count_documents({'status': 'approved'}),
            'total_bookings': db.bookings.count_documents({}),
            'active_bookings': db.bookings.count_documents({'status': 'confirmed'}),
            'total_revenue': 0
        }
        
        # Calculate total revenue
        pipeline = [
            {'$match': {'status': 'completed'}},
            {'$group': {'_id': None, 'total': {'$sum': '$total_cost'}}}
        ]
        revenue = list(db.transactions.aggregate(pipeline))
        if revenue:
            stats['total_revenue'] = revenue[0]['total']
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch dashboard', 'error': str(e)}), 500

# ==================== HEALTH CHECK ====================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        db.users.find_one()
        return jsonify({
            'status': 'healthy',
            'message': 'API is running',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# ==================== HOME ROUTE ====================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)