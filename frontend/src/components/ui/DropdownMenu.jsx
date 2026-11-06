import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router';

/**
 * items: [{ label, icon, onSelect | to, disabled }]. Theo mẫu ARIA: mũi tên, Home, End, Esc.
 * `header` là phần không chọn được ở đầu menu.
 */
export default function DropdownMenu({ trigger, triggerLabel, triggerClass = '', items, header }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  const triggerRef = useRef(null);
  const menuRef = useRef(null);

  function menuItems() {
    return [
      ...(menuRef.current?.querySelectorAll('[role="menuitem"]:not([aria-disabled="true"])') ?? []),
    ];
  }

  useEffect(() => {
    if (!open) {
      return undefined;
    }
    menuItems()[0]?.focus();
    function closeOnOutside(event) {
      if (!rootRef.current?.contains(event.target)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', closeOnOutside);
    return () => document.removeEventListener('mousedown', closeOnOutside);
  }, [open]);

  function closeAndFocus() {
    setOpen(false);
    triggerRef.current?.focus();
  }

  function handleMenuKey(event) {
    const list = menuItems();
    const index = list.indexOf(document.activeElement);
    const target = {
      ArrowDown: list[(index + 1) % list.length],
      ArrowUp: list[(index - 1 + list.length) % list.length],
      Home: list[0],
      End: list[list.length - 1],
    }[event.key];
    if (target) {
      event.preventDefault();
      target.focus();
    } else if (event.key === 'Escape') {
      event.preventDefault();
      closeAndFocus();
    } else if (event.key === 'Tab') {
      setOpen(false);
    }
  }

  function handleTriggerKey(event) {
    if (event.key === 'ArrowDown' && !open) {
      event.preventDefault();
      setOpen(true);
    }
  }

  return (
    <div ref={rootRef} className="dropdown">
      <button
        ref={triggerRef}
        type="button"
        className={`dropdown__trigger ${triggerClass}`.trim()}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={triggerLabel}
        onClick={() => setOpen((value) => !value)}
        onKeyDown={handleTriggerKey}
      >
        {trigger}
      </button>
      {open && (
        // eslint-disable-next-line jsx-a11y/interactive-supports-focus -- focus nằm ở từng mục
        <div ref={menuRef} role="menu" className="dropdown__menu" onKeyDown={handleMenuKey}>
          {header && <div className="dropdown__header">{header}</div>}
          {items.map((item) => {
            const Icon = item.icon;
            const content = (
              <>
                {Icon && <Icon size={16} aria-hidden="true" />}
                {item.label}
              </>
            );
            return item.to ? (
              <Link
                key={item.label}
                to={item.to}
                role="menuitem"
                className="dropdown__item"
                onClick={() => setOpen(false)}
              >
                {content}
              </Link>
            ) : (
              <button
                key={item.label}
                type="button"
                role="menuitem"
                className="dropdown__item"
                aria-disabled={item.disabled ? 'true' : undefined}
                onClick={() => {
                  if (!item.disabled) {
                    closeAndFocus();
                    item.onSelect?.();
                  }
                }}
              >
                {content}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
