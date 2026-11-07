import { X } from 'lucide-react';
import { useEffect, useRef } from 'react';
import Button from './Button';
import useFocusTrap from './useFocusTrap';

/** Panel nằm trong luồng trang, đẩy nội dung: không chặn phần còn lại; vẫn Esc và trả focus. */
function InlinePanel({ title, onClose, children }) {
  const closeRef = useRef(null);
  useEffect(() => {
    const opener = document.activeElement;
    closeRef.current?.focus();
    return () => opener?.focus?.();
  }, []);
  return (
    // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions -- chỉ bắt Esc
    <aside
      aria-label={title}
      className="side-panel side-panel--inline"
      onKeyDown={(event) => {
        if (event.key === 'Escape') {
          event.stopPropagation();
          onClose();
        }
      }}
    >
      <div className="side-panel__header">
        <h2>{title}</h2>
        <Button ref={closeRef} variant="ghost" size="sm" iconLeft={X} onClick={onClose}>
          Đóng
        </Button>
      </div>
      {children}
    </aside>
  );
}

function ModalPanel({ title, onClose, wide, children }) {
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

/** Panel bên phải: focus vào nút đóng, Tab không ra ngoài, Esc để đóng, đóng thì trả focus. */
export default function SidePanel({ title, onClose, wide = false, inline = false, children }) {
  const Panel = inline ? InlinePanel : ModalPanel;
  return (
    <Panel title={title} onClose={onClose} wide={wide}>
      {children}
    </Panel>
  );
}
