/** CR-05: trang Tổng quan và trang đích "Môn chưa đạt". */
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { apiError, jsonResponse, pendingResponse, renderApp } from '../../test/fakeApi';
import {
  callsTo,
  EMPTY_OVERVIEW,
  gradeRow,
  gradesBody,
  m11Api,
  overviewBody,
  RISKS,
} from './testData';

const search = () => screen.getByTestId('search').textContent;
const path = () => screen.getByTestId('path').textContent;

function card(title) {
  return screen.getByRole('link', { name: title }).closest('article');
}

function details(title) {
  return [...card(title).querySelectorAll('.metric-card__detail')].map((line) => line.textContent);
}

const S4 = { semester: 'S4' };

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

  it('kỳ hiện tại ở dòng hồ sơ, kỳ đang xem có nhãn "Kỳ đã qua" khi là kỳ trước', async () => {
    m11Api('student', {
      'GET /api/m11/overview': () => jsonResponse(200, overviewBody(S4)),
    });

    renderApp('/?semester=S4');

    const welcome = await screen.findByRole('region', { name: 'Lời chào' });
    expect(await within(welcome).findByText(/Kỳ hiện tại: HK1/)).toBeInTheDocument();
    expect(within(welcome).getByText('HK2 2025-2026', { selector: 'strong' })).toBeInTheDocument();
    expect(within(welcome).getByText('Kỳ đã qua')).toBeInTheDocument();
    expect(within(welcome).queryByText('(kỳ hiện tại)')).toBeNull();
  });

  it('kỳ đang xem là kỳ hiện tại thì ghi "(kỳ hiện tại)", không có nhãn kỳ đã qua', async () => {
    m11Api('student');

    renderApp('/');

    const welcome = await screen.findByRole('region', { name: 'Lời chào' });
    expect(await within(welcome).findByText('(kỳ hiện tại)')).toBeInTheDocument();
    expect(within(welcome).queryByText('Kỳ đã qua')).toBeNull();
  });

  it('dưới mỗi số có phạm vi, dòng phạm vi là dòng cuối, không thẻ nào quá 2 dòng phụ', async () => {
    m11Api('student');

    renderApp('/');
    await screen.findByText('3,11');

    expect(details('GPA học kỳ')).toEqual(['Riêng Kỳ S5']);
    expect(details('GPA tích lũy')).toEqual(['Tính đến Kỳ S5']);
    expect(details('Tín chỉ đạt')).toEqual(['Nợ 6 · Đang học 15', 'Tính đến Kỳ S5']);
    expect(details('Số môn chưa đạt')).toEqual(['Tính đến Kỳ S5']);
  });

  it('GPA kỳ trống: dòng Q80 rồi dòng phạm vi, đúng 2 dòng phụ', async () => {
    const body = overviewBody({ gpa: null });
    body.metrics.semester_gpa.denominator = 0;
    m11Api('student', { 'GET /api/m11/overview': () => jsonResponse(200, body) });

    renderApp('/');
    await screen.findByRole('link', { name: 'GPA học kỳ' });

    await waitFor(() => expect(details('GPA học kỳ')).toHaveLength(2));
    expect(details('GPA học kỳ')[1]).toBe('Riêng Kỳ S5');
  });

  it('lý do cảnh báo lấy từ API, mức cao trước; thẻ Tín chỉ đạt không còn mức', async () => {
    m11Api('student');

    renderApp('/');
    await screen.findByText('3,11');

    const summary = screen.getByRole('link', { name: /Mức cảnh báo chung/ });
    const reasons = await within(summary).findAllByRole('listitem');
    expect(reasons.map((item) => item.textContent)).toEqual([
      'GPA tích lũy 1,81, dưới ngưỡng 2,00',
      'Nợ 3 tín chỉ',
    ]);
    expect(within(reasons[1]).getByRole('img', { name: 'Chú ý' })).toBeInTheDocument();
    expect(card('Tín chỉ đạt').className).toBe('metric-card');
    expect(card('Tín chỉ đạt').querySelector('.status-chip, .status-text')).toBeNull();
  });

  it('tối đa 2 lý do; mức Ổn thì chỉ có mức và câu lưu ý', async () => {
    const many = {
      ...RISKS,
      outcomes: RISKS.outcomes.map((row) =>
        row.rule_code === 'registration'
          ? { ...row, level: 'watch', summary: 'Đăng ký 9 tín chỉ, dưới mức tối thiểu 10' }
          : row,
      ),
    };
    m11Api('student', { 'GET /api/m11/risks': () => jsonResponse(200, many) });
    renderApp('/');
    await screen.findByText('3,11');
    const summary = screen.getByRole('link', { name: /Mức cảnh báo chung/ });
    expect(await within(summary).findAllByRole('listitem')).toHaveLength(2);
  });

  it('mức Ổn: không có lý do, vẫn có câu tham khảo', async () => {
    const normal = overviewBody();
    normal.metrics.risk_level.value = 'normal';
    m11Api('student', { 'GET /api/m11/overview': () => jsonResponse(200, normal) });

    renderApp('/');
    await screen.findByText('3,11');

    const summary = screen.getByRole('link', { name: /Mức cảnh báo chung/ });
    expect(within(summary).queryByRole('list')).toBeNull();
    expect(summary).toHaveTextContent('tham khảo');
  });

  it('tách "Tính lúc" và "Điểm cập nhật lần cuối"; chưa có thì nói rõ', async () => {
    m11Api('student');
    renderApp('/');
    expect(
      await screen.findByText(/Tính lúc \d\d\/11\/2026 .* · Điểm cập nhật lần cuối 19\/06\/2026/),
    ).toBeInTheDocument();
  });

  it('chưa ghi nhận thời điểm nhập điểm', async () => {
    m11Api('student', { 'GET /api/m11/overview': () => jsonResponse(200, EMPTY_OVERVIEW) });
    renderApp('/');
    expect(await screen.findByText(/Chưa ghi nhận thời điểm nhập điểm/)).toBeInTheDocument();
  });

  it('không còn mã kỳ S1–S5 ở bất kỳ chữ nào trên trang', async () => {
    m11Api('student', {
      'GET /api/m11/overview': () =>
        jsonResponse(200, { ...overviewBody(), semester: { id: 'S5', name: 'HK1 2026-2027' } }),
    });
    renderApp('/');
    await screen.findByText('3,11');
    await waitFor(() => expect(document.body.textContent).toContain('Tính đến HK1 2026-2027'));
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
