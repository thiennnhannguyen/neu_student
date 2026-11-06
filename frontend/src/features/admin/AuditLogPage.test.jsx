import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { apiError, jsonResponse, loggedInAs, pendingResponse, renderApp } from '../../test/fakeApi';

const LOG = {
  id: 1,
  actor_id: 'user-sv01',
  actor_username: 'sv01',
  action: 'student.contact_update',
  entity: 'student',
  entity_id: 'SV01',
  before: { contact_phone: '0900000001' },
  after: { contact_phone: '0912345678' },
  created_at: '2026-03-10T12:00:00Z',
};

function logsApi(handler) {
  return loggedInAs('admin', { 'GET /api/admin/audit-logs': handler });
}

function page(items, overrides = {}) {
  return jsonResponse(200, { items, page: 1, page_size: 20, total: items.length, ...overrides });
}

function logCalls(fetchMock) {
  return fetchMock.mock.calls
    .map(([url]) => String(url))
    .filter((url) => url.startsWith('/api/admin/audit-logs'))
    .map((url) => new URL(url, 'http://x').searchParams);
}

describe('trang Nhật ký', () => {
  it('Xem mở panel so sánh 2 cột; Esc đóng và trả focus về nút', async () => {
    logsApi(() => page([LOG]));
    const user = userEvent.setup();

    renderApp('/quan-tri/nhat-ky');
    const open = await screen.findByRole('button', { name: 'Xem chi tiết bản ghi 1' });
    await user.click(open);

    const dialog = await screen.findByRole('dialog');
    const row = within(dialog).getByRole('row', { name: /contact_phone/ });
    expect(row).toHaveTextContent('0900000001');
    expect(row).toHaveTextContent('0912345678');
    expect(within(row).getByText('0912345678')).toHaveClass('diff-table__changed');
    await user.keyboard('{Escape}');
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(open).toHaveFocus();
  });

  it('bản ghi không có trước và sau thì nói rõ', async () => {
    logsApi(() => page([{ ...LOG, before: null, after: null }]));
    const user = userEvent.setup();

    renderApp('/quan-tri/nhat-ky');
    await user.click(await screen.findByRole('button', { name: 'Xem chi tiết bản ghi 1' }));

    expect(
      await screen.findByText('Bản ghi này không có dữ liệu trước và sau.'),
    ).toBeInTheDocument();
  });

  it('giá trị lồng nhau trong panel vẫn đọc được', async () => {
    logsApi(() => page([{ ...LOG, before: {}, after: { nested: { a: 1 } } }]));
    const user = userEvent.setup();

    renderApp('/quan-tri/nhat-ky');
    await user.click(await screen.findByRole('button', { name: 'Xem chi tiết bản ghi 1' }));

    expect(await screen.findByText('{"a":1}')).toBeInTheDocument();
  });

  it('hiện đang tải rồi bảng dữ liệu', async () => {
    const logs = pendingResponse();
    logsApi(logs.handler);

    renderApp('/quan-tri/nhat-ky');

    expect(await screen.findByText('Đang tải nhật ký...')).toBeInTheDocument();
    logs.resolve(page([LOG]));
    const table = await screen.findByRole('table');
    expect(within(table).getByText('sv01')).toBeInTheDocument();
    expect(within(table).getByText('student.contact_update')).toBeInTheDocument();
    expect(within(table).queryByText(/contact_phone/)).not.toBeInTheDocument();
  });

  it('bảng nằm trong vùng cuộn được bằng bàn phím', async () => {
    logsApi(() => page([LOG]));

    renderApp('/quan-tri/nhat-ky');

    const region = await screen.findByRole('region', { name: 'Bảng nhật ký' });
    expect(region).toHaveAttribute('tabindex', '0');
    expect(region).toHaveClass('table-scroll');
    expect(within(region).getByRole('table')).toBeInTheDocument();
  });

  it('bản ghi không có người thực hiện hiện "Hệ thống", before null hiện gạch', async () => {
    logsApi(() => page([{ ...LOG, actor_id: null, actor_username: null, before: null }]));

    renderApp('/quan-tri/nhat-ky');

    expect(await screen.findByText('Hệ thống')).toBeInTheDocument();
    await userEvent.setup().click(screen.getByRole('button', { name: 'Xem chi tiết bản ghi 1' }));
    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText('—')).toBeInTheDocument();
    expect(within(dialog).getByText('0912345678')).toBeInTheDocument();
  });

  it('không có dữ liệu thì hiện thông báo trống', async () => {
    logsApi(() => page([]));

    renderApp('/quan-tri/nhat-ky');

    expect(await screen.findByText('Không có bản ghi nhật ký phù hợp.')).toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('lỗi tải thì hiện lỗi và thử lại được', async () => {
    let calls = 0;
    logsApi(() => {
      calls += 1;
      return calls === 1 ? apiError(500, 'INTERNAL_ERROR', 'Hệ thống gặp lỗi.') : page([LOG]);
    });
    const user = userEvent.setup();

    renderApp('/quan-tri/nhat-ky');

    expect(await screen.findByRole('alert')).toHaveTextContent('Hệ thống gặp lỗi.');
    await user.click(screen.getByRole('button', { name: 'Thử lại' }));
    expect(await screen.findByRole('table')).toBeInTheDocument();
  });

  it('gửi đúng bộ lọc, ngày đổi sang mốc đầu và cuối ngày địa phương', async () => {
    const fetchMock = logsApi(() => page([LOG]));
    const user = userEvent.setup();

    renderApp('/quan-tri/nhat-ky');
    await screen.findByRole('table');
    await user.selectOptions(screen.getByLabelText('Đối tượng'), 'student');
    await user.type(screen.getByLabelText('Tên đăng nhập người thực hiện'), 'sv01');
    await user.type(screen.getByLabelText('Từ ngày'), '2026-03-10');
    await user.type(screen.getByLabelText('Đến ngày'), '2026-03-11');
    await user.keyboard('{Enter}');

    await waitFor(() => expect(logCalls(fetchMock)).toHaveLength(2));
    const params = logCalls(fetchMock)[1];
    expect(params.get('entity')).toBe('student');
    expect(params.get('actor')).toBe('sv01');
    expect(params.get('from')).toBe(new Date('2026-03-10T00:00:00.000').toISOString());
    expect(params.get('to')).toBe(new Date('2026-03-11T23:59:59.999').toISOString());
    expect(params.get('page')).toBe('1');
  });

  it('Xóa lọc đưa về không có bộ lọc', async () => {
    const fetchMock = logsApi(() => page([LOG]));
    const user = userEvent.setup();

    renderApp('/quan-tri/nhat-ky');
    await screen.findByRole('table');
    const entity = screen.getByLabelText('Đối tượng');
    await user.selectOptions(entity, 'student');
    await user.click(screen.getByRole('button', { name: 'Lọc' }));
    await waitFor(() => expect(logCalls(fetchMock)).toHaveLength(2));
    await user.click(await screen.findByRole('button', { name: 'Xóa lọc' }));

    await waitFor(() => expect(logCalls(fetchMock)).toHaveLength(3));
    expect(logCalls(fetchMock)[2].has('entity')).toBe(false);
    expect(entity).toHaveValue('');
  });

  it('lỗi 422 của bộ lọc hiện cạnh đúng ô', async () => {
    logsApi(() =>
      apiError(422, 'VALIDATION_ERROR', 'Dữ liệu không hợp lệ.', {
        fields: { from: ['Mốc bắt đầu không được sau mốc kết thúc.'] },
      }),
    );

    renderApp('/quan-tri/nhat-ky');

    expect(await screen.findByText('Mốc bắt đầu không được sau mốc kết thúc.')).toBeInTheDocument();
    expect(screen.getByLabelText('Từ ngày')).toHaveAttribute('aria-invalid', 'true');
  });

  it('phân trang: nút đúng trạng thái và gọi đúng trang', async () => {
    const fetchMock = logsApi((url) => {
      const current = Number(new URL(url, 'http://x').searchParams.get('page'));
      return page([{ ...LOG, id: current }], { page: current, total: 21 });
    });
    const user = userEvent.setup();

    renderApp('/quan-tri/nhat-ky');

    expect(await screen.findByText('Trang 1 / 2 (21 bản ghi)')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Trang trước' })).toBeDisabled();

    await user.click(screen.getByRole('button', { name: 'Trang sau' }));

    expect(await screen.findByText('Trang 2 / 2 (21 bản ghi)')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Trang sau' })).toBeDisabled();
    expect(logCalls(fetchMock)[1].get('page')).toBe('2');

    await user.click(screen.getByRole('button', { name: 'Trang trước' }));
    expect(await screen.findByText('Trang 1 / 2 (21 bản ghi)')).toBeInTheDocument();
  });
});
