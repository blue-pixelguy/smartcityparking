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
import razorpay
import hmac
import hashlib
from config import Config
from database import Database

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize Database
db = Database()

# Initialize Razorpay Client
razorpay_client = razorpay.Client(auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))

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
        
        # Validate role
        if data['role'] not in ['host', 'driver']:
            return jsonify({'message': 'Role must be either host or driver'}), 400
        
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
            'role': data['role'],
            'wallet_balance': 0,
            'payment_details': data.get('payment_details', {}),  # UPI, Bank account, etc.
            'created_at': datetime.utcnow(),
            'is_verified': True  # Auto-verify for now
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
                'phone': user['phone'],
                'role': user['role'],
                'wallet_balance': user['wallet_balance']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Login failed', 'error': str(e)}), 500

# ==================== USER PROFILE ====================

@app.route('/api/user/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    try:
        return jsonify({
            'id': str(current_user['_id']),
            'name': current_user['name'],
            'email': current_user['email'],
            'phone': current_user['phone'],
            'role': current_user['role'],
            'wallet_balance': current_user['wallet_balance'],
            'payment_details': current_user.get('payment_details', {}),
            'created_at': current_user['created_at'].isoformat()
        }), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch profile', 'error': str(e)}), 500

@app.route('/api/user/update-payment-details', methods=['PUT'])
@token_required
def update_payment_details(current_user):
    try:
        data = request.json
        
        db.users.update_one(
            {'_id': current_user['_id']},
            {'$set': {'payment_details': data}}
        )
        
        return jsonify({'message': 'Payment details updated successfully'}), 200
    except Exception as e:
        return jsonify({'message': 'Update failed', 'error': str(e)}), 500

# ==================== WALLET ROUTES WITH RAZORPAY ====================

@app.route('/api/wallet/balance', methods=['GET'])
@token_required
def get_wallet_balance(current_user):
    try:
        return jsonify({
            'balance': current_user['wallet_balance']
        }), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch balance', 'error': str(e)}), 500

@app.route('/api/wallet/create-order', methods=['POST'])
@token_required
def create_razorpay_order(current_user):
    try:
        data = request.json
        amount = data.get('amount')
        
        if not amount or amount <= 0:
            return jsonify({'message': 'Invalid amount'}), 400
        
        # Create Razorpay order
        order_data = {
            'amount': int(amount * 100),  # Convert to paisa
            'currency': 'INR',
            'receipt': f"wallet_{str(current_user['_id'])}_{int(datetime.utcnow().timestamp())}",
            'notes': {
                'user_id': str(current_user['_id']),
                'type': 'wallet_topup'
            }
        }
        
        order = razorpay_client.order.create(data=order_data)
        
        # Save transaction in database
        transaction = {
            'user_id': current_user['_id'],
            'type': 'wallet_topup',
            'method': 'razorpay',
            'amount': amount,
            'order_id': order['id'],
            'status': 'pending',
            'created_at': datetime.utcnow()
        }
        
        result = db.transactions.insert_one(transaction)
        
        return jsonify({
            'message': 'Order created successfully',
            'transaction_id': str(result.inserted_id),
            'order_id': order['id'],
            'amount': amount,
            'key_id': app.config['RAZORPAY_KEY_ID']
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Order creation failed', 'error': str(e)}), 500

@app.route('/api/wallet/verify-payment', methods=['POST'])
@token_required
def verify_razorpay_payment(current_user):
    try:
        data = request.json
        
        # Verify payment signature
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        
        # Create signature
        generated_signature = hmac.new(
            app.config['RAZORPAY_KEY_SECRET'].encode(),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature != razorpay_signature:
            return jsonify({'message': 'Invalid payment signature'}), 400
        
        # Update transaction
        transaction = db.transactions.find_one({'order_id': razorpay_order_id})
        
        if not transaction:
            return jsonify({'message': 'Transaction not found'}), 404
        
        # Update transaction status
        db.transactions.update_one(
            {'_id': transaction['_id']},
            {
                '$set': {
                    'status': 'completed',
                    'payment_id': razorpay_payment_id,
                    'completed_at': datetime.utcnow()
                }
            }
        )
        
        # Add money to wallet
        db.users.update_one(
            {'_id': current_user['_id']},
            {'$inc': {'wallet_balance': transaction['amount']}}
        )
        
        # Create notification
        notification = {
            'user_id': current_user['_id'],
            'type': 'wallet_topup',
            'message': f'₹{transaction["amount"]} added to your wallet',
            'created_at': datetime.utcnow(),
            'is_read': False
        }
        db.notifications.insert_one(notification)
        
        return jsonify({
            'message': 'Payment verified successfully',
            'new_balance': current_user['wallet_balance'] + transaction['amount']
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Verification failed', 'error': str(e)}), 500

# ==================== CRYPTO PAYMENT WITH NOWPAYMENTS ====================

@app.route('/api/wallet/create-crypto-payment', methods=['POST'])
@token_required
def create_crypto_payment(current_user):
    try:
        data = request.json
        amount = data.get('amount')
        pay_currency = data.get('currency', 'btc')  # btc, eth, usdt, etc.
        
        if not amount or amount <= 0:
            return jsonify({'message': 'Invalid amount'}), 400
        
        # Create NOWPayments invoice
        nowpayments_url = 'https://api.nowpayments.io/v1/invoice'
        headers = {
            'x-api-key': app.config['NOWPAYMENTS_API_KEY'],
            'Content-Type': 'application/json'
        }
        
        invoice_data = {
            'price_amount': amount,
            'price_currency': 'inr',
            'pay_currency': pay_currency,
            'order_id': f"wallet_{str(current_user['_id'])}_{int(datetime.utcnow().timestamp())}",
            'order_description': 'Wallet Top-up',
            'ipn_callback_url': f'{request.host_url}api/wallet/crypto-webhook',
            'success_url': f'{request.host_url}wallet-success',
            'cancel_url': f'{request.host_url}wallet-cancel'
        }
        
        response = requests.post(nowpayments_url, json=invoice_data, headers=headers)
        
        if response.status_code != 200:
            return jsonify({'message': 'Failed to create crypto payment', 'error': response.text}), 500
        
        invoice = response.json()
        
        # Save transaction in database
        transaction = {
            'user_id': current_user['_id'],
            'type': 'wallet_topup',
            'method': 'crypto',
            'amount': amount,
            'currency': pay_currency,
            'invoice_id': invoice['id'],
            'status': 'pending',
            'created_at': datetime.utcnow()
        }
        
        result = db.transactions.insert_one(transaction)
        
        return jsonify({
            'message': 'Crypto payment created',
            'transaction_id': str(result.inserted_id),
            'payment_url': invoice['invoice_url'],
            'invoice_id': invoice['id']
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Crypto payment creation failed', 'error': str(e)}), 500

@app.route('/api/wallet/crypto-webhook', methods=['POST'])
def crypto_webhook():
    try:
        data = request.json
        
        # Find transaction by invoice_id
        transaction = db.transactions.find_one({'invoice_id': data.get('invoice_id')})
        
        if not transaction:
            return jsonify({'message': 'Transaction not found'}), 404
        
        # Check payment status
        if data.get('payment_status') == 'finished':
            # Update transaction
            db.transactions.update_one(
                {'_id': transaction['_id']},
                {
                    '$set': {
                        'status': 'completed',
                        'payment_id': data.get('payment_id'),
                        'completed_at': datetime.utcnow()
                    }
                }
            )
            
            # Add money to wallet
            db.users.update_one(
                {'_id': transaction['user_id']},
                {'$inc': {'wallet_balance': transaction['amount']}}
            )
            
            # Create notification
            notification = {
                'user_id': transaction['user_id'],
                'type': 'wallet_topup',
                'message': f'₹{transaction["amount"]} added to your wallet via crypto',
                'created_at': datetime.utcnow(),
                'is_read': False
            }
            db.notifications.insert_one(notification)
        
        return jsonify({'message': 'Webhook processed'}), 200
        
    except Exception as e:
        return jsonify({'message': 'Webhook processing failed', 'error': str(e)}), 500

# ==================== PARKING MANAGEMENT ====================

@app.route('/api/parkings', methods=['POST'])
@token_required
def create_parking(current_user):
    try:
        if current_user['role'] != 'host':
            return jsonify({'message': 'Only hosts can create parking listings'}), 403
        
        data = request.json
        
        # Validate required fields
        required_fields = ['title', 'description', 'address', 'city', 'location', 'vehicle_type', 
                          'price_per_hour', 'total_hours', 'min_rental_hours']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'{field} is required'}), 400
        
        # Create parking listing
        parking = {
            'host_id': current_user['_id'],
            'host_name': current_user['name'],
            'host_phone': current_user['phone'],
            'host_payment_details': current_user.get('payment_details', {}),
            'title': data['title'],
            'description': data['description'],
            'address': data['address'],
            'city': data['city'].lower(),
            'state': data.get('state', 'tamil nadu').lower(),
            'location': {
                'type': 'Point',
                'coordinates': data['location']  # [longitude, latitude]
            },
            'vehicle_type': data['vehicle_type'],  # '2-wheeler' or '4-wheeler'
            'price_per_hour': float(data['price_per_hour']),
            'total_hours': int(data['total_hours']),
            'min_rental_hours': int(data['min_rental_hours']),
            'amenities': data.get('amenities', []),
            'images': data.get('images', []),
            'available_from': datetime.fromisoformat(data.get('available_from', datetime.utcnow().isoformat())),
            'available_to': datetime.fromisoformat(data.get('available_to', (datetime.utcnow() + timedelta(days=365)).isoformat())),
            'status': 'pending',  # pending, approved, rejected
            'is_available': True,
            'created_at': datetime.utcnow(),
            'ratings': [],
            'average_rating': 0
        }
        
        result = db.parkings.insert_one(parking)
        
        return jsonify({
            'message': 'Parking listing created successfully and pending approval',
            'parking_id': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        return jsonify({'message': 'Failed to create parking', 'error': str(e)}), 500

@app.route('/api/parkings', methods=['GET'])
def get_parkings():
    try:
        # Get query parameters
        city = request.args.get('city', '').lower()
        vehicle_type = request.args.get('vehicle_type')
        status = request.args.get('status', 'approved')
        
        # Build query
        query = {'status': status, 'is_available': True}
        
        if city:
            query['city'] = city
        
        if vehicle_type:
            query['vehicle_type'] = vehicle_type
        
        parkings = list(db.parkings.find(query).sort('created_at', -1))
        
        for parking in parkings:
            parking['_id'] = str(parking['_id'])
            parking['host_id'] = str(parking['host_id'])
            parking['available_from'] = parking['available_from'].isoformat()
            parking['available_to'] = parking['available_to'].isoformat()
            parking['created_at'] = parking['created_at'].isoformat()
            # Don't expose host payment details in listing
            parking.pop('host_payment_details', None)
        
        return jsonify({
            'count': len(parkings),
            'parkings': parkings
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch parkings', 'error': str(e)}), 500

@app.route('/api/parkings/<parking_id>', methods=['GET'])
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
        parking.pop('host_payment_details', None)
        
        return jsonify(parking), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch parking details', 'error': str(e)}), 500

@app.route('/api/parkings/search', methods=['GET'])
def search_parkings():
    try:
        # Get search parameters
        city = request.args.get('city', '').lower()
        vehicle_type = request.args.get('vehicle_type')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius = request.args.get('radius', 5000, type=int)  # in meters
        
        # Build query
        query = {'status': 'approved', 'is_available': True}
        
        if city:
            query['city'] = city
        
        if vehicle_type:
            query['vehicle_type'] = vehicle_type
        
        if min_price is not None or max_price is not None:
            query['price_per_hour'] = {}
            if min_price is not None:
                query['price_per_hour']['$gte'] = min_price
            if max_price is not None:
                query['price_per_hour']['$lte'] = max_price
        
        # Geospatial search
        if lat is not None and lng is not None:
            query['location'] = {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': [lng, lat]
                    },
                    '$maxDistance': radius
                }
            }
        
        parkings = list(db.parkings.find(query).limit(50))
        
        for parking in parkings:
            parking['_id'] = str(parking['_id'])
            parking['host_id'] = str(parking['host_id'])
            parking['available_from'] = parking['available_from'].isoformat()
            parking['available_to'] = parking['available_to'].isoformat()
            parking['created_at'] = parking['created_at'].isoformat()
            parking.pop('host_payment_details', None)
            
            # Calculate distance if coordinates provided
            if lat and lng:
                parking['distance'] = 'Available'  # Would calculate actual distance in production
        
        return jsonify({
            'count': len(parkings),
            'parkings': parkings
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Search failed', 'error': str(e)}), 500

@app.route('/api/parkings/my-listings', methods=['GET'])
@token_required
def get_my_listings(current_user):
    try:
        if current_user['role'] != 'host':
            return jsonify({'message': 'Only hosts can view their listings'}), 403
        
        parkings = list(db.parkings.find({'host_id': current_user['_id']}).sort('created_at', -1))
        
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

# ==================== BOOKING MANAGEMENT ====================

@app.route('/api/bookings', methods=['POST'])
@token_required
def create_booking(current_user):
    try:
        if current_user['role'] != 'driver':
            return jsonify({'message': 'Only drivers can create bookings'}), 403
        
        data = request.json
        parking_id = data.get('parking_id')
        hours = data.get('hours')
        payment_method = data.get('payment_method', 'wallet')  # 'wallet' or 'direct'
        
        if not parking_id or not hours:
            return jsonify({'message': 'Parking ID and hours are required'}), 400
        
        # Get parking details
        parking = db.parkings.find_one({'_id': ObjectId(parking_id)})
        
        if not parking:
            return jsonify({'message': 'Parking not found'}), 404
        
        if parking['status'] != 'approved' or not parking['is_available']:
            return jsonify({'message': 'Parking is not available'}), 400
        
        if hours < parking['min_rental_hours']:
            return jsonify({'message': f'Minimum rental hours is {parking["min_rental_hours"]}'}), 400
        
        # Calculate cost
        total_cost = parking['price_per_hour'] * hours
        
        # Check wallet balance if using wallet
        if payment_method == 'wallet' and current_user['wallet_balance'] < total_cost:
            return jsonify({'message': 'Insufficient wallet balance'}), 400
        
        # Create booking
        booking = {
            'driver_id': current_user['_id'],
            'driver_name': current_user['name'],
            'driver_phone': current_user['phone'],
            'host_id': parking['host_id'],
            'host_name': parking['host_name'],
            'host_phone': parking['host_phone'],
            'parking_id': parking['_id'],
            'parking_title': parking['title'],
            'parking_address': parking['address'],
            'hours': hours,
            'price_per_hour': parking['price_per_hour'],
            'total_cost': total_cost,
            'payment_method': payment_method,
            'status': 'pending',  # pending, confirmed, rejected, completed, cancelled
            'created_at': datetime.utcnow(),
            'start_time': None,
            'end_time': None,
            'payment_status': 'pending'  # pending, paid, refunded
        }
        
        result = db.bookings.insert_one(booking)
        
        # Notify host
        notification = {
            'user_id': parking['host_id'],
            'type': 'new_booking',
            'booking_id': result.inserted_id,
            'message': f'New booking request from {current_user["name"]} for {parking["title"]}',
            'created_at': datetime.utcnow(),
            'is_read': False
        }
        db.notifications.insert_one(notification)
        
        return jsonify({
            'message': 'Booking created successfully. Waiting for host approval',
            'booking_id': str(result.inserted_id),
            'total_cost': total_cost
        }), 201
        
    except Exception as e:
        return jsonify({'message': 'Booking creation failed', 'error': str(e)}), 500

@app.route('/api/bookings/<booking_id>/confirm', methods=['PUT'])
@token_required
def confirm_booking(current_user, booking_id):
    try:
        booking = db.bookings.find_one({'_id': ObjectId(booking_id)})
        
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404
        
        # Only host can confirm
        if booking['host_id'] != current_user['_id']:
            return jsonify({'message': 'Only the host can confirm this booking'}), 403
        
        if booking['status'] != 'pending':
            return jsonify({'message': 'Booking is not pending'}), 400
        
        # Update booking status
        db.bookings.update_one(
            {'_id': ObjectId(booking_id)},
            {
                '$set': {
                    'status': 'confirmed',
                    'confirmed_at': datetime.utcnow(),
                    'start_time': datetime.utcnow()
                }
            }
        )
        
        # Notify driver
        notification = {
            'user_id': booking['driver_id'],
            'type': 'booking_confirmed',
            'booking_id': booking['_id'],
            'message': f'Your booking for {booking["parking_title"]} has been confirmed',
            'created_at': datetime.utcnow(),
            'is_read': False
        }
        db.notifications.insert_one(notification)
        
        return jsonify({'message': 'Booking confirmed successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': 'Confirmation failed', 'error': str(e)}), 500

@app.route('/api/bookings/<booking_id>/complete-payment', methods=['POST'])
@token_required
def complete_booking_payment(current_user, booking_id):
    try:
        booking = db.bookings.find_one({'_id': ObjectId(booking_id)})
        
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404
        
        # Only driver can complete payment
        if booking['driver_id'] != current_user['_id']:
            return jsonify({'message': 'Unauthorized'}), 403
        
        if booking['status'] != 'confirmed':
            return jsonify({'message': 'Booking is not confirmed'}), 400
        
        if booking['payment_status'] == 'paid':
            return jsonify({'message': 'Payment already completed'}), 400
        
        payment_method = booking['payment_method']
        total_cost = booking['total_cost']
        
        if payment_method == 'wallet':
            # Deduct from driver's wallet
            if current_user['wallet_balance'] < total_cost:
                return jsonify({'message': 'Insufficient wallet balance'}), 400
            
            db.users.update_one(
                {'_id': current_user['_id']},
                {'$inc': {'wallet_balance': -total_cost}}
            )
            
            # Add to host's wallet (with platform fee deduction)
            platform_fee = total_cost * 0.05  # 5% platform fee
            host_amount = total_cost - platform_fee
            
            db.users.update_one(
                {'_id': booking['host_id']},
                {'$inc': {'wallet_balance': host_amount}}
            )
            
        elif payment_method == 'direct':
            # Direct payment to host
            # In production, this would integrate with payment gateway
            platform_fee = total_cost * 0.05
            host_amount = total_cost - platform_fee
        
        # Update booking
        db.bookings.update_one(
            {'_id': ObjectId(booking_id)},
            {
                '$set': {
                    'status': 'completed',
                    'payment_status': 'paid',
                    'end_time': datetime.utcnow(),
                    'completed_at': datetime.utcnow()
                }
            }
        )
        
        # Create transaction record
        transaction = {
            'booking_id': booking['_id'],
            'driver_id': booking['driver_id'],
            'host_id': booking['host_id'],
            'amount': total_cost,
            'platform_fee': platform_fee,
            'host_amount': host_amount,
            'payment_method': payment_method,
            'type': 'booking_payment',
            'status': 'completed',
            'created_at': datetime.utcnow()
        }
        db.transactions.insert_one(transaction)
        
        # Notify host
        notification = {
            'user_id': booking['host_id'],
            'type': 'payment_received',
            'booking_id': booking['_id'],
            'message': f'Payment of ₹{host_amount:.2f} received for booking #{str(booking["_id"])[:8]}',
            'created_at': datetime.utcnow(),
            'is_read': False
        }
        db.notifications.insert_one(notification)
        
        # Notify driver
        notification = {
            'user_id': booking['driver_id'],
            'type': 'booking_completed',
            'booking_id': booking['_id'],
            'message': f'Booking completed. Payment of ₹{total_cost} processed',
            'created_at': datetime.utcnow(),
            'is_read': False
        }
        db.notifications.insert_one(notification)
        
        return jsonify({
            'message': 'Payment completed successfully',
            'amount_paid': total_cost,
            'platform_fee': platform_fee
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Payment failed', 'error': str(e)}), 500

@app.route('/api/bookings/user', methods=['GET'])
@token_required
def get_user_bookings(current_user):
    try:
        role = current_user['role']
        
        if role == 'driver':
            bookings = list(db.bookings.find({'driver_id': current_user['_id']}).sort('created_at', -1))
        elif role == 'host':
            bookings = list(db.bookings.find({'host_id': current_user['_id']}).sort('created_at', -1))
        else:
            return jsonify({'message': 'Invalid role'}), 400
        
        for booking in bookings:
            booking['_id'] = str(booking['_id'])
            booking['driver_id'] = str(booking['driver_id'])
            booking['host_id'] = str(booking['host_id'])
            booking['parking_id'] = str(booking['parking_id'])
            booking['created_at'] = booking['created_at'].isoformat()
            if booking.get('start_time'):
                booking['start_time'] = booking['start_time'].isoformat()
            if booking.get('end_time'):
                booking['end_time'] = booking['end_time'].isoformat()
        
        return jsonify({
            'count': len(bookings),
            'bookings': bookings
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch bookings', 'error': str(e)}), 500

# ==================== NOTIFICATIONS ====================

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
            {'$set': {'status': 'approved', 'approved_at': datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            return jsonify({'message': 'Parking not found'}), 404
        
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

# ==================== HEALTH CHECK ====================

@app.route('/health', methods=['GET'])
def health_check():
    try:
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
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)