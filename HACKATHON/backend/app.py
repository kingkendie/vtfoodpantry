"""
Main entry point for the VT Pantry Flask backend.
Initializes the Flask app, configures CORS, sets up database connections
(Firebase), and registers the various route blueprints (inventory, vendors, export).
"""
import os
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Import blueprints
from routes.inventory import inventory_bp, limiter
from routes.vendors import vendors_bp
from routes.export import export_bp
from routes.auth_routes import auth_bp

app = Flask(__name__)
limiter.init_app(app)

# Enable CORS for all routes
CORS(app)

# Register blueprints
app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
app.register_blueprint(vendors_bp, url_prefix='/api/vendors')
app.register_blueprint(export_bp, url_prefix='/api/export')
app.register_blueprint(auth_bp, url_prefix='/api/auth')

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check route to verify server is running."""
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
