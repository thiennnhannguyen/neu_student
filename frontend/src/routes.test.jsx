import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RouterProvider, createMemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { routes } from './routes';

function renderAt(path) {
  return render(<RouterProvider router={createMemoryRouter(routes, { initialEntries: [path] })} />);
}

function jsonResponse(status, body) {
  return new Response(JSON.stringify(body), { status });
}

describe('khung ứng dụng', () => {
  let fetchMock;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
  });

  it('luôn có nhãn "Dữ liệu mẫu" và chỗ logo', async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, { status: 'ok' }));

    renderAt('/');

    const banner = screen.getByRole('banner');
    expect(within(banner).getByText('Dữ liệu mẫu')).toBeInTheDocument();
    expect(within(banner).getByRole('img')).toHaveAttribute('src', '/brand/logo.svg');
    await screen.findByText('Backend đang hoạt động.');
  });

  it('hiện trạng thái đang tải rồi thành công', async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, { status: 'ok' }));

    renderAt('/');

    expect(screen.getByText('Đang kiểm tra kết nối...')).toBeInTheDocument();
    expect(await screen.findByText('Backend đang hoạt động.')).toBeInTheDocument();
  });

  it('hiện lỗi và thử lại được bằng bàn phím', async () => {
    fetchMock.mockRejectedValueOnce(new TypeError('Failed to fetch'));
    fetchMock.mockResolvedValueOnce(jsonResponse(200, { status: 'ok' }));
    const user = userEvent.setup();

    renderAt('/');

    expect(await screen.findByRole('alert')).toHaveTextContent('Không kết nối được tới máy chủ.');
    const retry = screen.getByRole('button', { name: 'Thử lại' });
    while (document.activeElement !== retry) {
      await user.tab();
    }
    await user.keyboard('{Enter}');
    expect(await screen.findByText('Backend đang hoạt động.')).toBeInTheDocument();
  });

  it('đường dẫn không tồn tại hiện trang không tìm thấy', () => {
    renderAt('/khong-ton-tai');

    expect(screen.getByRole('heading', { name: 'Không tìm thấy trang' })).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
