"""
Routes for managing vendors.
Includes endpoints to manage where food is sourced from or distributed to.
"""
from flask import Blueprint, request, jsonify
from firebase_config import db
from auth import staff_required

vendors_bp = Blueprint('vendors', __name__)

@vendors_bp.route('/', methods=['GET'])
def get_vendors():
    """
    Get all vendors.
    """
    try:
        vendors_ref = db.collection('vendors')
        docs = vendors_ref.stream()

        vendors = []
        for doc in docs:
            v_data = doc.to_dict()
            v_data['id'] = doc.id
            vendors.append(v_data)
            
        return jsonify({'vendors': vendors}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vendors_bp.route('/', methods=['POST'])
@staff_required
def add_vendor():
    """
    Add a new vendor.
    Expected fields: name, contact_email, contact_phone, address
    """
    try:
        data = request.json
        if not data:
             return jsonify({'error': 'No data provided.'}), 400
             
        required_fields = ['name', 'contact_email', 'contact_phone', 'address']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        doc_ref = db.collection('vendors').document()
        doc_ref.set(data)
        
        new_vendor = data.copy()
        new_vendor['id'] = doc_ref.id
        
        return jsonify({'message': 'Vendor added successfully', 'vendor': new_vendor}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vendors_bp.route('/<vendor_id>', methods=['DELETE'])
@staff_required
def delete_vendor(vendor_id):
    """
    Remove a vendor.
    """
    try:
        doc_ref = db.collection('vendors').document(vendor_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return jsonify({'error': 'Vendor not found.'}), 404
            
        doc_ref.delete()
        
        return jsonify({'message': 'Vendor deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vendors_bp.route('/<vendor_id>/invoices', methods=['GET'])
def get_vendor_invoices(vendor_id):
    """
    Get all invoices for a specific vendor.
    """
    try:
        vendor_ref = db.collection('vendors').document(vendor_id)
        if not vendor_ref.get().exists:
            return jsonify({'error': 'Vendor not found.'}), 404

        invoices_ref = vendor_ref.collection('invoices')
        docs = invoices_ref.stream()

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
    Add an invoice to a specific vendor subcollection.
    Expected fields: date, amount, description, items_delivered
    """
    try:
        data = request.json
        if not data:
             return jsonify({'error': 'No data provided.'}), 400
             
        required_fields = ['date', 'amount', 'description', 'items_delivered']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        vendor_ref = db.collection('vendors').document(vendor_id)
        if not vendor_ref.get().exists:
            return jsonify({'error': 'Vendor not found.'}), 404

        invoice_ref = vendor_ref.collection('invoices').document()
        invoice_ref.set(data)
        
        new_invoice = data.copy()
        new_invoice['id'] = invoice_ref.id
        
        return jsonify({'message': 'Invoice added successfully', 'invoice': new_invoice}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

