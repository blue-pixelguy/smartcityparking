"""
Web Routes - Serve HTML pages
"""

from flask import Blueprint, render_template, redirect, url_for, session
from functools import wraps

web_bp = Blueprint('web', __name__)

def login_required(f):
    """Decorator to check if user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('web.login'))
        return f(*args, **kwargs)
    return decorated_function

# Public pages
@web_bp.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@web_bp.route('/login')
def login():
    """Login page"""
    return render_template('login.html')

@web_bp.route('/register')
def register():
    """Registration page"""
    return render_template('register.html')

# Protected pages (require login)
@web_bp.route('/dashboard')
def dashboard():
    """User dashboard"""
    return render_template('dashboard.html')

@web_bp.route('/find-parking')
def find_parking():
    """Find parking page"""
    return render_template('find-parking.html')

@web_bp.route('/booking/<parking_id>')
def booking_page(parking_id):
    """Booking page for a specific parking"""
    return render_template('booking.html')

@web_bp.route('/list-space')
def list_space():
    """List your parking space"""
    return render_template('list-space.html')

@web_bp.route('/my-bookings')
def my_bookings():
    """My bookings page"""
    return render_template('my-bookings.html')

@web_bp.route('/booking-requests')
def booking_requests():
    """Booking requests for hosts"""
    return render_template('booking-requests.html')

# Admin pages
@web_bp.route('/secret-admin-panel')
def admin_login():
    """Admin login page"""
    return render_template('admin-login.html')

@web_bp.route('/admin')
def admin_dashboard():
    """Admin dashboard"""
    return render_template('admin.html')

# Logout
@web_bp.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('web.index'))
