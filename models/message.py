"""
Message/Chat Model
"""

from datetime import datetime
from bson.objectid import ObjectId

class Message:
    """Message model for in-app chat between users"""
    
    @staticmethod
    def create(db, sender_id, receiver_id, booking_id, content):
        """Create a new message"""
        message_data = {
            'sender_id': ObjectId(sender_id),
            'receiver_id': ObjectId(receiver_id),
            'booking_id': ObjectId(booking_id),
            'content': content,
            'is_read': False,
            'created_at': datetime.utcnow()
        }
        
        return db.insert_one('messages', message_data)
    
    @staticmethod
    def get_by_booking(db, booking_id):
        """Get all messages for a booking"""
        return db.find_many(
            'messages',
            {'booking_id': ObjectId(booking_id)},
            sort=[('created_at', 1)]
        )
    
    @staticmethod
    def get_conversations(db, user_id):
        """Get all conversations for a user"""
        pipeline = [
            {
                '$match': {
                    '$or': [
                        {'sender_id': ObjectId(user_id)},
                        {'receiver_id': ObjectId(user_id)}
                    ]
                }
            },
            {
                '$sort': {'created_at': -1}
            },
            {
                '$group': {
                    '_id': '$booking_id',
                    'last_message': {'$first': '$$ROOT'},
                    'unread_count': {
                        '$sum': {
                            '$cond': [
                                {
                                    '$and': [
                                        {'$eq': ['$receiver_id', ObjectId(user_id)]},
                                        {'$eq': ['$is_read', False]}
                                    ]
                                },
                                1,
                                0
                            ]
                        }
                    }
                }
            },
            {
                '$sort': {'last_message.created_at': -1}
            }
        ]
        
        return db.aggregate('messages', pipeline)
    
    @staticmethod
    def mark_as_read(db, booking_id, receiver_id):
        """Mark all messages in a booking as read for the receiver"""
        result = db.db['messages'].update_many(
            {
                'booking_id': ObjectId(booking_id),
                'receiver_id': ObjectId(receiver_id),
                'is_read': False
            },
            {
                '$set': {'is_read': True}
            }
        )
        return result.modified_count
    
    @staticmethod
    def get_unread_count(db, user_id):
        """Get total unread message count for a user"""
        return db.count_documents(
            'messages',
            {
                'receiver_id': ObjectId(user_id),
                'is_read': False
            }
        )
    
    @staticmethod
    def to_dict(message):
        """Convert message document to dictionary"""
        if not message:
            return None
        
        return {
            'id': str(message['_id']),
            'sender_id': str(message['sender_id']),
            'receiver_id': str(message['receiver_id']),
            'booking_id': str(message['booking_id']),
            'content': message['content'],
            'is_read': message.get('is_read', False),
            'created_at': message['created_at'].isoformat()
        }
