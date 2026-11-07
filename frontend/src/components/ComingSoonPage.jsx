import { House } from 'lucide-react';
import { Button, EmptyState } from './ui';

export default function ComingSoonPage({ title, phase }) {
  return (
    <EmptyState
      heading="h1"
      title={title}
      description={phase ? `Đang phát triển. Dự kiến ở giai đoạn ${phase}.` : 'Đang phát triển.'}
      action={
        <Button to="/" iconLeft={House}>
          Về Tổng quan
        </Button>
      }
    />
  );
}
