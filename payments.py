import os
import requests
import hmac
import hashlib

RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')
NOWPAYMENTS_API_KEY = os.getenv('NOWPAYMENTS_API_KEY')

class RazorpayPayment:
    """Handle Razorpay INR payments"""
    
    @staticmethod
    def create_order(amount, receipt_id):
        """Create Razorpay order"""
        url = "https://api.razorpay.com/v1/orders"
        
        auth = (RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
        
        data = {
            "amount": int(amount * 100),  # Convert to paise
            "currency": "INR",
            "receipt": receipt_id,
            "payment_capture": 1
        }
        
        try:
            response = requests.post(url, json=data, auth=auth)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Razorpay order creation error: {e}")
            return None
    
    @staticmethod
    def verify_payment(order_id, payment_id, signature):
        """Verify Razorpay payment signature"""
        message = f"{order_id}|{payment_id}"
        
        generated_signature = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(generated_signature, signature)
    
    @staticmethod
    def fetch_payment(payment_id):
        """Fetch payment details"""
        url = f"https://api.razorpay.com/v1/payments/{payment_id}"
        
        auth = (RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
        
        try:
            response = requests.get(url, auth=auth)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Razorpay fetch payment error: {e}")
            return None


class CryptoPayment:
    """Handle NowPayments crypto payments"""
    
    BASE_URL = "https://api.nowpayments.io/v1"
    
    @staticmethod
    def get_available_currencies():
        """Get available cryptocurrencies"""
        url = f"{CryptoPayment.BASE_URL}/currencies"
        
        headers = {
            "x-api-key": NOWPAYMENTS_API_KEY
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"NowPayments currency error: {e}")
            return None
    
    @staticmethod
    def get_estimate(amount, currency_from='inr', currency_to='btc'):
        """Get estimated crypto amount"""
        url = f"{CryptoPayment.BASE_URL}/estimate"
        
        headers = {
            "x-api-key": NOWPAYMENTS_API_KEY
        }
        
        params = {
            "amount": amount,
            "currency_from": currency_from,
            "currency_to": currency_to
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"NowPayments estimate error: {e}")
            return None
    
    @staticmethod
    def create_payment(price_amount, price_currency, pay_currency, order_id, order_description):
        """Create crypto payment"""
        url = f"{CryptoPayment.BASE_URL}/payment"
        
        headers = {
            "x-api-key": NOWPAYMENTS_API_KEY,
            "Content-Type": "application/json"
        }
        
        data = {
            "price_amount": price_amount,
            "price_currency": price_currency,
            "pay_currency": pay_currency,
            "order_id": order_id,
            "order_description": order_description,
            "ipn_callback_url": "https://your-domain.com/api/payments/crypto/callback"
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"NowPayments create payment error: {e}")
            return None
    
    @staticmethod
    def get_payment_status(payment_id):
        """Get payment status"""
        url = f"{CryptoPayment.BASE_URL}/payment/{payment_id}"
        
        headers = {
            "x-api-key": NOWPAYMENTS_API_KEY
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"NowPayments status error: {e}")
            return None


class WalletPayment:
    """Handle wallet payments"""
    
    @staticmethod
    def process_payment(user_id, amount, description):
        """Process wallet payment"""
        from database import db
        from bson import ObjectId
        from models import Transaction
        from datetime import datetime
        
        try:
            # Get user wallet
            wallet = db.db.wallets.find_one({'user_id': ObjectId(user_id)})
            
            if not wallet:
                return {'success': False, 'error': 'Wallet not found'}
            
            if wallet['balance'] < amount:
                return {'success': False, 'error': 'Insufficient balance'}
            
            # Deduct amount
            new_balance = wallet['balance'] - amount
            
            db.db.wallets.update_one(
                {'user_id': ObjectId(user_id)},
                {
                    '$set': {
                        'balance': new_balance,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            # Create transaction record
            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                transaction_type='debit',
                payment_method='wallet',
                description=description
            )
            transaction.status = 'success'
            
            result = db.db.transactions.insert_one(transaction.to_dict())
            
            return {
                'success': True,
                'transaction_id': str(result.inserted_id),
                'new_balance': new_balance
            }
        
        except Exception as e:
            print(f"Wallet payment error: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def add_funds(user_id, amount, payment_method, payment_id):
        """Add funds to wallet"""
        from database import db
        from bson import ObjectId
        from models import Transaction
        from datetime import datetime
        
        try:
            # Get or create wallet
            wallet = db.db.wallets.find_one({'user_id': ObjectId(user_id)})
            
            if not wallet:
                from models import Wallet
                new_wallet = Wallet(user_id=user_id, balance=amount)
                db.db.wallets.insert_one(new_wallet.to_dict())
                new_balance = amount
            else:
                new_balance = wallet['balance'] + amount
                db.db.wallets.update_one(
                    {'user_id': ObjectId(user_id)},
                    {
                        '$set': {
                            'balance': new_balance,
                            'updated_at': datetime.utcnow()
                        }
                    }
                )
            
            # Create transaction record
            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                transaction_type='credit',
                payment_method=payment_method,
                description='Wallet recharge'
            )
            transaction.status = 'success'
            transaction.payment_id = payment_id
            
            result = db.db.transactions.insert_one(transaction.to_dict())
            
            return {
                'success': True,
                'transaction_id': str(result.inserted_id),
                'new_balance': new_balance
            }
        
        except Exception as e:
            print(f"Add funds error: {e}")
            return {'success': False, 'error': str(e)}
