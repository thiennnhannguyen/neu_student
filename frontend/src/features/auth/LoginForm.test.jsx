import { fireEvent, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiError, identityFor, jsonResponse, renderApp, stubApi } from '../../test/fakeApi';

const FOOTER =
  'Sản phẩm bài tập lớn – không phải hệ thống chính thức của Đại học Kinh tế Quốc dân.';

function anonymousApi(extra = {}) {
  return stubApi({
    'GET /api/auth/me': () => apiError(401, 'UNAUTHENTICATED', 'Bạn chưa đăng nhập.'),
    'GET /api/health': () => jsonResponse(200, { status: 'ok' }),
    'POST /api/auth/login': () => jsonResponse(200, identityFor('student', 'sv01')),
    ...extra,
  });
}

async function openLogin() {
  renderApp('/login');
  return screen.findByLabelText('Mật khẩu');
}

describe('nội dung trang đăng nhập', () => {
  beforeEach(() => {
    anonymousApi();
  });

  it('có đủ chữ theo yêu cầu, tên trường là chữ thường, không phải ảnh', async () => {
    await openLogin();

    for (const text of [
      'Nền tảng học tập sinh viên NEU',
      'Phân tích học tập · Hỗ trợ người học',
      'ĐẠI HỌC KINH TẾ QUỐC DÂN',
      'NATIONAL ECONOMICS UNIVERSITY',
      'Dùng tài khoản được cấp cho bạn',
      FOOTER,
    ]) {
      expect(screen.getByText(text)).toBeInTheDocument();
    }
    expect(screen.getByRole('img')).toHaveAttribute('src', '/images/brand/logo_neu.svg');
  });

  it('logo lỗi thì vẫn hiện chữ NEU dự phòng', async () => {
    await openLogin();

    fireEvent.error(screen.getByRole('img'));

    expect(screen.queryByRole('img')).not.toBeInTheDocument();
    expect(document.querySelector('.login-card .brand-fallback')).toHaveTextContent('NEU');
  });

  it('mọi mosaic đều aria-hidden và chữ NEU trang trí bị ẩn khỏi trợ năng', async () => {
    await openLogin();

    const mosaics = document.querySelectorAll('.motif-mosaic');
    expect(mosaics).toHaveLength(4);
    for (const mosaic of mosaics) {
      expect(mosaic).toHaveAttribute('aria-hidden', 'true');
    }
    expect(document.querySelector('.login-brand__word')).toHaveAttribute('aria-hidden', 'true');
  });

  it('cột thương hiệu có logo trang trí, xếp trên tiêu đề', async () => {
    await openLogin();

    const center = document.querySelector('.login-brand__center');
    const logo = center.firstElementChild;
    expect(logo.tagName).toBe('IMG');
    expect(logo).toHaveAttribute('src', '/images/brand/logo_neu.svg');
    expect(logo).toHaveAttribute('alt', '');
    expect(logo.nextElementSibling).toHaveTextContent('Nền tảng học tập sinh viên NEU');
    expect(logo.closest('.login-brand__copy')).toBeNull();
  });

  it('mosaic không nằm trong thẻ form', async () => {
    await openLogin();

    expect(document.querySelector('.login-card .motif-mosaic')).toBeNull();
  });
});

describe('hiện và ẩn mật khẩu', () => {
  it('đổi type, aria-label, aria-pressed', async () => {
    anonymousApi();
    const user = userEvent.setup();
    const password = await openLogin();
    expect(password).toHaveAttribute('type', 'password');

    await user.click(screen.getByRole('button', { name: 'Hiện mật khẩu' }));

    expect(password).toHaveAttribute('type', 'text');
    const hide = screen.getByRole('button', { name: 'Ẩn mật khẩu' });
    expect(hide).toHaveAttribute('aria-pressed', 'true');

    await user.click(hide);

    expect(password).toHaveAttribute('type', 'password');
    expect(screen.getByRole('button', { name: 'Hiện mật khẩu' })).toHaveAttribute(
      'aria-pressed',
      'false',
    );
  });

  it('không gửi form khi bấm nút', async () => {
    const fetchMock = anonymousApi();
    const user = userEvent.setup();
    await openLogin();

    await user.click(screen.getByRole('button', { name: 'Hiện mật khẩu' }));

    expect(fetchMock.mock.calls.some(([url]) => url === '/api/auth/login')).toBe(false);
    expect(screen.queryByText('Vui lòng nhập tên đăng nhập và mật khẩu.')).not.toBeInTheDocument();
  });
});

describe('cảnh báo Caps Lock', () => {
  it('hiện khi gõ lúc Caps Lock bật, tắt khi Caps Lock tắt, trong vùng aria-live polite', async () => {
    anonymousApi();
    const password = await openLogin();
    const region = document.getElementById('login-caps');
    expect(region).toHaveAttribute('aria-live', 'polite');
    expect(region).toBeEmptyDOMElement();

    fireEvent.keyDown(password, { key: 'A', modifierCapsLock: true });
    expect(region).toHaveTextContent('Caps Lock đang bật');

    fireEvent.keyUp(password, { key: 'a', modifierCapsLock: false });
    expect(region).toBeEmptyDOMElement();
  });

  it('rời ô mật khẩu thì ẩn cảnh báo', async () => {
    anonymousApi();
    const password = await openLogin();

    fireEvent.keyDown(password, { key: 'A', modifierCapsLock: true });
    fireEvent.blur(password);

    expect(document.getElementById('login-caps')).toBeEmptyDOMElement();
  });

  it('gõ ở ô tên đăng nhập không hiện cảnh báo', async () => {
    anonymousApi();
    await openLogin();

    fireEvent.keyDown(screen.getByLabelText('Tên đăng nhập'), {
      key: 'A',
      modifierCapsLock: true,
    });

    expect(document.getElementById('login-caps')).toBeEmptyDOMElement();
  });
});

describe('hộp lỗi và trạng thái gửi', () => {
  it('hộp lỗi có icon và lớp hiển thị; lúc chưa có lỗi thì rỗng', async () => {
    anonymousApi({
      'POST /api/auth/login': () => apiError(401, 'INVALID_CREDENTIALS', 'Thông báo chung.'),
    });
    const user = userEvent.setup();
    const password = await openLogin();
    const alert = document.getElementById('login-error');
    expect(alert).toBeEmptyDOMElement();
    expect(alert).not.toHaveClass('login-alert--visible');

    await user.type(screen.getByLabelText('Tên đăng nhập'), 'sv01');
    await user.type(password, 'sai{Enter}');

    await screen.findByText('Thông báo chung.');
    expect(alert).toHaveClass('login-alert--visible');
    expect(alert).toHaveAttribute('aria-live', 'assertive');
    expect(alert.querySelector('svg')).toHaveAttribute('aria-hidden', 'true');
  });

  it('đang gửi thì có spinner aria-hidden', async () => {
    let finish;
    anonymousApi({
      'POST /api/auth/login': () =>
        new Promise((resolve) => {
          finish = () => resolve(jsonResponse(200, identityFor('student', 'sv01')));
        }),
    });
    const user = userEvent.setup();
    const password = await openLogin();

    await user.type(screen.getByLabelText('Tên đăng nhập'), 'sv01');
    await user.type(password, 'Demo@12345{Enter}');

    const button = screen.getByRole('button', { name: 'Đang đăng nhập…' });
    expect(button).toBeDisabled();
    expect(button.querySelector('.spinner')).toHaveAttribute('aria-hidden', 'true');
    finish();
    await screen.findByRole('heading', { name: 'Tổng quan' });
  });
});

describe('hộp tài khoản demo', () => {
  it('biến môi trường false thì ẩn', async () => {
    vi.stubEnv('VITE_SHOW_DEMO_ACCOUNTS', 'false');
    anonymousApi();

    await openLogin();

    expect(screen.queryByText('Tài khoản demo (dữ liệu mẫu)')).not.toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('Demo@12345');
  });

  it('liệt kê đủ tài khoản, bấm thì điền đúng ô tên đăng nhập và chuyển tới ô mật khẩu', async () => {
    vi.stubEnv('VITE_SHOW_DEMO_ACCOUNTS', 'true');
    anonymousApi();
    const user = userEvent.setup();
    const password = await openLogin();

    await user.click(screen.getByText('Tài khoản demo (dữ liệu mẫu)'));

    const box = document.querySelector('.demo-box');
    expect(box).toHaveTextContent('Demo@12345');
    const names = within(box)
      .getAllByRole('button')
      .map((button) => button.querySelector('strong').textContent);
    expect(names).toEqual(['sv01', 'sv07', 'gv1', 'ht1', 'admin']);

    await user.click(within(box).getByRole('button', { name: /^gv1/ }));

    expect(screen.getByLabelText('Tên đăng nhập')).toHaveValue('gv1');
    expect(password).toHaveValue('');
    expect(password).toHaveFocus();
  });
});

describe('bàn phím', () => {
  it('Tab chỉ đi qua các điều khiển của form, không dừng ở họa tiết', async () => {
    vi.stubEnv('VITE_SHOW_DEMO_ACCOUNTS', 'true');
    anonymousApi();
    const user = userEvent.setup();
    await openLogin();

    const visited = [];
    for (let step = 0; step < 5; step += 1) {
      await user.tab();
      visited.push(document.activeElement);
    }

    expect(visited.map((element) => element.id || element.textContent)).toEqual([
      'login-username',
      'login-password',
      '', // Nút hiện mật khẩu chỉ có icon và aria-label.
      'Đăng nhập',
      'Tài khoản demo (dữ liệu mẫu)',
    ]);
    for (const element of visited) {
      expect(element.closest('.motif-mosaic')).toBeNull();
      expect(element.closest('.login-card')).not.toBeNull();
    }
  });

  it('mở hộp demo và chọn tài khoản chỉ bằng bàn phím', async () => {
    vi.stubEnv('VITE_SHOW_DEMO_ACCOUNTS', 'true');
    anonymousApi();
    const user = userEvent.setup();
    await openLogin();

    screen.getByText('Tài khoản demo (dữ liệu mẫu)').focus();
    await user.keyboard('{Enter}');
    await user.tab();
    await user.keyboard('{Enter}');

    expect(screen.getByLabelText('Tên đăng nhập')).toHaveValue('sv01');
  });
});
