import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError, apiRequest, setUnauthorizedHandler } from './client';

function jsonResponse(status, body) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

describe('apiRequest', () => {
  let fetchMock;

  beforeEach(() => {
    fetchMock = vi.fn().mockImplementation(async () => jsonResponse(200, { ok: true }));
    vi.stubGlobal('fetch', fetchMock);
  });

  it.each(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])(
    "gửi credentials 'include' với %s",
    async (method) => {
      await apiRequest('/api/x', { method });

      expect(fetchMock.mock.calls[0][1].credentials).toBe('include');
    },
  );

  it.each(['POST', 'PUT', 'PATCH', 'DELETE', 'post'])(
    'gắn X-Requested-With: fetch cho %s',
    async (method) => {
      await apiRequest('/api/x', { method });

      expect(fetchMock.mock.calls[0][1].headers['X-Requested-With']).toBe('fetch');
    },
  );

  it('không gắn X-Requested-With cho GET', async () => {
    await apiRequest('/api/x');

    expect(fetchMock.mock.calls[0][1].headers).not.toHaveProperty('X-Requested-With');
  });

  it('chuyển lỗi chuẩn thành ApiError', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(403, {
        error: { code: 'FORBIDDEN', message: 'Không có quyền.', details: { role: 'student' } },
      }),
    );

    const error = await apiRequest('/api/x').catch((caught) => caught);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 403,
      code: 'FORBIDDEN',
      message: 'Không có quyền.',
      details: { role: 'student' },
    });
  });

  it('phản hồi lỗi không phải JSON vẫn thành ApiError', async () => {
    fetchMock.mockResolvedValue(new Response('<html>Bad gateway</html>', { status: 502 }));

    await expect(apiRequest('/api/x')).rejects.toMatchObject({
      name: 'ApiError',
      status: 502,
      code: 'UNKNOWN_ERROR',
    });
  });

  it('lỗi mạng thành ApiError NETWORK_ERROR', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'));

    await expect(apiRequest('/api/x')).rejects.toMatchObject({
      name: 'ApiError',
      status: 0,
      code: 'NETWORK_ERROR',
    });
  });

  it('hủy request thì giữ nguyên AbortError', async () => {
    const abort = new DOMException('Aborted', 'AbortError');
    fetchMock.mockRejectedValue(abort);

    await expect(apiRequest('/api/x')).rejects.toBe(abort);
  });

  it('D-328: hủy lúc đang đọc thân phản hồi vẫn là AbortError, không trả null', async () => {
    const abort = new DOMException('Aborted', 'AbortError');
    const response = jsonResponse(200, { unread_count: 1 });
    response.json = () => Promise.reject(abort);
    fetchMock.mockResolvedValue(response);

    await expect(apiRequest('/api/x')).rejects.toBe(abort);
  });

  it('thân phản hồi không phải JSON (không do hủy) vẫn trả null', async () => {
    fetchMock.mockResolvedValue(new Response('không phải json', { status: 200 }));

    await expect(apiRequest('/api/x')).resolves.toBeNull();
  });

  it('gửi body dạng JSON và trả dữ liệu', async () => {
    const data = await apiRequest('/api/x', { method: 'POST', body: { a: 1 } });

    const options = fetchMock.mock.calls[0][1];
    expect(options.body).toBe('{"a":1}');
    expect(options.headers['Content-Type']).toBe('application/json');
    expect(data).toEqual({ ok: true });
  });

  it('204 trả null', async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));

    await expect(apiRequest('/api/x', { method: 'DELETE' })).resolves.toBeNull();
  });
});

describe('xử lý 401 toàn cục', () => {
  let handler;
  let unregister;

  function respondWith(status) {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        status === 204
          ? new Response(null, { status })
          : jsonResponse(status, { error: { code: 'X', message: 'lỗi', details: {} } }),
      ),
    );
  }

  beforeEach(() => {
    handler = vi.fn();
    unregister = setUnauthorizedHandler(handler);
  });

  afterEach(() => unregister());

  it('401 của API thường gọi bộ xử lý và vẫn ném lỗi', async () => {
    respondWith(401);

    await expect(apiRequest('/api/students/me')).rejects.toMatchObject({ status: 401 });

    expect(handler).toHaveBeenCalledTimes(1);
  });

  it.each(['/api/auth/login', '/api/auth/me'])('401 của %s không gọi bộ xử lý', async (path) => {
    respondWith(401);

    await expect(apiRequest(path)).rejects.toMatchObject({ status: 401 });

    expect(handler).not.toHaveBeenCalled();
  });

  it('401 của logout có gọi bộ xử lý', async () => {
    respondWith(401);

    await expect(apiRequest('/api/auth/logout', { method: 'POST' })).rejects.toBeDefined();

    expect(handler).toHaveBeenCalledTimes(1);
  });

  it.each([403, 404, 422, 500])('%s không gọi bộ xử lý', async (status) => {
    respondWith(status);

    await expect(apiRequest('/api/x')).rejects.toMatchObject({ status });

    expect(handler).not.toHaveBeenCalled();
  });

  it('sau khi hủy đăng ký thì không gọi nữa', async () => {
    unregister();
    respondWith(401);

    await expect(apiRequest('/api/x')).rejects.toBeDefined();

    expect(handler).not.toHaveBeenCalled();
  });

  it('hủy đăng ký cũ không xóa bộ xử lý mới', async () => {
    const newer = vi.fn();
    const unregisterNewer = setUnauthorizedHandler(newer);
    unregister();
    respondWith(401);

    await expect(apiRequest('/api/x')).rejects.toBeDefined();

    expect(newer).toHaveBeenCalledTimes(1);
    unregisterNewer();
  });
});
