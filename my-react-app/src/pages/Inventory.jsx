import { useState, useEffect, useCallback } from 'react';
import { getInventory, searchInventory, restockItem, transferItem, deleteItem } from '../api.js';
import Modal from '../components/Modal.jsx';
import { useToast } from '../components/Toast.jsx';

const PROGRAM_LABELS = { open_pantry: 'Open Pantry', grocery: 'Grocery' };

function ProgramBadge({ program }) {
  return program === 'open_pantry'
    ? <span className="badge badge-maroon"><span className="badge-dot" />Open Pantry</span>
    : <span className="badge badge-blue"><span className="badge-dot" />Grocery</span>;
}

export default function Inventory() {
  const [items, setItems]           = useState([]);
  const [loading, setLoading]       = useState(true);
  const [searchQ, setSearchQ]       = useState('');
  const [searching, setSearching]   = useState(false);
  const [program, setProgram]       = useState('all');

  // Modal states
  const [restockTarget,  setRestockTarget]  = useState(null);
  const [restockAmt,     setRestockAmt]     = useState('');
  const [restocking,     setRestocking]     = useState(false);
  const [transferTarget, setTransferTarget] = useState(null);
  const [transferring,   setTransferring]   = useState(false);
  const [deleteTarget,   setDeleteTarget]   = useState(null);
  const [deleting,       setDeleting]       = useState(false);

  const toast = useToast();

  const loadItems = useCallback(async (prog) => {
    setLoading(true);
    try {
      const data = await getInventory(prog === 'all' ? null : prog);
      setItems(data.items || []);
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadItems(program); }, [program]);

  async function handleSearch(q) {
    setSearchQ(q);
    if (!q.trim()) { loadItems(program); return; }
    setSearching(true);
    try {
      const data = await searchInventory(q.trim());
      let results = data.items || [];
      if (program !== 'all') results = results.filter(i => i.program === program);
      setItems(results);
    } catch {
      toast('Search failed', 'error');
    } finally {
      setSearching(false);
    }
  }

  async function doRestock() {
    const amount = parseInt(restockAmt, 10);
    if (!amount || amount <= 0) { toast('Enter a valid quantity', 'warning'); return; }
    setRestocking(true);
    try {
      const res = await restockItem(restockTarget.id, amount);
      toast(`${restockTarget.name} restocked. New qty: ${res.new_quantity}`, 'success');
      setRestockTarget(null); setRestockAmt('');
      loadItems(program);
    } catch (err) { toast(err.message, 'error'); }
    finally { setRestocking(false); }
  }

  async function doTransfer() {
    const newProg = transferTarget.program === 'open_pantry' ? 'grocery' : 'open_pantry';
    setTransferring(true);
    try {
      await transferItem(transferTarget.id, newProg);
      toast(`${transferTarget.name} moved to ${PROGRAM_LABELS[newProg]}`, 'success');
      setTransferTarget(null);
      loadItems(program);
    } catch (err) { toast(err.message, 'error'); }
    finally { setTransferring(false); }
  }

  async function doDelete() {
    setDeleting(true);
    try {
      await deleteItem(deleteTarget.id);
      toast(`${deleteTarget.name} removed from inventory`, 'success');
      setDeleteTarget(null);
      loadItems(program);
    } catch (err) { toast(err.message, 'error'); }
    finally { setDeleting(false); }
  }

  const newProgramLabel = transferTarget
    ? PROGRAM_LABELS[transferTarget.program === 'open_pantry' ? 'grocery' : 'open_pantry']
    : '';

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Inventory</h1>
        <p className="page-subtitle">All food items across both programs</p>
      </div>

      {/* Filter bar */}
      <div className="filter-bar">
        <div className="toggle-group">
          {['all', 'open_pantry', 'grocery'].map(p => (
            <button
              key={p}
              id={`filter-${p}-btn`}
              className={`toggle-option${program === p ? ' active' : ''}`}
              onClick={() => { setProgram(p); setSearchQ(''); }}
            >
              {p === 'all' ? 'All Items' : PROGRAM_LABELS[p]}
            </button>
          ))}
        </div>

        <div className="search-wrapper" style={{ flex: 1 }}>
          <span className="search-icon">🔍</span>
          <input
            id="inventory-search-input"
            type="search"
            className="search-input"
            placeholder="Search items (AI-powered)…"
            value={searchQ}
            onChange={e => handleSearch(e.target.value)}
          />
        </div>

        {searching && <span className="spinner spinner-dark" />}

        <span className="badge badge-gray">{items.length} items</span>
      </div>

      {/* Table */}
      {loading ? (
        <div className="page-loading">
          <span className="spinner spinner-dark" /> Loading inventory…
        </div>
      ) : items.length === 0 ? (
        <div className="empty-state" style={{ minHeight: '300px' }}>
          <span className="empty-state-icon">📭</span>
          <div className="empty-state-title">No items found</div>
          <div className="empty-state-desc">
            {searchQ ? 'Try a different search term.' : 'Add items using the Add / Restock page.'}
          </div>
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Category</th>
                <th>Vendor</th>
                <th>Program</th>
                <th>Qty</th>
                <th>Weight</th>
                <th>Price Type</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map(item => {
                const isLow = (item.quantity ?? 0) <= 10;
                return (
                  <tr key={item.id} className={isLow ? 'row-warning' : ''}>
                    <td>
                      <div className="font-medium">{item.name}</div>
                      {isLow && <div className="text-xs" style={{ color: 'var(--amber-600)' }}>⚠ Low stock</div>}
                    </td>
                    <td className="text-muted text-sm">{item.category || '—'}</td>
                    <td className="text-muted text-sm">{item.vendor || '—'}</td>
                    <td><ProgramBadge program={item.program} /></td>
                    <td>
                      <span className={`font-semibold${isLow ? ' text-sm' : ''}`}
                        style={{ color: isLow ? 'var(--amber-600)' : 'inherit' }}>
                        {item.quantity ?? 0}
                      </span>
                      <span className="text-xs text-muted"> {item.units}</span>
                    </td>
                    <td className="text-sm text-muted">{item.weight ? `${item.weight} lbs` : '—'}</td>
                    <td>
                      <span className="badge badge-gray">
                        {item.price_type === 'unit' ? 'Per Unit' : 'By Weight'}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end' }}>
                        <button
                          id={`restock-${item.id}-btn`}
                          className="btn btn-primary btn-sm"
                          onClick={() => { setRestockTarget(item); setRestockAmt(''); }}
                          title="Restock"
                        >
                          + Stock
                        </button>
                        <button
                          id={`transfer-${item.id}-btn`}
                          className="btn btn-secondary btn-sm"
                          onClick={() => setTransferTarget(item)}
                          title="Transfer to other program"
                        >
                          ⇄
                        </button>
                        <button
                          id={`delete-${item.id}-btn`}
                          className="btn btn-danger btn-sm"
                          onClick={() => setDeleteTarget(item)}
                          title="Remove item"
                        >
                          🗑
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Restock modal */}
      <Modal
        isOpen={!!restockTarget}
        onClose={() => { setRestockTarget(null); setRestockAmt(''); }}
        title="Add Stock"
        subtitle={restockTarget ? `${restockTarget.name} — current qty: ${restockTarget.quantity}` : ''}
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setRestockTarget(null)}>Cancel</button>
            <button id="confirm-restock-btn" className="btn btn-primary" onClick={doRestock} disabled={restocking}>
              {restocking ? <><span className="spinner" /> Saving…</> : 'Add Stock'}
            </button>
          </>
        }
      >
        <div className="form-group">
          <label className="form-label" htmlFor="restock-amount-input">Quantity to add</label>
          <input
            id="restock-amount-input"
            type="number"
            min="1"
            className="form-input"
            placeholder="e.g. 24"
            value={restockAmt}
            onChange={e => setRestockAmt(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && doRestock()}
            autoFocus
          />
        </div>
      </Modal>

      {/* Transfer modal */}
      <Modal
        isOpen={!!transferTarget}
        onClose={() => setTransferTarget(null)}
        title="Transfer Item"
        subtitle={transferTarget ? `Move "${transferTarget.name}" to ${newProgramLabel}` : ''}
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setTransferTarget(null)}>Cancel</button>
            <button id="confirm-transfer-btn" className="btn btn-primary" onClick={doTransfer} disabled={transferring}>
              {transferring ? <><span className="spinner" /> Moving…</> : `Move to ${newProgramLabel}`}
            </button>
          </>
        }
      >
        <div className="alert alert-warning">
          <span className="alert-icon">⚠</span>
          <div>
            This item is currently in <strong>
              {transferTarget ? PROGRAM_LABELS[transferTarget.program] : ''}
            </strong>. It will be moved to <strong>{newProgramLabel}</strong>.
          </div>
        </div>
      </Modal>

      {/* Delete modal */}
      <Modal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Remove Item"
        subtitle="This cannot be undone."
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setDeleteTarget(null)}>Cancel</button>
            <button id="confirm-delete-btn" className="btn btn-danger" onClick={doDelete} disabled={deleting}>
              {deleting ? <><span className="spinner" /> Removing…</> : 'Remove Item'}
            </button>
          </>
        }
      >
        <div className="alert alert-error">
          <span className="alert-icon">✕</span>
          <div>
            <strong>{deleteTarget?.name}</strong> will be permanently removed from the inventory.
          </div>
        </div>
      </Modal>
    </div>
  );
}
