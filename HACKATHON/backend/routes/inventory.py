"""
File: backend/routes/inventory.py
Description: Main Inventory Management Code.
This file is the core engine of the VT Pantry application. It handles everything related
to food items including fetching stock levels, adding new donations, handling smart AI-based
searches, pulling analytics, and securely taking yearly snapshots (rollovers).
"""
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

# Initialize rate limiting to prevent spam attacks (locks down based on user IP address)
limiter = Limiter(key_func=get_remote_address)

@inventory_bp.errorhandler(429)
def ratelimit_handler(e):
    """Fallback error sent when someone clicks a button too fast."""
    return jsonify({"error": "Too many requests, slow down"}), 429

@inventory_bp.route('/', methods=['GET'])
@limiter.limit("200 per minute")
def get_inventory():
    """
    Route: GET /
    Auth Required: None (Public access so anyone can see what food is available)
    Purpose: Pulls the entire list of food items from the database. It can also filter 
             down to just 'grocery' items or just 'open_pantry' items if requested.
    Returns: A JSON array of all matching food items.
    """
    try:
        # Check if the frontend asked for a specific program filter
        program_filter = request.args.get('program')
        items_ref = db.collection('inventory')
        
        # Apply the filter directly inside the database query if it was requested
        if program_filter:
            if program_filter not in ['open_pantry', 'grocery']:
                return jsonify({'error': 'Invalid program filter. Use "open_pantry" or "grocery".'}), 400
            query = items_ref.where('program', '==', program_filter)
            docs = query.stream()
        else:
            # Otherwise, just pull absolutely everything
            docs = items_ref.stream()

        # Build our list of items by reading each document from Firebase
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
    Route: POST /
    Auth Required: YES (Staff Only)
    Purpose: Accepts a form submission from the frontend to create a brand new food item.
             It rigorously checks that names aren't too long, quantities aren't negative, 
             and all fields are filled out.
    Returns: A success message and the newly created item with its ID.
    """
    try:
        data = request.json
        if not data:
             return jsonify({'error': 'No data provided in request body.'}), 400
             
        # Step 1: Ensure the user didn't leave any blank boxes on the form
        required_fields = ['name', 'vendor', 'category', 'weight', 'units', 'price_type', 'program', 'quantity']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        # Step 2: Clean up the text fields (remove extra spaces, cap max length at 200)
        string_fields = ['name', 'vendor', 'category', 'units', 'price_type', 'program']
        for field in string_fields:
            if not isinstance(data[field], str):
                return jsonify({'error': f"Field '{field}' must be a string."}), 400
            data[field] = data[field].strip()
            if len(data[field]) > 200:
                data[field] = data[field][:200]

        # Step 3: Ensure dropdown selections exactly match what the backend expects
        if data['price_type'] not in ['unit', 'weight']:
            return jsonify({'error': 'Invalid price_type. Use "unit" or "weight".'}), 400

        if data['program'] not in ['open_pantry', 'grocery']:
            return jsonify({'error': 'Invalid program. Use "open_pantry" or "grocery".'}), 400

        # Step 4: Ensure quantities are valid positive integers (you can't have negative apples)
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

        # Step 5: Save it definitively directly into Firebase
        doc_ref = db.collection('inventory').document()
        doc_ref.set(data)
        
        # Merge the generated ID back to send to the frontend
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
    Route: PATCH /<item_id>/restock
    Auth Required: YES (Staff Only)
    Purpose: Used when a new shipment of an existing food arrives. It bumps the quantity up.
    Returns: The new total quantity count.
    """
    try:
        data = request.json
        if not data or 'amount' not in data:
            return jsonify({'error': 'Missing "amount" field in request body.'}), 400

        # Verify they actually sent a positive number of things to restock
        try:
            amount_to_add = int(data['amount'])
            if amount_to_add <= 0:
                raise ValueError
        except Exception:
            return jsonify({'error': "Field 'amount' must be a positive integer."}), 400

        doc_ref = db.collection('inventory').document(item_id)
        doc = doc_ref.get()
        
        # Verify the item exists before modifying it
        if not doc.exists:
            return jsonify({'error': 'Item not found.'}), 404
            
        current_data = doc.to_dict()
        new_quantity = current_data.get('quantity', 0) + amount_to_add
        
        # Execute the targeted math update safely
        doc_ref.update({'quantity': new_quantity})
        
        return jsonify({'message': 'Item restocked successfully', 'new_quantity': new_quantity}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/<item_id>/transfer', methods=['PATCH'])
@limiter.limit("200 per minute")
@staff_required
def transfer_item(item_id):
    """
    Route: PATCH /<item_id>/transfer
    Auth Required: YES (Staff Only)
    Purpose: Moves a batch of food between the "Grocery" store side and the "Open Pantry" side.
    Returns: A confirmation message of the new assignment.
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
            
        # Execute the transfer update
        doc_ref.update({'program': new_program})
        
        return jsonify({'message': 'Item transferred successfully', 'new_program': new_program}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/<item_id>', methods=['DELETE'])
@limiter.limit("200 per minute")
@staff_required
def delete_item(item_id):
    """
    Route: DELETE /<item_id>
    Auth Required: YES (Staff Only)
    Purpose: Completely deletes a food item permanently from the active inventory tracker.
    Returns: A simple success confirmation.
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
    Route: GET /search?q=search term
    Auth Required: None (Public access for fast searching)
    Purpose: Our "Smart AI Search". Instead of doing rigid text matching, this connects to 
             Google's Gemini AI. If a user types "breakfast food", the AI understands that 
             Cereal and Oatmeal match that query, even if the word 'breakfast' isn't explicitly in the name!
    Returns: A list of items that the AI deemed relevant.
    """
    try:
        query = request.args.get('q')
        if not query:
            return jsonify({'error': 'Missing search query "q".'}), 400

        # Step 1: Rapidly fetch our entire inventory outline
        items_ref = db.collection('inventory')
        docs = items_ref.stream()
        
        inventory_items = []
        item_catalog = [] 
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            inventory_items.append(data)
            # Build a tiny catalog to give to the AI without overwhelming it
            item_catalog.append({'id': doc.id, 'name': data.get('name', 'Unknown')})
            
        if not inventory_items:
            return jsonify({'items': []}), 200

        matched_ids = []
        gemini_failed = False

        # Step 2: Try asking Google Gemini AI to analyze the items based on the user's intent 
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
            
            # AI's usually append "```json" backticks. Clean them up!
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
                
            matched_ids = json.loads(response_text)
            
            if not isinstance(matched_ids, list):
                raise ValueError("Gemini response is not a JSON array")
                
        except Exception as e:
            print(f"Gemini search failed: {e}")
            gemini_failed = True

        # Step 3: FALLBACK - If the AI crashed or timed out, default to a standard dumb-text search instantly
        if gemini_failed:
            query_lower = query.lower()
            matched_ids = [
                item['id'] for item in inventory_items
                if item.get('name') and query_lower in item['name'].lower()
            ]

        # Step 4: Gather the full data of whatever IDs were matched and send it back to the frontend
        matched_ids_set = set(matched_ids)
        result_items = [item for item in inventory_items if item['id'] in matched_ids_set]

        return jsonify({'items': result_items, 'fallback_used': gemini_failed}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/stats', methods=['GET'])
@limiter.limit("200 per minute")
def get_inventory_stats():
    """
    Route: GET /stats
    Auth Required: None (General transparency)
    Purpose: Instantly calculates the live analytics of the entire storage facility.
             This counts every box of food, categorizes it by program, and tallies low stock alerts.
    Returns: A JSON object compiling total items, category splits, and quantities.
    """
    try:
        # Fetch everything in one simple read to save database costs
        items_ref = db.collection('inventory')
        docs = items_ref.stream()
        
        stats = {
            "total_items": 0,
            "open_pantry_items": 0,
            "grocery_items": 0,
            "total_quantity": 0,
            "low_stock_items": 0
        }
        
        # Loop over every single food item and mathematically tally up the results
        for doc in docs:
            item_data = doc.to_dict()
            stats["total_items"] += 1
            
            program = item_data.get('program')
            if program == 'open_pantry':
                stats["open_pantry_items"] += 1
            elif program == 'grocery':
                stats["grocery_items"] += 1
                
            # Safely add up quantities, skipping any corrupted data
            try:
                qty = int(item_data.get('quantity', 0))
            except (ValueError, TypeError):
                qty = 0
                
            stats["total_quantity"] += qty
            
            # If stock dips below 10, flag it as a low stock alert
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
    Route: POST /checkpoint
    Auth Required: YES (Staff Only)
    Purpose: Takes an immediate snapshot picture of the entire inventory table and saves it into history.
             This allows staff to "freeze" time and look back at what stock was exactly at that moment.
    Returns: An ID indicating the newly created history checkpoint.
    """
    try:
        data = request.json or {}
        label = data.get('label', '')
        
        # Fetch current active inventory
        items_ref = db.collection('inventory')
        docs = items_ref.stream()
        
        items = []
        for doc in docs:
            item_data = doc.to_dict()
            item_data['id'] = doc.id
            items.append(item_data)
            
        # Log out the exact UTC time the snapshot was clicked
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        checkpoint_data = {
            'timestamp': timestamp,
            'label': label,
            'item_count': len(items),
            'items': items
        }
        
        # Save it permanently in the history collection
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
    Route: GET /checkpoints
    Auth Required: None
    Purpose: Pulls up a list of all historical snapshot moments ever taken in the database, ordered from newest to oldest.
    Returns: Summarized checkpoint information. It deliberately EXCLUDES the massive list of items to keep loading times fast.
    """
    try:
        # Order the snapshots by date DESCENDING so new snapshots are at the top
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
    Route: GET /checkpoints/<checkpoint_id>
    Auth Required: None
    Purpose: Loads the massive item-by-item snapshot data of a specifically requested checkpoint.
    Returns: The massive full JSON payload of that exact moment in time history.
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
    Route: POST /rollover
    Auth Required: YES (Staff Only)
    Purpose: The Annual Rollover function. It formally bundles up a checkpoint for the closure
             of the fiscal/school year, tags it, and copies the metrics off into a special 'rollovers' log. 
             It strictly carries over all inventory without deleting anything so numbers seamlessly roll into the next year.
    Returns: Aggregated statistics showing exactly how much food was securely carried forward.
    """
    try:
        now = datetime.utcnow()
        current_year = now.year
        timestamp = now.isoformat() + "Z"
        
        # 1. Swiftly count everything actively in the pantry
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
            
        # 2. Lock that state into an official final checkpoint labeled with the closing year
        checkpoint_label = f"Pre-Rollover Snapshot - {current_year}"
        checkpoint_data = {
            'timestamp': timestamp,
            'label': checkpoint_label,
            'item_count': len(items),
            'items': items
        }
        
        checkpoint_ref = db.collection('checkpoints').document()
        checkpoint_ref.set(checkpoint_data)
        
        # 3. Formally register the rollover in the master log
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
    Route: GET /low-stock?threshold=10
    Auth Required: None
    Purpose: Used by staff displays to actively track what items are plummeting dangerously 
             low on stock. Organizes the worst stock scenarios directly to the top.
    Returns: List of dangerously low items sorted lowest-first.
    """
    try:
        # Check what boundary the user requested, defaulting to 10 if blank
        threshold_str = request.args.get('threshold', '10')
        
        # Guard rail: Prevent anyone from inputting chaotic strings or negatives
        try:
            threshold = int(threshold_str)
            if threshold < 1 or threshold > 9999:
                raise ValueError
        except Exception:
            return jsonify({'error': 'threshold must be a positive integer between 1 and 9999'}), 400
            
        items_ref = db.collection('inventory')
        docs = items_ref.stream()
        
        # Build the filtered list
        low_stock_items = []
        for doc in docs:
            item_data = doc.to_dict()
            item_data['id'] = doc.id
            
            try:
                qty = int(item_data.get('quantity', 0))
            except (ValueError, TypeError):
                qty = 0
                
            # If the item crosses the red-line, push it to our alerts array
            if qty <= threshold:
                item_data['quantity'] = qty 
                low_stock_items.append(item_data)
                
        # Mathematically sort the final output so the absolute lowest numbers are #1 in the list
        low_stock_items.sort(key=lambda x: x.get('quantity', 0))
        
        return jsonify({
            "items": low_stock_items,
            "count": len(low_stock_items),
            "threshold_used": threshold
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
