import { Outlet } from 'react-router';
import BrandLogo from './BrandLogo';

export default function AppLayout() {
  return (
    <>
      <a className="skip-link" href="#main">
        Bỏ qua, tới nội dung chính
      </a>
      <header className="app-header">
        <BrandLogo />
        <p className="app-header__title">NEU Student Learning Platform</p>
        <span className="mock-badge">Dữ liệu mẫu</span>
      </header>
      <main id="main" className="app-main">
        <Outlet />
      </main>
    </>
  );
}
