"""
File: backend/app.py
Description: Main entry point for the VT Pantry Flask backend architecture.
It initializes the Flask application framework, configures Cross-Origin Resource Sharing (CORS) 
so that our frontend can securely talk to the API, and binds all routing blueprints 
(inventory, vendors, export, authentication) to their respective URL prefixes.
Outputs: A globally exposed Flask 'app' object running locally on port 5000.
"""
import os
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

# Load local environment configuration (API keys, service paths, etc)
load_dotenv()

# Import routing modules containing all the endpoint definitions
from routes.inventory import inventory_bp, limiter
from routes.vendors import vendors_bp
from routes.export import export_bp
from routes.auth_routes import auth_bp

# Initialize the core application 
app = Flask(__name__)

# Bind the rate-limiter system to the main application to handle traffic spikes properly
limiter.init_app(app)

# Allow Cross-Origin requests so the standalone HTML frontend can reach this backend
CORS(app)

# Map our imported routing logic (blueprints) to standard URL endpoints
app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
app.register_blueprint(vendors_bp, url_prefix='/api/vendors')
app.register_blueprint(export_bp, url_prefix='/api/export')
app.register_blueprint(auth_bp, url_prefix='/api/auth')

@app.route('/health', methods=['GET'])
def health_check():
    """
    Route: GET /health
    Auth Required: None (Public)
    Purpose: A basic network probe to ensure the backend is alive and listening.
    Returns: A simple JSON structure {"status": "ok"} with an HTTP 200 code.
    """
    # Return a basic status indicator to confirm uptime to any clients checking
    return jsonify({"status": "ok"}), 200

# Start the Flask web server automatically if this script is executed
if __name__ == '__main__':
    # Launch in development mode on localhost port 5000
    app.run(debug=True, port=5000)
