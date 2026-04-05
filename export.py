"""
Routes for export functionality.
Handles exporting inventory data to Google Sheets using gspread.
"""
from flask import Blueprint

export_bp = Blueprint('export', __name__)
