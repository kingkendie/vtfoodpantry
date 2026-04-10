import { useState } from 'react';
import { registerStaff } from '../api.js';
import { useToast } from '../components/Toast.jsx';

export default function Staff() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  async function handleSubmit(e) {
    e.preventDefault();
    if (!email || !password) {
      toast('Please enter both email and password.', 'warning');
      return;
    }

    setLoading(true);
    try {
      await registerStaff(email.trim(), password);
      toast(`Success! Account created for ${email}`, 'success');
      setEmail('');
      setPassword('');
    } catch (err) {
      toast(err.message || 'Failed to create account.', 'error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Staff Management</h1>
        <p className="page-subtitle">Create accounts for new pantry volunteers and administrators</p>
      </div>

      <div className="dashboard-grid">
        <div className="card" style={{ maxWidth: '500px' }}>
          <div className="card-header">
            <span className="card-title">Register New Staff Member</span>
          </div>
          <div className="card-body">
            <form onSubmit={handleSubmit} className="form-group">
              <div className="form-group" style={{ marginBottom: '16px' }}>
                <label className="form-label" htmlFor="new-staff-email">Staff Email Address</label>
                <input
                  id="new-staff-email"
                  type="email"
                  className="form-input"
                  placeholder="volunteer@vtpantry.org"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  disabled={loading}
                />
                <p className="form-hint">They will use this email to log in.</p>
              </div>

              <div className="form-group" style={{ marginBottom: '24px' }}>
                <label className="form-label" htmlFor="new-staff-password">Temporary Password</label>
                <input
                  id="new-staff-password"
                  type="password"
                  className="form-input"
                  placeholder="Set a strong password..."
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  disabled={loading}
                />
                <p className="form-hint">Must be at least 6 characters long.</p>
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading || !email || !password}
                style={{ width: '100%' }}
              >
                {loading ? <><span className="spinner" /> Creating Account…</> : 'Create Staff Account'}
              </button>
            </form>
          </div>
        </div>

        <div className="card" style={{ maxWidth: '500px', alignSelf: 'flex-start' }}>
          <div className="card-header">
            <span className="card-title">Security Notice</span>
          </div>
          <div className="card-body">
            <p style={{ fontSize: '14px', color: 'var(--color-text-muted)', lineHeight: '1.6' }}>
              Only authenticated administrators can view this page and create new accounts. 
              When you create an account, it is immediately active and can be used to log into the VT Food Pantry backend.
              <br/><br/>
              <strong>Please securely transmit the temporary password to the new hire immediately after creation.</strong>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
