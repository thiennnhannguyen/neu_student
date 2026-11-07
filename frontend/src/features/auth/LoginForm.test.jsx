import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it } from 'vitest';
import { apiError, identityFor, jsonResponse, renderApp, stubApi } from '../../test/fakeApi';

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

  it('cột thương hiệu có ảnh tòa nhà trang trí, nằm sau khối chữ', async () => {
    await openLogin();

    const building = document.querySelector('.login-brand__building');
    expect(building).toHaveAttribute('src', '/images/brand/toa_nha_a2.svg');
    expect(building).toHaveAttribute('alt', '');
    expect(building.previousElementSibling).toHaveClass('login-brand__headline');
  });

  it('thẻ form không còn hộp tài khoản demo và dòng chữ chân trang', async () => {
    await openLogin();

    const card = document.querySelector('.login-card');
    expect(card).not.toHaveTextContent('Tài khoản demo');
    expect(card).not.toHaveTextContent('Demo@12345');
    expect(card).not.toHaveTextContent('Sản phẩm bài tập lớn');
    expect(card.lastElementChild.tagName).toBe('FORM');
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

describe('bàn phím', () => {
  it('Tab chỉ đi qua các điều khiển của form, không dừng ở họa tiết', async () => {
    anonymousApi();
    const user = userEvent.setup();
    await openLogin();

    const visited = [];
    for (let step = 0; step < 4; step += 1) {
      await user.tab();
      visited.push(document.activeElement);
    }

    expect(visited.map((element) => element.id || element.textContent)).toEqual([
      'login-username',
      'login-password',
      '', // Nút hiện mật khẩu chỉ có icon và aria-label.
      'Đăng nhập',
    ]);
    for (const element of visited) {
      expect(element.closest('.motif-mosaic')).toBeNull();
      expect(element.closest('.login-card')).not.toBeNull();
    }
  });
});

describe('hộp tài khoản demo (profile demo-k68)', () => {
  const ACCOUNTS = [
    { username: 'demo05', full_name: 'Sinh viên DEMO05 (mẫu)', role: 'student' },
    { username: 'gv2', full_name: 'Cố vấn 2 (mẫu)', role: 'advisor' },
  ];

  function withAccounts(handler) {
    return stubApi({
      'GET /api/auth/me': () => apiError(401, 'UNAUTHENTICATED', 'Bạn chưa đăng nhập.'),
      'GET /api/auth/demo-accounts': handler,
    });
  }

  it('hiện ngoài thẻ form; bấm thì điền tên đăng nhập, chuyển con trỏ sang mật khẩu', async () => {
    const user = userEvent.setup();
    withAccounts(() => jsonResponse(200, { accounts: ACCOUNTS }));
    renderApp('/login');

    const box = await screen.findByRole('region', { name: 'Tài khoản demo' });
    expect(document.querySelector('.login-card')).not.toContainElement(box);
    expect(box).not.toHaveTextContent('Demo@12345');

    await user.click(within(box).getByRole('button', { name: /demo05/ }));
    expect(screen.getByLabelText('Tên đăng nhập')).toHaveValue('demo05');
    expect(screen.getByLabelText('Mật khẩu')).toHaveFocus();
  });

  it('profile test trả rỗng thì không có hộp', async () => {
    const fetchMock = withAccounts(() => jsonResponse(200, { accounts: [] }));
    renderApp('/login');

    await screen.findByRole('heading', { name: 'Đăng nhập' });
    await waitFor(() =>
      expect(fetchMock.mock.calls.some(([url]) => url === '/api/auth/demo-accounts')).toBe(true),
    );
    expect(screen.queryByRole('region', { name: 'Tài khoản demo' })).toBeNull();
  });

  it('production trả 404 thì không có hộp, trang vẫn dùng được', async () => {
    withAccounts(() => apiError(404, 'NOT_FOUND', 'Không tìm thấy.'));
    renderApp('/login');

    await screen.findByRole('heading', { name: 'Đăng nhập' });
    expect(screen.queryByRole('region', { name: 'Tài khoản demo' })).toBeNull();
  });
});
