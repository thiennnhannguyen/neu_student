import { House } from 'lucide-react';
import { Button, EmptyState } from './ui';

export default function NotFoundPage() {
  return (
    <EmptyState
      heading="h1"
      title="Không tìm thấy trang"
      description="Đường dẫn này không tồn tại hoặc đã được đổi."
      action={
        <Button to="/" iconLeft={House}>
          Về Tổng quan
        </Button>
      }
    />
  );
}
