import { describe, expect, it } from 'vitest';
import { safeRedirectPath } from './redirect';

describe('safeRedirectPath', () => {
  it.each(['/', '/ho-so', '/m11/ket-qua', '/quan-tri/nhat-ky'])('nhận %s', (path) => {
    expect(safeRedirectPath(path)).toBe(path);
  });

  it.each([
    '//evil.test',
    '//evil.test/ho-so',
    '/\\evil.test',
    'https://evil.test',
    'javascript:alert(1)',
    'ho-so',
    '',
    '/login',
    null,
    undefined,
    42,
    { pathname: '/ho-so' },
  ])('từ chối %j, về Tổng quan', (from) => {
    expect(safeRedirectPath(from)).toBe('/');
  });
});
