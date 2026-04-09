"""
File: backend/routes/export.py
Description: Data Export capabilities for the VT Pantry backend.
This file connects to the existing Google Sheets API, retrieves all the current 
inventory data from our Firebase database, and cleanly writes it directly into a specific Spreadsheet.
"""
import os
import gspread
from google.oauth2.service_account import Credentials
from flask import Blueprint, jsonify
from firebase_config import db

export_bp = Blueprint('export', __name__)

@export_bp.route('/sheets', methods=['GET'])
def export_to_sheets():
    """
    Route: GET /sheets
    Auth Required: None (Public access endpoint for quick downloads)
    Purpose: Clears out an old targeted Google Spreadsheet and entirely refills it 
             row-by-row with the absolute latest inventory cache right from Firestore.
    Returns: A JSON object tracking exactly how many rows got written successfully.
    """
    try:
        # Load up the paths and IDs necessary to find the Google Sheet securely
        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
        sheet_id = os.getenv('GOOGLE_SHEETS_ID')

        # Check if settings are missing 
        if not service_account_path or not os.path.exists(service_account_path):
            return jsonify({"error": "Service account path is missing or invalid. Check FIREBASE_SERVICE_ACCOUNT_PATH."}), 500

        if not sheet_id:
            return jsonify({"error": "Missing GOOGLE_SHEETS_ID in environment variables."}), 500

        # Define the permission access levels we need (Sheets + Drive combo)
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        # Log into the Google backend using our secure service account file
        credentials = Credentials.from_service_account_file(service_account_path, scopes=scopes)
        gc = gspread.authorize(credentials)

        # Connect directly to the provided spreadsheet
        try:
            workbook = gc.open_by_key(sheet_id)
            sheet = workbook.sheet1
        except Exception as e:
            return jsonify({"error": f"Failed to open Google Sheet: {str(e)}"}), 500

        # Fetch the entire current inventory from Firestore
        items_ref = db.collection('inventory')
        docs = items_ref.stream()

        # Outline the exact column headers the Excel sheet needs
        headers = ["Name", "Vendor", "Category", "Weight", "Units", "Price Type", "Program", "Quantity"]
        
        # Build the initial array of rows, dropping headers in index 0
        rows = [headers]
        for doc in docs:
            data = doc.to_dict()
            # Construct a row, replacing any weird missing data with a blank space
            row = [
                data.get('name', ''),
                data.get('vendor', ''),
                data.get('category', ''),
                data.get('weight', ''),
                data.get('units', ''),
                data.get('price_type', ''),
                data.get('program', ''),
                data.get('quantity', '')
            ]
            rows.append(row)

        # Wipe absolutely everything in the sheet clean so we don't end up duplicating things
        sheet.clear()
        
        # Bulk append the new data rows safely into the sheet
        sheet.append_rows(rows)

        # Count the length to confirm if things moved appropriately
        rows_written = len(rows) - 1

        return jsonify({"success": True, "rows_written": rows_written}), 200

    except Exception as e:
        # Crash safety: surface the string formatted error message directly so nothing breaks completely
        return jsonify({"error": str(e)}), 500
