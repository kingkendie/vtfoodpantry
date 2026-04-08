# VT Pantry System - API Reference
This document outlines all stable backend endpoints available for frontend integrations. The base URL mapping applies `/api/` prior to the blueprints.

**Server Default Prefix**: `http://127.0.0.1:5000/api`
**Authorization**: Routes marked `Auth Required: Yes` require a valid JWT passed safely via `Authorization: Bearer <idToken>` header.

---

## 🔒 Authentication (`/api/auth`)

### `POST /auth/login`
- **Auth Required**: No
- **Description**: Authenticates a staff account directly against Google Firebase Identity. 
- **Request Body**:
```json
{
  "email": "staff@vtpantry.com",
  "password": "securepassword123"
}
```
- **Response**:
```json
{
  "idToken": "eyJhbGciOiJSUzI1NiIs..."
}
```

### `POST /auth/register`
- **Auth Required**: Yes (Existing Staff Only)
- **Description**: Permits an active, logged-in administrator to whitelist and register a completely new staff user account securely.
- **Request Body**:
```json
{
  "email": "new.hire@vtpantry.com",
  "password": "temporarypassword!"
}
```
- **Response**:
```json
{
  "success": true,
  "uid": "1Xz9kPOqawd1..."
}
```

---

## 📦 Inventory Management (`/api/inventory`)

### `GET /inventory/`
- **Auth Required**: No 
- **Description**: Retrieves the complete inventory catalog safely.
- **Query Params**: `?program=open_pantry` or `?program=grocery` (Optional)
- **Response**:
```json
{
  "items": [
    {
      "id": "abc123xyz",
      "name": "Canned Soup",
      "quantity": 42,
      "program": "open_pantry",
      ...
    }
  ]
}
```

### `POST /inventory/`
- **Auth Required**: Yes
- **Description**: Registers a brand new food item classification safely into the live pantry system.
- **Request Body**:
```json
{
  "name": "Cereal Box",
  "vendor": "Local Farm Co.",
  "category": "Dry Goods",
  "weight": 1.5,
  "units": "lbs",
  "price_type": "unit",
  "program": "open_pantry",
  "quantity": 100
}
```
- **Response**:
```json
{
  "message": "Item added successfully",
  "item": { "id": "generated_id_here", "name": "Cereal Box", ... }
}
```

### `PATCH /inventory/<item_id>/restock`
- **Auth Required**: Yes
- **Description**: Submits a numeric increment when a new delivery box arrives.
- **Request Body**:
```json
{
  "amount": 50
}
```
- **Response**:
```json
{
  "message": "Item restocked successfully",
  "new_quantity": 150
}
```

### `PATCH /inventory/<item_id>/transfer`
- **Auth Required**: Yes
- **Description**: Swaps an active inventory item fluidly between the 'Grocery' store branch or the 'Open Pantry' branch.
- **Request Body**:
```json
{
  "program": "grocery"
}
```
- **Response**:
```json
{
  "message": "Item transferred successfully",
  "new_program": "grocery"
}
```

### `DELETE /inventory/<item_id>`
- **Auth Required**: Yes
- **Description**: Permanently wipes a discontinued item from tracking visibility.
- **Response**: `{"message": "Item deleted successfully"}`

### `GET /inventory/search`
- **Auth Required**: No
- **Description**: Smart Google Gemini AI semantic search handler. Automatically matches generic user intents against the catalog safely.
- **Query Params**: `?q=search term` 
- **Response**:
```json
{
  "fallback_used": false,
  "items": [ ... ]
}
```

### `GET /inventory/stats`
- **Auth Required**: No
- **Description**: Generates an instantaneous analytical breakdown tallying exactly how much data sits in the system right now.
- **Response**:
```json
{
  "grocery_items": 45,
  "low_stock_items": 3,
  "open_pantry_items": 120,
  "total_items": 165,
  "total_quantity": 1940
}
```

### `GET /inventory/low-stock`
- **Auth Required**: No
- **Description**: Pulls an array of items mathematically teetering on empty, explicitly sorted by worst shortage first.
- **Query Params**: `?threshold=10` (Defaults to 10 if omitted)
- **Response**:
```json
{
  "count": 3,
  "threshold_used": 10,
  "items": [...]
}
```

---

## ⏳ System Checkpoints & Rollovers (`/api/inventory`) 
*(Also embedded in the inventory blueprint)*

### `POST /inventory/checkpoint`
- **Auth Required**: Yes
- **Description**: "Freezes time"; saves the absolute current state of numbers into an immutable historical log.
- **Request Body**: `{"label": "End of Fall Semester"}` (Optional)
- **Response**: `{"success": true, "checkpoint_id": "doc_id", "item_count": 165}`

### `GET /inventory/checkpoints`
- **Auth Required**: No
- **Description**: Returns all historical timestamp headers without the massive bandwidth load of their full payloads.
- **Response**:
```json
{
  "checkpoints": [
    {
      "id": "doc_id_123",
      "timestamp": "2026-04-08T15:00:00Z",
      "label": "End of Fall Semester",
      "item_count": 165
    }
  ]
}
```

### `GET /inventory/checkpoints/<checkpoint_id>`
- **Auth Required**: No
- **Description**: Drops down the massive JSON array recording exactly what the pantry looked like at that specified checkpoint. 
- **Response**: `{"checkpoint": { "id": "doc_id_123", "items": [...] }}`

### `POST /inventory/rollover`
- **Auth Required**: Yes
- **Description**: Runs an official, heavy-duty annual Rollover logging exact closing quantity volume. Pre-saves a dedicated snapshot safely.
- **Response**:
```json
{
  "success": true,
  "year": 2026,
  "items_carried_forward": 165,
  "total_quantity": 1940,
  "checkpoint_id": "snapshot_doc_id"
}
```

---

## 🏭 Vendors & Receiving (`/api/vendors`)

### `GET /vendors/`
- **Auth Required**: No
- **Description**: Pulls a list of all active supplying agencies.
- **Response**: `{"vendors": [{"id": "v1", "name": "Local Farm", ...}]}`

### `POST /vendors/`
- **Auth Required**: Yes
- **Description**: Whitelists a new donor or vendor relation firm into the pipeline.
- **Request Body**:
```json
{
  "name": "Local Co-op",
  "contact_email": "hello@coop.com",
  "contact_phone": "555-0123",
  "address": "123 Main St"
}
```
- **Response**: `{"message": "Vendor added successfully", "vendor": {...}}`

### `DELETE /vendors/<vendor_id>`
- **Auth Required**: Yes
- **Description**: Wipes a vendor completely.
- **Response**: `{"message": "Vendor deleted successfully"}`

### `GET /vendors/<vendor_id>/invoices`
- **Auth Required**: No
- **Description**: Fetches all attached receipts/invoices uniquely tied beneath a targeted vendor.
- **Response**: `{"invoices": [{"amount": 250.00, "date": "2026-02-01", ...}]}`

### `POST /vendors/<vendor_id>/invoices`
- **Auth Required**: Yes
- **Description**: Files a finalized delivery shipment directly into a specific supplier's file cabinet.
- **Request Body**:
```json
{
  "date": "2026-04-08",
  "amount": 420.50,
  "description": "Weekly Veggie Load",
  "items_delivered": "50x Carrots, 20x Potatoes"
}
```
- **Response**: `{"message": "Invoice added successfully", "invoice": {...}}`

---

## 📊 Integrations (`/api/export`)

### `GET /export/sheets`
- **Auth Required**: No
- **Description**: Safely commands the system to compile the massive live catalog mapping, connects directly to the authenticated Google Spreadsheet pipeline, flushes old data out, and streams the absolute latest rows up.
- **Response**:
```json
{
  "success": true,
  "rows_written": 165
}
```
