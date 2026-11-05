import HomePage from '../../components/HomePage';
import { useAuth } from '../auth/AuthContext';
import OverviewPage from './OverviewPage';

/** support_staff không được xem bảng điểm nên giữ trang chung (Q79). */
export default function HomeRoute() {
  const { role } = useAuth();
  return role === 'support_staff' ? <HomePage /> : <OverviewPage />;
}
