from flask import Blueprint, request, jsonify
from database import db
from auth import token_required
from bson import ObjectId
from datetime import datetime
from payments import RazorpayPayment, CryptoPayment, WalletPayment
from models import Transaction
from utils import send_notification_to_user
import os

wallet_bp = Blueprint('wallet', __name__)

@wallet_bp.route('/balance', methods=['GET'])
@token_required
def get_balance():
    """Get wallet balance"""
    try:
        wallet = db.db.wallets.find_one({'user_id': ObjectId(request.user_id)})
        
        if not wallet:
            return jsonify({'balance': 0.0}), 200
        
        return jsonify({
            'balance': wallet['balance'],
            'updated_at': wallet['updated_at'].isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@wallet_bp.route('/transactions', methods=['GET'])
@token_required
def get_transactions():
    """Get wallet transactions"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        skip = (page - 1) * per_page
        
        transactions = list(db.db.transactions.find({
            'user_id': ObjectId(request.user_id)
        }).sort('created_at', -1).skip(skip).limit(per_page))
        
        total = db.db.transactions.count_documents({'user_id': ObjectId(request.user_id)})
        
        results = []
        for txn in transactions:
            results.append({
                'id': str(txn['_id']),
                'amount': txn['amount'],
                'transaction_type': txn['transaction_type'],
                'payment_method': txn['payment_method'],
                'description': txn['description'],
                'status': txn['status'],
                'created_at': txn['created_at'].isoformat()
            })
        
        return jsonify({
            'transactions': results,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@wallet_bp.route('/add-money/razorpay/create-order', methods=['POST'])
@token_required
def create_razorpay_order():
    """Create Razorpay order for adding money"""
    try:
        data = request.get_json()
        
        if 'amount' not in data:
            return jsonify({'error': 'Amount is required'}), 400
        
        amount = float(data['amount'])
        
        if amount < 100:
            return jsonify({'error': 'Minimum amount is ₹100'}), 400
        
        # Create Razorpay order
        receipt_id = f"wallet_{request.user_id}_{int(datetime.utcnow().timestamp())}"
        order = RazorpayPayment.create_order(amount, receipt_id)
        
        if not order:
            return jsonify({'error': 'Failed to create payment order'}), 500
        
        # Create pending transaction
        transaction = Transaction(
            user_id=request.user_id,
            amount=amount,
            transaction_type='credit',
            payment_method='razorpay',
            description='Wallet recharge'
        )
        transaction.payment_id = order['id']
        
        db.db.transactions.insert_one(transaction.to_dict())
        
        return jsonify({
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency'],
            'key': os.getenv('RAZORPAY_KEY_ID')
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@wallet_bp.route('/add-money/razorpay/verify', methods=['POST'])
@token_required
def verify_razorpay_payment():
    """Verify Razorpay payment and add money to wallet"""
    try:
        data = request.get_json()
        
        required_fields = ['order_id', 'payment_id', 'signature']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Verify signature
        is_valid = RazorpayPayment.verify_payment(
            data['order_id'],
            data['payment_id'],
            data['signature']
        )
        
        if not is_valid:
            return jsonify({'error': 'Invalid payment signature'}), 400
        
        # Get payment details
        payment = RazorpayPayment.fetch_payment(data['payment_id'])
        
        if not payment or payment['status'] != 'captured':
            return jsonify({'error': 'Payment not captured'}), 400
        
        amount = payment['amount'] / 100  # Convert from paise
        
        # Add funds to wallet
        result = WalletPayment.add_funds(
            user_id=request.user_id,
            amount=amount,
            payment_method='razorpay',
            payment_id=data['payment_id']
        )
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        
        # Send notification
        send_notification_to_user(
            request.user_id,
            'Money Added',
            f'₹{amount} has been added to your wallet',
            'payment'
        )
        
        return jsonify({
            'message': 'Money added successfully',
            'amount': amount,
            'new_balance': result['new_balance']
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@wallet_bp.route('/add-money/crypto/estimate', methods=['POST'])
@token_required
def get_crypto_estimate():
    """Get crypto payment estimate"""
    try:
        data = request.get_json()
        
        if 'amount' not in data or 'currency' not in data:
            return jsonify({'error': 'Amount and currency are required'}), 400
        
        estimate = CryptoPayment.get_estimate(
            amount=float(data['amount']),
            currency_from='inr',
            currency_to=data['currency']
        )
        
        if not estimate:
            return jsonify({'error': 'Failed to get estimate'}), 500
        
        return jsonify(estimate), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@wallet_bp.route('/add-money/crypto/create-payment', methods=['POST'])
@token_required
def create_crypto_payment():
    """Create crypto payment for adding money"""
    try:
        data = request.get_json()
        
        required_fields = ['amount', 'pay_currency']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        amount = float(data['amount'])
        
        if amount < 100:
            return jsonify({'error': 'Minimum amount is ₹100'}), 400
        
        # Create crypto payment
        order_id = f"wallet_{request.user_id}_{int(datetime.utcnow().timestamp())}"
        
        payment = CryptoPayment.create_payment(
            price_amount=amount,
            price_currency='inr',
            pay_currency=data['pay_currency'],
            order_id=order_id,
            order_description='Wallet recharge'
        )
        
        if not payment:
            return jsonify({'error': 'Failed to create crypto payment'}), 500
        
        # Create pending transaction
        transaction = Transaction(
            user_id=request.user_id,
            amount=amount,
            transaction_type='credit',
            payment_method='crypto',
            description='Wallet recharge (Crypto)'
        )
        transaction.payment_id = str(payment['payment_id'])
        
        db.db.transactions.insert_one(transaction.to_dict())
        
        return jsonify({
            'payment_id': payment['payment_id'],
            'payment_url': payment['pay_address'],
            'pay_amount': payment['pay_amount'],
            'pay_currency': payment['pay_currency']
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@wallet_bp.route('/add-money/crypto/callback', methods=['POST'])
def crypto_payment_callback():
    """Handle crypto payment callback"""
    try:
        data = request.get_json()
        
        payment_id = data.get('payment_id')
        
        if not payment_id:
            return jsonify({'error': 'Payment ID required'}), 400
        
        # Get payment status
        payment = CryptoPayment.get_payment_status(payment_id)
        
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        
        if payment['payment_status'] != 'finished':
            return jsonify({'message': 'Payment not completed'}), 200
        
        # Find transaction
        transaction = db.db.transactions.find_one({'payment_id': str(payment_id)})
        
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        if transaction['status'] == 'success':
            return jsonify({'message': 'Already processed'}), 200
        
        # Add funds to wallet
        result = WalletPayment.add_funds(
            user_id=str(transaction['user_id']),
            amount=transaction['amount'],
            payment_method='crypto',
            payment_id=str(payment_id)
        )
        
        if result['success']:
            # Send notification
            send_notification_to_user(
                str(transaction['user_id']),
                'Money Added',
                f'₹{transaction["amount"]} has been added to your wallet via crypto',
                'payment'
            )
        
        return jsonify({'message': 'Payment processed'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@wallet_bp.route('/add-money/crypto/check-status/<payment_id>', methods=['GET'])
@token_required
def check_crypto_status(payment_id):
    """Check crypto payment status"""
    try:
        payment = CryptoPayment.get_payment_status(payment_id)
        
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        
        return jsonify({
            'payment_status': payment['payment_status'],
            'pay_amount': payment.get('pay_amount'),
            'actually_paid': payment.get('actually_paid')
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
