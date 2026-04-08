"""
Authentication routes for logging in and registering staff users.
"""
import os
import requests
from flask import Blueprint, request, jsonify
from firebase_admin import auth as firebase_auth
from auth import staff_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login endpoint.
    Accepts: { "email": "...", "password": "..." }
    Returns: { "idToken": "..." }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"error": "Missing email or password"}), 400
            
        web_api_key = os.getenv("FIREBASE_WEB_API_KEY")
        if not web_api_key or web_api_key == "your_web_api_key_here":
            return jsonify({"error": "Firebase Web API Key is not configured."}), 500
            
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={web_api_key}"
        
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        response = requests.post(url, json=payload)
        res_data = response.json()
        
        if response.ok:
            return jsonify({"idToken": res_data.get("idToken")}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/register', methods=['POST'])
@staff_required
def register():
    """
    Register endpoint. Staff only.
    Accepts: { "email": "...", "password": "..." }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"error": "Missing email or password"}), 400
            
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters long."}), 400
            
        user = firebase_auth.create_user(
            email=email,
            password=password
        )
        
        return jsonify({"success": True, "uid": user.uid}), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
