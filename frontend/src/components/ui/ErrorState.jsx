import { RotateCcw } from 'lucide-react';
import Button from './Button';
import EmptyState from './EmptyState';

export default function ErrorState({ title, description, onRetry }) {
  return (
    <EmptyState
      role="alert"
      title={title}
      description={description}
      action={
        onRetry && (
          <Button iconLeft={RotateCcw} onClick={onRetry}>
            Thử lại
          </Button>
        )
      }
    />
  );
}
