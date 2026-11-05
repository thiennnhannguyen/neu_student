export const HOME_PATH = '/';
export const LOGIN_PATH = '/login';

/**
 * Đích quay lại sau đăng nhập. Chỉ nhận đường dẫn trong ứng dụng để tránh open redirect:
 * "//evil.test" và "/\evil.test" đều bị trình duyệt hiểu là tên miền khác.
 */
export function safeRedirectPath(from) {
  if (
    typeof from !== 'string' ||
    !from.startsWith('/') ||
    from.startsWith('//') ||
    from.startsWith('/\\') ||
    from === LOGIN_PATH
  ) {
    return HOME_PATH;
  }
  return from;
}
