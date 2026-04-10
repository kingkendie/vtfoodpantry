import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getStats, getLowStock, restockItem } from '../api.js';
import StatCard from '../components/StatCard.jsx';
import Modal from '../components/Modal.jsx';
import { useToast } from '../components/Toast.jsx';

export default function Dashboard() {
  const [stats, setStats]         = useState(null);
  const [lowStock, setLowStock]   = useState([]);
  const [loading, setLoading]     = useState(true);
  const [restockItem_, setRestockItem] = useState(null);
  const [restockAmt, setRestockAmt]   = useState('');
  const [restocking, setRestocking]   = useState(false);
  const toast   = useToast();
  const navigate = useNavigate();

  async function load() {
    setLoading(true);
    try {
      const [s, ls] = await Promise.all([getStats(), getLowStock(10)]);
      setStats(s);
      setLowStock(ls.items || []);
    } catch {
      toast('Failed to load dashboard data', 'error');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleRestock() {
    const amount = parseInt(restockAmt, 10);
    if (!amount || amount <= 0) { toast('Enter a valid quantity', 'warning'); return; }
    setRestocking(true);
    try {
      const res = await restockItem(restockItem_.id, amount);
      toast(`✓ ${restockItem_.name} restocked — new qty: ${res.new_quantity}`, 'success');
      setRestockItem(null);
      setRestockAmt('');
      load();
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      setRestocking(false);
    }
  }

  const programPct = stats && stats.total_items > 0
    ? Math.round((stats.open_pantry_items / stats.total_items) * 100)
    : 50;

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">Live snapshot of pantry inventory</p>
      </div>

      {loading ? (
        <div className="page-loading">
          <span className="spinner spinner-dark" />
          Loading…
        </div>
      ) : (
        <>
          {/* Stat grid */}
          <div className="stat-grid">
            <StatCard
              icon="📦"
              value={stats?.total_items ?? 0}
              label="Total Items"
              color="var(--color-primary)"
            />
            <StatCard
              icon="🏪"
              value={stats?.open_pantry_items ?? 0}
              label="Open Pantry"
              color="var(--color-primary)"
            />
            <StatCard
              icon="🛒"
              value={stats?.grocery_items ?? 0}
              label="Grocery Setup"
              color="var(--blue-600)"
            />
            <StatCard
              icon="📊"
              value={stats?.total_quantity?.toLocaleString() ?? 0}
              label="Total Quantity"
              color="var(--amber-500)"
            />
            <StatCard
              icon="⚠️"
              value={stats?.low_stock_items ?? 0}
              label="Low Stock"
              color="var(--red-600)"
            />
          </div>

          {/* Main grid */}
          <div className="dashboard-grid">
            {/* Program split visual */}
            <div className="card">
              <div className="card-header">
                <span className="card-title">Program Breakdown</span>
                <button
                  className="btn btn-secondary btn-sm"
                  id="view-inventory-btn"
                  onClick={() => navigate('/inventory')}
                >
                  View All →
                </button>
              </div>
              <div className="card-body">
                <div style={{ marginBottom: '16px' }}>
                  <div className="flex items-center justify-between mb-4" style={{ marginBottom: '8px' }}>
                    <span className="text-sm font-medium">Open Pantry</span>
                    <span className="text-sm text-muted">{stats?.open_pantry_items} items</span>
                  </div>
                  <div style={{
                    height: '12px',
                    background: 'var(--gray-100)',
                    borderRadius: 'var(--radius-full)',
                    overflow: 'hidden',
                  }}>
                    <div style={{
                      height: '100%',
                      width: `${programPct}%`,
                      background: 'linear-gradient(90deg, var(--color-primary), var(--color-accent))',
                      borderRadius: 'var(--radius-full)',
                      transition: 'width 0.6s ease',
                    }} />
                  </div>
                  <div className="flex items-center justify-between mt-2" style={{ marginTop: '8px' }}>
                    <span className="text-sm font-medium" style={{ color: 'var(--blue-600)' }}>Grocery Setup</span>
                    <span className="text-sm text-muted">{stats?.grocery_items} items</span>
                  </div>
                  <div style={{
                    height: '12px',
                    background: 'var(--gray-100)',
                    borderRadius: 'var(--radius-full)',
                    overflow: 'hidden',
                    marginTop: '8px',
                  }}>
                    <div style={{
                      height: '100%',
                      width: `${100 - programPct}%`,
                      background: 'linear-gradient(90deg, var(--blue-600), #60a5fa)',
                      borderRadius: 'var(--radius-full)',
                      transition: 'width 0.6s ease',
                    }} />
                  </div>
                </div>

                <div className="divider" />

                <div style={{ display: 'flex', gap: '16px', justifyContent: 'center' }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '28px', fontWeight: '700', color: 'var(--color-primary)' }}>
                      {stats?.total_items > 0 ? `${programPct}%` : '—'}
                    </div>
                    <div className="text-xs text-muted">Open Pantry Share</div>
                  </div>
                  <div style={{ width: '1px', background: 'var(--color-border)' }} />
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '28px', fontWeight: '700', color: 'var(--blue-600)' }}>
                      {stats?.total_items > 0 ? `${100 - programPct}%` : '—'}
                    </div>
                    <div className="text-xs text-muted">Grocery Share</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Low stock alerts */}
            <div className="card">
              <div className="card-header">
                <span className="card-title">⚠️ Low Stock Alerts</span>
                <span className="badge badge-amber">{lowStock.length}</span>
              </div>
              <div className="card-body" style={{ padding: '16px' }}>
                {lowStock.length === 0 ? (
                  <div className="empty-state" style={{ padding: '32px 16px' }}>
                    <span className="empty-state-icon">✅</span>
                    <span className="empty-state-title">All stocked up!</span>
                    <span className="empty-state-desc text-xs">No items below the threshold of 10.</span>
                  </div>
                ) : (
                  <div className="low-stock-list">
                    {lowStock.slice(0, 8).map(item => (
                      <div key={item.id} className="low-stock-item">
                        <div>
                          <div className="low-stock-name">{item.name}</div>
                          <div className="low-stock-qty">
                            {item.quantity} left · {item.program === 'open_pantry' ? 'Open Pantry' : 'Grocery'}
                          </div>
                        </div>
                        <button
                          className="btn btn-primary btn-sm"
                          id={`restock-${item.id}-btn`}
                          onClick={() => { setRestockItem(item); setRestockAmt(''); }}
                        >
                          Restock
                        </button>
                      </div>
                    ))}
                    {lowStock.length > 8 && (
                      <button
                        className="btn btn-ghost btn-sm w-full"
                        onClick={() => navigate('/inventory')}
                      >
                        View {lowStock.length - 8} more →
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}

      {/* Restock modal */}
      <Modal
        isOpen={!!restockItem_}
        onClose={() => { setRestockItem(null); setRestockAmt(''); }}
        title={`Restock: ${restockItem_?.name}`}
        subtitle={`Current quantity: ${restockItem_?.quantity}`}
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setRestockItem(null)}>Cancel</button>
            <button
              id="confirm-restock-btn"
              className="btn btn-primary"
              onClick={handleRestock}
              disabled={restocking}
            >
              {restocking ? <><span className="spinner" /> Saving…</> : 'Add Stock'}
            </button>
          </>
        }
      >
        <div className="form-group">
          <label className="form-label" htmlFor="dashboard-restock-amount">
            Quantity to add
          </label>
          <input
            id="dashboard-restock-amount"
            type="number"
            min="1"
            className="form-input"
            placeholder="e.g. 24"
            value={restockAmt}
            onChange={e => setRestockAmt(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleRestock()}
            autoFocus
          />
        </div>
      </Modal>
    </div>
  );
}
