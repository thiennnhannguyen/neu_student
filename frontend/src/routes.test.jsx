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
    loggedInAs('student');

    renderApp('/');

    const banner = await screen.findByRole('banner');
    expect(within(banner).getByText('Dữ liệu mẫu')).toBeInTheDocument();
    expect(within(banner).getByRole('img')).toHaveAttribute('src', '/images/brand/logo_neu.svg');
    expect(
      screen.getByText(
        'Sản phẩm bài tập lớn – không phải hệ thống chính thức của Đại học Kinh tế Quốc dân.',
      ),
    ).toBeInTheDocument();
    await screen.findByText('Backend đang hoạt động.');
  });

  it('hiện trạng thái đang tải rồi thành công', async () => {
    const health = pendingResponse();
    loggedInAs('student', { 'GET /api/health': health.handler });

    renderApp('/');

    expect(await screen.findByText('Đang kiểm tra kết nối...')).toBeInTheDocument();
    health.resolve(jsonResponse(200, { status: 'ok' }));
    expect(await screen.findByText('Backend đang hoạt động.')).toBeInTheDocument();
  });

  it('hiện lỗi và thử lại được bằng bàn phím', async () => {
    let healthCalls = 0;
    loggedInAs('student', {
      'GET /api/health': () => {
        healthCalls += 1;
        if (healthCalls === 1) {
          throw new TypeError('Failed to fetch');
        }
        return jsonResponse(200, { status: 'ok' });
      },
    });
    const user = userEvent.setup();

    renderApp('/');

    expect(await screen.findByRole('alert')).toHaveTextContent('Không kết nối được tới máy chủ.');
    const retry = screen.getByRole('button', { name: 'Thử lại' });
    while (document.activeElement !== retry) {
      await user.tab();
    }
    await user.keyboard('{Enter}');
    expect(await screen.findByText('Backend đang hoạt động.')).toBeInTheDocument();
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

    renderApp('/m11/ket-qua');

    expect(await screen.findByRole('heading', { name: 'Kết quả' })).toBeInTheDocument();
    expect(screen.getByText(/Đang phát triển/)).toBeInTheDocument();
  });
});
