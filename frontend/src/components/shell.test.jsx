import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { m11Api } from '../features/m11/testData';
import { jsonResponse, loggedInAs, renderApp } from '../test/fakeApi';
import { MOCK_NOTICE } from './MockNotice';
import { pageMetaFor } from './menu';

const STORAGE_KEY = 'neu.sidebar.collapsed';

function nav() {
  return screen.getByRole('navigation', { name: 'Menu chính' });
}

beforeEach(() => window.localStorage.clear());
afterEach(() => window.localStorage.clear());

describe('sidebar', () => {
  it('mỗi mục có icon aria-hidden; mục đang chọn có aria-current="page"', async () => {
    loggedInAs('student');

    renderApp('/m12/dinh-huong');

    const current = await within(
      await screen.findByRole('navigation', { name: 'Menu chính' }),
    ).findByRole('link', { name: 'Định hướng nghề' });
    expect(current).toHaveAttribute('aria-current', 'page');
    for (const link of within(nav()).getAllByRole('link')) {
      expect(link.querySelector('svg')).toHaveAttribute('aria-hidden', 'true');
    }
    expect(
      within(nav())
        .getAllByRole('link')
        .filter((link) => link.hasAttribute('aria-current')),
    ).toHaveLength(1);
  });

  it('có logo, tên sản phẩm, dải họa tiết aria-hidden và thẻ người dùng', async () => {
    loggedInAs('admin');

    renderApp('/m12/hoc-lieu');

    await screen.findByRole('navigation', { name: 'Menu chính' });
    expect(within(nav()).getByText('NEU Student')).toBeInTheDocument();
    expect(within(nav()).getByText('Learning Platform')).toBeInTheDocument();
    expect(nav().querySelector('.motif-mosaic')).toHaveAttribute('aria-hidden', 'true');
    expect(within(nav()).getByText('Người dùng admin (mẫu)')).toBeInTheDocument();
  });

  it('thu gọn: nhớ trong localStorage, tên mục vẫn đọc được, mở lại được', async () => {
    loggedInAs('student');
    const user = userEvent.setup();

    const { container, unmount } = renderApp('/m12/dinh-huong');
    const collapse = await screen.findByRole('button', { name: 'Thu gọn menu' });
    expect(collapse).toHaveAttribute('aria-pressed', 'false');

    await user.click(collapse);

    expect(container.querySelector('.app-frame')).toHaveClass('app-frame--rail');
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe('1');
    expect(within(nav()).getByRole('link', { name: 'Kết quả' })).toHaveAttribute(
      'data-tooltip',
      'Kết quả',
    );

    unmount();
    renderApp('/m12/dinh-huong');
    const expand = await screen.findByRole('button', { name: 'Mở rộng menu' });
    expect(expand).toHaveAttribute('aria-pressed', 'true');
    await user.click(expand);
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe('0');
  });

  it('localStorage lỗi thì vẫn thu gọn được trong phiên, không vỡ trang', async () => {
    vi.spyOn(window.localStorage.__proto__, 'getItem').mockImplementation(() => {
      throw new Error('bị chặn');
    });
    vi.spyOn(window.localStorage.__proto__, 'setItem').mockImplementation(() => {
      throw new Error('bị chặn');
    });
    loggedInAs('student');
    const user = userEvent.setup();

    const { container } = renderApp('/m12/dinh-huong');
    await user.click(await screen.findByRole('button', { name: 'Thu gọn menu' }));

    expect(container.querySelector('.app-frame')).toHaveClass('app-frame--rail');
  });

  it('drawer: mở bằng nút Menu, focus vào trong, khóa Tab, Esc đóng và trả focus', async () => {
    loggedInAs('student');
    const user = userEvent.setup();

    renderApp('/m12/dinh-huong');
    const toggle = await screen.findByRole('button', { name: 'Menu' });
    toggle.focus();
    await user.keyboard('{Enter}');

    expect(nav()).toHaveClass('sidebar--open');
    expect(nav()).toContainElement(document.activeElement);
    const links = within(nav()).getAllByRole('link');
    links[0].focus();
    await user.tab({ shift: true });
    expect(nav()).toContainElement(document.activeElement);

    await user.keyboard('{Escape}');
    expect(nav()).not.toHaveClass('sidebar--open');
    expect(toggle).toHaveFocus();
  });

  it('drawer: bấm nền mờ thì đóng; phóng to tới 1024px thì đóng', async () => {
    let listener;
    window.matchMedia = vi.fn(() => ({
      addEventListener: (_name, handler) => {
        listener = handler;
      },
      removeEventListener: vi.fn(),
    }));
    loggedInAs('student');
    const user = userEvent.setup();

    const { container } = renderApp('/m12/dinh-huong');
    const toggle = await screen.findByRole('button', { name: 'Menu' });
    await user.click(toggle);
    await user.click(container.querySelector('.sidebar-scrim'));
    expect(toggle).toHaveAttribute('aria-expanded', 'false');

    await user.click(toggle);
    listener({ matches: false });
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    listener({ matches: true });
    await waitFor(() => expect(toggle).toHaveAttribute('aria-expanded', 'false'));
    delete window.matchMedia;
  });
});

describe('topbar', () => {
  it('có đường dẫn phân cấp, chuông đã hoạt động', async () => {
    loggedInAs('student');

    renderApp('/m12/dinh-huong');

    const banner = await screen.findByRole('banner');
    const crumbs = within(banner).getByRole('navigation', { name: 'Vị trí trang' });
    expect(within(crumbs).getByRole('link', { name: 'Tổng quan' })).toHaveAttribute('href', '/');
    expect(crumbs).toHaveTextContent('Định hướng & hỗ trợ');
    expect(within(banner).getByRole('button', { name: /Thông báo/ })).not.toHaveAttribute(
      'aria-disabled',
    );
  });

  it('trang không có trong menu vẫn có tên sản phẩm', async () => {
    loggedInAs('student');

    renderApp('/khong-co');

    const banner = await screen.findByRole('banner');
    expect(within(banner).getByText('NEU Student')).toBeInTheDocument();
    expect(pageMetaFor('/khong-co')).toBeNull();
  });

  it('sinh viên có mục Hồ sơ trong menu người dùng, vai trò khác thì không', async () => {
    loggedInAs('student');
    const user = userEvent.setup();

    renderApp('/m12/dinh-huong');
    await user.click(await screen.findByRole('button', { name: /Người dùng/ }));
    await user.click(screen.getByRole('menuitem', { name: 'Hồ sơ' }));

    expect(screen.getByTestId('path')).toHaveTextContent('/ho-so');
  });

  it('cố vấn không có mục Hồ sơ', async () => {
    loggedInAs('advisor');
    const user = userEvent.setup();

    renderApp('/m12/hoc-lieu');
    await user.click(await screen.findByRole('button', { name: /Người dùng/ }));

    expect(screen.queryByRole('menuitem', { name: 'Hồ sơ' })).toBeNull();
    expect(screen.getByRole('menuitem', { name: 'Đăng xuất' })).toBeInTheDocument();
  });
});

describe('một tiêu đề cho mỗi màn hình', () => {
  const PAGES = [
    ['student', '/', 'Tổng quan'],
    ['support_staff', '/', 'Tổng quan'],
    ['student', '/m11/ket-qua', 'Kết quả'],
    ['student', '/m11/phan-tich', 'Phân tích'],
    ['student', '/m11/canh-bao', 'Cảnh báo'],
    ['student', '/ho-so', 'Hồ sơ'],
    ['student', '/m12/dinh-huong', 'Định hướng nghề'],
    ['student', '/khong-co', 'Không tìm thấy trang'],
    ['admin', '/quan-tri/nhat-ky', 'Nhật ký thay đổi'],
  ];

  it.each(PAGES)('%s ở %s: đúng một h1 "%s"', async (role, path, title) => {
    m11Api(role, {
      'GET /api/students/me': () =>
        jsonResponse(200, {
          id: 'SV01',
          student_code: 'SV01',
          full_name: 'Sinh viên 01 (mẫu)',
          cohort: 'K66',
          program: { id: 'prog', name: 'CNTT (mẫu)' },
          program_version: { id: 'pv', name: 'CTĐT K66 (mẫu)', version: 1 },
          current_semester: { id: 'S5', name: 'HK1 (mẫu)' },
          advisors: [],
          contact_email: null,
          contact_phone: null,
          is_mock: true,
        }),
      'GET /api/admin/audit-logs': () =>
        jsonResponse(200, { items: [], page: 1, page_size: 20, total: 0 }),
    });

    renderApp(path);

    const heading = await screen.findByRole('heading', { level: 1, name: title });
    expect(screen.getAllByRole('heading', { level: 1 })).toEqual([heading]);
    expect(document.querySelectorAll('h1')).toHaveLength(1);
  });

  it('thanh trên cùng chỉ có đường dẫn phân cấp, không lặp tiêu đề trang', async () => {
    m11Api('student');

    renderApp('/m11/ket-qua');

    await screen.findByRole('heading', { level: 1, name: 'Kết quả' });
    const banner = screen.getByRole('banner');
    expect(within(banner).queryByRole('heading')).toBeNull();
    const crumbs = within(banner).getByRole('navigation', { name: 'Vị trí trang' });
    expect(within(banner).getAllByText('Kết quả')).toEqual([within(crumbs).getByText('Kết quả')]);
    expect(document.querySelector('.topbar__title')).toBeNull();
  });

  it('Tổng quan: bỏ PageHeader, h1 chỉ cho trình đọc màn hình, không có đường dẫn', async () => {
    m11Api('student');

    renderApp('/');

    const heading = await screen.findByRole('heading', { level: 1, name: 'Tổng quan' });
    expect(heading).toHaveClass('visually-hidden');
    expect(document.querySelector('.page-header')).toBeNull();
    expect(screen.getByRole('region', { name: 'Lời chào' })).toBeInTheDocument();
    expect(screen.queryByRole('navigation', { name: 'Vị trí trang' })).toBeNull();
    expect(await screen.findByLabelText('Học kỳ')).toBeInTheDocument();
  });
});

describe('trang theo vai trò', () => {
  it.each(['student', 'advisor', 'support_staff', 'admin'])(
    '%s: mọi trang có dòng chân trang và badge mẫu',
    async (role) => {
      loggedInAs(role);

      renderApp('/khong-co');

      await screen.findByRole('heading', { name: 'Không tìm thấy trang' });
      expect(screen.getByText(MOCK_NOTICE)).toBeInTheDocument();
      expect(screen.getByText('Dữ liệu mẫu')).toBeInTheDocument();
    },
  );

  it('nhân sự hỗ trợ có Tổng quan riêng: chào mừng và 2 lối tắt, không có số liệu', async () => {
    const fetchMock = loggedInAs('support_staff');

    renderApp('/');

    expect(await screen.findByRole('heading', { level: 1, name: 'Tổng quan' })).toBeInTheDocument();
    expect(screen.getByText('Chào Người dùng support_staff (mẫu)')).toBeInTheDocument();
    const shortcuts = screen.getByRole('region', { name: 'Lối tắt' });
    expect(
      within(shortcuts)
        .getAllByRole('link')
        .map((link) => link.getAttribute('href')),
    ).toEqual(['/m12/yeu-cau-ho-tro', '/m12/hoc-lieu']);
    expect(screen.queryByRole('article')).toBeNull();
    expect(fetchMock.mock.calls.filter(([url]) => String(url).startsWith('/api/m11'))).toEqual([]);
  });

  it('sinh viên thấy chào mừng với khóa, ngành, kỳ hiện tại và 4 lối tắt', async () => {
    loggedInAs('student', {
      'GET /api/students/me': () =>
        jsonResponse(200, {
          cohort: 'K66',
          program: { name: 'CNTT (mẫu)' },
          current_semester: { name: 'HK1 (mẫu)' },
        }),
    });

    renderApp('/');

    expect(await screen.findByText('K66 · CNTT (mẫu) · HK1 (mẫu)')).toBeInTheDocument();
    const shortcuts = screen.getByRole('region', { name: 'Lối tắt' });
    expect(within(shortcuts).getAllByRole('link')).toHaveLength(4);
  });

  it.each(['advisor', 'admin'])(
    '%s thấy vai trò ở thẻ chào mừng, không gọi API hồ sơ',
    async (role) => {
      const fetchMock = loggedInAs(role);

      renderApp('/');

      await screen.findByText(`Chào Người dùng ${role} (mẫu)`);
      expect(fetchMock.mock.calls.filter(([url]) => url === '/api/students/me')).toEqual([]);
    },
  );

  it('họa tiết ở thẻ chào mừng aria-hidden', async () => {
    loggedInAs('support_staff');

    renderApp('/');

    const welcome = await screen.findByRole('region', { name: 'Lời chào' });
    expect(welcome.querySelector('.motif-mosaic')).toHaveAttribute('aria-hidden', 'true');
  });

  it('trang đang phát triển có nút về Tổng quan', async () => {
    loggedInAs('student');

    renderApp('/m12/hoc-lieu');

    expect(await screen.findByRole('heading', { level: 1, name: 'Học liệu' })).toBeInTheDocument();
    expect(screen.getByText('Đang phát triển.')).toBeInTheDocument();
    expect(
      within(screen.getByRole('main')).getByRole('link', { name: 'Về Tổng quan' }),
    ).toHaveAttribute('href', '/');
  });

  it('không có quyền và 404 có nút về Tổng quan', async () => {
    loggedInAs('student');

    renderApp('/quan-tri/nhat-ky');

    await screen.findByRole('heading', { level: 1, name: 'Bạn không có quyền xem trang này' });
    expect(
      within(screen.getByRole('main')).getByRole('link', { name: 'Về Tổng quan' }),
    ).toBeInTheDocument();
  });

  it('styleguide có khi chạy dev, không cần đăng nhập', async () => {
    window.HTMLElement.prototype.scrollIntoView = vi.fn();
    renderApp('/dev/styleguide');

    expect(
      await screen.findByRole('heading', { level: 1, name: 'Hệ thống thiết kế NEU 2026' }),
    ).toBeInTheDocument();
    expect(await screen.findByText('Thang chữ Inter')).toBeInTheDocument();
  });
});

describe('quy tắc họa tiết sau đăng nhập', () => {
  it('họa tiết chỉ ở 4 vị trí đã định, không nằm trong bảng hay form', async () => {
    const { readdirSync, readFileSync } = await import('node:fs');
    const { join } = await import('node:path');
    const root = 'src';
    const users = readdirSync(root, { recursive: true })
      .filter((name) => /\.jsx$/.test(name) && !/\.test\.jsx$/.test(name))
      .filter((name) => readFileSync(join(root, name), 'utf8').includes('<MotifMosaic'))
      .map((name) => name.replaceAll('\\', '/'))
      .sort();

    expect(users).toEqual([
      'components/Sidebar.jsx',
      'components/WelcomeCard.jsx',
      'components/ui/EmptyState.jsx',
      'components/ui/PageHeader.jsx',
      'features/auth/LoginPage.jsx',
    ]);
  });
});
