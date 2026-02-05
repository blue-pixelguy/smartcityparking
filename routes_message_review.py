from flask import Blueprint, request, jsonify
from database import db
from models import Message, Review
from auth import token_required
from bson import ObjectId
from utils import send_notification_to_user

message_bp = Blueprint('message', __name__)
review_bp = Blueprint('review', __name__)

# ========== MESSAGE ROUTES ==========

@message_bp.route('/send', methods=['POST'])
@token_required
def send_message():
    """Send a message"""
    try:
        data = request.get_json()
        
        required_fields = ['receiver_id', 'booking_id', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Verify booking exists and user is part of it
        booking = db.db.bookings.find_one({'_id': ObjectId(data['booking_id'])})
        
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        parking = db.db.parking_spaces.find_one({'_id': booking['parking_id']})
        
        # User must be either driver or owner
        if (str(booking['driver_id']) != request.user_id and 
            str(parking['owner_id']) != request.user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Create message
        message = Message(
            sender_id=request.user_id,
            receiver_id=data['receiver_id'],
            booking_id=data['booking_id'],
            content=data['content']
        )
        
        result = db.db.messages.insert_one(message.to_dict())
        
        # Send notification to receiver
        sender = db.db.users.find_one({'_id': ObjectId(request.user_id)})
        send_notification_to_user(
            data['receiver_id'],
            'New Message',
            f'{sender["name"]} sent you a message',
            'message'
        )
        
        return jsonify({
            'message': 'Message sent successfully',
            'message_id': str(result.inserted_id)
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@message_bp.route('/conversation/<booking_id>', methods=['GET'])
@token_required
def get_conversation(booking_id):
    """Get messages for a booking"""
    try:
        booking = db.db.bookings.find_one({'_id': ObjectId(booking_id)})
        
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        parking = db.db.parking_spaces.find_one({'_id': booking['parking_id']})
        
        # Verify user is part of this booking
        if (str(booking['driver_id']) != request.user_id and 
            str(parking['owner_id']) != request.user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get messages
        messages = list(db.db.messages.find({
            'booking_id': ObjectId(booking_id)
        }).sort('created_at', 1))
        
        # Mark received messages as read
        db.db.messages.update_many(
            {
                'booking_id': ObjectId(booking_id),
                'receiver_id': ObjectId(request.user_id),
                'is_read': False
            },
            {'$set': {'is_read': True}}
        )
        
        results = []
        for msg in messages:
            sender = db.db.users.find_one({'_id': msg['sender_id']})
            
            results.append({
                'id': str(msg['_id']),
                'sender': {
                    'id': str(sender['_id']),
                    'name': sender['name']
                },
                'content': msg['content'],
                'is_read': msg['is_read'],
                'created_at': msg['created_at'].isoformat(),
                'is_mine': str(msg['sender_id']) == request.user_id
            })
        
        return jsonify({
            'messages': results,
            'total': len(results)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@message_bp.route('/unread-count', methods=['GET'])
@token_required
def get_unread_count():
    """Get unread message count"""
    try:
        count = db.db.messages.count_documents({
            'receiver_id': ObjectId(request.user_id),
            'is_read': False
        })
        
        return jsonify({'unread_count': count}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@message_bp.route('/conversations', methods=['GET'])
@token_required
def get_conversations():
    """Get all conversations for user"""
    try:
        # Get all bookings where user is involved
        driver_bookings = list(db.db.bookings.find({'driver_id': ObjectId(request.user_id)}))
        
        parking_spaces = list(db.db.parking_spaces.find({'owner_id': ObjectId(request.user_id)}))
        parking_ids = [p['_id'] for p in parking_spaces]
        owner_bookings = list(db.db.bookings.find({'parking_id': {'$in': parking_ids}}))
        
        all_bookings = driver_bookings + owner_bookings
        booking_ids = [b['_id'] for b in all_bookings]
        
        conversations = []
        seen_bookings = set()
        
        for booking_id in booking_ids:
            if booking_id in seen_bookings:
                continue
            seen_bookings.add(booking_id)
            
            booking = db.db.bookings.find_one({'_id': booking_id})
            parking = db.db.parking_spaces.find_one({'_id': booking['parking_id']})
            
            # Determine other user
            if str(booking['driver_id']) == request.user_id:
                other_user_id = parking['owner_id']
            else:
                other_user_id = booking['driver_id']
            
            other_user = db.db.users.find_one({'_id': other_user_id})
            
            # Get last message
            last_message = db.db.messages.find_one(
                {'booking_id': booking_id},
                sort=[('created_at', -1)]
            )
            
            # Get unread count
            unread_count = db.db.messages.count_documents({
                'booking_id': booking_id,
                'receiver_id': ObjectId(request.user_id),
                'is_read': False
            })
            
            conversations.append({
                'booking_id': str(booking_id),
                'parking_title': parking['title'],
                'other_user': {
                    'id': str(other_user['_id']),
                    'name': other_user['name']
                },
                'last_message': {
                    'content': last_message['content'] if last_message else None,
                    'created_at': last_message['created_at'].isoformat() if last_message else None
                },
                'unread_count': unread_count
            })
        
        return jsonify({
            'conversations': conversations,
            'total': len(conversations)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========== REVIEW ROUTES ==========

@review_bp.route('/create', methods=['POST'])
@token_required
def create_review():
    """Create a review for a parking space"""
    try:
        data = request.get_json()
        
        required_fields = ['booking_id', 'rating', 'comment']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Verify booking
        booking = db.db.bookings.find_one({'_id': ObjectId(data['booking_id'])})
        
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        if str(booking['driver_id']) != request.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if booking['status'] != 'completed':
            return jsonify({'error': 'Can only review completed bookings'}), 400
        
        # Check if already reviewed
        existing_review = db.db.reviews.find_one({
            'booking_id': ObjectId(data['booking_id'])
        })
        
        if existing_review:
            return jsonify({'error': 'Already reviewed this booking'}), 400
        
        # Validate rating
        rating = int(data['rating'])
        if rating < 1 or rating > 5:
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        # Create review
        review = Review(
            parking_id=str(booking['parking_id']),
            reviewer_id=request.user_id,
            booking_id=data['booking_id'],
            rating=rating,
            comment=data['comment']
        )
        
        result = db.db.reviews.insert_one(review.to_dict())
        
        # Notify parking owner
        parking = db.db.parking_spaces.find_one({'_id': booking['parking_id']})
        send_notification_to_user(
            str(parking['owner_id']),
            'New Review',
            f'You received a {rating}-star review for {parking["title"]}',
            'review'
        )
        
        return jsonify({
            'message': 'Review submitted successfully',
            'review_id': str(result.inserted_id)
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@review_bp.route('/parking/<parking_id>', methods=['GET'])
@token_required
def get_parking_reviews(parking_id):
    """Get reviews for a parking space"""
    try:
        reviews = list(db.db.reviews.find({'parking_id': ObjectId(parking_id)}).sort('created_at', -1))
        
        results = []
        for review in reviews:
            reviewer = db.db.users.find_one({'_id': review['reviewer_id']})
            
            results.append({
                'id': str(review['_id']),
                'rating': review['rating'],
                'comment': review['comment'],
                'reviewer': {
                    'name': reviewer['name'],
                    'profile_image': reviewer.get('profile_image')
                },
                'created_at': review['created_at'].isoformat()
            })
        
        # Calculate average rating
        avg_rating = sum(r['rating'] for r in reviews) / len(reviews) if reviews else 0
        
        return jsonify({
            'reviews': results,
            'total': len(results),
            'average_rating': round(avg_rating, 1)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@review_bp.route('/my-reviews', methods=['GET'])
@token_required
def get_my_reviews():
    """Get user's reviews"""
    try:
        reviews = list(db.db.reviews.find({'reviewer_id': ObjectId(request.user_id)}).sort('created_at', -1))
        
        results = []
        for review in reviews:
            parking = db.db.parking_spaces.find_one({'_id': review['parking_id']})
            
            results.append({
                'id': str(review['_id']),
                'parking': {
                    'id': str(parking['_id']),
                    'title': parking['title'],
                    'address': parking['address']
                },
                'rating': review['rating'],
                'comment': review['comment'],
                'created_at': review['created_at'].isoformat()
            })
        
        return jsonify({
            'reviews': results,
            'total': len(results)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
