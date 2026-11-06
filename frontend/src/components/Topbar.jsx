import { Bell, Menu } from 'lucide-react';
import { useState } from 'react';
import { useLocation } from 'react-router';
import StudentPicker from '../features/m11/StudentPicker';
import { pageMetaFor } from './menu';
import Badge from './ui/Badge';
import { Breadcrumb } from './ui/PageHeader';
import UserMenu from './UserMenu';

export default function Topbar({ menuOpen, onToggleMenu }) {
  const { pathname } = useLocation();
  const [error, setError] = useState('');
  const meta = pageMetaFor(pathname);

  return (
    <header className="topbar">
      <button
        type="button"
        className="icon-button topbar__menu"
        aria-label="Menu"
        aria-expanded={menuOpen}
        aria-controls="app-sidebar"
        onClick={onToggleMenu}
      >
        <Menu size={22} aria-hidden="true" />
      </button>
      <div className="topbar__title">
        <p>{meta?.title ?? 'NEU Student'}</p>
        {meta && meta.trail.length > 1 && <Breadcrumb items={meta.trail} />}
      </div>
      <div className="topbar__tools">
        <StudentPicker />
        <Badge tone="outline" className="mock-badge">
          Dữ liệu mẫu
        </Badge>
        <span className="tooltip-host" data-tooltip="Có ở giai đoạn sau">
          <button
            type="button"
            className="icon-button"
            aria-label="Thông báo, có ở giai đoạn sau"
            aria-disabled="true"
          >
            <Bell size={20} aria-hidden="true" />
          </button>
        </span>
        <UserMenu onLogoutError={setError} />
      </div>
      {error && (
        <p role="alert" className="status-error topbar__error">
          {error}
        </p>
      )}
    </header>
  );
}
