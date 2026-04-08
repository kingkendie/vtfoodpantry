"""
File: backend/routes/vendors.py
Description: Supplier & Partner Management endpoints.
This file tracks all the logistics surrounding *where* the pantry food comes from.
It handles creating/viewing vendor profiles (like local farms or grocery chains) 
and securely storing digital invoices attached to those specific vendors.
"""
from flask import Blueprint, request, jsonify
from firebase_config import db
from auth import staff_required

vendors_bp = Blueprint('vendors', __name__)

@vendors_bp.route('/', methods=['GET'])
def get_vendors():
    """
    Route: GET /
    Auth Required: None (Publicly visible to read partners)
    Purpose: Pulls down a complete list of every single vendor working with the pantry.
    Returns: A JSON object containing an array of 'vendors', each with their ID and contact info.
    """
    try:
        # Establish a connection specifically to the 'vendors' folder in the database
        vendors_ref = db.collection('vendors')
        docs = vendors_ref.stream()

        # Build an empty list, then fill it up one by one with vendor info
        vendors = []
        for doc in docs:
            v_data = doc.to_dict()
            v_data['id'] = doc.id
            vendors.append(v_data)
            
        return jsonify({'vendors': vendors}), 200

    except Exception as e:
        # Failsafe error return so the system doesn't crash on the user
        return jsonify({'error': str(e)}), 500

@vendors_bp.route('/', methods=['POST'])
@staff_required
def add_vendor():
    """
    Route: POST /
    Auth Required: YES (Staff Only)
    Purpose: Allows administrators to create a brand new vendor relationship profile in the system.
    Returns: A confirmation message and the newly created vendor profile including its new ID.
    """
    try:
        data = request.json
        if not data:
             return jsonify({'error': 'No data provided.'}), 400
             
        # Enforce that all basic contact details must be strictly provided
        required_fields = ['name', 'contact_email', 'contact_phone', 'address']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        # Ask Firebase to automatically carve out a new slot for this vendor
        doc_ref = db.collection('vendors').document()
        doc_ref.set(data)
        
        # Merge the generated ID back into the payload so the frontend knows what it is
        new_vendor = data.copy()
        new_vendor['id'] = doc_ref.id
        
        return jsonify({'message': 'Vendor added successfully', 'vendor': new_vendor}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vendors_bp.route('/<vendor_id>', methods=['DELETE'])
@staff_required
def delete_vendor(vendor_id):
    """
    Route: DELETE /<vendor_id>
    Auth Required: YES (Staff Only)
    Purpose: Completely deletes a vendor profile from the database system if relationships end.
    Returns: A JSON success message if deleted, or a 404 error if they never existed.
    """
    try:
        # Target the exact vendor document the user wants to eliminate
        doc_ref = db.collection('vendors').document(vendor_id)
        doc = doc_ref.get()
        
        # Verify the vendor actually exists before trying to delete them
        if not doc.exists:
            return jsonify({'error': 'Vendor not found.'}), 404
            
        # Execute the hard wipe
        doc_ref.delete()
        
        return jsonify({'message': 'Vendor deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vendors_bp.route('/<vendor_id>/invoices', methods=['GET'])
def get_vendor_invoices(vendor_id):
    """
    Route: GET /<vendor_id>/invoices
    Auth Required: None (General transparency)
    Purpose: Pulls up every single invoice/receipt formally attached to this specific vendor.
    Returns: A JSON array of all past invoice records.
    """
    try:
        # Look up the root vendor first to make sure they are real
        vendor_ref = db.collection('vendors').document(vendor_id)
        if not vendor_ref.get().exists:
            return jsonify({'error': 'Vendor not found.'}), 404

        # Dive into the 'invoices' sub-folder nested underneath this specific vendor
        invoices_ref = vendor_ref.collection('invoices')
        docs = invoices_ref.stream()

        # Gather up all the receipts
        invoices = []
        for doc in docs:
            inv_data = doc.to_dict()
            inv_data['id'] = doc.id
            invoices.append(inv_data)

        return jsonify({'invoices': invoices}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vendors_bp.route('/<vendor_id>/invoices', methods=['POST'])
@staff_required
def add_vendor_invoice(vendor_id):
    """
    Route: POST /<vendor_id>/invoices
    Auth Required: YES (Staff Only)
    Purpose: Files a new receipt/invoice directly into a vendor's inner records.
    Returns: Success confirmation alongside a copy of the finalized receipt.
    """
    try:
        data = request.json
        if not data:
             return jsonify({'error': 'No data provided.'}), 400
             
        # Strictly mandate that financial records have dates, amounts, and item details
        required_fields = ['date', 'amount', 'description', 'items_delivered']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        # Validate that the vendor exists before assigning a bill to them
        vendor_ref = db.collection('vendors').document(vendor_id)
        if not vendor_ref.get().exists:
            return jsonify({'error': 'Vendor not found.'}), 404

        # Push the record into the appropriate Firebase sub-collection
        invoice_ref = vendor_ref.collection('invoices').document()
        invoice_ref.set(data)
        
        # Bundle the new record ID to return to the staff member's screen
        new_invoice = data.copy()
        new_invoice['id'] = invoice_ref.id
        
        return jsonify({'message': 'Invoice added successfully', 'invoice': new_invoice}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500
