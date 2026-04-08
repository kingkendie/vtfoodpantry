"""
Authentication module for the VT Pantry backend.
Provides functions and decorators to verify Firebase Authentication tokens
for protected routes.
"""
from functools import wraps
from flask import request, jsonify
from firebase_admin import auth

def verify_staff_token(req):
    """
    Reads the Authorization header from the request and verifies the Firebase ID token.
    Throws an exception if the token is missing, malformed, or invalid.
    """
    auth_header = req.headers.get('Authorization')
    if not auth_header:
        raise ValueError("Missing Authorization header")
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise ValueError("Invalid Authorization header format. Expected 'Bearer <token>'")
    
    token = parts[1]
    
    # Verify the token using Firebase Admin SDK
    # Note: firebase_admin must be initialized before this is called
    decoded_token = auth.verify_id_token(token)
    return decoded_token

def staff_required(f):
    """
    Decorator for routes that require a valid staff login.
    Returns a 401 Unauthorized JSON response if the token is invalid or missing.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Verify the token on incoming request
            verify_staff_token(request)
        except Exception as e:
            return jsonify({"error": "Unauthorized"}), 401
            
        return f(*args, **kwargs)
        
    return decorated_function
