import { Link, Outlet } from 'react-router';
import { useAuth } from './AuthContext';

/** Chỉ phục vụ trải nghiệm người dùng, quyền thật do server kiểm tra. */
export default function RoleRoute({ roles }) {
  const { role } = useAuth();

  if (!roles.includes(role)) {
    return (
      <section className="card">
        <h1>Bạn không có quyền xem trang này</h1>
        <Link to="/">Về Tổng quan</Link>
      </section>
    );
  }
  return <Outlet />;
}
