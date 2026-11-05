import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { ROLE_LABELS } from '../../components/menu';
import {
  apiError,
  identityFor,
  jsonResponse,
  loggedInAs,
  renderApp,
  stubApi,
} from '../../test/fakeApi';

const LOGIN_MESSAGE =
  'Đăng nhập không thành công. Nếu nhập sai nhiều lần, tài khoản sẽ tạm khóa 15 phút.';

function anonymousApi(extra = {}) {
  return stubApi({
    'GET /api/auth/me': () => apiError(401, 'UNAUTHENTICATED', 'Bạn chưa đăng nhập.'),
    'GET /api/health': () => jsonResponse(200, { status: 'ok' }),
    'POST /api/auth/login': () => jsonResponse(200, identityFor('student', 'sv01')),
    ...extra,
  });
}

async function fillAndSubmit(user, username = 'sv01', password = 'Demo@12345') {
  await user.type(await screen.findByLabelText('Tên đăng nhập'), username);
  await user.type(screen.getByLabelText('Mật khẩu'), password);
  await user.click(screen.getByRole('button', { name: 'Đăng nhập' }));
}

function currentPath() {
  return screen.getByTestId('path').textContent;
}

describe('đăng nhập', () => {
  it('chưa đăng nhập vào trang bảo vệ thì chuyển tới /login, API me không gây vòng lặp', async () => {
    const fetchMock = anonymousApi();

    renderApp('/ho-so');

    expect(await screen.findByRole('heading', { name: 'Đăng nhập' })).toBeInTheDocument();
    expect(currentPath()).toBe('/login');
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('đăng nhập đúng thì về Tổng quan', async () => {
    const fetchMock = anonymousApi();
    const user = userEvent.setup();

    renderApp('/login');
    await fillAndSubmit(user);

    expect(await screen.findByRole('heading', { name: 'Tổng quan' })).toBeInTheDocument();
    expect(currentPath()).toBe('/');
    const [, options] = fetchMock.mock.calls.find(([url]) => url === '/api/auth/login');
    expect(JSON.parse(options.body)).toEqual({ username: 'sv01', password: 'Demo@12345' });
    expect(options.headers['X-Requested-With']).toBe('fetch');
  });

  it('đã đăng nhập mà mở /login thì về Tổng quan', async () => {
    loggedInAs('student');

    renderApp('/login');

    expect(await screen.findByRole('heading', { name: 'Tổng quan' })).toBeInTheDocument();
  });

  it('quay lại trang định vào sau khi đăng nhập', async () => {
    anonymousApi({
      'GET /api/students/me': () => apiError(500, 'INTERNAL_ERROR', 'Lỗi.'),
    });
    const user = userEvent.setup();

    renderApp('/m11/phan-tich');
    await fillAndSubmit(user);

    expect(await screen.findByRole('heading', { name: 'Phân tích' })).toBeInTheDocument();
    expect(currentPath()).toBe('/m11/phan-tich');
  });

  it.each(['//evil.test', '/\\evil.test', 'https://evil.test'])(
    'from không an toàn %s thì về Tổng quan',
    async (from) => {
      anonymousApi();
      const user = userEvent.setup();

      renderApp({ pathname: '/login', state: { from } });
      await fillAndSubmit(user);

      expect(await screen.findByRole('heading', { name: 'Tổng quan' })).toBeInTheDocument();
      expect(currentPath()).toBe('/');
    },
  );

  it('sai mật khẩu: hiện lỗi trong vùng aria-live, xóa mật khẩu, ở lại trang', async () => {
    anonymousApi({
      'POST /api/auth/login': () => apiError(401, 'INVALID_CREDENTIALS', LOGIN_MESSAGE),
    });
    const user = userEvent.setup();

    renderApp('/login');
    await fillAndSubmit(user, 'sv01', 'sai');

    const error = await screen.findByText(LOGIN_MESSAGE);
    expect(error).toHaveAttribute('aria-live', 'assertive');
    expect(screen.getByLabelText('Mật khẩu')).toHaveValue('');
    expect(screen.getByLabelText('Tên đăng nhập')).toHaveValue('sv01');
    expect(screen.getByRole('button', { name: 'Đăng nhập' })).toBeEnabled();
    expect(currentPath()).toBe('/login');
  });

  it('thiếu thông tin thì báo lỗi, không gọi API', async () => {
    const fetchMock = anonymousApi();
    const user = userEvent.setup();

    renderApp('/login');
    await user.click(await screen.findByRole('button', { name: 'Đăng nhập' }));

    expect(screen.getByText('Vui lòng nhập tên đăng nhập và mật khẩu.')).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([url]) => url === '/api/auth/login')).toBe(false);
  });

  it('dùng được hoàn toàn bằng bàn phím: Tab đúng thứ tự, Enter để gửi', async () => {
    const fetchMock = anonymousApi();
    const user = userEvent.setup();

    renderApp('/login');
    const username = await screen.findByLabelText('Tên đăng nhập');
    const password = screen.getByLabelText('Mật khẩu');
    username.focus();

    await user.keyboard('sv01');
    await user.tab();
    expect(password).toHaveFocus();
    await user.keyboard('Demo@12345');
    await user.tab();
    expect(screen.getByRole('button', { name: 'Hiện mật khẩu' })).toHaveFocus();
    await user.tab();
    expect(screen.getByRole('button', { name: 'Đăng nhập' })).toHaveFocus();
    await user.tab({ shift: true });
    await user.tab({ shift: true });
    expect(password).toHaveFocus();
    await user.keyboard('{Enter}');

    expect(await screen.findByRole('heading', { name: 'Tổng quan' })).toBeInTheDocument();
    expect(fetchMock.mock.calls.filter(([url]) => url === '/api/auth/login')).toHaveLength(1);
  });

  it('nút bị khóa khi đang gửi và không gửi hai lần', async () => {
    let finish;
    const fetchMock = anonymousApi({
      'POST /api/auth/login': () =>
        new Promise((resolve) => {
          finish = () => resolve(jsonResponse(200, identityFor('student', 'sv01')));
        }),
    });
    const user = userEvent.setup();

    renderApp('/login');
    await fillAndSubmit(user);

    expect(screen.getByRole('button', { name: 'Đang đăng nhập…' })).toBeDisabled();
    await user.keyboard('{Enter}');
    expect(fetchMock.mock.calls.filter(([url]) => url === '/api/auth/login')).toHaveLength(1);

    finish();
    expect(await screen.findByRole('heading', { name: 'Tổng quan' })).toBeInTheDocument();
  });

  it('trang đăng nhập không còn badge "Dữ liệu mẫu" (quản lý dự án yêu cầu xóa)', async () => {
    anonymousApi();

    renderApp('/login');

    await screen.findByLabelText('Mật khẩu');
    expect(screen.queryByText('Dữ liệu mẫu')).not.toBeInTheDocument();
  });

  it('lỗi kết nối khi kiểm tra phiên thì hiện lỗi và thử lại được', async () => {
    let calls = 0;
    stubApi({
      'GET /api/auth/me': () => {
        calls += 1;
        if (calls === 1) {
          throw new TypeError('Failed to fetch');
        }
        return jsonResponse(200, identityFor('student'));
      },
      'GET /api/health': () => jsonResponse(200, { status: 'ok' }),
    });
    const user = userEvent.setup();

    renderApp('/');

    expect(await screen.findByRole('alert')).toHaveTextContent('Không kết nối được tới máy chủ.');
    await user.click(screen.getByRole('button', { name: 'Thử lại' }));
    expect(await screen.findByRole('heading', { name: 'Tổng quan' })).toBeInTheDocument();
  });
});

describe('401 giữa phiên', () => {
  it('API trả 401 thì về /login, đăng nhập lại thì quay về đúng trang', async () => {
    let expired = true;
    loggedInAs('student', {
      'GET /api/students/me': () =>
        expired
          ? apiError(401, 'UNAUTHENTICATED', 'Bạn chưa đăng nhập.')
          : jsonResponse(200, {
              id: 'SV01',
              student_code: 'SV01',
              full_name: 'Sinh viên (mẫu)',
              cohort: 'K66',
              program: { id: 'p', name: 'Ngành (mẫu)' },
              program_version: { id: 'v', name: 'CTĐT (mẫu)', version: 1 },
              current_semester: null,
              advisors: [],
              contact_email: null,
              contact_phone: null,
              is_mock: true,
            }),
      'POST /api/auth/login': () => {
        expired = false;
        return jsonResponse(200, identityFor('student', 'sv01'));
      },
    });
    const user = userEvent.setup();

    renderApp('/ho-so');

    expect(await screen.findByLabelText('Mật khẩu')).toBeInTheDocument();
    expect(currentPath()).toBe('/login');

    await fillAndSubmit(user);

    expect(await screen.findByRole('heading', { name: 'Hồ sơ' })).toBeInTheDocument();
    expect(currentPath()).toBe('/ho-so');
  });
});

describe('đăng xuất', () => {
  it('gọi API, về /login và lần đăng nhập sau về Tổng quan', async () => {
    const fetchMock = loggedInAs('student', {
      'POST /api/auth/logout': () => new Response(null, { status: 204 }),
      'POST /api/auth/login': () => jsonResponse(200, identityFor('student', 'sv01')),
    });
    const user = userEvent.setup();

    renderApp('/m11/ket-qua');
    await user.click(await screen.findByRole('button', { name: 'Đăng xuất' }));

    expect(await screen.findByLabelText('Mật khẩu')).toBeInTheDocument();
    expect(currentPath()).toBe('/login');
    const [, options] = fetchMock.mock.calls.find(([url]) => url === '/api/auth/logout');
    expect(options.method).toBe('POST');

    await fillAndSubmit(user);
    expect(await screen.findByRole('heading', { name: 'Tổng quan' })).toBeInTheDocument();
  });

  it('đăng xuất lỗi thì báo và vẫn ở lại', async () => {
    loggedInAs('student', {
      'POST /api/auth/logout': () => apiError(500, 'INTERNAL_ERROR', 'Hệ thống gặp lỗi.'),
    });
    const user = userEvent.setup();

    renderApp('/m11/ket-qua');
    await user.click(await screen.findByRole('button', { name: 'Đăng xuất' }));

    expect(await screen.findByText(/Không đăng xuất được/)).toBeInTheDocument();
    expect(currentPath()).toBe('/m11/ket-qua');
    expect(screen.getByRole('button', { name: 'Đăng xuất' })).toBeEnabled();
  });
});

const EXPECTED_MENU = {
  student: {
    '': ['Tổng quan', 'Hồ sơ'],
    M11: ['Kết quả', 'Phân tích', 'Cảnh báo'],
    M12: ['Định hướng nghề', 'Kế hoạch học tập', 'Học liệu', 'Yêu cầu hỗ trợ', 'Nhắc nhở'],
  },
  advisor: {
    '': ['Tổng quan'],
    M11: ['Kết quả', 'Phân tích', 'Cảnh báo'],
    M12: ['Định hướng nghề', 'Kế hoạch học tập', 'Học liệu', 'Yêu cầu hỗ trợ'],
  },
  support_staff: {
    '': ['Tổng quan'],
    M12: ['Học liệu', 'Yêu cầu hỗ trợ'],
  },
  admin: {
    '': ['Tổng quan'],
    M11: ['Kết quả', 'Phân tích', 'Cảnh báo'],
    M12: ['Định hướng nghề', 'Học liệu', 'Yêu cầu hỗ trợ'],
    'Quản trị': ['Nhật ký'],
  },
};

describe('menu và khung theo vai trò', () => {
  it.each(Object.keys(EXPECTED_MENU))('%s thấy đúng menu', async (role) => {
    loggedInAs(role);

    renderApp('/');

    const nav = await screen.findByRole('navigation', { name: 'Menu chính' });
    const groups = {};
    for (const group of nav.querySelectorAll('.sidebar__group')) {
      const title = group.querySelector('.sidebar__title')?.textContent ?? '';
      groups[title] = within(group)
        .getAllByRole('link')
        .map((link) => link.textContent);
    }
    expect(groups).toEqual(EXPECTED_MENU[role]);
  });

  it.each(Object.keys(EXPECTED_MENU))(
    '%s: navbar có tên, vai trò và nút đăng xuất',
    async (role) => {
      loggedInAs(role);

      renderApp('/');

      const banner = await screen.findByRole('banner');
      expect(within(banner).getByText(`Người dùng ${role} (mẫu)`)).toBeInTheDocument();
      expect(banner).toHaveTextContent(ROLE_LABELS[role]);
      expect(within(banner).getByRole('button', { name: 'Đăng xuất' })).toBeInTheDocument();
      expect(within(banner).getByText('Dữ liệu mẫu')).toBeInTheDocument();
    },
  );

  it.each([
    ['student', '/quan-tri/nhat-ky'],
    ['advisor', '/ho-so'],
    ['admin', '/m12/nhac-nho'],
    ['support_staff', '/m11/ket-qua'],
  ])('%s mở %s thì thấy thông báo không có quyền', async (role, path) => {
    loggedInAs(role);

    renderApp(path);

    expect(
      await screen.findByRole('heading', { name: 'Bạn không có quyền xem trang này' }),
    ).toBeInTheDocument();
  });

  it('nút Menu mở, đóng sidebar và đóng lại sau khi chọn mục', async () => {
    loggedInAs('student');
    const user = userEvent.setup();

    renderApp('/');

    const toggle = await screen.findByRole('button', { name: 'Menu' });
    const nav = screen.getByRole('navigation', { name: 'Menu chính' });
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    expect(toggle).toHaveAttribute('aria-controls', nav.id);
    expect(nav).not.toHaveClass('sidebar--open');

    await user.click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(nav).toHaveClass('sidebar--open');

    await user.click(within(nav).getByRole('link', { name: 'Kết quả' }));
    expect(await screen.findByRole('heading', { name: 'Kết quả' })).toBeInTheDocument();
    await waitFor(() => expect(toggle).toHaveAttribute('aria-expanded', 'false'));
  });
});
