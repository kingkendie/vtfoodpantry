import os
import json
from datetime import datetime
from google import genai
from flask import Blueprint, request, jsonify
from firebase_config import db
from auth import staff_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

inventory_bp = Blueprint('inventory', __name__)

limiter = Limiter(key_func=get_remote_address)

@inventory_bp.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Too many requests, slow down"}), 429

@inventory_bp.route('/', methods=['GET'])
@limiter.limit("200 per minute")
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
@limiter.limit("200 per minute")
@staff_required
def add_inventory_item():
    """
    Add a new item to the inventory.
    Expected fields: name, vendor, category, weight, units, price_type, program, quantity
    """
    try:
        data = request.json
        if not data:
             return jsonify({'error': 'No data provided in request body.'}), 400
             
        required_fields = ['name', 'vendor', 'category', 'weight', 'units', 'price_type', 'program', 'quantity']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        # String fields sanitization
        string_fields = ['name', 'vendor', 'category', 'units', 'price_type', 'program']
        for field in string_fields:
            if not isinstance(data[field], str):
                return jsonify({'error': f"Field '{field}' must be a string."}), 400
            data[field] = data[field].strip()
            if len(data[field]) > 200:
                data[field] = data[field][:200]

        # Validate price_type
        if data['price_type'] not in ['unit', 'weight']:
            return jsonify({'error': 'Invalid price_type. Use "unit" or "weight".'}), 400

        # Validate program
        if data['program'] not in ['open_pantry', 'grocery']:
            return jsonify({'error': 'Invalid program. Use "open_pantry" or "grocery".'}), 400

        # Number fields sanitization
        try:
            quantity = int(data['quantity'])
            if quantity < 0 or quantity > 999999:
                raise ValueError
            data['quantity'] = quantity
        except Exception:
            return jsonify({'error': "Field 'quantity' must be an integer between 0 and 999999."}), 400

        try:
            weight = float(data['weight'])
            if weight < 0 or weight > 999999:
                raise ValueError
            data['weight'] = weight
        except Exception:
            return jsonify({'error': "Field 'weight' must be a positive number between 0 and 999999."}), 400

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
@limiter.limit("200 per minute")
@staff_required
def restock_item(item_id):
    """
    Increase an existing item's quantity.
    Expected body: {'amount': <number>}
    """
    try:
        data = request.json
        if not data or 'amount' not in data:
            return jsonify({'error': 'Missing "amount" field in request body.'}), 400

        try:
            amount_to_add = int(data['amount'])
            if amount_to_add <= 0:
                raise ValueError
        except Exception:
            return jsonify({'error': "Field 'amount' must be a positive integer."}), 400

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
@limiter.limit("200 per minute")
@staff_required
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
@limiter.limit("200 per minute")
@staff_required
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
@limiter.limit("30 per minute")
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
                
            client = genai.Client(api_key=api_key)
            
            prompt = f"""
            You are a smart search assistant for a pantry inventory system.
            Given the following user search query: "{query}"
            
            Find the items in the catalog that best match the query.
            Return ONLY a valid JSON array of strings, where each string is an item ID.
            Do not include any other text, markdown formatting, or explanation.
            
            Catalog:
            {json.dumps(item_catalog)}
            """
            
            response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
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

@inventory_bp.route('/stats', methods=['GET'])
@limiter.limit("200 per minute")
def get_inventory_stats():
    """
    Get inventory statistics in a single read.
    """
    try:
        items_ref = db.collection('inventory')
        docs = items_ref.stream()
        
        stats = {
            "total_items": 0,
            "open_pantry_items": 0,
            "grocery_items": 0,
            "total_quantity": 0,
            "low_stock_items": 0
        }
        
        for doc in docs:
            item_data = doc.to_dict()
            stats["total_items"] += 1
            
            program = item_data.get('program')
            if program == 'open_pantry':
                stats["open_pantry_items"] += 1
            elif program == 'grocery':
                stats["grocery_items"] += 1
                
            try:
                qty = int(item_data.get('quantity', 0))
            except (ValueError, TypeError):
                qty = 0
                
            stats["total_quantity"] += qty
            if qty < 10:
                stats["low_stock_items"] += 1
                
        return jsonify(stats), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/checkpoint', methods=['POST'])
@limiter.limit("20 per minute")
@staff_required
def create_checkpoint():
    """
    Take a full snapshot of current inventory and save it to checkpoints collection.
    """
    try:
        data = request.json or {}
        label = data.get('label', '')
        
        # 1. Fetch all items in a single read
        items_ref = db.collection('inventory')
        docs = items_ref.stream()
        
        items = []
        for doc in docs:
            item_data = doc.to_dict()
            item_data['id'] = doc.id
            items.append(item_data)
            
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        checkpoint_data = {
            'timestamp': timestamp,
            'label': label,
            'item_count': len(items),
            'items': items
        }
        
        doc_ref = db.collection('checkpoints').document()
        doc_ref.set(checkpoint_data)
        
        return jsonify({
            "success": True, 
            "checkpoint_id": doc_ref.id, 
            "item_count": len(items)
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/checkpoints', methods=['GET'])
@limiter.limit("50 per minute")
def get_checkpoints():
    """
    Return all checkpoints ordered by timestamp descending.
    Excludes the full items list.
    """
    try:
        checkpoints_ref = db.collection('checkpoints').order_by('timestamp', direction='DESCENDING')
        docs = checkpoints_ref.stream()
        
        checkpoints = []
        for doc in docs:
            data = doc.to_dict()
            checkpoints.append({
                'id': doc.id,
                'timestamp': data.get('timestamp'),
                'label': data.get('label'),
                'item_count': data.get('item_count', 0)
            })
            
        return jsonify({'checkpoints': checkpoints}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/checkpoints/<checkpoint_id>', methods=['GET'])
@limiter.limit("50 per minute")
def get_checkpoint_details(checkpoint_id):
    """
    Return the full checkpoint including all items snapshot.
    """
    try:
        doc_ref = db.collection('checkpoints').document(checkpoint_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return jsonify({'error': 'Checkpoint not found.'}), 404
            
        data = doc.to_dict()
        data['id'] = doc.id
        
        return jsonify({'checkpoint': data}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/rollover', methods=['POST'])
@limiter.limit("5 per minute")
@staff_required
def inventory_rollover():
    """
    Perform a yearly rollover:
    1. Create a checkpoint labeled "Pre-Rollover Snapshot - <year>"
    2. Save a rollover record.
    """
    try:
        now = datetime.utcnow()
        current_year = now.year
        timestamp = now.isoformat() + "Z"
        
        # 1. Fetch all items in a single read
        items_ref = db.collection('inventory')
        docs = items_ref.stream()
        
        items = []
        total_quantity = 0
        
        for doc in docs:
            item_data = doc.to_dict()
            item_data['id'] = doc.id
            items.append(item_data)
            
            try:
                qty = int(item_data.get('quantity', 0))
            except (ValueError, TypeError):
                qty = 0
            total_quantity += qty
            
        # 2. Create checkpoint
        checkpoint_label = f"Pre-Rollover Snapshot - {current_year}"
        checkpoint_data = {
            'timestamp': timestamp,
            'label': checkpoint_label,
            'item_count': len(items),
            'items': items
        }
        
        checkpoint_ref = db.collection('checkpoints').document()
        checkpoint_ref.set(checkpoint_data)
        
        # 3. Save rollover record
        rollover_data = {
            'timestamp': timestamp,
            'year': current_year,
            'checkpoint_id': checkpoint_ref.id,
            'item_count': len(items),
            'total_quantity': total_quantity
        }
        
        db.collection('rollovers').document().set(rollover_data)
        
        return jsonify({
            "success": True, 
            "year": current_year, 
            "items_carried_forward": len(items),
            "total_quantity": total_quantity,
            "checkpoint_id": checkpoint_ref.id
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/low-stock', methods=['GET'])
@limiter.limit("50 per minute")
def get_low_stock():
    """
    Return all items with quantity <= threshold.
    """
    try:
        threshold_str = request.args.get('threshold', '10')
        
        try:
            threshold = int(threshold_str)
            if threshold < 1 or threshold > 9999:
                raise ValueError
        except Exception:
            return jsonify({'error': 'threshold must be a positive integer between 1 and 9999'}), 400
            
        items_ref = db.collection('inventory')
        docs = items_ref.stream()
        
        low_stock_items = []
        for doc in docs:
            item_data = doc.to_dict()
            item_data['id'] = doc.id
            
            try:
                qty = int(item_data.get('quantity', 0))
            except (ValueError, TypeError):
                qty = 0
                
            if qty <= threshold:
                item_data['quantity'] = qty 
                low_stock_items.append(item_data)
                
        # Sort ascending
        low_stock_items.sort(key=lambda x: x.get('quantity', 0))
        
        return jsonify({
            "items": low_stock_items,
            "count": len(low_stock_items),
            "threshold_used": threshold
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
