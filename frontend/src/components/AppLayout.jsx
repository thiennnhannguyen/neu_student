import { Outlet } from 'react-router';
import { M11ScopeProvider } from '../features/m11/M11ScopeContext';
import MockNotice from './MockNotice';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import { ToastProvider } from './ui/Toast';
import useSidebarState from './useSidebarState';

export default function AppLayout() {
  const { open, setOpen, collapsed, toggleCollapsed } = useSidebarState();

  return (
    <ToastProvider>
      <a className="skip-link" href="#main">
        Bỏ qua, tới nội dung chính
      </a>
      <div className={`app-frame${collapsed ? ' app-frame--rail' : ''}`}>
        <Sidebar
          open={open}
          onClose={() => setOpen(false)}
          collapsed={collapsed}
          onToggleCollapsed={toggleCollapsed}
        />
        {open && (
          // Nền mờ chỉ bắt chuột; bàn phím đóng bằng Esc.
          // eslint-disable-next-line jsx-a11y/no-static-element-interactions, jsx-a11y/click-events-have-key-events
          <div className="sidebar-scrim" onClick={() => setOpen(false)} />
        )}
        <div className="app-column">
          <M11ScopeProvider>
            <Topbar menuOpen={open} onToggleMenu={() => setOpen((value) => !value)} />
            <main id="main" className="app-main">
              <div className="app-content">
                <Outlet />
              </div>
              <MockNotice className="app-main__notice" />
            </main>
          </M11ScopeProvider>
        </div>
      </div>
    </ToastProvider>
  );
}
