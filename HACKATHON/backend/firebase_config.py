"""
Firebase configuration module.
Initializes the Firebase Admin SDK using credentials from environment variables
or a service account key file. Provides access to Firestore.
"""
import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load env variables in case this is run/imported before app.py
load_dotenv()

def initialize_firebase():
    """Initializes the Firebase Admin SDK and returns a Firestore client."""
    # Check if we've already initialized to prevent hot-reload crashes
    if not firebase_admin._apps:
        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
        
        if not service_account_path:
            print("Error: FIREBASE_SERVICE_ACCOUNT_PATH not found in .env.", file=sys.stderr)
            print("Please add it and point it to your Firebase service account JSON file.", file=sys.stderr)
            sys.exit(1)
            
        if not os.path.exists(service_account_path):
            print(f"Error: Firebase service account file not found at path: {service_account_path}", file=sys.stderr)
            sys.exit(1)

        try:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize Firebase Admin SDK: {e}", file=sys.stderr)
            sys.exit(1)
            
    return firestore.client()

# Export a single Firestore instance that other modules can import
db = initialize_firebase()
