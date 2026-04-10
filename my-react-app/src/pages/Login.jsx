import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, registerStaff } from '../api.js';
import { useAuth } from '../App.jsx';
import vtPantryLogo from '../assets/VTPantry.png';

export default function Login() {
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const [success, setSuccess]   = useState('');
  const [loading, setLoading]   = useState(false);
  const navigate = useNavigate();
  const { setAuth } = useAuth();

  async function handleSubmit(e) {
    e.preventDefault();
    if (!email || !password) { setError('Please enter your email and password.'); return; }
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      if (isSignUp) {
        await registerStaff(email.trim(), password);
        setSuccess('Account created! Logging you in...');
        // Auto login after sign up
        const data = await login(email.trim(), password);
        setAuth(data.idToken, email.trim());
        navigate('/', { replace: true });
      } else {
        const data = await login(email.trim(), password);
        setAuth(data.idToken, email.trim());
        navigate('/', { replace: true });
      }
    } catch (err) {
      setError(err.message || (isSignUp ? 'Registration failed.' : 'Invalid credentials. Please try again.'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <img src={vtPantryLogo} alt="VT Food Pantry" className="login-logo" />
        <h1 className="login-title">VT Food Pantry</h1>
        <p className="login-subtitle">{isSignUp ? 'Create a new account' : 'Sign in to manage inventory'}</p>

        <form className="login-form" onSubmit={handleSubmit} id="login-form">
          {error && (
            <div className="login-error">
              <span>⚠</span> {error}
            </div>
          )}
          {success && (
            <div className="login-error" style={{ background: 'var(--color-success)', color: 'white', borderColor: 'var(--color-success)' }}>
              <span>✓</span> {success}
            </div>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="login-email">Email address</label>
            <input
              id="login-email"
              type="email"
              className="form-input"
              placeholder="staff@vtpantry.org"
              value={email}
              onChange={e => setEmail(e.target.value)}
              autoComplete="email"
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              className="form-input"
              placeholder={isSignUp ? "Must be at least 6 characters" : "Enter your password"}
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete={isSignUp ? "new-password" : "current-password"}
            />
          </div>

          <button
            id="login-submit-btn"
            type="submit"
            className="btn btn-primary btn-lg w-full"
            disabled={loading}
            style={{ marginTop: '8px' }}
          >
            {loading ? <><span className="spinner" /> {isSignUp ? 'Creating account…' : 'Signing in…'}</> : (isSignUp ? 'Sign Up' : 'Sign In')}
          </button>
        </form>

        <p className="text-muted text-xs" style={{ marginTop: '24px', textAlign: 'center' }}>
          {isSignUp ? (
            <>Already have an account? <button type="button" className="btn-ghost" style={{ padding: 0, textDecoration: 'underline' }} onClick={() => { setIsSignUp(false); setError(''); setSuccess(''); }}>Sign In</button></>
          ) : (
            <>Need an account? <button type="button" className="btn-ghost" style={{ padding: 0, textDecoration: 'underline' }} onClick={() => { setIsSignUp(true); setError(''); setSuccess(''); }}>Sign Up</button></>
          )}
        </p>
      </div>
    </div>
  );
}
