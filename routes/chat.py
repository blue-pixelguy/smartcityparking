"""
Chat/Messaging Routes
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.message import Message
from models.booking import Booking
from models.user import User

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/send', methods=['POST'])
@jwt_required()
def send_message():
    """Send a message"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['booking_id', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Get booking to determine receiver
        booking = Booking.get_by_id(current_app.db, data['booking_id'])
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Determine receiver (if sender is user, receiver is owner and vice versa)
        if str(booking['user_id']) == user_id:
            receiver_id = str(booking['owner_id'])
        elif str(booking['owner_id']) == user_id:
            receiver_id = str(booking['user_id'])
        else:
            return jsonify({'error': 'You are not part of this booking'}), 403
        
        # Create message
        message_id = Message.create(
            current_app.db,
            user_id,
            receiver_id,
            data['booking_id'],
            data['content']
        )
        
        # Get created message
        message = current_app.db.find_one('messages', {'_id': message_id})
        
        return jsonify({
            'message': 'Message sent successfully',
            'data': Message.to_dict(message)
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to send message', 'details': str(e)}), 500

@chat_bp.route('/booking/<booking_id>', methods=['GET'])
@jwt_required()
def get_booking_messages(booking_id):
    """Get all messages for a booking"""
    try:
        user_id = get_jwt_identity()
        
        # Check if user is part of this booking
        booking = Booking.get_by_id(current_app.db, booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        if str(booking['user_id']) != user_id and str(booking['owner_id']) != user_id:
            return jsonify({'error': 'You do not have permission to view these messages'}), 403
        
        # Get messages
        messages = Message.get_by_booking(current_app.db, booking_id)
        
        # Mark messages as read
        Message.mark_as_read(current_app.db, booking_id, user_id)
        
        # Get sender details for each message
        messages_with_users = []
        for message in messages:
            sender = User.get_by_id(current_app.db, str(message['sender_id']))
            message_dict = Message.to_dict(message)
            message_dict['sender'] = {
                'id': str(sender['_id']),
                'name': sender['name'],
                'profile_image': sender.get('profile_image')
            }
            messages_with_users.append(message_dict)
        
        return jsonify({
            'count': len(messages_with_users),
            'messages': messages_with_users
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get messages', 'details': str(e)}), 500

@chat_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    """Get all conversations for current user"""
    try:
        user_id = get_jwt_identity()
        
        conversations = Message.get_conversations(current_app.db, user_id)
        
        # Get booking and user details for each conversation
        conversations_with_details = []
        for conv in conversations:
            booking = Booking.get_by_id(current_app.db, str(conv['_id']))
            if not booking:
                continue
            
            # Determine the other user in the conversation
            other_user_id = str(booking['owner_id']) if str(booking['user_id']) == user_id else str(booking['user_id'])
            other_user = User.get_by_id(current_app.db, other_user_id)
            
            last_message = conv['last_message']
            
            conversations_with_details.append({
                'booking_id': str(conv['_id']),
                'other_user': {
                    'id': str(other_user['_id']),
                    'name': other_user['name'],
                    'profile_image': other_user.get('profile_image')
                },
                'last_message': Message.to_dict(last_message),
                'unread_count': conv['unread_count']
            })
        
        return jsonify({
            'count': len(conversations_with_details),
            'conversations': conversations_with_details
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get conversations', 'details': str(e)}), 500

@chat_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """Get total unread message count"""
    try:
        user_id = get_jwt_identity()
        count = Message.get_unread_count(current_app.db, user_id)
        
        return jsonify({
            'unread_count': count
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get unread count', 'details': str(e)}), 500
