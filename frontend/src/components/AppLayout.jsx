import { Outlet } from 'react-router-dom';

export default function AppLayout() {
  return (
    <>
      <a className="skip-link" href="#main">
        Bỏ qua, tới nội dung chính
      </a>
      <header className="app-header">
        <img
          className="app-header__logo"
          src="/brand/logo.svg"
          alt="Logo Đại học Kinh tế Quốc dân"
        />
        <p className="app-header__title">NEU Student Learning Platform</p>
        <span className="mock-badge">Dữ liệu mẫu</span>
      </header>
      <main id="main" className="app-main">
        <Outlet />
      </main>
    </>
  );
}
