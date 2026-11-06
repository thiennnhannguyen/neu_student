import { X } from 'lucide-react';
import { useRef } from 'react';
import Button from './Button';
import useFocusTrap from './useFocusTrap';

/** Panel bên phải: focus vào nút đóng, Tab không ra ngoài, Esc để đóng, đóng thì trả focus. */
export default function SidePanel({ title, onClose, wide = false, children }) {
  const panelRef = useRef(null);
  const closeRef = useRef(null);
  useFocusTrap(panelRef, true, onClose, closeRef);

  return (
    // Nền chỉ bắt chuột để đóng; bàn phím đã có nút Đóng và phím Esc.
    // eslint-disable-next-line jsx-a11y/no-static-element-interactions
    <div className="side-panel__backdrop" onMouseDown={onClose}>
      {/* eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions */}
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`side-panel${wide ? ' side-panel--wide' : ''}`}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="side-panel__header">
          <h2>{title}</h2>
          <Button ref={closeRef} variant="ghost" size="sm" iconLeft={X} onClick={onClose}>
            Đóng
          </Button>
        </div>
        {children}
      </div>
    </div>
  );
}
