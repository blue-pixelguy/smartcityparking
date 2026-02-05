from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import routes
from routes import auth, slots, bookings, users

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Enable CORS
CORS(app)

# Register blueprints
app.register_blueprint(auth.bp, url_prefix='/api/auth')
app.register_blueprint(slots.bp, url_prefix='/api/slots')
app.register_blueprint(bookings.bp, url_prefix='/api/bookings')
app.register_blueprint(users.bp, url_prefix='/api/users')

# Routes
@app.route('/')
def index():
    """Homepage"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    return render_template('dashboard.html')

# API Status endpoint
@app.route('/api/status')
def api_status():
    """Check API status"""
    from config.database import db
    
    db_status = "connected" if db.get_db() is not None else "disconnected"
    
    return jsonify({
        'status': 'ok',
        'message': 'Parking Management API is running',
        'database': db_status,
        'version': '1.0.0'
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    print('=' * 60)
    print('  PARKING MANAGEMENT SYSTEM')
    print('=' * 60)
    print(f'\n🚀 Server starting...')
    print(f'   URL: http://localhost:{port}')
    print(f'   API: http://localhost:{port}/api/status')
    print(f'   Debug: {debug}')
    print('\n' + '=' * 60 + '\n')
    
    app.run(host=host, port=port, debug=debug)
