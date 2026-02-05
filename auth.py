import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from bson import ObjectId
from database import db

JWT_SECRET = os.getenv('JWT_SECRET', 'dev-jwt-secret-please-change-in-production')
JWT_ALGORITHM = 'HS256'

def create_token(user_id, role):
    """Create JWT token for user"""
    payload = {
        'user_id': str(user_id),
        'role': role,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def decode_token(token):
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator to require valid token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        payload = decode_token(token)
        
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add user info to request
        request.user_id = payload['user_id']
        request.user_role = payload['role']
        
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        payload = decode_token(token)
        
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        if payload['role'] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        request.user_id = payload['user_id']
        request.user_role = payload['role']
        
        return f(*args, **kwargs)
    
    return decorated

def host_required(f):
    """Decorator to require host role"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        payload = decode_token(token)
        
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        if payload['role'] not in ['host', 'admin']:
            return jsonify({'error': 'Host access required'}), 403
        
        request.user_id = payload['user_id']
        request.user_role = payload['role']
        
        return f(*args, **kwargs)
    
    return decorated