import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import {
  identityFor,
  jsonResponse,
  loggedInAs,
  pendingResponse,
  renderApp,
  stubApi,
} from './test/fakeApi';

describe('khung ứng dụng', () => {
  it('luôn có nhãn "Dữ liệu mẫu" và chỗ logo', async () => {
    loggedInAs('support_staff');

    renderApp('/');

    const banner = await screen.findByRole('banner');
    expect(within(banner).getByText('Dữ liệu mẫu')).toBeInTheDocument();
    const nav = screen.getByRole('navigation', { name: 'Menu chính' });
    expect(within(nav).getByRole('img')).toHaveAttribute('src', '/images/brand/logo_neu.svg');
    expect(
      screen.getByText(
        'Sản phẩm bài tập lớn – không phải hệ thống chính thức của Đại học Kinh tế Quốc dân.',
      ),
    ).toBeInTheDocument();
  });

  it.each(['student', 'advisor', 'support_staff'])(
    '%s không thấy trạng thái máy chủ, kể cả trong menu người dùng',
    async (role) => {
      const fetchMock = loggedInAs(role);
      const user = userEvent.setup();

      renderApp('/');
      await user.click(await screen.findByRole('button', { name: /Người dùng/ }));

      await screen.findByRole('menu');
      expect(screen.queryByText(/Máy chủ đang|kiểm tra máy chủ/)).not.toBeInTheDocument();
      expect(fetchMock.mock.calls.filter(([url]) => url === '/api/health')).toEqual([]);
    },
  );

  it('admin thấy chấm trạng thái trong menu người dùng: đang tải rồi hoạt động', async () => {
    const health = pendingResponse();
    loggedInAs('admin', { 'GET /api/health': health.handler });
    const user = userEvent.setup();

    renderApp('/');
    await user.click(await screen.findByRole('button', { name: /Người dùng/ }));

    expect(await screen.findByText('Đang kiểm tra máy chủ')).toBeInTheDocument();
    health.resolve(jsonResponse(200, { status: 'ok' }));
    expect(await screen.findByText('Máy chủ đang hoạt động')).toBeInTheDocument();
  });

  it('admin thấy lỗi kết nối trong menu người dùng', async () => {
    loggedInAs('admin', {
      'GET /api/health': () => {
        throw new TypeError('Failed to fetch');
      },
    });
    const user = userEvent.setup();

    renderApp('/');
    await user.click(await screen.findByRole('button', { name: /Người dùng/ }));

    expect(await screen.findByText('Không kết nối được máy chủ')).toBeInTheDocument();
  });

  it('đường dẫn không tồn tại hiện trang không tìm thấy', async () => {
    const fetchMock = stubApi({
      'GET /api/auth/me': () => jsonResponse(200, identityFor('student')),
    });

    renderApp('/khong-ton-tai');

    expect(
      await screen.findByRole('heading', { name: 'Không tìm thấy trang' }),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('trang chưa làm hiện "Đang phát triển"', async () => {
    loggedInAs('student');

    renderApp('/m12/dinh-huong');

    expect(await screen.findByRole('heading', { name: 'Định hướng nghề' })).toBeInTheDocument();
    expect(screen.getByText(/Đang phát triển/)).toBeInTheDocument();
  });
});
