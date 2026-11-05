import { useState } from 'react';
import { Outlet } from 'react-router';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

export default function AppLayout() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <>
      <a className="skip-link" href="#main">
        Bỏ qua, tới nội dung chính
      </a>
      <Navbar menuOpen={menuOpen} onToggleMenu={() => setMenuOpen((value) => !value)} />
      <div className="app-shell">
        <Sidebar open={menuOpen} onNavigate={() => setMenuOpen(false)} />
        <main id="main" className="app-main">
          <Outlet />
        </main>
      </div>
    </>
  );
}
