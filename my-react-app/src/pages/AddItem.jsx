import { useState, useEffect, useRef } from 'react';
import { getInventory, addItem, restockItem, searchInventory, getVendors } from '../api.js';
import { useToast } from '../components/Toast.jsx';

const CATEGORIES = [
  'Produce', 'Dry Goods', 'Dairy', 'Protein', 'Canned Goods',
  'Frozen', 'Baked Goods', 'Beverages', 'Personal Care', 'Other',
];
const UNITS = ['lbs', 'oz', 'kg', 'each', 'case', 'bag', 'box', 'can'];

// ── Quick Restock Tab ─────────────────────────────────────────────────────────
function QuickRestock() {
  const [query,    setQuery]    = useState('');
  const [results,  setResults]  = useState([]);
  const [selected, setSelected] = useState(null);
  const [amount,   setAmount]   = useState('');
  const [searching, setSearching] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const debounceRef = useRef(null);
  const toast = useToast();

  function handleQueryChange(val) {
    setQuery(val);
    setSelected(null);
    clearTimeout(debounceRef.current);
    if (!val.trim()) { setResults([]); return; }
    debounceRef.current = setTimeout(async () => {
      setSearching(true);
      try {
        const data = await searchInventory(val.trim());
        setResults(data.items || []);
      } catch {
        setResults([]);
      } finally {
        setSearching(false);
      }
    }, 400);
  }

  function selectItem(item) {
    setSelected(item);
    setQuery(item.name);
    setResults([]);
    setAmount('');
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!selected) { toast('Search and select an item first', 'warning'); return; }
    const amt = parseInt(amount, 10);
    if (!amt || amt <= 0) { toast('Enter a valid quantity to add', 'warning'); return; }
    setSubmitting(true);
    try {
      const res = await restockItem(selected.id, amt);
      toast(`✓ Added ${amt} to ${selected.name}. New total: ${res.new_quantity}`, 'success');
      setQuery(''); setSelected(null); setAmount(''); setResults([]);
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">🔍 Quick Restock — Look Up an Existing Item</span>
      </div>
      <div className="card-body">
        <p className="text-sm text-muted mb-4" style={{ marginBottom: '16px' }}>
          Search for an item that's already in the system and add more stock — no re-entry needed.
        </p>
        <form onSubmit={handleSubmit} id="quick-restock-form">
          <div className="form-group" style={{ marginBottom: '16px' }}>
            <label className="form-label" htmlFor="quick-search-input">Item name</label>
            <div className="search-wrapper">
              <span className="search-icon">🔍</span>
              <input
                id="quick-search-input"
                type="text"
                className="search-input"
                placeholder="e.g. Canned Soup, Rice, Bread…"
                value={query}
                onChange={e => handleQueryChange(e.target.value)}
                autoComplete="off"
              />
              {searching && (
                <span style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)' }}>
                  <span className="spinner spinner-dark" />
                </span>
              )}
            </div>

            {results.length > 0 && !selected && (
              <div className="search-results">
                {results.map(item => (
                  <div
                    key={item.id}
                    className="search-result-item"
                    id={`search-result-${item.id}`}
                    onClick={() => selectItem(item)}
                  >
                    <div>
                      <div className="search-result-name">{item.name}</div>
                      <div className="search-result-meta">
                        {item.category} · {item.vendor} ·{' '}
                        {item.program === 'open_pantry' ? 'Open Pantry' : 'Grocery'}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <div className="font-semibold text-sm">{item.quantity}</div>
                      <div className="text-xs text-muted">current qty</div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {query && !searching && results.length === 0 && !selected && (
              <div className="text-xs text-muted mt-2" style={{ marginTop: '8px' }}>
                No items found. Try a different name or add it as a new item below.
              </div>
            )}
          </div>

          {selected && (
            <div className="alert alert-success" style={{ marginBottom: '16px' }}>
              <span className="alert-icon">✓</span>
              <div>
                <strong>{selected.name}</strong> selected ·{' '}
                {selected.category} · {selected.vendor} ·{' '}
                Current stock: <strong>{selected.quantity} {selected.units}</strong>
              </div>
            </div>
          )}

          <div className="form-grid" style={{ alignItems: 'flex-end' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="restock-qty-input">
                Quantity to add
              </label>
              <input
                id="restock-qty-input"
                type="number"
                min="1"
                className="form-input"
                placeholder="e.g. 24"
                value={amount}
                onChange={e => setAmount(e.target.value)}
                disabled={!selected}
              />
            </div>
            <button
              id="quick-restock-submit-btn"
              type="submit"
              className="btn btn-primary"
              disabled={!selected || submitting}
            >
              {submitting ? <><span className="spinner" /> Adding…</> : '+ Add Stock'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── New Item Form ──────────────────────────────────────────────────────────────
function NewItemForm() {
  const toast = useToast();
  const [vendors, setVendors]   = useState([]);
  const [submitting, setSubmitting] = useState(false);

  const BLANK = {
    name: '', vendor: '', category: '', weight: '', units: 'lbs',
    price_type: 'unit', price: '', program: 'open_pantry', quantity: '',
  };
  const [form, setForm] = useState(BLANK);

  useEffect(() => {
    getVendors().then(d => setVendors(d.vendors || [])).catch(() => {});
  }, []);

  function set(field, val) {
    setForm(prev => ({ ...prev, [field]: val }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const { name, vendor, category, weight, units, price_type, program, quantity } = form;
    if (!name.trim())     { toast('Item name is required', 'warning'); return; }
    if (!vendor.trim())   { toast('Vendor is required', 'warning'); return; }
    if (!category)        { toast('Category is required', 'warning'); return; }
    if (!quantity || parseInt(quantity) < 0) { toast('Enter a valid quantity', 'warning'); return; }

    setSubmitting(true);
    try {
      const payload = {
        name: name.trim(),
        vendor: vendor.trim(),
        category,
        weight: parseFloat(weight) || 0,
        units,
        price_type,
        program,
        quantity: parseInt(quantity),
        ...(form.price ? { price: parseFloat(form.price) } : {}),
      };
      await addItem(payload);
      toast(`✓ "${name}" added to inventory!`, 'success');
      setForm(BLANK);
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">📋 Add a Brand-New Item</span>
      </div>
      <div className="card-body">
        <form onSubmit={handleSubmit} id="new-item-form">
          <div className="form-grid" style={{ marginBottom: '16px' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="item-name-input">Item name *</label>
              <input
                id="item-name-input"
                type="text"
                className="form-input"
                placeholder="e.g. Organic Oats"
                value={form.name}
                onChange={e => set('name', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="item-category-select">Category *</label>
              <select
                id="item-category-select"
                className="form-select"
                value={form.category}
                onChange={e => set('category', e.target.value)}
              >
                <option value="">Select category…</option>
                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: '16px' }}>
            <label className="form-label" htmlFor="item-vendor-input">
              Vendor *{' '}
              <span>{vendors.length > 0 ? `(${vendors.length} on file)` : ''}</span>
            </label>
            <input
              id="item-vendor-input"
              type="text"
              className="form-input"
              placeholder="Enter vendor name"
              list="vendors-datalist"
              value={form.vendor}
              onChange={e => set('vendor', e.target.value)}
            />
            <datalist id="vendors-datalist">
              {vendors.map(v => <option key={v.id} value={v.name} />)}
            </datalist>
          </div>

          <div className="form-grid-3" style={{ marginBottom: '16px' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="item-weight-input">
                Weight <span>(optional)</span>
              </label>
              <input
                id="item-weight-input"
                type="number"
                min="0"
                step="0.01"
                className="form-input"
                placeholder="e.g. 2.5"
                value={form.weight}
                onChange={e => set('weight', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="item-units-select">Units</label>
              <select
                id="item-units-select"
                className="form-select"
                value={form.units}
                onChange={e => set('units', e.target.value)}
              >
                {UNITS.map(u => <option key={u} value={u}>{u}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="item-quantity-input">Initial quantity *</label>
              <input
                id="item-quantity-input"
                type="number"
                min="0"
                className="form-input"
                placeholder="e.g. 48"
                value={form.quantity}
                onChange={e => set('quantity', e.target.value)}
              />
            </div>
          </div>

          <div className="form-grid" style={{ marginBottom: '16px' }}>
            <div className="form-group">
              <label className="form-label">Pricing type</label>
              <div className="toggle-group">
                <button
                  type="button"
                  id="price-type-unit-btn"
                  className={`toggle-option${form.price_type === 'unit' ? ' active' : ''}`}
                  onClick={() => set('price_type', 'unit')}
                >
                  Per Unit
                </button>
                <button
                  type="button"
                  id="price-type-weight-btn"
                  className={`toggle-option${form.price_type === 'weight' ? ' active' : ''}`}
                  onClick={() => set('price_type', 'weight')}
                >
                  By Weight
                </button>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="item-price-input">
                Price <span>(optional, $/unit or $/lb)</span>
              </label>
              <input
                id="item-price-input"
                type="number"
                min="0"
                step="0.01"
                className="form-input"
                placeholder="e.g. 1.25"
                value={form.price}
                onChange={e => set('price', e.target.value)}
              />
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: '20px' }}>
            <label className="form-label">Program assignment</label>
            <div className="toggle-group">
              <button
                type="button"
                id="program-open-pantry-btn"
                className={`toggle-option${form.program === 'open_pantry' ? ' active' : ''}`}
                onClick={() => set('program', 'open_pantry')}
              >
                🏪 Open Pantry
              </button>
              <button
                type="button"
                id="program-grocery-btn"
                className={`toggle-option${form.program === 'grocery' ? ' active' : ''}`}
                onClick={() => set('program', 'grocery')}
              >
                🛒 Grocery Setup
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setForm(BLANK)}>
              Clear
            </button>
            <button id="new-item-submit-btn" type="submit" className="btn btn-primary btn-lg" disabled={submitting}>
              {submitting ? <><span className="spinner" /> Adding Item…</> : 'Add to Inventory'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────
export default function AddItem() {
  const [tab, setTab] = useState('restock');

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Add / Restock</h1>
        <p className="page-subtitle">Log incoming food and add stock to existing items</p>
      </div>

      <div className="add-item-tabs">
        <button
          id="tab-restock-btn"
          className={`add-item-tab${tab === 'restock' ? ' active' : ''}`}
          onClick={() => setTab('restock')}
        >
          🔍 Quick Restock
        </button>
        <button
          id="tab-new-item-btn"
          className={`add-item-tab${tab === 'new' ? ' active' : ''}`}
          onClick={() => setTab('new')}
        >
          ➕ Add New Item
        </button>
      </div>

      {tab === 'restock' ? <QuickRestock /> : <NewItemForm />}
    </div>
  );
}
