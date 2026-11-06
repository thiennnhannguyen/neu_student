import { ChevronLeft, ChevronRight } from 'lucide-react';
import Button from './Button';

export default function Pagination({ page, lastPage, summary, label, onPage }) {
  return (
    <nav className="pagination" aria-label={label}>
      <Button
        variant="secondary"
        size="sm"
        iconLeft={ChevronLeft}
        disabled={page <= 1}
        onClick={() => onPage(page - 1)}
      >
        Trang trước
      </Button>
      <span>{summary}</span>
      <Button
        variant="secondary"
        size="sm"
        iconRight={ChevronRight}
        disabled={page >= lastPage}
        onClick={() => onPage(page + 1)}
      >
        Trang sau
      </Button>
    </nav>
  );
}
