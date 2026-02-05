from datetime import datetime
from bson import ObjectId
import bcrypt

class User:
    def __init__(self, name, email, phone, password, role='driver'):
        self.name = name
        self.email = email
        self.phone = phone
        self.password = self.hash_password(password)
        self.role = role  # 'driver', 'host', 'admin'
        self.created_at = datetime.utcnow()
        self.is_verified = False
        self.profile_image = None
        self.address = None
    
    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password, hashed):
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def to_dict(self):
        return {
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'password': self.password,
            'role': self.role,
            'created_at': self.created_at,
            'is_verified': self.is_verified,
            'profile_image': self.profile_image,
            'address': self.address
        }

class ParkingSpace:
    def __init__(self, owner_id, title, description, address, location, 
                 vehicle_type, price_per_hour, total_hours, images=None):
        self.owner_id = ObjectId(owner_id)
        self.title = title
        self.description = description
        self.address = address
        self.location = location  # GeoJSON format
        self.vehicle_type = vehicle_type  # '2-wheeler', '4-wheeler', 'both'
        self.price_per_hour = float(price_per_hour)
        self.total_hours = int(total_hours)
        self.min_hours = int(total_hours * 0.7)  # 70% minimum
        self.images = images or []
        self.status = 'pending'  # 'pending', 'approved', 'rejected', 'booked', 'available'
        self.created_at = datetime.utcnow()
        self.features = []
        self.availability_start = None
        self.availability_end = None
    
    def to_dict(self):
        return {
            'owner_id': self.owner_id,
            'title': self.title,
            'description': self.description,
            'address': self.address,
            'location': self.location,
            'vehicle_type': self.vehicle_type,
            'price_per_hour': self.price_per_hour,
            'total_hours': self.total_hours,
            'min_hours': self.min_hours,
            'images': self.images,
            'status': self.status,
            'created_at': self.created_at,
            'features': self.features,
            'availability_start': self.availability_start,
            'availability_end': self.availability_end
        }

class Booking:
    def __init__(self, driver_id, parking_id, start_time, end_time, hours, total_amount):
        self.driver_id = ObjectId(driver_id)
        self.parking_id = ObjectId(parking_id)
        self.start_time = start_time
        self.end_time = end_time
        self.hours = int(hours)
        self.total_amount = float(total_amount)
        self.status = 'pending'  # 'pending', 'confirmed', 'cancelled', 'completed'
        self.payment_status = 'pending'  # 'pending', 'paid', 'refunded'
        self.payment_method = None
        self.created_at = datetime.utcnow()
        self.confirmation_code = None
    
    def to_dict(self):
        return {
            'driver_id': self.driver_id,
            'parking_id': self.parking_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'hours': self.hours,
            'total_amount': self.total_amount,
            'status': self.status,
            'payment_status': self.payment_status,
            'payment_method': self.payment_method,
            'created_at': self.created_at,
            'confirmation_code': self.confirmation_code
        }

class Wallet:
    def __init__(self, user_id, balance=0.0):
        self.user_id = ObjectId(user_id)
        self.balance = float(balance)
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'balance': self.balance,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class Transaction:
    def __init__(self, user_id, amount, transaction_type, payment_method, description):
        self.user_id = ObjectId(user_id)
        self.amount = float(amount)
        self.transaction_type = transaction_type  # 'credit', 'debit'
        self.payment_method = payment_method  # 'razorpay', 'crypto', 'wallet'
        self.description = description
        self.status = 'pending'  # 'pending', 'success', 'failed'
        self.created_at = datetime.utcnow()
        self.payment_id = None
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'amount': self.amount,
            'transaction_type': self.transaction_type,
            'payment_method': self.payment_method,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at,
            'payment_id': self.payment_id
        }

class Message:
    def __init__(self, sender_id, receiver_id, booking_id, content):
        self.sender_id = ObjectId(sender_id)
        self.receiver_id = ObjectId(receiver_id)
        self.booking_id = ObjectId(booking_id)
        self.content = content
        self.is_read = False
        self.created_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'booking_id': self.booking_id,
            'content': self.content,
            'is_read': self.is_read,
            'created_at': self.created_at
        }

class Review:
    def __init__(self, parking_id, reviewer_id, booking_id, rating, comment):
        self.parking_id = ObjectId(parking_id)
        self.reviewer_id = ObjectId(reviewer_id)
        self.booking_id = ObjectId(booking_id)
        self.rating = int(rating)
        self.comment = comment
        self.created_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'parking_id': self.parking_id,
            'reviewer_id': self.reviewer_id,
            'booking_id': self.booking_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at
        }

class Notification:
    def __init__(self, user_id, title, message, notification_type):
        self.user_id = ObjectId(user_id)
        self.title = title
        self.message = message
        self.notification_type = notification_type  # 'booking', 'payment', 'message', 'review'
        self.is_read = False
        self.created_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'is_read': self.is_read,
            'created_at': self.created_at
        }
