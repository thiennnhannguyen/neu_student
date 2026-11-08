import { Menu } from 'lucide-react';
import { useState } from 'react';
import { useLocation } from 'react-router';
import ScopeChip from '../features/m11/ScopeChip';
import StudentPicker from '../features/m11/StudentPicker';
import useStudentOptions from '../features/m11/useStudentOptions';
import { pageMetaFor } from './menu';
import { Breadcrumb } from './ui/PageHeader';
import NotificationBell from '../features/notifications/NotificationBell';
import UserMenu from './UserMenu';

/** Thanh trên cùng chỉ có đường dẫn phân cấp; tiêu đề trang là h1 duy nhất, nằm trong trang. */
export default function Topbar({ menuOpen, onToggleMenu }) {
  const { pathname } = useLocation();
  const [logoutError, setLogoutError] = useState('');
  const students = useStudentOptions();
  const meta = pageMetaFor(pathname);
  const error = logoutError || (students.failed ? 'Không tải được danh sách sinh viên.' : '');

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
      <div className="topbar__crumbs">
        {meta ? (
          meta.trail.length > 1 && <Breadcrumb items={meta.trail} />
        ) : (
          <p className="topbar__product">NEU Student</p>
        )}
      </div>
      <div className="topbar__tools">
        {students.enabled && <StudentPicker students={students} />}
        <ScopeChip students={students} />
        <NotificationBell />
        <UserMenu onLogoutError={setLogoutError} />
      </div>
      {error && (
        <p role="alert" className="status-error topbar__error">
          {error}
        </p>
      )}
    </header>
  );
}
