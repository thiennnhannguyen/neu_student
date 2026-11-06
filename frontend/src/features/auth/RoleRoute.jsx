import { House } from 'lucide-react';
import { Outlet } from 'react-router';
import { Button, EmptyState } from '../../components/ui';
import { useAuth } from './AuthContext';

/** Chỉ phục vụ trải nghiệm người dùng, quyền thật do server kiểm tra. */
export default function RoleRoute({ roles }) {
  const { role } = useAuth();

  if (!roles.includes(role)) {
    return (
      <EmptyState
        heading="h1"
        title="Bạn không có quyền xem trang này"
        description="Trang này dành cho vai trò khác. Nếu cần truy cập, hãy liên hệ quản trị viên."
        action={
          <Button to="/" iconLeft={House}>
            Về Tổng quan
          </Button>
        }
      />
    );
  }
  return <Outlet />;
}
