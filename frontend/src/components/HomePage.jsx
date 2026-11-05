import { useAuth } from '../features/auth/AuthContext';
import HealthStatus from './HealthStatus';

export default function HomePage() {
  const { identity } = useAuth();

  return (
    <section className="card">
      <h1>Tổng quan</h1>
      <p>Xin chào {identity.user.full_name}. Nội dung tổng quan đang phát triển.</p>
      <h2>Trạng thái hệ thống</h2>
      <HealthStatus />
    </section>
  );
}
