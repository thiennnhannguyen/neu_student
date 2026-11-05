import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { useLocation, useNavigate } from 'react-router';
import { apiRequest, setUnauthorizedHandler } from '../../api/client';
import { LOGIN_PATH } from './redirect';

const AuthContext = createContext(null);

const ANONYMOUS = { status: 'anonymous', identity: null, message: null, loggedOut: false };

export function AuthProvider({ children }) {
  const [state, setState] = useState({ ...ANONYMOUS, status: 'loading' });
  const [attempt, setAttempt] = useState(0);
  const navigate = useNavigate();
  const location = useLocation();

  // Bộ xử lý 401 đọc đường dẫn mới nhất mà không phải đăng ký lại sau mỗi lần chuyển trang.
  const pathRef = useRef(location.pathname);
  useEffect(() => {
    pathRef.current = location.pathname;
  }, [location.pathname]);

  useEffect(() => {
    const controller = new AbortController();
    apiRequest('/api/auth/me', { signal: controller.signal })
      .then((identity) => setState({ ...ANONYMOUS, status: 'authenticated', identity }))
      .catch((error) => {
        if (error.name === 'AbortError') {
          return;
        }
        if (error.status === 401) {
          setState(ANONYMOUS);
        } else {
          setState({ ...ANONYMOUS, status: 'error', message: error.message });
        }
      });
    return () => controller.abort();
  }, [attempt]);

  useEffect(
    () =>
      setUnauthorizedHandler(() => {
        setState(ANONYMOUS);
        navigate(LOGIN_PATH, { state: { from: pathRef.current }, replace: true });
      }),
    [navigate],
  );

  const retry = useCallback(() => {
    setState({ ...ANONYMOUS, status: 'loading' });
    setAttempt((value) => value + 1);
  }, []);

  const login = useCallback(async (username, password) => {
    const identity = await apiRequest('/api/auth/login', {
      method: 'POST',
      body: { username, password },
    });
    setState({ ...ANONYMOUS, status: 'authenticated', identity });
  }, []);

  const logout = useCallback(async () => {
    await apiRequest('/api/auth/logout', { method: 'POST' });
    // ProtectedRoute chuyển về /login. loggedOut để không giữ trang cũ cho người đăng nhập sau.
    setState({ ...ANONYMOUS, loggedOut: true });
  }, []);

  const value = useMemo(
    () => ({ ...state, role: state.identity?.role ?? null, login, logout, retry }),
    [state, login, logout, retry],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
