import { X } from 'lucide-react';
import { useRef } from 'react';
import Button from './Button';
import useFocusTrap from './useFocusTrap';

/** Tấm trượt từ đáy màn hình, dùng trên điện thoại. Focus giữ trong tấm, Esc đóng, đóng thì trả focus. */
export default function BottomSheet({ title, onClose, footer, children }) {
  const sheetRef = useRef(null);
  const closeRef = useRef(null);
  useFocusTrap(sheetRef, true, onClose, closeRef);

  return (
    // Nền chỉ bắt chuột để đóng; bàn phím đã có nút Đóng và phím Esc.
    // eslint-disable-next-line jsx-a11y/no-static-element-interactions
    <div className="bottom-sheet__backdrop" onMouseDown={onClose}>
      {/* eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions */}
      <div
        ref={sheetRef}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="bottom-sheet"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="bottom-sheet__header">
          <h2>{title}</h2>
          <Button ref={closeRef} variant="ghost" size="sm" iconLeft={X} onClick={onClose}>
            Đóng
          </Button>
        </div>
        <div className="bottom-sheet__body">{children}</div>
        {footer && <div className="bottom-sheet__footer">{footer}</div>}
      </div>
    </div>
  );
}
