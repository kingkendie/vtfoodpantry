"""
File: backend/routes/auth_routes.py
Description: Authentication logic for the Pantry backend.
This file contains the endpoints used for logging in staff members and 
creating new staff accounts securely using Google Firebase Auth.
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
    Route: POST /login
    Auth Required: None (This is the route where you get authorized!)
    Purpose: Accepts an email and password, sends it to Google Firebase, and if valid,
             returns a secure 'idToken' that the frontend can use as a digital VIP pass.
    Returns: JSON containing {"idToken": "<long string>"} on success, or an error message on failure.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        email = data.get('email')
        password = data.get('password')
        
        # Verify both fields were actually sent
        if not email or not password:
            return jsonify({"error": "Missing email or password"}), 400
            
        # Get the secret API key used to communicate with Google's login servers
        web_api_key = os.getenv("FIREBASE_WEB_API_KEY")
        if not web_api_key or web_api_key == "your_web_api_key_here":
            return jsonify({"error": "Firebase Web API Key is not configured."}), 500
            
        # Call Google's Identity Service directly
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={web_api_key}"
        
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        # Execute the check and read Google's response
        response = requests.post(url, json=payload)
        res_data = response.json()
        
        # If Google says 'OK', forward the secure token back to the frontend
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
    Route: POST /register
    Auth Required: YES (Staff Only)
    Purpose: Creates a brand new Staff account with a given email and password.
             A regular person cannot create an account; only an existing staff member
             can trigger this route for a new hire.
    Returns: JSON containing {"success": True, "uid": "<new user ID>"}
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        email = data.get('email')
        password = data.get('password')
        
        # Verify inputs are present
        if not email or not password:
            return jsonify({"error": "Missing email or password"}), 400
            
        # Enforce basic security standards
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters long."}), 400
            
        # Create an official new database administrator account inside Firebase
        user = firebase_auth.create_user(
            email=email,
            password=password
        )
        
        return jsonify({"success": True, "uid": user.uid}), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
