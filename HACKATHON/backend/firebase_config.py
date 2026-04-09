"""
File: backend/firebase_config.py
Description: Firebase database configuration module.
This file is responsible for initializing the Google Firebase interface so the 
backend can talk to our cloud database. It loads security credentials from the server,
authenticates with Google securely, and returns a 'database instance' (Firestore)
so the rest of our routes can easily request and store pantry data.
"""
import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load security variables (like passwords and paths) directly from the environment
load_dotenv()

def initialize_firebase():
    """
    Function: initialize_firebase
    Purpose: Safely logs the backend server into Firebase using the secret service account.
    Returns: An active Firestore reference connection that can be used to query data.
    """
    # Prevent the database from reconnecting a second time if the server reloads randomly
    if not firebase_admin._apps:
        # Step 1: Look up the path to our secret Google JSON credentials Key
        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
        
        # Security Check: Stop the server immediately if the password file is completely missing
        if not service_account_path:
            print("Error: FIREBASE_SERVICE_ACCOUNT_PATH not found in .env.", file=sys.stderr)
            print("Please add it and point it to your Firebase service account JSON file.", file=sys.stderr)
            sys.exit(1)
            
        # Security Check: Stop the server if the file doesn't actually exist strictly on disk
        if not os.path.exists(service_account_path):
            print(f"Error: Firebase service account file not found at path: {service_account_path}", file=sys.stderr)
            sys.exit(1)

        # Step 2: Attempt standard login directly against the Google Servers
        try:
            # Package the key and attempt the connection!
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully.")
        except Exception as e:
            # If the servers reject us, freeze the app cleanly to avoid confusing errors downstream
            print(f"Failed to initialize Firebase Admin SDK: {e}", file=sys.stderr)
            sys.exit(1)
            
    # Step 3: Return the specific database component (Firestore) ready to handle queries
    return firestore.client()

# Globally expose a 'db' variable so routes can just import 'db' and use it!
db = initialize_firebase()
