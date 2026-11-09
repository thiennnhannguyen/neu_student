import { createContext, useContext } from 'react';
import { useLocation } from 'react-router';
import { M11_READERS } from '../../components/menu';
import { useAuth } from '../auth/AuthContext';
import useM11Scope from './useM11Scope';

/** Trang M11 và trang đó có "Tất cả các kỳ" hay không (Q74). */
const M11_PAGES = {
  '/': false,
  '/m11/ket-qua': true,
  '/m11/phan-tich': false,
};

// Trang chi tiết môn đang học (CR-13, D-314): cùng phạm vi sinh viên, không có "Tất cả các kỳ".
const M11_PAGE_PREFIXES = ['/m11/phan-tich/mon/'];

export function isM11Page(pathname) {
  return (
    Object.hasOwn(M11_PAGES, pathname) ||
    M11_PAGE_PREFIXES.some((prefix) => pathname.startsWith(prefix))
  );
}

const M11ScopeContext = createContext(null);

/**
 * Một nguồn duy nhất cho thanh trên cùng và trang đang mở, nên chỉ gọi /api/m11/semesters một lần.
 * Giá trị là null ở trang không thuộc M11 và với vai trò không được xem.
 */
export function M11ScopeProvider({ children }) {
  const { pathname } = useLocation();
  const { role } = useAuth();
  const path = pathname.length > 1 ? pathname.replace(/\/$/, '') : pathname;
  const enabled = isM11Page(path) && M11_READERS.includes(role);
  const scope = useM11Scope({ enabled, allowAll: enabled && M11_PAGES[path] === true });
  return (
    <M11ScopeContext.Provider value={enabled ? scope : null}>{children}</M11ScopeContext.Provider>
  );
}

export function useM11ScopeValue() {
  return useContext(M11ScopeContext);
}
