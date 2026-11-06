import Button from '../../components/ui/Button';
import { Navigate, Outlet, useLocation } from 'react-router';
import { useAuth } from './AuthContext';
import { LOGIN_PATH } from './redirect';

/**
 * Chỉ phục vụ trải nghiệm người dùng: ẩn trang và chuyển hướng cho đúng.
 * Bảo vệ thật nằm ở server (@require_roles). Không dựa vào component này để bảo mật.
 */
export default function ProtectedRoute() {
  const { status, message, loggedOut, retry } = useAuth();
  const location = useLocation();

  if (status === 'loading') {
    return (
      <p role="status" className="page-status">
        Đang kiểm tra phiên đăng nhập...
      </p>
    );
  }
  if (status === 'error') {
    return (
      <div role="alert" className="page-status">
        <p className="status-error">Không kiểm tra được phiên đăng nhập: {message}</p>
        <Button onClick={retry}>Thử lại</Button>
      </div>
    );
  }
  if (status === 'anonymous') {
    const state = loggedOut ? undefined : { from: location.pathname };
    return <Navigate to={LOGIN_PATH} state={state} replace />;
  }
  return <Outlet />;
}
