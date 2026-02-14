"""
Wallet Model
"""

from datetime import datetime
from bson.objectid import ObjectId

class Wallet:
    """Wallet model for managing user balances"""
    
    TRANSACTION_TYPES = ['credit', 'debit', 'refund', 'earning', 'withdrawal']
    
    @staticmethod
    def create(db, user_id):
        """Create a new wallet for a user"""
        existing_wallet = db.find_one('wallets', {'user_id': ObjectId(user_id)})
        if existing_wallet:
            return str(existing_wallet['_id'])
        
        wallet_data = {
            'user_id': ObjectId(user_id),
            'balance': 0.0,
            'total_credited': 0.0,
            'total_debited': 0.0,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        return db.insert_one('wallets', wallet_data)
    
    @staticmethod
    def get_by_user_id(db, user_id):
        """Get wallet by user ID"""
        return db.find_one('wallets', {'user_id': ObjectId(user_id)})
    
    @staticmethod
    def get_balance(db, user_id):
        """Get wallet balance for a user"""
        wallet = Wallet.get_by_user_id(db, user_id)
        if not wallet:
            # Create wallet if doesn't exist
            Wallet.create(db, user_id)
            return 0.0
        return wallet.get('balance', 0.0)
    
    @staticmethod
    def add_balance(db, user_id, amount, transaction_type='credit', description=''):
        """Add money to wallet"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        wallet = Wallet.get_by_user_id(db, user_id)
        if not wallet:
            Wallet.create(db, user_id)
            wallet = Wallet.get_by_user_id(db, user_id)
        
        new_balance = wallet['balance'] + amount
        
        # Update wallet balance
        db.update_one(
            'wallets',
            {'user_id': ObjectId(user_id)},
            {'$set': {
                'balance': new_balance,
                'total_credited': wallet['total_credited'] + amount,
                'updated_at': datetime.utcnow()
            }}
        )
        
        # Create transaction record
        transaction_data = {
            'wallet_id': wallet['_id'],
            'user_id': ObjectId(user_id),
            'amount': amount,
            'type': transaction_type,
            'description': description,
            'balance_after': new_balance,
            'created_at': datetime.utcnow()
        }
        db.insert_one('wallet_transactions', transaction_data)
        
        return new_balance
    
    @staticmethod
    def deduct_balance(db, user_id, amount, transaction_type='debit', description=''):
        """Deduct money from wallet"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        wallet = Wallet.get_by_user_id(db, user_id)
        if not wallet:
            raise ValueError("Wallet not found")
        
        if wallet['balance'] < amount:
            raise ValueError("Insufficient balance")
        
        new_balance = wallet['balance'] - amount
        
        # Update wallet balance
        db.update_one(
            'wallets',
            {'user_id': ObjectId(user_id)},
            {'$set': {
                'balance': new_balance,
                'total_debited': wallet['total_debited'] + amount,
                'updated_at': datetime.utcnow()
            }}
        )
        
        # Create transaction record
        transaction_data = {
            'wallet_id': wallet['_id'],
            'user_id': ObjectId(user_id),
            'amount': -amount,
            'type': transaction_type,
            'description': description,
            'balance_after': new_balance,
            'created_at': datetime.utcnow()
        }
        db.insert_one('wallet_transactions', transaction_data)
        
        return new_balance
    
    @staticmethod
    def get_transactions(db, user_id, limit=50):
        """Get wallet transaction history"""
        return db.find_many(
            'wallet_transactions',
            {'user_id': ObjectId(user_id)},
            sort=[('created_at', -1)],
            limit=limit
        )
    
    @staticmethod
    def to_dict(wallet):
        """Convert wallet document to dictionary"""
        if not wallet:
            return None
        
        return {
            'id': str(wallet['_id']),
            'user_id': str(wallet['user_id']),
            'balance': wallet['balance'],
            'total_credited': wallet.get('total_credited', 0.0),
            'total_debited': wallet.get('total_debited', 0.0),
            'created_at': wallet['created_at'].isoformat(),
            'updated_at': wallet['updated_at'].isoformat()
        }
    
    @staticmethod
    def transaction_to_dict(transaction):
        """Convert transaction document to dictionary"""
        if not transaction:
            return None
        
        return {
            'id': str(transaction['_id']),
            'wallet_id': str(transaction['wallet_id']),
            'user_id': str(transaction['user_id']),
            'amount': transaction['amount'],
            'type': transaction['type'],
            'description': transaction['description'],
            'balance_after': transaction['balance_after'],
            'created_at': transaction['created_at'].isoformat()
        }
