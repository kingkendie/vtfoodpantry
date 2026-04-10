import { createContext, useContext, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastProvider } from './components/Toast.jsx';
import NavBar from './components/NavBar.jsx';
import Login from './pages/Login.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Inventory from './pages/Inventory.jsx';
import AddItem from './pages/AddItem.jsx';
import Vendors from './pages/Vendors.jsx';
import Operations from './pages/Operations.jsx';

// Auth context
const AuthContext = createContext(null);
export function useAuth() { return useContext(AuthContext); }

function ProtectedLayout() {
  return (
    <div className="app-layout">
      <NavBar />
      <main className="main-content">
        <Routes>
          <Route path="/"           element={<Dashboard />} />
          <Route path="/inventory"  element={<Inventory />} />
          <Route path="/add"        element={<AddItem />} />
          <Route path="/vendors"    element={<Vendors />} />
          <Route path="/operations" element={<Operations />} />
          <Route path="*"           element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

function RequireAuth({ children }) {
  const token = sessionStorage.getItem('vtp_token');
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  const [authState, setAuthState] = useState({
    token: sessionStorage.getItem('vtp_token'),
    email: sessionStorage.getItem('vtp_email'),
  });

  function setAuth(token, email) {
    sessionStorage.setItem('vtp_token', token);
    sessionStorage.setItem('vtp_email', email);
    setAuthState({ token, email });
  }

  return (
    <AuthContext.Provider value={{ ...authState, setAuth }}>
      <ToastProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/*"
              element={
                <RequireAuth>
                  <ProtectedLayout />
                </RequireAuth>
              }
            />
          </Routes>
        </Router>
      </ToastProvider>
    </AuthContext.Provider>
  );
}