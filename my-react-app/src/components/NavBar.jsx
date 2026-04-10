import { NavLink, useNavigate } from 'react-router-dom';
import vtPantryLogo from '../assets/VTPantry.png';

const NAV_ITEMS = [
  { to: '/',           icon: '📊', label: 'Dashboard'   },
  { to: '/inventory',  icon: '📦', label: 'Inventory'   },
  { to: '/add',        icon: '➕', label: 'Add / Restock' },
  { to: '/vendors',    icon: '🏭', label: 'Vendors'     },
  { to: '/operations', icon: '⚙️', label: 'Operations'  },
  { to: '/staff',      icon: '👥', label: 'Staff'       },
];

export default function NavBar() {
  const navigate = useNavigate();
  const email = sessionStorage.getItem('vtp_email') || 'Staff';
  const initial = email.charAt(0).toUpperCase();

  function handleLogout() {
    sessionStorage.removeItem('vtp_token');
    sessionStorage.removeItem('vtp_email');
    navigate('/login');
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <img src={vtPantryLogo} alt="VT Pantry" />
        <div>
          <div className="sidebar-logo-text">VT Food Pantry</div>
          <div className="sidebar-logo-sub">Inventory System</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              'sidebar-nav-item' + (isActive ? ' active' : '')
            }
          >
            <span className="sidebar-nav-icon">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="sidebar-user-avatar">{initial}</div>
          <div className="sidebar-user-email">{email}</div>
        </div>
        <button className="sidebar-logout-btn" id="logout-btn" onClick={handleLogout}>
          🚪 Log out
        </button>
      </div>
    </aside>
  );
}
