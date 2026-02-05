import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
from database import db
from models import Notification
from bson import ObjectId

UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 5242880))  # 5MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file, subfolder='general'):
    """Save uploaded image file"""
    if not file or not allowed_file(file.filename):
        return None
    
    # Create upload directory if doesn't exist
    upload_path = os.path.join(UPLOAD_FOLDER, subfolder)
    os.makedirs(upload_path, exist_ok=True)
    
    # Generate unique filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_path, filename)
    
    try:
        # Save and compress image
        image = Image.open(file)
        
        # Resize if too large
        max_size = (1920, 1080)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save with optimization
        image.save(filepath, optimize=True, quality=85)
        
        return f"{subfolder}/{filename}"
    
    except Exception as e:
        print(f"Error saving image: {e}")
        return None

def delete_image(filepath):
    """Delete image file"""
    try:
        full_path = os.path.join(UPLOAD_FOLDER, filepath)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting image: {e}")
        return False

def create_notification(user_id, title, message, notification_type):
    """Create a notification for user"""
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type
        )
        
        result = db.db.notifications.insert_one(notification.to_dict())
        return str(result.inserted_id)
    
    except Exception as e:
        print(f"Error creating notification: {e}")
        return None

def send_notification_to_user(user_id, title, message, notification_type):
    """Send notification to user"""
    return create_notification(user_id, title, message, notification_type)

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in kilometers"""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    distance = R * c
    return distance

def generate_confirmation_code():
    """Generate unique confirmation code"""
    import random
    import string
    
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def validate_trichy_location(latitude, longitude):
    """Validate if location is in Trichy area"""
    # Trichy approximate bounds
    TRICHY_LAT_MIN = 10.7
    TRICHY_LAT_MAX = 10.9
    TRICHY_LON_MIN = 78.6
    TRICHY_LON_MAX = 78.8
    
    return (TRICHY_LAT_MIN <= latitude <= TRICHY_LAT_MAX and 
            TRICHY_LON_MIN <= longitude <= TRICHY_LON_MAX)

# Trichy area locations for reference
TRICHY_AREAS = [
    {"name": "Srirangam", "lat": 10.8650, "lon": 78.6936},
    {"name": "Thillai Nagar", "lat": 10.8055, "lon": 78.6856},
    {"name": "Cantonment", "lat": 10.8225, "lon": 78.6867},
    {"name": "Tennur", "lat": 10.8139, "lon": 78.7047},
    {"name": "K.K. Nagar", "lat": 10.7671, "lon": 78.7005},
    {"name": "Anna Nagar", "lat": 10.8081, "lon": 78.7058},
    {"name": "Woraiyur", "lat": 10.8303, "lon": 78.6972},
    {"name": "Palakarai", "lat": 10.8500, "lon": 78.6794},
    {"name": "Crawford", "lat": 10.8231, "lon": 78.6950},
    {"name": "Salai Road", "lat": 10.8275, "lon": 78.6881}
]
