import { useCallback, useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';

/** path là null thì không gọi API. Đổi path thì quay về đang tải và hủy lời gọi cũ. */
export default function useApiResource(path) {
  const [result, setResult] = useState({ path: null, attempt: 0 });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!path) {
      return undefined;
    }
    const controller = new AbortController();
    // Lời gọi đã bị hủy (đổi kỳ nhanh) mà vẫn trả về thì bỏ qua, không ghi đè kết quả mới hơn.
    apiRequest(path, { signal: controller.signal })
      .then((data) => {
        if (!controller.signal.aborted) {
          setResult({ path, attempt, status: 'ok', data });
        }
      })
      .catch((error) => {
        if (error.name !== 'AbortError' && !controller.signal.aborted) {
          setResult({ path, attempt, status: 'error', error });
        }
      });
    return () => controller.abort();
  }, [path, attempt]);

  const retry = useCallback(() => setAttempt((value) => value + 1), []);

  if (!path) {
    return { status: 'idle', retry };
  }
  if (result.path !== path || result.attempt !== attempt) {
    return { status: 'loading', retry };
  }
  return { ...result, retry };
}
