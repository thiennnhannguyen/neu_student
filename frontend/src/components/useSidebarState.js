import { useCallback, useEffect, useState } from 'react';

const STORAGE_KEY = 'neu.sidebar.collapsed';
const DESKTOP_QUERY = '(min-width: 1024px)';

function readCollapsed() {
  try {
    return window.localStorage.getItem(STORAGE_KEY) === '1';
  } catch {
    return false;
  }
}

function writeCollapsed(value) {
  try {
    window.localStorage.setItem(STORAGE_KEY, value ? '1' : '0');
  } catch {
    // Không ghi được (chế độ riêng tư): lựa chọn chỉ có tác dụng trong phiên này.
  }
}

/** Thu gọn thành rail từ 1024px, nhớ trong localStorage. Dưới 1024px, sidebar là drawer. */
export default function useSidebarState() {
  const [open, setOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(readCollapsed);

  const toggleCollapsed = useCallback(() => {
    setCollapsed((value) => {
      writeCollapsed(!value);
      return !value;
    });
  }, []);

  useEffect(() => {
    if (!open || typeof window.matchMedia !== 'function') {
      return undefined;
    }
    // Phóng to cửa sổ trong lúc drawer đang mở thì đóng lại, để không còn khóa focus.
    const query = window.matchMedia(DESKTOP_QUERY);
    const close = (event) => {
      if (event.matches) {
        setOpen(false);
      }
    };
    query.addEventListener('change', close);
    return () => query.removeEventListener('change', close);
  }, [open]);

  return { open, setOpen, collapsed, toggleCollapsed };
}
