import { House } from 'lucide-react';
import { Button, EmptyState } from './ui';

export default function ComingSoonPage({ title, phase }) {
  return (
    <EmptyState
      heading="h1"
      title={title}
      description={`Đang phát triển. Dự kiến ở giai đoạn ${phase}.`}
      action={
        <Button to="/" iconLeft={House}>
          Về Tổng quan
        </Button>
      }
    />
  );
}
