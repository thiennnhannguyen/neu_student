import { useAuth } from '../features/auth/AuthContext';
import { ROLE_LABELS } from './menu';
import ShortcutGrid from './ShortcutGrid';
import WelcomeCard from './WelcomeCard';

/** Tổng quan của nhân sự hỗ trợ: không xem được bảng điểm nên không có số liệu học tập. */
export default function HomePage() {
  const { identity, role } = useAuth();
  return (
    <>
      <h1 className="visually-hidden">Tổng quan</h1>
      <WelcomeCard name={identity.user.full_name} line={ROLE_LABELS[role]} />
      <ShortcutGrid paths={['/m12/yeu-cau-ho-tro', '/m12/hoc-lieu']} />
    </>
  );
}
