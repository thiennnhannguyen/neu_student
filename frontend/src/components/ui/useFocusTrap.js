import { useEffect } from 'react';

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea, summary, [tabindex="0"]';

/** Khi active: focus vào phần tử đầu, Tab không ra ngoài, Esc gọi onEscape, tắt thì trả focus. */
export default function useFocusTrap(ref, active, onEscape, initialRef) {
  useEffect(() => {
    if (!active || !ref.current) {
      return undefined;
    }
    const container = ref.current;
    const opener = document.activeElement;
    (initialRef?.current ?? container.querySelector(FOCUSABLE))?.focus();

    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        event.stopPropagation();
        onEscape();
        return;
      }
      if (event.key !== 'Tab') {
        return;
      }
      const items = [...container.querySelectorAll(FOCUSABLE)];
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    container.addEventListener('keydown', handleKeyDown);
    return () => {
      container.removeEventListener('keydown', handleKeyDown);
      opener?.focus?.();
    };
    // Chỉ chạy lại khi bật hoặc tắt; onEscape đổi theo mỗi lần render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);
}
