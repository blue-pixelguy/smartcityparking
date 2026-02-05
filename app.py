import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database to initialize
from database import db

# Import routes
from routes_auth import auth_bp
from routes_parking import parking_bp
from routes_booking import booking_bp
from routes_wallet import wallet_bp
from routes_message_review import message_bp, review_bp
from routes_admin_notification import admin_bp, notification_bp

# Create Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_FILE_SIZE', 5242880))

# Enable CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Create upload folder if doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(parking_bp, url_prefix='/api/parking')
app.register_blueprint(booking_bp, url_prefix='/api/booking')
app.register_blueprint(wallet_bp, url_prefix='/api/wallet')
app.register_blueprint(message_bp, url_prefix='/api/messages')
app.register_blueprint(review_bp, url_prefix='/api/reviews')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(notification_bp, url_prefix='/api/notifications')

# Root route
@app.route('/')
def index():
    return jsonify({
        'message': 'P2P Parking System API',
        'version': '1.0.0',
        'status': 'running'
    })

# Health check route
@app.route('/health')
def health_check():
    try:
        # Check database connection
        db.client.server_info()
        return jsonify({
            'status': 'healthy',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 500

# Serve uploaded files
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({'error': 'File too large'}), 413

if __name__ == '__main__':
    print("=" * 50)
    print("P2P Parking System Starting...")
    print("=" * 50)
    print(f"Environment: {os.getenv('FLASK_ENV')}")
    print(f"Database: {os.getenv('DB_NAME')}")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print("=" * 50)
    print("\nAPI Endpoints:")
    print("Authentication: /api/auth/*")
    print("Parking: /api/parking/*")
    print("Booking: /api/booking/*")
    print("Wallet: /api/wallet/*")
    print("Messages: /api/messages/*")
    print("Reviews: /api/reviews/*")
    print("Admin: /api/admin/*")
    print("Notifications: /api/notifications/*")
    print("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('FLASK_DEBUG', 'True') == 'True'
    )
