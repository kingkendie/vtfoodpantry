"""
Routes for export functionality.
Handles exporting inventory data to Google Sheets using gspread.
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
    Pulls all inventory items from Firestore and writes them to a Google Sheet.
    Clears the sheet first to avoid duplicates.
    """
    try:
        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
        sheet_id = os.getenv('GOOGLE_SHEETS_ID')

        if not service_account_path or not os.path.exists(service_account_path):
            return jsonify({"error": "Service account path is missing or invalid. Check FIREBASE_SERVICE_ACCOUNT_PATH."}), 500

        if not sheet_id:
            return jsonify({"error": "Missing GOOGLE_SHEETS_ID in environment variables."}), 500

        # Scope for Google Sheets API and Google Drive API
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        # Authenticate using the same service account file as Firebase
        credentials = Credentials.from_service_account_file(service_account_path, scopes=scopes)
        gc = gspread.authorize(credentials)

        # Open the specific Google Sheet by ID
        try:
            workbook = gc.open_by_key(sheet_id)
            sheet = workbook.sheet1
        except Exception as e:
            return jsonify({"error": f"Failed to open Google Sheet: {str(e)}"}), 500

        # Fetch inventory from Firestore
        items_ref = db.collection('inventory')
        docs = items_ref.stream()

        # Define headers
        headers = ["Name", "Vendor", "Category", "Weight", "Units", "Price Type", "Program", "Quantity"]
        
        # Build rows
        rows = [headers]
        for doc in docs:
            data = doc.to_dict()
            # Handle potential None values gracefully
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

        # Clear the sheet and update with new data
        sheet.clear()
        # use append_rows which is safely supported across most gspread versions without syntax warnings
        sheet.append_rows(rows)

        # Number of inventory items written (excluding the header row)
        rows_written = len(rows) - 1

        return jsonify({"success": True, "rows_written": rows_written}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

