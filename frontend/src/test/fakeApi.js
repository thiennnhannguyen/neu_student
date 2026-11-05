import { render } from '@testing-library/react';
import { createElement, Fragment } from 'react';
import { MemoryRouter, useLocation } from 'react-router';
import { vi } from 'vitest';
import AppRoutes from '../routes';

const EMPTY_PAGE = { items: [], page: 1, page_size: 100, total: 0 };

export function jsonResponse(status, body) {
  return new Response(body === undefined ? null : JSON.stringify(body), { status });
}

export function apiError(status, code, message, details = {}) {
  return jsonResponse(status, { error: { code, message, details } });
}

/** Response chưa trả về, để test giữ được trạng thái đang tải. */
export function pendingResponse() {
  let resolve;
  const promise = new Promise((done) => {
    resolve = done;
  });
  return { handler: () => promise, resolve };
}

export function identityFor(role, username = role) {
  return {
    user: { id: `user-${username}`, username, full_name: `Người dùng ${username} (mẫu)` },
    role,
    student_id: role === 'student' ? 'SV01' : null,
  };
}

/**
 * Giả lập API theo khóa "METHOD /duong-dan". Giá trị là hàm nhận (url, options) trả Response.
 * Gọi tới đường dẫn chưa khai báo thì test đỏ, tránh bỏ sót lời gọi.
 */
export function stubApi(routes) {
  const fetchMock = vi.fn(async (url, options = {}) => {
    const key = `${options.method ?? 'GET'} ${String(url).split('?')[0]}`;
    if (!routes[key]) {
      throw new Error(`Chưa khai báo API giả: ${key}`);
    }
    return routes[key](url, options);
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

export function loggedInAs(role, extra = {}) {
  return stubApi({
    'GET /api/auth/me': () => jsonResponse(200, identityFor(role)),
    'GET /api/health': () => jsonResponse(200, { status: 'ok' }),
    'GET /api/advisor/students': () => jsonResponse(200, EMPTY_PAGE),
    'GET /api/admin/students': () => jsonResponse(200, EMPTY_PAGE),
    ...extra,
  });
}

function LocationProbe() {
  const location = useLocation();
  return createElement(
    Fragment,
    null,
    createElement('output', { 'data-testid': 'path' }, location.pathname),
    createElement('output', { 'data-testid': 'search' }, location.search),
  );
}

export function renderApp(initialEntry = '/') {
  return render(
    createElement(
      MemoryRouter,
      { initialEntries: [initialEntry] },
      createElement(AppRoutes),
      createElement(LocationProbe),
    ),
  );
}
