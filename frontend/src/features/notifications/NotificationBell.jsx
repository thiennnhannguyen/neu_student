import { Bell } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Link, useLocation } from 'react-router';
import { apiRequest } from '../../api/client';
import { Button } from '../../components/ui';
import { RealTimeNote } from '../m11/SystemTime';

const URL = '/api/notifications';
const TIME_FORMAT = new Intl.DateTimeFormat('vi-VN', { dateStyle: 'short', timeStyle: 'short' });
const EMPTY = { items: [], unread_count: 0, note: '' };

/** Tải khi vào trang và khi đổi trang; không chạy định kỳ. */
export default function NotificationBell() {
  const { pathname } = useLocation();
  const [data, setData] = useState(EMPTY);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [status, setStatus] = useState('loading');
  const rootRef = useRef(null);
  const buttonRef = useRef(null);

  useEffect(() => {
    const controller = new AbortController();
    apiRequest(`${URL}?page_size=20`, { signal: controller.signal })
      .then((body) => {
        setData(body);
        setStatus('ok');
      })
      .catch((cause) => {
        if (cause.name !== 'AbortError') {
          setData(EMPTY);
          setStatus('error');
        }
      });
    return () => controller.abort();
  }, [pathname, attempt]);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!open) {
      return undefined;
    }
    function closeOnOutside(event) {
      if (!rootRef.current?.contains(event.target)) {
        setOpen(false);
      }
    }
    function closeOnEscape(event) {
      if (event.key === 'Escape') {
        setOpen(false);
        buttonRef.current?.focus();
      }
    }
    document.addEventListener('mousedown', closeOnOutside);
    document.addEventListener('keydown', closeOnEscape);
    return () => {
      document.removeEventListener('mousedown', closeOnOutside);
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, [open]);

  async function act(path) {
    setError('');
    try {
      await apiRequest(path, { method: 'POST', body: {} });
      setAttempt((value) => value + 1);
    } catch (cause) {
      setError(cause.message);
    }
  }

  const unread = data.unread_count;
  return (
    <div className="notification-bell" ref={rootRef}>
      <button
        ref={buttonRef}
        type="button"
        className="icon-button"
        aria-label={unread > 0 ? `Thông báo, ${unread} chưa đọc` : 'Thông báo'}
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <Bell size={20} aria-hidden="true" />
        {unread > 0 && (
          <span className="notification-bell__count" aria-hidden="true">
            {unread > 99 ? '99+' : unread}
          </span>
        )}
      </button>
      {open && (
        <section className="notification-panel" aria-label="Danh sách thông báo">
          <header className="notification-panel__head">
            <h2>Thông báo</h2>
            {unread > 0 && (
              <Button variant="ghost" size="sm" onClick={() => act(`${URL}/read-all`)}>
                Đọc tất cả
              </Button>
            )}
          </header>
          {error && (
            <p role="alert" className="status-error">
              {error}
            </p>
          )}
          {status === 'loading' && (
            <p role="status" className="notification-panel__empty">
              Đang tải thông báo...
            </p>
          )}
          {status === 'error' && (
            <div role="alert" className="notification-panel__empty">
              <p>Không tải được thông báo.</p>
              <Button variant="ghost" size="sm" onClick={() => setAttempt((value) => value + 1)}>
                Thử lại
              </Button>
            </div>
          )}
          {status === 'ok' && data.items.length === 0 && (
            <p className="notification-panel__empty">Chưa có thông báo.</p>
          )}
          {data.items.length > 0 && (
            <ul className="notification-panel__list">
              {data.items.map((item) => (
                <li
                  key={item.id}
                  className={`notification-item${item.read ? '' : ' notification-item--unread'}`}
                >
                  <Link
                    to={item.link ?? '/'}
                    onClick={() => {
                      if (!item.read) {
                        act(`${URL}/${item.id}/read`);
                      }
                    }}
                  >
                    <strong>{item.title}</strong>
                    {item.body && <span>{item.body}</span>}
                    <time dateTime={item.created_at}>
                      {TIME_FORMAT.format(new Date(item.created_at))}
                      <RealTimeNote />
                    </time>
                  </Link>
                  {!item.read && <span className="notification-item__tag">Chưa đọc</span>}
                </li>
              ))}
            </ul>
          )}
          <p className="notification-panel__note">{data.note}</p>
        </section>
      )}
    </div>
  );
}
