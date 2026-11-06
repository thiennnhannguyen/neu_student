import { Info } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

export default function InfoPopover({ label, children }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  const buttonRef = useRef(null);

  useEffect(() => {
    if (!open) {
      return undefined;
    }
    function closeOnOutside(event) {
      if (!rootRef.current?.contains(event.target)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', closeOnOutside);
    return () => document.removeEventListener('mousedown', closeOnOutside);
  }, [open]);

  function handleKeyDown(event) {
    if (event.key === 'Escape' && open) {
      setOpen(false);
      buttonRef.current?.focus();
    }
  }

  return (
    // eslint-disable-next-line jsx-a11y/no-static-element-interactions -- chỉ bắt Esc từ nút bên trong
    <span ref={rootRef} className="info-popover" onKeyDown={handleKeyDown}>
      <button
        ref={buttonRef}
        type="button"
        className="icon-button"
        aria-label={label}
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <Info size={18} aria-hidden="true" />
      </button>
      {open && (
        <span role="status" className="info-popover__content">
          {children}
        </span>
      )}
    </span>
  );
}
