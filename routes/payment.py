"""
Payment Routes - Razorpay and NOWPayments Integration
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.booking import Booking
from models.wallet import Wallet
import razorpay
import requests
import hmac
import hashlib

payment_bp = Blueprint('payment', __name__)

def get_razorpay_client():
    """Get Razorpay client instance"""
    return razorpay.Client(
        auth=(
            current_app.config['RAZORPAY_KEY_ID'],
            current_app.config['RAZORPAY_KEY_SECRET']
        )
    )

@payment_bp.route('/create-order', methods=['POST'])
@jwt_required()
def create_payment_order():
    """Create Razorpay payment order"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if 'amount' not in data:
            return jsonify({'error': 'Amount is required'}), 400
        
        # Create Razorpay order
        client = get_razorpay_client()
        
        order_data = {
            'amount': int(float(data['amount']) * 100),  # Convert to paise
            'currency': 'INR',
            'payment_capture': 1
        }
        
        if 'booking_id' in data:
            order_data['notes'] = {
                'booking_id': data['booking_id'],
                'user_id': user_id
            }
        
        order = client.order.create(data=order_data)
        
        return jsonify({
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency'],
            'key_id': current_app.config['RAZORPAY_KEY_ID']
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to create order', 'details': str(e)}), 500

@payment_bp.route('/verify-payment', methods=['POST'])
@jwt_required()
def verify_payment():
    """Verify Razorpay payment"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Verify signature
        client = get_razorpay_client()
        
        params_dict = {
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        }
        
        try:
            client.utility.verify_payment_signature(params_dict)
        except:
            return jsonify({'error': 'Invalid payment signature'}), 400
        
        # Get payment details
        payment = client.payment.fetch(data['razorpay_payment_id'])
        amount = payment['amount'] / 100  # Convert from paise to rupees
        
        # If booking_id is provided, update booking
        if 'booking_id' in data:
            booking_id = data['booking_id']
            booking = Booking.get_by_id(current_app.db, booking_id)
            
            if not booking:
                return jsonify({'error': 'Booking not found'}), 404
            
            if str(booking['user_id']) != user_id:
                return jsonify({'error': 'Unauthorized'}), 403
            
            # Update booking payment status
            Booking.update_payment_status(
                current_app.db,
                booking_id,
                data['razorpay_payment_id'],
                'completed'
            )
            
            # Deduct from user's wallet
            try:
                Wallet.deduct_balance(
                    current_app.db,
                    user_id,
                    amount,
                    'debit',
                    f'Payment for booking {booking_id}'
                )
            except ValueError:
                # If insufficient wallet balance, payment is still recorded
                pass
            
            return jsonify({
                'message': 'Payment verified successfully. Booking confirmed.',
                'payment_id': data['razorpay_payment_id']
            }), 200
        else:
            # Add to wallet
            Wallet.add_balance(
                current_app.db,
                user_id,
                amount,
                'credit',
                'Wallet recharge via Razorpay'
            )
            
            return jsonify({
                'message': 'Payment verified successfully. Amount added to wallet.',
                'amount': amount,
                'payment_id': data['razorpay_payment_id']
            }), 200
        
    except Exception as e:
        return jsonify({'error': 'Payment verification failed', 'details': str(e)}), 500

@payment_bp.route('/crypto/create-payment', methods=['POST'])
@jwt_required()
def create_crypto_payment():
    """Create NOWPayments crypto payment"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if 'amount' not in data:
            return jsonify({'error': 'Amount (in USD) is required'}), 400
        
        # Create NOWPayments payment
        headers = {
            'x-api-key': current_app.config['NOWPAYMENTS_API_KEY'],
            'Content-Type': 'application/json'
        }
        
        payment_data = {
            'price_amount': float(data['amount']),
            'price_currency': 'usd',
            'pay_currency': data.get('currency', 'btc'),
            'order_id': data.get('booking_id', f'wallet_{user_id}'),
            'order_description': data.get('description', 'Parking payment')
        }
        
        response = requests.post(
            'https://api.nowpayments.io/v1/payment',
            json=payment_data,
            headers=headers
        )
        
        if response.status_code != 201:
            return jsonify({'error': 'Failed to create crypto payment'}), 500
        
        payment = response.json()
        
        return jsonify({
            'payment_id': payment['payment_id'],
            'pay_address': payment['pay_address'],
            'pay_amount': payment['pay_amount'],
            'pay_currency': payment['pay_currency'],
            'price_amount': payment['price_amount'],
            'price_currency': payment['price_currency'],
            'payment_status': payment['payment_status']
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to create crypto payment', 'details': str(e)}), 500

@payment_bp.route('/crypto/status/<payment_id>', methods=['GET'])
@jwt_required()
def get_crypto_payment_status(payment_id):
    """Get NOWPayments payment status"""
    try:
        headers = {
            'x-api-key': current_app.config['NOWPAYMENTS_API_KEY']
        }
        
        response = requests.get(
            f'https://api.nowpayments.io/v1/payment/{payment_id}',
            headers=headers
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to get payment status'}), 500
        
        payment = response.json()
        
        # If payment is finished, process it
        if payment['payment_status'] == 'finished':
            user_id = get_jwt_identity()
            amount = payment['price_amount']
            
            # Add to wallet
            Wallet.add_balance(
                current_app.db,
                user_id,
                amount,
                'credit',
                f'Wallet recharge via crypto (NOWPayments)'
            )
        
        return jsonify({
            'payment_status': payment['payment_status'],
            'pay_amount': payment['pay_amount'],
            'actually_paid': payment.get('actually_paid', 0)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get payment status', 'details': str(e)}), 500

@payment_bp.route('/book-with-wallet', methods=['POST'])
@jwt_required()
def book_with_wallet():
    """Pay for booking using wallet balance"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if 'booking_id' not in data:
            return jsonify({'error': 'Booking ID is required'}), 400
        
        booking_id = data['booking_id']
        booking = Booking.get_by_id(current_app.db, booking_id)
        
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        if str(booking['user_id']) != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if booking['payment_status'] == 'completed':
            return jsonify({'error': 'Booking already paid'}), 400
        
        # Deduct from wallet
        try:
            Wallet.deduct_balance(
                current_app.db,
                user_id,
                booking['total_price'],
                'debit',
                f'Payment for booking {booking_id}'
            )
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        # Update booking payment status
        Booking.update_payment_status(
            current_app.db,
            booking_id,
            f'wallet_{user_id}',
            'completed'
        )
        
        return jsonify({
            'message': 'Booking paid successfully using wallet',
            'booking_id': booking_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Payment failed', 'details': str(e)}), 500
