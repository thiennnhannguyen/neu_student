/** CR-05: trang Tổng quan và trang đích "Môn chưa đạt". */
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { apiError, jsonResponse, pendingResponse, renderApp } from '../../test/fakeApi';
import { callsTo, gradeRow, gradesBody, m11Api, overviewBody } from './testData';

const search = () => screen.getByTestId('search').textContent;
const path = () => screen.getByTestId('path').textContent;

describe('CR-05 Tổng quan', () => {
  it('thẻ Số môn chưa đạt dẫn tới danh sách tính đến kỳ đang xem, giữ sinh viên', async () => {
    m11Api('admin', {
      'GET /api/admin/students': () =>
        jsonResponse(200, { items: [], page: 1, page_size: 100, total: 0 }),
    });
    const user = userEvent.setup();

    renderApp('/?student=SV04&semester=S4');
    await screen.findByText('3,11');
    await user.click(screen.getByRole('link', { name: 'Số môn chưa đạt' }));

    expect(path()).toBe('/m11/ket-qua');
    const params = new URLSearchParams(search());
    expect(params.get('student')).toBe('SV04');
    expect(params.get('semester')).toBe('S4');
    expect(params.get('view')).toBe('failed');
  });

  // D-306 (CR-08) bỏ khỏi Tổng quan: nhãn "Đang xem", "Kỳ đã qua", "(kỳ hiện tại)", "Kỳ hiện tại: …"
  // (D-293), dòng phạm vi và tối đa 2 dòng phụ (D-295), dòng Q80 (D-292), khối "Mức cảnh báo chung"
  // (D-294), dòng "Tính lúc … · Điểm cập nhật lần cuối …" (D-293). Test thay thế: overviewCr08.test.jsx.

  it('không còn mã kỳ S1–S5 ở bất kỳ chữ nào trên trang', async () => {
    m11Api('student', {
      'GET /api/m11/overview': () =>
        jsonResponse(200, { ...overviewBody(), semester: { id: 'S5', name: 'HK1 2026-2027' } }),
    });
    renderApp('/');
    await screen.findByText('3,11');
    // D-306: chờ hai biểu đồ tải xong thay cho dòng phạm vi đã bỏ.
    await screen.findByRole('table', { name: 'Tín chỉ theo CTĐT' });
    await screen.findByRole('table', { name: 'Điểm trung bình theo kỳ' });
    const main = document.querySelector('main') ?? document.body;
    expect(main.textContent).not.toMatch(/\bS[1-9]\b/);
  });

  it('đổi kỳ nhanh liên tiếp: không hiện số của kỳ cũ trả về muộn', async () => {
    const slow = pendingResponse();
    m11Api('student', {
      'GET /api/m11/overview': (url) => {
        const semester = new URL(url, 'http://test').searchParams.get('semester_id');
        if (semester === 'S4') {
          return slow.handler();
        }
        return jsonResponse(200, overviewBody({ gpa: '2.22' }));
      },
    });
    const user = userEvent.setup();

    renderApp('/');
    await screen.findByText('2,22');
    await user.selectOptions(screen.getByLabelText('Học kỳ'), 'S4');
    await user.selectOptions(screen.getByLabelText('Học kỳ'), 'S5');
    expect(await screen.findByText('2,22')).toBeInTheDocument();

    slow.resolve(jsonResponse(200, overviewBody({ gpa: '9.99', semester: 'S4' })));
    await new Promise((resolve) => window.setTimeout(resolve, 20));
    expect(screen.queryByText('9,99')).toBeNull();
    expect(screen.getByText('2,22')).toBeInTheDocument();
  });

  it('API lỗi 500: báo lỗi và thử lại được', async () => {
    m11Api('student', {
      'GET /api/m11/overview': () => apiError(500, 'INTERNAL_ERROR', 'Lỗi máy chủ'),
    });
    renderApp('/');
    expect(await screen.findByText('Không tải được tổng quan')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Thử lại/ })).toBeInTheDocument();
  });
});

describe('CR-05 trang đích Môn chưa đạt', () => {
  const failedRows = [
    gradeRow({
      course_id: 'TOK',
      code: 'TOKT1145',
      name: 'Xác suất',
      status: 'failed',
      letter: 'F',
      retaking_semester: null,
    }),
    gradeRow({
      course_id: 'CTD',
      code: 'TIHT1101',
      name: 'Cấu trúc dữ liệu',
      status: 'failed',
      letter: 'F',
      retaking_semester: { id: 'S5', name: 'HK1 2026-2027', order: 5 },
    }),
  ];

  it('gọi view=failed_as_of, tiêu đề nói rõ phạm vi, số dòng bằng số trong tiêu đề', async () => {
    const fetchMock = m11Api('student', {
      'GET /api/m11/grades': () =>
        jsonResponse(
          200,
          gradesBody(failedRows, { meta: { ...gradesBody([]).meta, reference_semester: 'S4' } }),
        ),
    });

    renderApp('/m11/ket-qua?semester=S4&view=failed');

    expect(
      await screen.findByRole('heading', { name: 'Môn chưa đạt tính đến HK2 2025-2026: 2 môn' }),
    ).toBeInTheDocument();
    const call = callsTo(fetchMock, '/api/m11/grades').at(-1);
    expect(call.get('view')).toBe('failed_as_of');
    expect(call.get('semester_id')).toBe('S4');
    expect(call.get('status')).toBeNull();
    expect(screen.queryByLabelText('Trạng thái')).toBeNull();
    expect(screen.getAllByRole('row')).toHaveLength(3);
    expect(screen.getByText('Đang học lại HK1 2026-2027')).toBeInTheDocument();
  });

  it('không có tham số semester thì dùng kỳ hiện tại của hồ sơ', async () => {
    const fetchMock = m11Api('student', {
      'GET /api/m11/grades': () => jsonResponse(200, gradesBody([])),
    });
    renderApp('/m11/ket-qua?view=failed');
    expect(
      await screen.findByRole('heading', { name: 'Môn chưa đạt tính đến HK1 2026-2027: 0 môn' }),
    ).toBeInTheDocument();
    expect(callsTo(fetchMock, '/api/m11/grades').at(-1).get('semester_id')).toBe('S5');
    expect(screen.getByText('Không có môn chưa đạt tính đến kỳ này.')).toBeInTheDocument();
  });

  it('semester=all với view=failed: quay về bảng điểm tất cả các kỳ', async () => {
    const fetchMock = m11Api('student');
    renderApp('/m11/ket-qua?semester=all&view=failed');
    await waitFor(() => expect(search()).toBe('?semester=all'));
    await screen.findByText('Nhập môn');
    for (const call of callsTo(fetchMock, '/api/m11/grades')) {
      expect(call.get('view')).toBeNull();
    }
  });

  it('nút "Xem bảng điểm kỳ này" bỏ chế độ môn chưa đạt, giữ kỳ', async () => {
    m11Api('student', {
      'GET /api/m11/grades': () => jsonResponse(200, gradesBody(failedRows)),
    });
    const user = userEvent.setup();
    renderApp('/m11/ket-qua?semester=S4&view=failed');
    await user.click(await screen.findByRole('button', { name: 'Xem bảng điểm kỳ này' }));
    expect(search()).toBe('?semester=S4');
  });

  it('đổi kỳ trong chế độ môn chưa đạt thì giữ chế độ', async () => {
    m11Api('student', {
      'GET /api/m11/grades': () => jsonResponse(200, gradesBody(failedRows)),
    });
    const user = userEvent.setup();
    renderApp('/m11/ket-qua?semester=S4&view=failed');
    await screen.findByRole('button', { name: 'Xem bảng điểm kỳ này' });
    await user.selectOptions(screen.getByLabelText('Học kỳ'), 'S5');
    const params = new URLSearchParams(search());
    expect(params.get('semester')).toBe('S5');
    expect(params.get('view')).toBe('failed');
  });
});

describe('CR-05 nhãn nguồn dữ liệu', () => {
  it('panel giải thích không còn tên bảng tiếng Anh nào', async () => {
    m11Api('student');
    const user = userEvent.setup();
    renderApp('/');
    await user.click(await screen.findByRole('button', { name: 'Giải thích: Số môn chưa đạt' }));
    const dialog = await screen.findByRole('dialog', { name: 'Số môn chưa đạt' });
    await within(dialog).findByText('Công thức');
    expect(dialog.textContent).not.toMatch(/[a-z]+_[a-z_]+/);
  });
});
