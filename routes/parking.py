"""
Parking Space Routes
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.parking import ParkingSpace
from models.user import User
from models.review import Review
from models.database import db as database
from werkzeug.utils import secure_filename
import os
import uuid

parking_bp = Blueprint('parking', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@parking_bp.route('/create', methods=['POST'])
@jwt_required()
def create_parking():
    """Create a new parking space listing"""
    try:
        user_id = get_jwt_identity()
        
        # Verify database is initialized
        if database.db is None:
            return jsonify({'error': 'Database not initialized. Please contact support.'}), 500
        
        # Verify user exists
        user = User.get_by_id(database, user_id)
        
        if not user:
            return jsonify({
                'error': 'User not found. Your session may have expired. Please log in again.'
            }), 404
        
        # Any user can list a parking space (become a host)
        data = request.get_json()
        
        # Log the received data for debugging
        print(f"Received parking data: {data}")
        
        # Validate required fields
        required_fields = ['title', 'address', 'latitude', 'longitude', 
                          'price_per_hour', 'total_hours', 'available_from', 'available_to']
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Create parking space
        parking_id = ParkingSpace.create(database, user_id, data)
        
        # Get created parking space
        parking = ParkingSpace.get_by_id(database, str(parking_id))
        
        return jsonify({
            'message': 'Parking space created successfully. Pending admin approval.',
            'parking': ParkingSpace.to_dict(parking)
        }), 201
        
    except ValueError as e:
        print(f"ValueError in parking creation: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Exception in parking creation: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to create parking space: {str(e)}'}), 500

@parking_bp.route('/upload-image', methods=['POST'])
@jwt_required()
def upload_image():
    """Upload parking space image"""
    try:
        user_id = get_jwt_identity()
        
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif'}), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save file
        file.save(filepath)
        
        # Return file URL
        file_url = f"/static/uploads/{unique_filename}"
        
        return jsonify({
            'message': 'Image uploaded successfully',
            'url': file_url
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to upload image', 'details': str(e)}), 500

@parking_bp.route('/search', methods=['GET'])
def search_parking():
    """Search parking spaces with filters"""
    try:
        filters = {
            'city': request.args.get('city'),  # Add city filter
            'latitude': request.args.get('latitude'),
            'longitude': request.args.get('longitude'),
            'radius': request.args.get('radius', 5000),  # Default 5km
            'vehicle_type': request.args.get('vehicle_type'),
            'max_price': request.args.get('max_price'),
            'start_time': request.args.get('start_time'),
            'end_time': request.args.get('end_time'),
            'limit': int(request.args.get('limit', 50))
        }
        
        parking_spaces = ParkingSpace.search(database, filters)
        
        # Add remaining hours calculation for each parking space
        from datetime import datetime
        import pytz
        
        # Use IST timezone
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        
        spaces_with_time = []
        for p in parking_spaces:
            space_dict = ParkingSpace.to_dict(p)
            
            # Calculate remaining hours from now until available_to
            available_to = p['available_to']
            
            # If available_to is naive (no timezone), assume it's IST
            if available_to.tzinfo is None:
                available_to = ist.localize(available_to)
            else:
                # Convert to IST if it has a different timezone
                available_to = available_to.astimezone(ist)
            
            # Make current_time offset-aware if needed for comparison
            if current_time.tzinfo is None:
                current_time = ist.localize(current_time)
            
            if available_to > current_time:
                remaining_seconds = (available_to - current_time).total_seconds()
                remaining_hours = max(0, remaining_seconds / 3600)
                space_dict['remaining_hours'] = round(remaining_hours, 1)
                space_dict['min_booking_hours'] = round(remaining_hours * 0.7, 1)
            else:
                # Expired parking (shouldn't happen due to search filter, but safety check)
                space_dict['remaining_hours'] = 0
                space_dict['min_booking_hours'] = 0
            
            spaces_with_time.append(space_dict)
        
        return jsonify({
            'count': len(spaces_with_time),
            'parking_spaces': spaces_with_time
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Search failed', 'details': str(e)}), 500

@parking_bp.route('/<parking_id>', methods=['GET'])
def get_parking_details(parking_id):
    """Get parking space details"""
    try:
        print(f"Fetching parking details for ID: {parking_id}")
        
        # Validate parking_id format
        from bson.objectid import ObjectId
        from bson.errors import InvalidId
        
        try:
            ObjectId(parking_id)
        except (InvalidId, TypeError) as e:
            print(f"Invalid parking ID format: {parking_id}")
            return jsonify({'error': 'Invalid parking ID format'}), 400
        
        parking = ParkingSpace.get_by_id(database, parking_id)
        
        if not parking:
            print(f"Parking space not found: {parking_id}")
            return jsonify({'error': 'Parking space not found'}), 404
        
        print(f"Parking found: {parking.get('title', 'N/A')}")
        
        # Get owner details
        try:
            owner = User.get_by_id(database, str(parking['owner_id']))
            if not owner:
                print(f"Owner not found for parking: {parking_id}")
                return jsonify({'error': 'Parking owner not found'}), 404
        except Exception as e:
            print(f"Error fetching owner: {str(e)}")
            return jsonify({'error': 'Failed to fetch owner details', 'details': str(e)}), 500
        
        # Get reviews (non-critical, can fail gracefully)
        try:
            reviews = Review.get_by_parking(database, parking_id, limit=10)
        except Exception as e:
            print(f"Error fetching reviews (non-critical): {str(e)}")
            reviews = []
        
        response_data = {
            'parking': ParkingSpace.to_dict(parking),
            'owner': {
                'id': str(owner['_id']),
                'name': owner['name'],
                'email': owner['email']
            },
            'reviews': [Review.to_dict(r) for r in reviews]
        }
        
        # Add remaining hours calculation
        from datetime import datetime
        import pytz
        
        # Use IST timezone
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        available_to = parking['available_to']
        
        # If available_to is naive (no timezone), assume it's IST
        if available_to.tzinfo is None:
            available_to = ist.localize(available_to)
        else:
            # Convert to IST if it has a different timezone
            available_to = available_to.astimezone(ist)
        
        # Make current_time offset-aware if needed for comparison
        if current_time.tzinfo is None:
            current_time = ist.localize(current_time)
        
        if available_to > current_time:
            remaining_seconds = (available_to - current_time).total_seconds()
            remaining_hours = max(0, remaining_seconds / 3600)
            response_data['parking']['remaining_hours'] = round(remaining_hours, 1)
            response_data['parking']['min_booking_hours'] = round(remaining_hours * 0.7, 1)
        else:
            response_data['parking']['remaining_hours'] = 0
            response_data['parking']['min_booking_hours'] = 0
        
        print(f"Successfully returning parking details for: {parking_id}")
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"Unexpected error in get_parking_details: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get parking details', 'details': str(e)}), 500

@parking_bp.route('/my-listings', methods=['GET'])
@jwt_required()
def get_my_listings():
    """Get user's parking listings"""
    try:
        user_id = get_jwt_identity()
        status = request.args.get('status')
        
        parking_spaces = ParkingSpace.get_by_owner(database, user_id, status)
        
        return jsonify({
            'count': len(parking_spaces),
            'parking_spaces': [ParkingSpace.to_dict(p) for p in parking_spaces]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get listings', 'details': str(e)}), 500

@parking_bp.route('/<parking_id>', methods=['PUT'])
@jwt_required()
def update_parking(parking_id):
    """Update parking space"""
    try:
        user_id = get_jwt_identity()
        
        # Check if user owns this parking space
        parking = ParkingSpace.get_by_id(database, parking_id)
        if not parking:
            return jsonify({'error': 'Parking space not found'}), 404
        
        if str(parking['owner_id']) != user_id:
            return jsonify({'error': 'You do not have permission to update this parking space'}), 403
        
        data = request.get_json()
        
        # Update parking space
        ParkingSpace.update(database, parking_id, data)
        
        # Get updated parking space
        updated_parking = ParkingSpace.get_by_id(database, parking_id)
        
        return jsonify({
            'message': 'Parking space updated successfully',
            'parking': ParkingSpace.to_dict(updated_parking)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to update parking space', 'details': str(e)}), 500

@parking_bp.route('/<parking_id>', methods=['DELETE'])
@jwt_required()
def delete_parking(parking_id):
    """Delete/deactivate parking space"""
    try:
        user_id = get_jwt_identity()
        
        # Check if user owns this parking space
        parking = ParkingSpace.get_by_id(database, parking_id)
        if not parking:
            return jsonify({'error': 'Parking space not found'}), 404
        
        if str(parking['owner_id']) != user_id:
            return jsonify({'error': 'You do not have permission to delete this parking space'}), 403
        
        # Deactivate instead of delete
        ParkingSpace.update_status(database, parking_id, 'inactive')
        
        return jsonify({
            'message': 'Parking space deactivated successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to delete parking space', 'details': str(e)}), 500

@parking_bp.route('/<parking_id>/reviews', methods=['GET'])
def get_parking_reviews(parking_id):
    """Get reviews for a parking space"""
    try:
        reviews = Review.get_by_parking(database, parking_id)
        
        # Get user details for each review
        reviews_with_users = []
        for review in reviews:
            user = User.get_by_id(database, str(review['user_id']))
            review_dict = Review.to_dict(review)
            review_dict['user'] = {
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
