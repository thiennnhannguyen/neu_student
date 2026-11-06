import { useAuth } from '../features/auth/AuthContext';
import { ROLE_LABELS } from './menu';
import ShortcutGrid from './ShortcutGrid';
import { PageHeader } from './ui';
import WelcomeCard from './WelcomeCard';

/** Tổng quan của nhân sự hỗ trợ: không xem được bảng điểm nên không có số liệu học tập. */
export default function HomePage() {
  const { identity, role } = useAuth();
  return (
    <>
      <PageHeader title="Tổng quan" description="Lối vào các việc hỗ trợ người học." />
      <WelcomeCard name={identity.user.full_name} line={ROLE_LABELS[role]} />
      <ShortcutGrid paths={['/m12/yeu-cau-ho-tro', '/m12/hoc-lieu']} />
    </>
  );
}
