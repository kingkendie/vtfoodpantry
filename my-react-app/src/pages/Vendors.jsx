import { useState, useEffect } from 'react';
import { getVendors, addVendor, deleteVendor, getInvoices, addInvoice } from '../api.js';
import Modal from '../components/Modal.jsx';
import { useToast } from '../components/Toast.jsx';

function InvoiceRow({ invoice }) {
  return (
    <tr>
      <td className="text-sm">{invoice.date || '—'}</td>
      <td className="text-sm">${parseFloat(invoice.amount || 0).toFixed(2)}</td>
      <td className="text-sm">{invoice.description || '—'}</td>
      <td className="text-sm text-muted">{invoice.items_delivered || '—'}</td>
    </tr>
  );
}

function VendorCard({ vendor, onDelete }) {
  const [expanded,  setExpanded]  = useState(false);
  const [invoices,  setInvoices]  = useState([]);
  const [loadingInv, setLoadingInv] = useState(false);
  const [showInvModal, setShowInvModal] = useState(false);
  const [invForm, setInvForm]    = useState({ date: '', amount: '', description: '', items_delivered: '' });
  const [saving, setSaving]      = useState(false);
  const toast = useToast();

  async function toggleExpand() {
    const next = !expanded;
    setExpanded(next);
    if (next && invoices.length === 0) {
      setLoadingInv(true);
      try {
        const data = await getInvoices(vendor.id);
        setInvoices(data.invoices || []);
      } catch {
        toast('Could not load invoices', 'error');
      } finally {
        setLoadingInv(false);
      }
    }
  }

  async function handleAddInvoice(e) {
    e.preventDefault();
    const { date, amount, description, items_delivered } = invForm;
    if (!date || !amount || !description || !items_delivered) {
      toast('All invoice fields are required', 'warning'); return;
    }
    setSaving(true);
    try {
      const data = await addInvoice(vendor.id, {
        date,
        amount: parseFloat(amount),
        description,
        items_delivered,
      });
      setInvoices(prev => [...prev, data.invoice]);
      toast('Invoice logged successfully', 'success');
      setShowInvModal(false);
      setInvForm({ date: '', amount: '', description: '', items_delivered: '' });
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="vendor-card">
      <div className="vendor-card-header">
        <div>
          <div className="vendor-name">{vendor.name}</div>
          <div className="vendor-info" style={{ marginTop: '6px' }}>
            {vendor.contact_email && (
              <div className="vendor-info-row">
                <span>✉</span> {vendor.contact_email}
              </div>
            )}
            {vendor.contact_phone && (
              <div className="vendor-info-row">
                <span>📞</span> {vendor.contact_phone}
              </div>
            )}
            {vendor.address && (
              <div className="vendor-info-row">
                <span>📍</span> {vendor.address}
              </div>
            )}
          </div>
        </div>
        <button
          className="btn btn-danger btn-sm btn-icon"
          id={`delete-vendor-${vendor.id}-btn`}
          onClick={() => onDelete(vendor)}
          title="Remove vendor"
        >
          🗑
        </button>
      </div>

      <div className="vendor-actions">
        <button
          className="btn btn-secondary btn-sm"
          id={`expand-vendor-${vendor.id}-btn`}
          onClick={toggleExpand}
        >
          {expanded ? '▲ Hide Invoices' : '▼ View Invoices'}
        </button>
        <button
          className="btn btn-primary btn-sm"
          id={`add-invoice-${vendor.id}-btn`}
          onClick={() => setShowInvModal(true)}
        >
          + Log Invoice
        </button>
      </div>

      {expanded && (
        <div className="invoice-section">
          {loadingInv ? (
            <div className="page-loading" style={{ minHeight: '60px' }}>
              <span className="spinner spinner-dark" /> Loading invoices…
            </div>
          ) : invoices.length === 0 ? (
            <p className="text-sm text-muted" style={{ marginTop: '8px' }}>
              No invoices logged yet.
            </p>
          ) : (
            <div className="table-wrapper" style={{ marginTop: '12px' }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Amount</th>
                    <th>Description</th>
                    <th>Items Delivered</th>
                  </tr>
                </thead>
                <tbody>
                  {invoices.map(inv => <InvoiceRow key={inv.id} invoice={inv} />)}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Add invoice modal */}
      <Modal
        isOpen={showInvModal}
        onClose={() => setShowInvModal(false)}
        title={`Log Invoice — ${vendor.name}`}
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setShowInvModal(false)}>Cancel</button>
            <button
              id={`save-invoice-${vendor.id}-btn`}
              className="btn btn-primary"
              onClick={handleAddInvoice}
              disabled={saving}
            >
              {saving ? <><span className="spinner" /> Saving…</> : 'Log Invoice'}
            </button>
          </>
        }
      >
        <div className="form-group">
          <label className="form-label" htmlFor={`inv-date-${vendor.id}`}>Delivery date *</label>
          <input
            id={`inv-date-${vendor.id}`}
            type="date"
            className="form-input"
            value={invForm.date}
            onChange={e => setInvForm(p => ({ ...p, date: e.target.value }))}
          />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor={`inv-amount-${vendor.id}`}>Invoice amount ($) *</label>
          <input
            id={`inv-amount-${vendor.id}`}
            type="number"
            min="0"
            step="0.01"
            className="form-input"
            placeholder="e.g. 250.00"
            value={invForm.amount}
            onChange={e => setInvForm(p => ({ ...p, amount: e.target.value }))}
          />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor={`inv-desc-${vendor.id}`}>Description *</label>
          <input
            id={`inv-desc-${vendor.id}`}
            type="text"
            className="form-input"
            placeholder="e.g. Weekly produce delivery"
            value={invForm.description}
            onChange={e => setInvForm(p => ({ ...p, description: e.target.value }))}
          />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor={`inv-items-${vendor.id}`}>Items delivered *</label>
          <textarea
            id={`inv-items-${vendor.id}`}
            className="form-textarea"
            placeholder="e.g. 50x Apples, 20x Bags of Rice, 12x Canned Beans"
            value={invForm.items_delivered}
            onChange={e => setInvForm(p => ({ ...p, items_delivered: e.target.value }))}
          />
        </div>
      </Modal>
    </div>
  );
}

export default function Vendors() {
  const [vendors,   setVendors]   = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [showAdd,   setShowAdd]   = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [saving,   setSaving]   = useState(false);
  const [newVendor, setNewVendor] = useState({
    name: '', contact_email: '', contact_phone: '', address: '',
  });
  const toast = useToast();

  async function load() {
    setLoading(true);
    try {
      const data = await getVendors();
      setVendors(data.vendors || []);
    } catch {
      toast('Failed to load vendors', 'error');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleAddVendor(e) {
    e.preventDefault();
    if (!newVendor.name.trim()) { toast('Vendor name is required', 'warning'); return; }
    setSaving(true);
    try {
      await addVendor(newVendor);
      toast(`${newVendor.name} added`, 'success');
      setShowAdd(false);
      setNewVendor({ name: '', contact_email: '', contact_phone: '', address: '' });
      load();
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await deleteVendor(deleteTarget.id);
      toast(`${deleteTarget.name} removed`, 'success');
      setDeleteTarget(null);
      load();
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      setDeleting(false);
    }
  }

  function setNV(field, val) {
    setNewVendor(p => ({ ...p, [field]: val }));
  }

  return (
    <div className="page">
      <div className="page-header">
        <div className="section-heading">
          <div>
            <h1 className="page-title">Vendors</h1>
            <p className="page-subtitle">Suppliers and delivery invoice tracking</p>
          </div>
          <button
            id="add-vendor-btn"
            className="btn btn-primary"
            onClick={() => setShowAdd(true)}
          >
            + Add Vendor
          </button>
        </div>
      </div>

      {loading ? (
        <div className="page-loading">
          <span className="spinner spinner-dark" /> Loading vendors…
        </div>
      ) : vendors.length === 0 ? (
        <div className="empty-state">
          <span className="empty-state-icon">🏭</span>
          <div className="empty-state-title">No vendors yet</div>
          <div className="empty-state-desc">Add your first vendor to track deliveries and invoices.</div>
          <button className="btn btn-primary" onClick={() => setShowAdd(true)}>+ Add First Vendor</button>
        </div>
      ) : (
        <div className="vendor-grid">
          {vendors.map(v => (
            <VendorCard key={v.id} vendor={v} onDelete={setDeleteTarget} />
          ))}
        </div>
      )}

      {/* Add vendor modal */}
      <Modal
        isOpen={showAdd}
        onClose={() => setShowAdd(false)}
        title="Add New Vendor"
        subtitle="Track this supplier's deliveries and invoices"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setShowAdd(false)}>Cancel</button>
            <button
              id="save-vendor-btn"
              className="btn btn-primary"
              onClick={handleAddVendor}
              disabled={saving}
            >
              {saving ? <><span className="spinner" /> Saving…</> : 'Add Vendor'}
            </button>
          </>
        }
      >
        <div className="form-group">
          <label className="form-label" htmlFor="new-vendor-name">Vendor name *</label>
          <input
            id="new-vendor-name"
            type="text"
            className="form-input"
            placeholder="e.g. Local Farm Co."
            value={newVendor.name}
            onChange={e => setNV('name', e.target.value)}
            autoFocus
          />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="new-vendor-email">Contact email</label>
          <input
            id="new-vendor-email"
            type="email"
            className="form-input"
            placeholder="contact@vendor.com"
            value={newVendor.contact_email}
            onChange={e => setNV('contact_email', e.target.value)}
          />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="new-vendor-phone">Contact phone</label>
          <input
            id="new-vendor-phone"
            type="tel"
            className="form-input"
            placeholder="555-123-4567"
            value={newVendor.contact_phone}
            onChange={e => setNV('contact_phone', e.target.value)}
          />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="new-vendor-address">Address</label>
          <input
            id="new-vendor-address"
            type="text"
            className="form-input"
            placeholder="123 Main St, Burlington VT"
            value={newVendor.address}
            onChange={e => setNV('address', e.target.value)}
          />
        </div>
      </Modal>

      {/* Delete confirm modal */}
      <Modal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Remove Vendor"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setDeleteTarget(null)}>Cancel</button>
            <button
              id="confirm-delete-vendor-btn"
              className="btn btn-danger"
              onClick={handleDelete}
              disabled={deleting}
            >
              {deleting ? <><span className="spinner" /> Removing…</> : 'Remove Vendor'}
            </button>
          </>
        }
      >
        <div className="alert alert-error">
          <span className="alert-icon">✕</span>
          <div>
            <strong>{deleteTarget?.name}</strong> and all their invoice records will be permanently removed.
          </div>
        </div>
      </Modal>
    </div>
  );
}
