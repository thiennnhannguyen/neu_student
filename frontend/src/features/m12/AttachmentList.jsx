import { Paperclip } from 'lucide-react';

export const ACCEPT_FILES = '.pdf,.png,.jpg,.jpeg,.docx';

function sizeText(bytes) {
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

/** Tải qua API có kiểm quyền; server luôn trả dạng tải về, không mở trong trình duyệt. */
export default function AttachmentList({ items }) {
  if (items.length === 0) {
    return null;
  }
  return (
    <ul className="attachment-list">
      {items.map((item) => (
        <li key={item.id}>
          <a href={item.url}>
            <Paperclip size={14} aria-hidden="true" />
            {item.original_name}
          </a>
          <span>{sizeText(item.size_bytes)}</span>
        </li>
      ))}
    </ul>
  );
}
