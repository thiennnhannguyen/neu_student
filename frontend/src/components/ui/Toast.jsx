import { X, XCircle } from 'lucide-react';
import CheckBadge from './CheckBadge';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

const ToastContext = createContext(null);
const DISMISS_MS = 5000;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const nextId = useRef(1);
  const timers = useRef(new Set());

  const dismiss = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const show = useCallback(
    (message, kind = 'success') => {
      const id = nextId.current;
      nextId.current += 1;
      setToasts((current) => [...current, { id, message, kind }]);
      const timer = window.setTimeout(() => {
        timers.current.delete(timer);
        dismiss(id);
      }, DISMISS_MS);
      timers.current.add(timer);
    },
    [dismiss],
  );

  useEffect(() => {
    const active = timers.current;
    return () => active.forEach((timer) => window.clearTimeout(timer));
  }, []);

  const value = useMemo(() => ({ show }), [show]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-region">
        {toasts.map((toast) => {
          const Icon = toast.kind === 'error' ? XCircle : CheckBadge;
          return (
            <div key={toast.id} className={`toast toast--${toast.kind}`}>
              <Icon size={18} aria-hidden="true" />
              <p role="status" aria-live="polite">
                {toast.message}
              </p>
              <button
                type="button"
                className="icon-button"
                aria-label="Đóng thông báo"
                onClick={() => dismiss(toast.id)}
              >
                <X size={16} aria-hidden="true" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
