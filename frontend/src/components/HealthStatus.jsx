import { useCallback, useEffect, useState } from 'react';
import { apiRequest } from '../api/client';

export default function HealthStatus() {
  const [state, setState] = useState({ status: 'loading' });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    apiRequest('/api/health', { signal: controller.signal })
      .then(() => setState({ status: 'ok' }))
      .catch((error) => {
        if (error.name !== 'AbortError') {
          setState({ status: 'error', message: error.message });
        }
      });
    return () => controller.abort();
  }, [attempt]);

  const retry = useCallback(() => {
    setState({ status: 'loading' });
    setAttempt((value) => value + 1);
  }, []);

  if (state.status === 'loading') {
    return <p role="status">Đang kiểm tra kết nối...</p>;
  }
  if (state.status === 'error') {
    return (
      <div role="alert">
        <p className="status-error">Không kết nối được backend: {state.message}</p>
        <button type="button" className="button" onClick={retry}>
          Thử lại
        </button>
      </div>
    );
  }
  return (
    <p role="status" className="status-ok">
      Backend đang hoạt động.
    </p>
  );
}
