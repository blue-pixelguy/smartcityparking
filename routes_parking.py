from flask import Blueprint, request, jsonify
from database import db
from models import ParkingSpace
from auth import token_required, host_required
from bson import ObjectId
from datetime import datetime
from utils import save_image, validate_trichy_location, send_notification_to_user

parking_bp = Blueprint('parking', __name__)

@parking_bp.route('/list', methods=['POST'])
@host_required
def create_parking():
    """Create parking space listing"""
    try:
        data = request.form.to_dict()
        
        # Validate required fields
        required_fields = ['title', 'description', 'address', 'latitude', 'longitude', 
                          'vehicle_type', 'price_per_hour', 'total_hours']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        
        # Validate Trichy location
        if not validate_trichy_location(latitude, longitude):
            return jsonify({'error': 'Location must be within Trichy area'}), 400
        
        # Handle image uploads
        images = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files[:5]:  # Max 5 images
                image_path = save_image(file, 'parking')
                if image_path:
                    images.append(image_path)
        
        # Create parking space
        parking = ParkingSpace(
            owner_id=request.user_id,
            title=data['title'],
            description=data['description'],
            address=data['address'],
            location={
                'type': 'Point',
                'coordinates': [longitude, latitude]
            },
            vehicle_type=data['vehicle_type'],
            price_per_hour=float(data['price_per_hour']),
            total_hours=int(data['total_hours']),
            images=images
        )
        
        if 'features' in data:
            parking.features = data['features'].split(',')
        
        if 'availability_start' in data:
            parking.availability_start = datetime.fromisoformat(data['availability_start'])
        
        if 'availability_end' in data:
            parking.availability_end = datetime.fromisoformat(data['availability_end'])
        
        result = db.db.parking_spaces.insert_one(parking.to_dict())
        
        return jsonify({
            'message': 'Parking space listed successfully',
            'parking_id': str(result.inserted_id),
            'status': 'pending'
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@parking_bp.route('/search', methods=['POST'])
@token_required
def search_parking():
    """Search parking spaces"""
    try:
        data = request.get_json()
        
        query = {'status': 'approved'}
        
        # Location-based search
        if 'latitude' in data and 'longitude' in data:
            radius = data.get('radius', 5000)  # Default 5km
            
            query['location'] = {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': [float(data['longitude']), float(data['latitude'])]
                    },
                    '$maxDistance': radius
                }
            }
        
        # Vehicle type filter
        if 'vehicle_type' in data:
            query['vehicle_type'] = {'$in': [data['vehicle_type'], 'both']}
        
        # Price range filter
        if 'min_price' in data:
            query['price_per_hour'] = {'$gte': float(data['min_price'])}
        
        if 'max_price' in data:
            if 'price_per_hour' in query:
                query['price_per_hour']['$lte'] = float(data['max_price'])
            else:
                query['price_per_hour'] = {'$lte': float(data['max_price'])}
        
        # Get results
        parking_spaces = list(db.db.parking_spaces.find(query).limit(50))
        
        # Format results
        results = []
        for space in parking_spaces:
            owner = db.db.users.find_one({'_id': space['owner_id']})
            
            # Calculate average rating
            reviews = list(db.db.reviews.find({'parking_id': space['_id']}))
            avg_rating = sum(r['rating'] for r in reviews) / len(reviews) if reviews else 0
            
            results.append({
                'id': str(space['_id']),
                'title': space['title'],
                'description': space['description'],
                'address': space['address'],
                'location': {
                    'latitude': space['location']['coordinates'][1],
                    'longitude': space['location']['coordinates'][0]
                },
                'vehicle_type': space['vehicle_type'],
                'price_per_hour': space['price_per_hour'],
                'total_hours': space['total_hours'],
                'min_hours': space['min_hours'],
                'images': space['images'],
                'features': space.get('features', []),
                'owner': {
                    'id': str(owner['_id']),
                    'name': owner['name'],
                    'phone': owner['phone']
                },
                'rating': round(avg_rating, 1),
                'total_reviews': len(reviews)
            })
        
        return jsonify({
            'results': results,
            'total': len(results)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@parking_bp.route('/<parking_id>', methods=['GET'])
@token_required
def get_parking_details(parking_id):
    """Get parking space details"""
    try:
        parking = db.db.parking_spaces.find_one({'_id': ObjectId(parking_id)})
        
        if not parking:
            return jsonify({'error': 'Parking space not found'}), 404
        
        owner = db.db.users.find_one({'_id': parking['owner_id']})
        
        # Get reviews
        reviews = list(db.db.reviews.find({'parking_id': ObjectId(parking_id)}))
        avg_rating = sum(r['rating'] for r in reviews) / len(reviews) if reviews else 0
        
        review_list = []
        for review in reviews:
            reviewer = db.db.users.find_one({'_id': review['reviewer_id']})
            review_list.append({
                'rating': review['rating'],
                'comment': review['comment'],
                'reviewer_name': reviewer['name'],
                'created_at': review['created_at'].isoformat()
            })
        
        return jsonify({
            'id': str(parking['_id']),
            'title': parking['title'],
            'description': parking['description'],
            'address': parking['address'],
            'location': {
                'latitude': parking['location']['coordinates'][1],
                'longitude': parking['location']['coordinates'][0]
            },
            'vehicle_type': parking['vehicle_type'],
            'price_per_hour': parking['price_per_hour'],
            'total_hours': parking['total_hours'],
            'min_hours': parking['min_hours'],
            'images': parking['images'],
            'features': parking.get('features', []),
            'status': parking['status'],
            'availability_start': parking.get('availability_start').isoformat() if parking.get('availability_start') else None,
            'availability_end': parking.get('availability_end').isoformat() if parking.get('availability_end') else None,
            'owner': {
                'id': str(owner['_id']),
                'name': owner['name'],
                'phone': owner['phone'],
                'email': owner['email']
            },
            'rating': round(avg_rating, 1),
            'total_reviews': len(reviews),
            'reviews': review_list
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@parking_bp.route('/my-listings', methods=['GET'])
@host_required
def get_my_listings():
    """Get host's parking listings"""
    try:
        parking_spaces = list(db.db.parking_spaces.find({'owner_id': ObjectId(request.user_id)}))
        
        results = []
        for space in parking_spaces:
            # Count bookings
            bookings_count = db.db.bookings.count_documents({'parking_id': space['_id']})
            
            results.append({
                'id': str(space['_id']),
                'title': space['title'],
                'address': space['address'],
                'vehicle_type': space['vehicle_type'],
                'price_per_hour': space['price_per_hour'],
                'status': space['status'],
                'total_bookings': bookings_count,
                'created_at': space['created_at'].isoformat()
            })
        
        return jsonify({
            'listings': results,
            'total': len(results)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@parking_bp.route('/<parking_id>', methods=['PUT'])
@host_required
def update_parking(parking_id):
    """Update parking space"""
    try:
        parking = db.db.parking_spaces.find_one({'_id': ObjectId(parking_id)})
        
        if not parking:
            return jsonify({'error': 'Parking space not found'}), 404
        
        if str(parking['owner_id']) != request.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        update_fields = {}
        allowed_fields = ['title', 'description', 'price_per_hour', 'features']
        
        for field in allowed_fields:
            if field in data:
                update_fields[field] = data[field]
        
        if update_fields:
            db.db.parking_spaces.update_one(
                {'_id': ObjectId(parking_id)},
                {'$set': update_fields}
            )
        
        return jsonify({'message': 'Parking space updated successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@parking_bp.route('/<parking_id>', methods=['DELETE'])
@host_required
def delete_parking(parking_id):
    """Delete parking space"""
    try:
        parking = db.db.parking_spaces.find_one({'_id': ObjectId(parking_id)})
        
        if not parking:
            return jsonify({'error': 'Parking space not found'}), 404
        
        if str(parking['owner_id']) != request.user_id and request.user_role != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Check for active bookings
        active_bookings = db.db.bookings.count_documents({
            'parking_id': ObjectId(parking_id),
            'status': {'$in': ['pending', 'confirmed']}
        })
        
        if active_bookings > 0:
            return jsonify({'error': 'Cannot delete parking with active bookings'}), 400
        
        db.db.parking_spaces.delete_one({'_id': ObjectId(parking_id)})
        
        return jsonify({'message': 'Parking space deleted successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
