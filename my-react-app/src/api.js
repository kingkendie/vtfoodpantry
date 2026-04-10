/**
 * api.js — Centralized API layer for VT Food Pantry
 * All fetch calls go through here. Auth token is auto-attached from sessionStorage.
 */

const BASE_URL = 'http://127.0.0.1:5000/api';

function getToken() {
  return sessionStorage.getItem('vtp_token');
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const message = data.error || `Request failed (${res.status})`;
    throw new Error(message);
  }

  return data;
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export async function login(email, password) {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function registerStaff(email, password) {
  return request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

// ── Inventory ─────────────────────────────────────────────────────────────────
export async function getInventory(program = null) {
  const qs = program ? `?program=${program}` : '';
  return request(`/inventory/${qs}`);
}

export async function addItem(data) {
  return request('/inventory/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function restockItem(itemId, amount) {
  return request(`/inventory/${itemId}/restock`, {
    method: 'PATCH',
    body: JSON.stringify({ amount }),
  });
}

export async function transferItem(itemId, program) {
  return request(`/inventory/${itemId}/transfer`, {
    method: 'PATCH',
    body: JSON.stringify({ program }),
  });
}

export async function deleteItem(itemId) {
  return request(`/inventory/${itemId}`, { method: 'DELETE' });
}

export async function searchInventory(q) {
  return request(`/inventory/search?q=${encodeURIComponent(q)}`);
}

export async function getStats() {
  return request('/inventory/stats');
}

export async function getLowStock(threshold = 10) {
  return request(`/inventory/low-stock?threshold=${threshold}`);
}

// ── Checkpoints & Rollover ────────────────────────────────────────────────────
export async function createCheckpoint(label = '') {
  return request('/inventory/checkpoint', {
    method: 'POST',
    body: JSON.stringify({ label }),
  });
}

export async function getCheckpoints() {
  return request('/inventory/checkpoints');
}

export async function getCheckpointDetails(checkpointId) {
  return request(`/inventory/checkpoints/${checkpointId}`);
}

export async function runRollover() {
  return request('/inventory/rollover', { method: 'POST' });
}

// ── Vendors ───────────────────────────────────────────────────────────────────
export async function getVendors() {
  return request('/vendors/');
}

export async function addVendor(data) {
  return request('/vendors/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function deleteVendor(vendorId) {
  return request(`/vendors/${vendorId}`, { method: 'DELETE' });
}

export async function getInvoices(vendorId) {
  return request(`/vendors/${vendorId}/invoices`);
}

export async function addInvoice(vendorId, data) {
  return request(`/vendors/${vendorId}/invoices`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ── Export ────────────────────────────────────────────────────────────────────
export async function exportToSheets() {
  return request('/export/sheets');
}
