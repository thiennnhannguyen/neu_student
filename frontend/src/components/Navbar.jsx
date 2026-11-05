import { useState } from 'react';
import { useAuth } from '../features/auth/AuthContext';
import BrandLogo from './BrandLogo';
import { ROLE_LABELS } from './menu';

export default function Navbar({ menuOpen, onToggleMenu }) {
  const { identity, role, logout } = useAuth();
  const [loggingOut, setLoggingOut] = useState(false);
  const [error, setError] = useState('');

  async function handleLogout() {
    setError('');
    setLoggingOut(true);
    try {
      await logout();
    } catch (caught) {
      setError(`Không đăng xuất được: ${caught.message}`);
      setLoggingOut(false);
    }
  }

  return (
    <header className="app-header">
      <button
        type="button"
        className="button button--ghost menu-toggle"
        aria-expanded={menuOpen}
        aria-controls="app-sidebar"
        onClick={onToggleMenu}
      >
        Menu
      </button>
      <BrandLogo />
      <p className="app-header__title">NEU Student Learning Platform</p>
      <span className="mock-badge">Dữ liệu mẫu</span>
      <div className="app-header__user">
        <span>
          <strong>{identity.user.full_name}</strong> · {ROLE_LABELS[role]}
        </span>
        <button
          type="button"
          className="button button--ghost"
          disabled={loggingOut}
          onClick={handleLogout}
        >
          Đăng xuất
        </button>
      </div>
      {error && (
        <p role="alert" className="status-error app-header__error">
          {error}
        </p>
      )}
    </header>
  );
}
