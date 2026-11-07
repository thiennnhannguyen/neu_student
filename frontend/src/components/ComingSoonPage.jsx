import { House } from 'lucide-react';
import { Button, EmptyState } from './ui';

export default function ComingSoonPage({ title }) {
  return (
    <EmptyState
      heading="h1"
      title={title}
      description="Đang phát triển."
      action={
        <Button to="/" iconLeft={House}>
          Về Tổng quan
        </Button>
      }
    />
  );
}
