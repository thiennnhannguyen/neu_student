import { createContext, useContext, useEffect, useState } from 'react';
import { useLocation } from 'react-router';

/**
 * Nhãn cuối của đường dẫn phân cấp mà chỉ trang biết sau khi tải dữ liệu (ví dụ tên môn ở trang chi
 * tiết môn, CR-13b). Nhãn gắn với đường dẫn đã đặt, nên chuyển trang thì tự hết hiệu lực.
 */
const PageLabelContext = createContext({ label: null, setLabel: () => {} });

export function PageLabelProvider({ children }) {
  const [label, setLabel] = useState(null);
  return (
    <PageLabelContext.Provider value={{ label, setLabel }}>{children}</PageLabelContext.Provider>
  );
}

/** Nhãn của trang đang mở, null nếu trang chưa đặt. */
export function useCurrentPageLabel() {
  const { label } = useContext(PageLabelContext);
  const { pathname } = useLocation();
  return label && label.pathname === pathname ? label.text : null;
}

/** Trang gọi để đặt nhãn cuối của đường dẫn phân cấp. */
export function usePageLabel(text) {
  const { setLabel } = useContext(PageLabelContext);
  const { pathname } = useLocation();
  useEffect(() => {
    if (!text) {
      return undefined;
    }
    setLabel({ pathname, text });
    return () => setLabel(null);
  }, [pathname, setLabel, text]);
}
