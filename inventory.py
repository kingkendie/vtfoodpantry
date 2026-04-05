import os
import json
import google.generativeai as genai
from flask import Blueprint, request, jsonify
from firebase_config import db

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/', methods=['GET'])
def get_inventory():
    """
    Get all inventory items.
    Optional query param: ?program=open_pantry or ?program=grocery
    """
    try:
        program_filter = request.args.get('program')
        items_ref = db.collection('inventory')
        
        if program_filter:
            if program_filter not in ['open_pantry', 'grocery']:
                return jsonify({'error': 'Invalid program filter. Use "open_pantry" or "grocery".'}), 400
            query = items_ref.where('program', '==', program_filter)
            docs = query.stream()
        else:
            docs = items_ref.stream()

        items = []
        for doc in docs:
            item_data = doc.to_dict()
            item_data['id'] = doc.id
            items.append(item_data)
            
        return jsonify({'items': items}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/', methods=['POST'])
def add_inventory_item():
    """
    Add a new item to the inventory.
    Expected fields: name, vendor, category, weight, units, price_type, program, quantity
    """
    try:
        data = request.json
        required_fields = ['name', 'vendor', 'category', 'weight', 'units', 'price_type', 'program', 'quantity']
        
        # Check for missing required fields
        if not data:
             return jsonify({'error': 'No data provided in request body.'}), 400
             
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
            
        if data['program'] not in ['open_pantry', 'grocery']:
            return jsonify({'error': 'Invalid program. Use "open_pantry" or "grocery".'}), 400

        # Add to Firestore
        doc_ref = db.collection('inventory').document()
        doc_ref.set(data)
        
        # Return the created item with its generated ID
        new_item = data.copy()
        new_item['id'] = doc_ref.id
        
        return jsonify({'message': 'Item added successfully', 'item': new_item}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/<item_id>/restock', methods=['PATCH'])
def restock_item(item_id):
    """
    Increase an existing item's quantity.
    Expected body: {'amount': <number>}
    """
    try:
        data = request.json
        if not data or 'amount' not in data or not isinstance(data['amount'], (int, float)):
            return jsonify({'error': 'Missing or invalid "amount" field in request body.'}), 400
            
        amount_to_add = data['amount']
        if amount_to_add <= 0:
            return jsonify({'error': 'Amount to restock must be positive.'}), 400

        doc_ref = db.collection('inventory').document(item_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return jsonify({'error': 'Item not found.'}), 404
            
        current_data = doc.to_dict()
        new_quantity = current_data.get('quantity', 0) + amount_to_add
        
        doc_ref.update({'quantity': new_quantity})
        
        return jsonify({'message': 'Item restocked successfully', 'new_quantity': new_quantity}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/<item_id>/transfer', methods=['PATCH'])
def transfer_item(item_id):
    """
    Change an item's program between "open_pantry" and "grocery".
    Expected body: {'program': 'open_pantry' | 'grocery'}
    """
    try:
        data = request.json
        if not data or 'program' not in data:
            return jsonify({'error': 'Missing "program" field in request body.'}), 400
            
        new_program = data['program']
        if new_program not in ['open_pantry', 'grocery']:
            return jsonify({'error': 'Invalid program. Use "open_pantry" or "grocery".'}), 400

        doc_ref = db.collection('inventory').document(item_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return jsonify({'error': 'Item not found.'}), 404
            
        doc_ref.update({'program': new_program})
        
        return jsonify({'message': 'Item transferred successfully', 'new_program': new_program}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    """
    Remove an item from inventory.
    """
    try:
        doc_ref = db.collection('inventory').document(item_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return jsonify({'error': 'Item not found.'}), 404
            
        doc_ref.delete()
        
        return jsonify({'message': 'Item deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/search', methods=['GET'])
def search_inventory():
    """
    Smart search over inventory items using Gemini API.
    Fallbacks to simple string matching if Gemini fails.
    """
    try:
        query = request.args.get('q')
        if not query:
            return jsonify({'error': 'Missing search query "q".'}), 400

        # Fetch inventory ONCE
        items_ref = db.collection('inventory')
        docs = items_ref.stream()
        
        inventory_items = []
        item_catalog = [] # for the LLM
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            inventory_items.append(data)
            # Only send id and name for token efficiency
            item_catalog.append({'id': doc.id, 'name': data.get('name', 'Unknown')})
            
        if not inventory_items:
            return jsonify({'items': []}), 200

        matched_ids = []
        gemini_failed = False

        # Attempt smart search with Gemini
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("Missing GEMINI_API_KEY")
                
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            prompt = f"""
            You are a smart search assistant for a pantry inventory system.
            Given the following user search query: "{query}"
            
            Find the items in the catalog that best match the query.
            Return ONLY a valid JSON array of strings, where each string is an item ID.
            Do not include any other text, markdown formatting, or explanation.
            
            Catalog:
            {json.dumps(item_catalog)}
            """
            
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up potential markdown formatting
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
                
            matched_ids = json.loads(response_text)
            
            # Validate it's a list
            if not isinstance(matched_ids, list):
                raise ValueError("Gemini response is not a JSON array")
                
        except Exception as e:
            print(f"Gemini search failed: {e}")
            gemini_failed = True

        # Fallback to simple string match
        if gemini_failed:
            query_lower = query.lower()
            matched_ids = [
                item['id'] for item in inventory_items
                if item.get('name') and query_lower in item['name'].lower()
            ]

        # Filter the single inventory list based on matched IDs
        matched_ids_set = set(matched_ids)
        result_items = [item for item in inventory_items if item['id'] in matched_ids_set]

        return jsonify({'items': result_items, 'fallback_used': gemini_failed}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
