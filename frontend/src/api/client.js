const WRITE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

// Trang đăng nhập tự hiện lỗi; AuthContext coi 401 của me là "chưa đăng nhập".
const PATHS_HANDLING_OWN_401 = new Set(['/api/auth/login', '/api/auth/me']);

let unauthorizedHandler = null;

/** Trả về hàm hủy đăng ký. */
export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = handler;
  return () => {
    if (unauthorizedHandler === handler) {
      unauthorizedHandler = null;
    }
  };
}

export class ApiError extends Error {
  constructor({ status, code, message, details = {} }) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function readJson(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function toApiError(response, body) {
  const error = body?.error;
  if (error?.code && error?.message) {
    return new ApiError({
      status: response.status,
      code: error.code,
      message: error.message,
      details: error.details ?? {},
    });
  }
  return new ApiError({
    status: response.status,
    code: 'UNKNOWN_ERROR',
    message: 'Máy chủ trả về phản hồi không xác định.',
  });
}

export async function apiRequest(path, { method = 'GET', body, signal } = {}) {
  const upperMethod = method.toUpperCase();
  const headers = {};
  if (WRITE_METHODS.has(upperMethod)) {
    headers['X-Requested-With'] = 'fetch';
  }
  const isForm = body instanceof FormData;
  if (body !== undefined && !isForm) {
    headers['Content-Type'] = 'application/json';
  }

  let response;
  try {
    response = await fetch(path, {
      method: upperMethod,
      credentials: 'include',
      headers,
      signal,
      body: body === undefined || isForm ? body : JSON.stringify(body),
    });
  } catch (cause) {
    if (cause?.name === 'AbortError') {
      throw cause;
    }
    throw new ApiError({
      status: 0,
      code: 'NETWORK_ERROR',
      message: 'Không kết nối được tới máy chủ.',
    });
  }

  if (response.status === 204) {
    return null;
  }
  const data = await readJson(response);
  if (!response.ok) {
    if (response.status === 401 && !PATHS_HANDLING_OWN_401.has(path)) {
      unauthorizedHandler?.();
    }
    throw toApiError(response, data);
  }
  return data;
}
