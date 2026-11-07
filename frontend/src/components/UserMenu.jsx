import { Award, LogOut, UserRound } from 'lucide-react';
import { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import { useAuth } from '../features/auth/AuthContext';
import { CERTIFICATES_PATH, ROLE_LABELS } from './menu';
import Avatar from './ui/Avatar';
import DropdownMenu from './ui/DropdownMenu';

/** Chấm trạng thái máy chủ, chỉ admin thấy, trong menu người dùng. */
function HealthDot() {
  const [status, setStatus] = useState('loading');

  useEffect(() => {
    const controller = new AbortController();
    apiRequest('/api/health', { signal: controller.signal })
      .then(() => setStatus('ok'))
      .catch((error) => {
        if (error.name !== 'AbortError') {
          setStatus('error');
        }
      });
    return () => controller.abort();
  }, []);

  const text = {
    loading: 'Đang kiểm tra máy chủ',
    ok: 'Máy chủ đang hoạt động',
    error: 'Không kết nối được máy chủ',
  }[status];
  return (
    <p className="health-dot">
      <span className={`health-dot__mark health-dot__mark--${status}`} aria-hidden="true" />
      {text}
    </p>
  );
}

export default function UserMenu({ onLogoutError }) {
  const { identity, role, logout } = useAuth();
  const name = identity.user.full_name;

  async function handleLogout() {
    onLogoutError('');
    try {
      await logout();
    } catch (caught) {
      onLogoutError(`Không đăng xuất được: ${caught.message}`);
    }
  }

  const items = [
    ...(role === 'student'
      ? [
          { label: 'Hồ sơ', icon: UserRound, to: '/ho-so' },
          { label: 'Chứng chỉ của tôi', icon: Award, to: CERTIFICATES_PATH },
        ]
      : []),
    { label: 'Đăng xuất', icon: LogOut, onSelect: handleLogout },
  ];

  return (
    <DropdownMenu
      triggerClass="user-menu__trigger"
      trigger={
        <>
          <Avatar name={name} size="sm" />
          <span className="user-menu__text">
            <strong>{name}</strong>
            <span>{ROLE_LABELS[role]}</span>
          </span>
        </>
      }
      header={role === 'admin' ? <HealthDot /> : null}
      items={items}
    />
  );
}
