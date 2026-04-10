import { useState, useEffect } from 'react';
import {
  getCheckpoints, createCheckpoint,
  runRollover, exportToSheets,
} from '../api.js';
import Modal from '../components/Modal.jsx';
import { useToast } from '../components/Toast.jsx';

function formatDate(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch { return iso; }
}

export default function Operations() {
  const [checkpoints,   setCheckpoints]   = useState([]);
  const [loadingCPs,    setLoadingCPs]    = useState(true);
  const [cpLabel,       setCpLabel]       = useState('');
  const [savingCP,      setSavingCP]      = useState(false);
  const [showCPModal,   setShowCPModal]   = useState(false);

  const [showRollover,  setShowRollover]  = useState(false);
  const [rollingOver,   setRollingOver]   = useState(false);
  const [rolloverResult, setRolloverResult] = useState(null);

  const [exporting,     setExporting]     = useState(false);
  const [exportResult,  setExportResult]  = useState(null);

  const toast = useToast();

  async function loadCheckpoints() {
    setLoadingCPs(true);
    try {
      const data = await getCheckpoints();
      setCheckpoints(data.checkpoints || []);
    } catch {
      toast('Failed to load checkpoints', 'error');
    } finally {
      setLoadingCPs(false);
    }
  }

  useEffect(() => { loadCheckpoints(); }, []);

  async function handleCreateCheckpoint() {
    setSavingCP(true);
    try {
      const res = await createCheckpoint(cpLabel.trim());
      toast(`Checkpoint saved — ${res.item_count} items captured`, 'success');
      setCpLabel('');
      setShowCPModal(false);
      loadCheckpoints();
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      setSavingCP(false);
    }
  }

  async function handleRollover() {
    setRollingOver(true);
    try {
      const res = await runRollover();
      setRolloverResult(res);
      toast(`Year-end rollover complete for ${res.year}`, 'success');
      setShowRollover(false);
      loadCheckpoints();
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      setRollingOver(false);
    }
  }

  async function handleExport() {
    setExporting(true);
    setExportResult(null);
    try {
      const res = await exportToSheets();
      setExportResult(res);
      toast(`${res.rows_written} rows synced to Google Sheets`, 'success');
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Operations</h1>
        <p className="page-subtitle">Checkpoints, year-end rollover, and data export</p>
      </div>

      <div className="operations-grid">
        {/* Left column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

          {/* Checkpoints */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">📋 Inventory Checkpoints</span>
              <button
                id="create-checkpoint-btn"
                className="btn btn-primary btn-sm"
                onClick={() => setShowCPModal(true)}
              >
                + New Checkpoint
              </button>
            </div>
            <div className="card-body" style={{ padding: '16px' }}>
              <p className="text-sm text-muted mb-4" style={{ marginBottom: '12px' }}>
                A checkpoint freezes the current inventory state as a historical record.
                Use these to set periodic baselines or before a major change.
              </p>

              {loadingCPs ? (
                <div className="page-loading" style={{ minHeight: '80px' }}>
                  <span className="spinner spinner-dark" /> Loading…
                </div>
              ) : checkpoints.length === 0 ? (
                <div className="empty-state" style={{ padding: '24px' }}>
                  <span className="empty-state-icon">📷</span>
                  <div className="empty-state-title">No checkpoints yet</div>
                  <div className="empty-state-desc">Create your first checkpoint to start tracking history.</div>
                </div>
              ) : (
                <div className="checkpoint-list">
                  {checkpoints.map(cp => (
                    <div key={cp.id} className="checkpoint-item">
                      <div>
                        <div className="checkpoint-label">
                          {cp.label || 'Unlabeled checkpoint'}
                        </div>
                        <div className="checkpoint-meta">{formatDate(cp.timestamp)}</div>
                      </div>
                      <span className="badge badge-maroon">{cp.item_count} items</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Google Sheets Export */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">📊 Google Sheets Export</span>
            </div>
            <div className="card-body">
              <div className="export-box">
                <span className="export-icon">📗</span>
                <div className="export-info">
                  <div className="export-title">Sync to Spreadsheet</div>
                  <div className="export-desc">
                    Writes the full inventory to the connected Google Sheet.
                    Previous data is cleared and replaced with the latest snapshot.
                  </div>
                </div>
                <button
                  id="export-sheets-btn"
                  className="btn btn-primary btn-sm"
                  disabled={exporting}
                  onClick={handleExport}
                  style={{ flexShrink: 0 }}
                >
                  {exporting ? <><span className="spinner" /> Syncing…</> : 'Sync Now'}
                </button>
              </div>

              {exportResult && (
                <div className="alert alert-success" style={{ marginTop: '12px' }}>
                  <span className="alert-icon">✓</span>
                  <div>
                    <strong>{exportResult.rows_written}</strong> rows written to Google Sheets successfully.
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right column — Rollover */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="card">
            <div className="card-header">
              <span className="card-title">🔄 Year-End Rollover</span>
            </div>
            <div className="card-body">
              <div className="rollover-box">
                <span className="rollover-icon">🎯</span>
                <div className="rollover-title">Annual Inventory Rollover</div>
                <div className="rollover-desc">
                  Captures the current inventory as a year-end snapshot, records
                  total quantities, and carries all remaining stock forward as the
                  starting baseline for the new year. Run this once at year-end.
                </div>
                <button
                  id="run-rollover-btn"
                  className="btn btn-primary btn-lg"
                  onClick={() => setShowRollover(true)}
                >
                  Run Year-End Rollover
                </button>
              </div>

              {rolloverResult && (
                <div className="alert alert-success" style={{ marginTop: '16px' }}>
                  <span className="alert-icon">✓</span>
                  <div>
                    <strong>{rolloverResult.year}</strong> rollover complete ·{' '}
                    <strong>{rolloverResult.items_carried_forward}</strong> items carried forward ·{' '}
                    Total quantity: <strong>{rolloverResult.total_quantity?.toLocaleString()}</strong>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* What is a checkpoint — explainer */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">💡 When to Use Each Feature</span>
            </div>
            <div className="card-body">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div>
                  <div className="font-semibold text-sm" style={{ marginBottom: '4px' }}>📋 Checkpoint</div>
                  <div className="text-sm text-muted">
                    Take a snapshot at any time — weekly, monthly, or before a big order.
                    Labels like "End of Fall Semester" make them easy to find later.
                  </div>
                </div>
                <div className="divider" style={{ margin: '0' }} />
                <div>
                  <div className="font-semibold text-sm" style={{ marginBottom: '4px' }}>🔄 Rollover</div>
                  <div className="text-sm text-muted">
                    Run once at year-end. It automatically creates a pre-rollover
                    checkpoint and logs the annual totals for reporting.
                  </div>
                </div>
                <div className="divider" style={{ margin: '0' }} />
                <div>
                  <div className="font-semibold text-sm" style={{ marginBottom: '4px' }}>📊 Export</div>
                  <div className="text-sm text-muted">
                    Sync any time you want a fresh copy in Google Sheets for
                    reporting, printing, or sharing with leadership.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Create Checkpoint Modal */}
      <Modal
        isOpen={showCPModal}
        onClose={() => setShowCPModal(false)}
        title="Create Checkpoint"
        subtitle="Saves the current state of all inventory items"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setShowCPModal(false)}>Cancel</button>
            <button
              id="save-checkpoint-btn"
              className="btn btn-primary"
              onClick={handleCreateCheckpoint}
              disabled={savingCP}
            >
              {savingCP ? <><span className="spinner" /> Saving…</> : 'Save Checkpoint'}
            </button>
          </>
        }
      >
        <div className="form-group">
          <label className="form-label" htmlFor="checkpoint-label-input">
            Label <span>(optional)</span>
          </label>
          <input
            id="checkpoint-label-input"
            type="text"
            className="form-input"
            placeholder="e.g. End of Fall Semester 2025"
            value={cpLabel}
            onChange={e => setCpLabel(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleCreateCheckpoint()}
            autoFocus
          />
          <div className="form-hint">
            Leave blank for an unlabeled snapshot.
          </div>
        </div>
      </Modal>

      {/* Rollover Confirm Modal */}
      <Modal
        isOpen={showRollover}
        onClose={() => setShowRollover(false)}
        title="Run Year-End Rollover?"
        subtitle={`This will snapshot ${new Date().getFullYear()} and carry stock forward.`}
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setShowRollover(false)}>Cancel</button>
            <button
              id="confirm-rollover-btn"
              className="btn btn-primary"
              onClick={handleRollover}
              disabled={rollingOver}
            >
              {rollingOver ? <><span className="spinner" /> Running…</> : `Yes, Run ${new Date().getFullYear()} Rollover`}
            </button>
          </>
        }
      >
        <div className="alert alert-warning">
          <span className="alert-icon">⚠</span>
          <div>
            This will:<br />
            <strong>1.</strong> Save a year-end snapshot of all current inventory<br />
            <strong>2.</strong> Log the totals for {new Date().getFullYear()}<br />
            <strong>3.</strong> Carry all remaining stock into the next year<br /><br />
            Existing items are <strong>not deleted</strong>. You can run this safely.
          </div>
        </div>
      </Modal>
    </div>
  );
}
