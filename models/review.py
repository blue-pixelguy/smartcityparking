"""
Review Model
"""

from datetime import datetime
from bson import ObjectId

class Review:
    """Review model for parking spaces"""
    
    @staticmethod
    def create(db, user_id, parking_id, data):
        """Create a new review"""
        review = {
            'user_id': ObjectId(user_id),
            'parking_id': ObjectId(parking_id),
            'rating': data.get('rating'),
            'comment': data.get('comment', ''),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Validate rating
        if not review['rating'] or review['rating'] < 1 or review['rating'] > 5:
            raise ValueError('Rating must be between 1 and 5')
        
        result = db.reviews.insert_one(review)
        
        # Update parking space average rating
        Review.update_parking_rating(db, parking_id)
        
        return result.inserted_id
    
    @staticmethod
    def update_parking_rating(db, parking_id):
        """Update average rating for a parking space"""
        reviews = list(db.reviews.find({'parking_id': ObjectId(parking_id)}))
        
        if reviews:
            avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
            db.parking_spaces.update_one(
                {'_id': ObjectId(parking_id)},
                {
                    '$set': {
                        'average_rating': round(avg_rating, 2),
                        'total_reviews': len(reviews),
                        'updated_at': datetime.utcnow()
                    }
                }
            )
    
    @staticmethod
    def get_by_parking(db, parking_id, limit=None):
        """Get reviews for a parking space"""
        query = {'parking_id': ObjectId(parking_id)}
        cursor = db.reviews.find(query).sort('created_at', -1)
        
        if limit:
            cursor = cursor.limit(limit)
        
        return list(cursor)
    
    @staticmethod
    def get_by_user(db, user_id):
        """Get reviews by a user"""
        return list(db.reviews.find({'user_id': ObjectId(user_id)}).sort('created_at', -1))
    
    @staticmethod
    def get_by_id(db, review_id):
        """Get a review by ID"""
        return db.reviews.find_one({'_id': ObjectId(review_id)})
    
    @staticmethod
    def update(db, review_id, data):
        """Update a review"""
        update_data = {
            'updated_at': datetime.utcnow()
        }
        
        if 'rating' in data:
            if data['rating'] < 1 or data['rating'] > 5:
                raise ValueError('Rating must be between 1 and 5')
            update_data['rating'] = data['rating']
        
        if 'comment' in data:
            update_data['comment'] = data['comment']
        
        result = db.reviews.update_one(
            {'_id': ObjectId(review_id)},
            {'$set': update_data}
        )
        
        # Update parking space rating
        review = Review.get_by_id(db, review_id)
        if review:
            Review.update_parking_rating(db, str(review['parking_id']))
        
        return result.modified_count > 0
    
    @staticmethod
    def delete(db, review_id):
        """Delete a review"""
        review = Review.get_by_id(db, review_id)
        if not review:
            return False
        
        parking_id = str(review['parking_id'])
        
        result = db.reviews.delete_one({'_id': ObjectId(review_id)})
        
        # Update parking space rating
        if result.deleted_count > 0:
            Review.update_parking_rating(db, parking_id)
        
        return result.deleted_count > 0
    
    @staticmethod
    def user_has_reviewed(db, user_id, parking_id):
        """Check if a user has already reviewed a parking space"""
        review = db.reviews.find_one({
            'user_id': ObjectId(user_id),
            'parking_id': ObjectId(parking_id)
        })
        return review is not None
    
    @staticmethod
    def to_dict(review):
        """Convert review to dictionary"""
        return {
            'id': str(review['_id']),
            'user_id': str(review['user_id']),
            'parking_id': str(review['parking_id']),
            'rating': review['rating'],
            'comment': review.get('comment', ''),
            'created_at': review['created_at'].isoformat(),
            'updated_at': review['updated_at'].isoformat()
        }
