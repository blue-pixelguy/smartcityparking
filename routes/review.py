"""
Review Routes
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.review import Review
from models.booking import Booking
from models.user import User

review_bp = Blueprint('review', __name__)

@review_bp.route('/create', methods=['POST'])
@jwt_required()
def create_review():
    """Create a review for a parking space"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if 'parking_id' not in data or 'rating' not in data:
            return jsonify({'error': 'parking_id and rating are required'}), 400
        
        parking_id = data['parking_id']
        
        # Check if user has already reviewed this parking space
        if Review.user_has_reviewed(current_app.db, user_id, parking_id):
            return jsonify({'error': 'You have already reviewed this parking space'}), 400
        
        # Verify user has completed a booking at this parking space
        completed_booking = current_app.db.bookings.find_one({
            'user_id': user_id,
            'parking_id': parking_id,
            'status': 'completed'
        })
        
        if not completed_booking:
            return jsonify({'error': 'You can only review parking spaces you have used'}), 403
        
        # Create review
        review_id = Review.create(current_app.db, user_id, parking_id, data)
        
        # Get created review
        review = Review.get_by_id(current_app.db, str(review_id))
        
        return jsonify({
            'message': 'Review created successfully',
            'review': Review.to_dict(review)
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to create review', 'details': str(e)}), 500

@review_bp.route('/parking/<parking_id>', methods=['GET'])
def get_parking_reviews(parking_id):
    """Get all reviews for a parking space"""
    try:
        limit = request.args.get('limit', type=int)
        
        reviews = Review.get_by_parking(current_app.db, parking_id, limit)
        
        # Get user details for each review
        reviews_with_users = []
        for review in reviews:
            user = User.get_by_id(current_app.db, str(review['user_id']))
            review_dict = Review.to_dict(review)
            review_dict['user'] = {
                'id': str(user['_id']),
                'name': user['name'],
                'profile_image': user.get('profile_image')
            }
            reviews_with_users.append(review_dict)
        
        return jsonify({
            'count': len(reviews_with_users),
            'reviews': reviews_with_users
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get reviews', 'details': str(e)}), 500

@review_bp.route('/my-reviews', methods=['GET'])
@jwt_required()
def get_my_reviews():
    """Get all reviews written by the current user"""
    try:
        user_id = get_jwt_identity()
        
        reviews = Review.get_by_user(current_app.db, user_id)
        
        return jsonify({
            'count': len(reviews),
            'reviews': [Review.to_dict(r) for r in reviews]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get reviews', 'details': str(e)}), 500

@review_bp.route('/<review_id>', methods=['PUT'])
@jwt_required()
def update_review(review_id):
    """Update a review"""
    try:
        user_id = get_jwt_identity()
        
        # Check if review exists and belongs to user
        review = Review.get_by_id(current_app.db, review_id)
        if not review:
            return jsonify({'error': 'Review not found'}), 404
        
        if str(review['user_id']) != user_id:
            return jsonify({'error': 'You do not have permission to update this review'}), 403
        
        data = request.get_json()
        
        # Update review
        Review.update(current_app.db, review_id, data)
        
        # Get updated review
        updated_review = Review.get_by_id(current_app.db, review_id)
        
        return jsonify({
            'message': 'Review updated successfully',
            'review': Review.to_dict(updated_review)
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to update review', 'details': str(e)}), 500

@review_bp.route('/<review_id>', methods=['DELETE'])
@jwt_required()
def delete_review(review_id):
    """Delete a review"""
    try:
        user_id = get_jwt_identity()
        
        # Check if review exists and belongs to user
        review = Review.get_by_id(current_app.db, review_id)
        if not review:
            return jsonify({'error': 'Review not found'}), 404
        
        if str(review['user_id']) != user_id:
            return jsonify({'error': 'You do not have permission to delete this review'}), 403
        
        # Delete review
        Review.delete(current_app.db, review_id)
        
        return jsonify({
            'message': 'Review deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to delete review', 'details': str(e)}), 500

@review_bp.route('/<review_id>', methods=['GET'])
def get_review(review_id):
    """Get a specific review by ID"""
    try:
        review = Review.get_by_id(current_app.db, review_id)
        
        if not review:
            return jsonify({'error': 'Review not found'}), 404
        
        # Get user details
        user = User.get_by_id(current_app.db, str(review['user_id']))
        review_dict = Review.to_dict(review)
        review_dict['user'] = {
            'id': str(user['_id']),
            'name': user['name'],
            'profile_image': user.get('profile_image')
        }
        
        return jsonify({
            'review': review_dict
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get review', 'details': str(e)}), 500
