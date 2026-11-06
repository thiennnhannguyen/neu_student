import { ChevronRight } from 'lucide-react';

/** Khối mở rộng dùng thẻ details gốc nên bàn phím và trình đọc màn hình hoạt động sẵn. */
export default function Disclosure({ summary, children }) {
  return (
    <details className="disclosure">
      <summary>
        <ChevronRight size={16} aria-hidden="true" className="disclosure__icon" />
        {summary}
      </summary>
      <div className="disclosure__body">{children}</div>
    </details>
  );
}
