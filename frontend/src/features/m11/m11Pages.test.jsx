import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { apiError, jsonResponse, pendingResponse, renderApp } from '../../test/fakeApi';
import { gpaThresholds, shortSemesterName, toChartData } from './GpaTrendChart';
import {
  ATTEMPTS,
  callsTo,
  COMPARE,
  CURRICULUM,
  EMPTY_OVERVIEW,
  gradeRow,
  gradesBody,
  m11Api,
  overviewBody,
  RISKS,
  SEMESTERS,
  STRENGTHS,
  TREND,
} from './testData';

/** Hai kỳ đều có điểm, để bảng so sánh có dữ liệu. */
const TWO_GRADED = {
  'GET /api/m11/gpa-trend': () =>
    jsonResponse(200, {
      ...TREND,
      points: [
        { semester_id: 'S4', order: 4, name: 'Kỳ 4', value: '2.75' },
        { semester_id: 'S5', order: 5, name: 'Kỳ 5', value: '3.00' },
      ],
    }),
};

const search = () => screen.getByTestId('search').textContent;
const path = () => screen.getByTestId('path').textContent;

/** Chờ các lời gọi đang chạy trả về, để kiểm "không xuất hiện" không qua sớm. */
const settled = () => new Promise((resolve) => window.setTimeout(resolve, 20));

function cellsOf(region, name) {
  const row = within(region).getByRole('rowheader', { name }).closest('tr');
  return within(row)
    .getAllByRole('cell')
    .map((cell) => cell.textContent);
}

function card(title) {
  return screen.getByRole('link', { name: title }).closest('article');
}

describe('chọn sinh viên', () => {
  it.each(['advisor', 'admin'])('%s chưa chọn: hiện hướng dẫn, không gọi API M11', async (role) => {
    const fetchMock = m11Api(role);

    renderApp('/m11/phan-tich');

    expect(await screen.findByText(/Chọn sinh viên ở ô/)).toBeInTheDocument();
    const m11Calls = fetchMock.mock.calls.filter(([url]) => String(url).startsWith('/api/m11'));
    expect(m11Calls).toEqual([]);
  });

  it('cố vấn chọn sinh viên: lưu vào URL và gọi API với student_id', async () => {
    const fetchMock = m11Api('advisor', {
      'GET /api/advisor/students': () =>
        jsonResponse(200, {
          items: [{ id: 'SV04', student_code: 'SV04', full_name: 'Sinh viên 04', cohort: 'K66' }],
          page: 1,
          page_size: 100,
          total: 1,
        }),
    });
    const user = userEvent.setup();

    renderApp('/');
    await screen.findByRole('option', { name: 'SV04 – Sinh viên 04' });
    await user.selectOptions(screen.getByLabelText('Sinh viên'), 'SV04');

    expect(await screen.findByText('3,11')).toBeInTheDocument();
    expect(search()).toContain('student=SV04');
    expect(callsTo(fetchMock, '/api/m11/overview').at(-1).get('student_id')).toBe('SV04');
    expect(screen.queryByLabelText('Tìm sinh viên')).not.toBeInTheDocument();
  });

  it('quản trị có ô tìm, gửi q lên API; bỏ chọn thì xóa khỏi URL', async () => {
    const fetchMock = m11Api('admin');
    const user = userEvent.setup();

    renderApp('/?student=SV09');
    await user.type(await screen.findByLabelText('Tìm sinh viên'), 'sv0');

    await waitFor(() =>
      expect(callsTo(fetchMock, '/api/admin/students').at(-1).get('q')).toBe('sv0'),
    );
    expect(screen.getByRole('option', { name: 'SV09' })).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText('Sinh viên'), '');
    expect(search()).toBe('');
  });

  it('sinh viên không có ô chọn, không gửi student_id dù URL có', async () => {
    const fetchMock = m11Api('student');

    renderApp('/?student=SV09');

    await screen.findByText('3,11');
    expect(screen.queryByLabelText('Sinh viên')).not.toBeInTheDocument();
    expect(callsTo(fetchMock, '/api/m11/overview')[0].has('student_id')).toBe(false);
  });

  it('sinh viên ngoài phạm vi: hiện lỗi và thử lại được', async () => {
    m11Api('advisor', {
      'GET /api/m11/semesters': () => apiError(404, 'NOT_FOUND', 'Không tìm thấy tài nguyên.'),
    });

    renderApp('/?student=SV05');

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Không tải được dữ liệu của sinh viên này',
    );
    expect(screen.getByRole('button', { name: 'Thử lại' })).toBeInTheDocument();
  });

  it('danh sách sinh viên lỗi thì báo ngay trên thanh trên', async () => {
    m11Api('advisor', {
      'GET /api/advisor/students': () => apiError(500, 'INTERNAL_ERROR', 'Lỗi'),
    });

    renderApp('/');

    expect(await screen.findByText('Không tải được danh sách sinh viên.')).toBeInTheDocument();
  });

  it('nhân sự hỗ trợ giữ trang chung, không gọi API M11', async () => {
    const fetchMock = m11Api('support_staff');

    renderApp('/');

    expect(await screen.findByText('Chào Người dùng support_staff')).toBeInTheDocument();
    expect(screen.queryByLabelText('Sinh viên')).not.toBeInTheDocument();
    expect(callsTo(fetchMock, '/api/m11/overview')).toEqual([]);
  });
});

describe('bộ lọc kỳ', () => {
  it('TC04: đổi kỳ thì gọi lại API, render số mới và lưu vào URL', async () => {
    const fetchMock = m11Api('student', {
      'GET /api/m11/overview': (url) => {
        const semester = new URL(url, 'http://x').searchParams.get('semester_id');
        const gpa = semester === 'S4' ? '2.75' : '3.11';
        return jsonResponse(200, overviewBody({ gpa, semester }));
      },
    });
    const user = userEvent.setup();

    renderApp('/');
    expect(await screen.findByText('3,11')).toBeInTheDocument();
    expect(callsTo(fetchMock, '/api/m11/overview')[0].get('semester_id')).toBe('S5');

    await user.selectOptions(screen.getByLabelText('Học kỳ'), 'S4');

    expect(await screen.findByText('2,75')).toBeInTheDocument();
    expect(screen.queryByText('3,11')).not.toBeInTheDocument();
    expect(search()).toContain('semester=S4');
    expect(callsTo(fetchMock, '/api/m11/overview').at(-1).get('semester_id')).toBe('S4');
  });

  it('đổi kỳ thì về trang 1 của bảng điểm', async () => {
    m11Api('student');
    const user = userEvent.setup();

    renderApp('/m11/ket-qua?page=3');
    await screen.findByRole('table');
    await user.selectOptions(screen.getByLabelText('Học kỳ'), 'S4');

    await waitFor(() => expect(search()).toBe('?semester=S4'));
  });

  it('kỳ hiện tại được ghi rõ trong danh sách', async () => {
    m11Api('student');

    renderApp('/');

    expect(
      await screen.findByRole('option', { name: 'HK1 2026-2027 – hiện tại' }),
    ).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'HK2 2025-2026' })).toBeInTheDocument();
  });

  it('mặc định là kỳ hiện tại, mở URL có kỳ thì dùng kỳ đó', async () => {
    const fetchMock = m11Api('student');

    renderApp('/?semester=S4');

    await screen.findByText('3,11');
    expect(screen.getByLabelText('Học kỳ')).toHaveValue('S4');
    expect(callsTo(fetchMock, '/api/m11/overview').at(-1).get('semester_id')).toBe('S4');
  });

  it.each(['/', '/m11/phan-tich', '/m11/canh-bao'])(
    '%s nhận semester=all: dùng kỳ hiện tại và bỏ all khỏi URL',
    async (page) => {
      m11Api('student');

      renderApp(`${page}?semester=all&student=SV01`);

      await waitFor(() => expect(search()).toBe('?student=SV01'));
      expect(await screen.findByLabelText('Học kỳ')).toHaveValue('S5');
      expect(screen.queryByRole('option', { name: 'Tất cả các kỳ' })).not.toBeInTheDocument();
    },
  );

  it('kỳ không có trong danh sách thì quay về kỳ hiện tại', async () => {
    m11Api('student');

    renderApp('/?semester=S99');

    await waitFor(() => expect(search()).toBe(''));
    expect(await screen.findByLabelText('Học kỳ')).toHaveValue('S5');
  });

  it('sidebar giữ sinh viên và kỳ khi chuyển trang', async () => {
    m11Api('admin');
    const user = userEvent.setup();

    renderApp('/?student=SV04&semester=S4');
    await screen.findByText('3,11');

    await user.click(
      within(screen.getByRole('navigation', { name: 'Menu chính' })).getByRole('link', {
        name: 'Cảnh báo',
      }),
    );

    expect(path()).toBe('/m11/canh-bao');
    expect(search()).toBe('?student=SV04&semester=S4');
  });

  it('chuyển từ Kết quả sang trang khác, sidebar không mang all', async () => {
    m11Api('admin');
    const user = userEvent.setup();

    renderApp('/m11/ket-qua?student=SV07&semester=all&status=failed');
    await screen.findByRole('table');

    await user.click(
      within(screen.getByRole('navigation', { name: 'Menu chính' })).getByRole('link', {
        name: 'Phân tích',
      }),
    );

    expect(path()).toBe('/m11/phan-tich');
    expect(search()).toBe('?student=SV07');
  });
});

describe('Tổng quan', () => {
  it('đang tải rồi 4 thẻ số liệu và dải cảnh báo', async () => {
    const overview = pendingResponse();
    m11Api('student', { 'GET /api/m11/overview': overview.handler });

    renderApp('/');

    expect(await screen.findByText('Đang tải tổng quan...')).toBeInTheDocument();
    overview.resolve(jsonResponse(200, overviewBody()));
    expect(await screen.findByText('3,11')).toBeInTheDocument();
    expect(screen.getAllByRole('article')).toHaveLength(4);
    expect(within(card('GPA tích lũy')).getByText('2,88')).toBeInTheDocument();
    expect(within(card('Tín chỉ đạt')).getByText('19')).toBeInTheDocument();
    expect(within(card('Tín chỉ đạt')).getByText('Nợ 6 · Đang học 15')).toBeInTheDocument();
    expect(within(card('Số môn chưa đạt')).getByText('2')).toBeInTheDocument();
    expect(
      within(screen.getByRole('link', { name: /Mức cảnh báo chung/ })).getByText('Cảnh báo'),
    ).toHaveClass('status-text');
    expect(screen.getByRole('link', { name: /Mức cảnh báo chung/ })).toHaveTextContent('tham khảo');
  });

  it('kỳ tham chiếu và thời điểm cập nhật chỉ có 1 dòng chung, không nằm trong thẻ', async () => {
    m11Api('student');

    renderApp('/');

    await screen.findByText('3,11');
    const lines = screen.getAllByText(/Kỳ tham chiếu Kỳ S5 · Cập nhật \d\d\/11\/2026/);
    expect(lines).toHaveLength(1);
    expect(lines[0].closest('article')).toBeNull();
    expect(lines[0]).toHaveTextContent('Quy chế K66-mau-v1');
  });

  it('thẻ theo mức của đúng quy tắc: có viền và nhãn; thẻ khác không có', async () => {
    m11Api('student');

    renderApp('/');

    await screen.findByText('3,11');
    const gpa = await waitFor(() => {
      const found = card('GPA tích lũy');
      expect(found).toHaveClass('metric-card--warning');
      return found;
    });
    expect(within(gpa).getByText('Cảnh báo')).toHaveClass('status-text');
    const credits = card('Tín chỉ đạt');
    expect(credits).toHaveClass('metric-card--watch');
    expect(within(credits).getByText('Chú ý')).toBeInTheDocument();
    for (const title of ['GPA học kỳ', 'Số môn chưa đạt']) {
      expect(card(title).className).toBe('metric-card');
      expect(card(title).querySelector('.status-chip')).toBeNull();
    }
  });

  it.each(['normal', 'insufficient_data', 'not_applicable'])(
    'quy tắc ở mức %s: thẻ không có viền và nhãn',
    async (level) => {
      m11Api('student', {
        'GET /api/m11/risks': () =>
          jsonResponse(200, {
            ...RISKS,
            outcomes: RISKS.outcomes.map((outcome) => ({ ...outcome, level })),
          }),
      });

      renderApp('/');

      await screen.findByText('3,11');
      await settled();
      expect(card('GPA tích lũy').className).toBe('metric-card');
      expect(card('Tín chỉ đạt').className).toBe('metric-card');
    },
  );

  it('không đọc được cảnh báo: số liệu vẫn hiện, không có nhãn', async () => {
    const fetchMock = m11Api('student', {
      'GET /api/m11/risks': () => apiError(500, 'INTERNAL_ERROR', 'Lỗi'),
    });

    renderApp('/?semester=S4');

    expect(await screen.findByText('3,11')).toBeInTheDocument();
    await settled();
    expect(card('GPA tích lũy').className).toBe('metric-card');
    expect(callsTo(fetchMock, '/api/m11/risks')[0].get('semester_id')).toBe('S4');
  });

  it('bộ lọc kỳ nằm trong thẻ chào mừng', async () => {
    m11Api('student');

    renderApp('/');

    const welcome = await screen.findByRole('region', { name: 'Lời chào' });
    expect(await within(welcome).findByLabelText('Học kỳ')).toHaveValue('S5');
  });

  it.each([
    ['GPA học kỳ', '/m11/phan-tich'],
    ['Tín chỉ đạt', '/m11/phan-tich'],
    ['Số môn chưa đạt', '/m11/ket-qua'],
  ])('bấm thẻ %s sang trang chi tiết, giữ tham số', async (title, target) => {
    m11Api('student');
    const user = userEvent.setup();

    renderApp('/?semester=S4');
    await screen.findByText('3,11');
    await user.click(screen.getByRole('link', { name: title }));

    expect(path()).toBe(target);
    expect(search()).toBe('?semester=S4');
  });

  it('không lặp biểu đồ của trang Phân tích', async () => {
    const fetchMock = m11Api('student');

    renderApp('/');

    await screen.findByText('3,11');
    expect(callsTo(fetchMock, '/api/m11/gpa-trend')).toEqual([]);
  });

  it('SV05 chưa có dữ liệu: hiện gạch và giải thích, không hiện 0 cho GPA', async () => {
    m11Api('student', { 'GET /api/m11/overview': () => jsonResponse(200, EMPTY_OVERVIEW) });

    renderApp('/');

    expect(await screen.findByText(/Chưa có kết quả học tập/)).toBeInTheDocument();
    expect(within(card('GPA học kỳ')).getByText('—')).toBeInTheDocument();
    expect(within(card('GPA tích lũy')).getByText('—')).toBeInTheDocument();
    expect(within(card('Tín chỉ đạt')).getByText('0')).toBeInTheDocument();
  });

  it('lỗi thì hiện thông báo và thử lại bằng bàn phím', async () => {
    let calls = 0;
    m11Api('student', {
      'GET /api/m11/overview': () => {
        calls += 1;
        return calls === 1
          ? apiError(500, 'INTERNAL_ERROR', 'Hệ thống gặp lỗi.')
          : jsonResponse(200, overviewBody());
      },
    });
    const user = userEvent.setup();

    renderApp('/');

    expect(await screen.findByRole('alert')).toHaveTextContent('Không tải được tổng quan');
    screen.getByRole('button', { name: 'Thử lại' }).focus();
    await user.keyboard('{Enter}');
    expect(await screen.findByText('3,11')).toBeInTheDocument();
  });

  it('nút "i" mở panel giải thích; Esc đóng và trả focus về nút', async () => {
    const fetchMock = m11Api('student');
    const user = userEvent.setup();

    renderApp('/');
    const info = await screen.findByRole('button', { name: 'Giải thích: Số môn chưa đạt' });
    expect(callsTo(fetchMock, '/api/m11/metrics-glossary')).toEqual([]);
    info.focus();
    await user.keyboard('{Enter}');

    const dialog = await screen.findByRole('dialog', { name: 'Số môn chưa đạt' });
    expect(
      await within(dialog).findByText('Số nhóm môn có lần hiệu lực trượt.'),
    ).toBeInTheDocument();
    expect(within(dialog).getByText('grade_attempts')).toBeInTheDocument();
    expect(within(dialog).getByText('K66-mau-v1')).toBeInTheDocument();
    expect(within(dialog).getByText(/lớn hơn số dòng "Chưa đạt"/)).toBeInTheDocument();
    expect(within(dialog).getByRole('button', { name: 'Đóng' })).toHaveFocus();

    await user.keyboard('{Tab}');
    expect(within(dialog).getByRole('button', { name: 'Đóng' })).toHaveFocus();
    await user.keyboard('{Escape}');

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(info).toHaveFocus();
  });

  it('panel giải thích: khóa không có quy chế ghi "Không xác định"', async () => {
    m11Api('student', {
      'GET /api/m11/metrics-glossary': () =>
        jsonResponse(200, {
          items: [
            { key: 'semester_gpa', formula: 'CT', source: 'Nguồn', rule_version: null, note: 'G' },
          ],
        }),
    });
    const user = userEvent.setup();

    renderApp('/');
    await user.click(await screen.findByRole('button', { name: 'Giải thích: GPA học kỳ' }));

    expect(await screen.findByText('Không xác định')).toBeInTheDocument();
  });

  it('panel giải thích: chỉ số chưa có giải thích', async () => {
    m11Api('student');
    const user = userEvent.setup();

    renderApp('/');
    await user.click(await screen.findByRole('button', { name: 'Giải thích: GPA học kỳ' }));

    expect(await screen.findByText('Chưa có giải thích cho chỉ số này.')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Đóng' }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});

describe('Tổng quan: GPA học kỳ trống (Q80)', () => {
  const noSemesterResult = () => {
    const body = overviewBody({ gpa: null });
    body.metrics.semester_gpa.denominator = 0;
    return jsonResponse(200, body);
  };

  it('mẫu số bằng 0: ghi chưa có kết quả và kỳ gần nhất có điểm, các thẻ khác giữ kỳ', async () => {
    const fetchMock = m11Api('student', {
      'GET /api/m11/overview': noSemesterResult,
      'GET /api/m11/gpa-trend': () =>
        jsonResponse(200, {
          ...TREND,
          points: [
            { semester_id: 'S3', order: 3, name: 'Kỳ 3', value: '2.50' },
            { semester_id: 'S4', order: 4, name: 'Kỳ 4', value: '3.11' },
            { semester_id: 'S5', order: 5, name: 'Kỳ 5', value: null },
          ],
        }),
    });

    renderApp('/?semester=S5');

    await screen.findByRole('link', { name: 'GPA học kỳ' });
    const gpaCard = card('GPA học kỳ');
    expect(await within(gpaCard).findByText('Kỳ này chưa có kết quả')).toBeInTheDocument();
    expect(await within(gpaCard).findByText('Kỳ gần nhất có điểm (S4): 3,11')).toBeInTheDocument();
    expect(within(gpaCard).getByText('Chưa có kết quả · Gần nhất S4: 3,11')).toBeInTheDocument();
    expect(within(gpaCard).getByText('—')).toBeInTheDocument();
    expect(screen.getByText(/Kỳ tham chiếu Kỳ S5/)).toBeInTheDocument();
    expect(callsTo(fetchMock, '/api/m11/gpa-trend')[0].get('semester_id')).toBe('S5');
    expect(screen.getByLabelText('Học kỳ')).toHaveValue('S5');
  });

  it('không có kỳ nào có điểm: chỉ ghi dòng đầu', async () => {
    m11Api('student', {
      'GET /api/m11/overview': noSemesterResult,
      'GET /api/m11/gpa-trend': () =>
        jsonResponse(200, {
          ...TREND,
          points: [{ semester_id: 'S5', order: 5, name: 'Kỳ 5', value: null }],
        }),
    });

    renderApp('/');

    expect(await screen.findByText('Kỳ này chưa có kết quả')).toBeInTheDocument();
    await settled();
    expect(screen.queryByText(/Kỳ gần nhất có điểm/)).not.toBeInTheDocument();
    expect(screen.getByText('Chưa có kết quả')).toBeInTheDocument();
  });

  it('lỗi khi đọc kỳ gần nhất: vẫn có dòng đầu, không làm hỏng trang', async () => {
    m11Api('student', {
      'GET /api/m11/overview': noSemesterResult,
      'GET /api/m11/gpa-trend': () => apiError(500, 'INTERNAL_ERROR', 'Lỗi'),
    });

    renderApp('/');

    expect(await screen.findByText('Kỳ này chưa có kết quả')).toBeInTheDocument();
    await settled();
    expect(screen.queryByText(/Kỳ gần nhất có điểm/)).not.toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('có mẫu số: không có dòng này, không gọi thêm API', async () => {
    const fetchMock = m11Api('student');

    renderApp('/');

    await screen.findByText('3,11');
    expect(screen.queryByText('Kỳ này chưa có kết quả')).not.toBeInTheDocument();
    expect(callsTo(fetchMock, '/api/m11/gpa-trend')).toEqual([]);
  });
});

describe('Kết quả', () => {
  const STATUS_ROWS = [
    ['done', 'Đạt'],
    ['done_via_equivalency', 'Đạt qua tương đương'],
    ['exempt', 'Miễn'],
    ['in_progress', 'Đang học'],
    ['failed', 'Chưa đạt'],
    ['not_started', 'Chưa học'],
  ];

  function oneRow(row) {
    return { 'GET /api/m11/grades': () => jsonResponse(200, gradesBody([row])) };
  }

  it('đang tải rồi bảng; số theo kiểu Việt Nam', async () => {
    const grades = pendingResponse();
    m11Api('student', { 'GET /api/m11/grades': grades.handler });

    renderApp('/m11/ket-qua');

    expect(await screen.findByText('Đang tải bảng điểm...')).toBeInTheDocument();
    grades.resolve(jsonResponse(200, gradesBody([gradeRow()])));
    const table = await screen.findByRole('table');
    expect(within(table).getByText('8,60')).toBeInTheDocument();
    expect(within(table).getByText('4,00')).toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Bảng điểm' })).toHaveAttribute('tabindex', '0');
  });

  it.each(STATUS_ROWS)(
    'trạng thái %s có biểu tượng tên "%s", không chỉ màu',
    async (status, label) => {
      m11Api('student', oneRow(gradeRow({ status })));

      renderApp('/m11/ket-qua');

      const table = await screen.findByRole('table');
      const icon = within(table).getByRole('img', { name: label });
      expect(icon).toHaveClass('status-icon');
      expect(icon.querySelector('svg[aria-hidden="true"]')).toBeInTheDocument();
    },
  );

  it('có đủ 6 trạng thái trong bộ lọc, chọn thì gửi status và về trang 1', async () => {
    const fetchMock = m11Api('student');
    const user = userEvent.setup();

    renderApp('/m11/ket-qua?page=2');
    await screen.findByRole('table');
    const select = screen.getByLabelText('Trạng thái');
    for (const [, label] of STATUS_ROWS) {
      expect(within(select).getByRole('option', { name: label })).toBeInTheDocument();
    }

    await user.selectOptions(select, 'failed');

    await waitFor(() => expect(search()).toBe('?status=failed'));
    const last = callsTo(fetchMock, '/api/m11/grades').at(-1);
    expect(last.get('status')).toBe('failed');
    expect(last.get('page')).toBe('1');
  });

  it('ô không có giá trị được đánh dấu để ẩn trên thẻ di động, vẫn hiện gạch', async () => {
    m11Api(
      'student',
      oneRow(gradeRow({ semester: null, score_10: null, letter: null, grade_4: null })),
    );

    renderApp('/m11/ket-qua');

    const table = await screen.findByRole('table');
    expect(table.querySelectorAll('td.ui-table__blank')).toHaveLength(4);
    expect(within(table).getAllByText('—')).toHaveLength(4);
  });

  it('mã null hiện "Chưa có mã"', async () => {
    m11Api('student', oneRow(gradeRow({ code: null })));

    renderApp('/m11/ket-qua');

    expect(
      await within(await screen.findByRole('table')).findByText('Chưa có mã'),
    ).toBeInTheDocument();
  });

  it('tìm môn: gửi q khi bấm Tìm', async () => {
    const fetchMock = m11Api('student');
    const user = userEvent.setup();

    renderApp('/m11/ket-qua');
    await user.type(await screen.findByLabelText('Tìm môn'), 'giải tích{Enter}');

    await waitFor(() =>
      expect(callsTo(fetchMock, '/api/m11/grades').at(-1).get('q')).toBe('giải tích'),
    );
    expect(search()).toContain('q=');
  });

  it('"Tất cả các kỳ": lưu all vào URL, không gửi semester_id', async () => {
    const fetchMock = m11Api('student');
    const user = userEvent.setup();

    renderApp('/m11/ket-qua');
    await screen.findByRole('table');
    expect(callsTo(fetchMock, '/api/m11/grades')[0].get('semester_id')).toBe('S5');

    await user.selectOptions(screen.getByLabelText('Học kỳ'), 'all');

    await waitFor(() => expect(search()).toBe('?semester=all'));
    expect(callsTo(fetchMock, '/api/m11/grades').at(-1).has('semester_id')).toBe(false);
  });

  it('mở trực tiếp ?semester=all và lọc Chưa học', async () => {
    const fetchMock = m11Api(
      'student',
      oneRow(
        gradeRow({
          status: 'not_started',
          semester: null,
          score_10: null,
          letter: null,
          grade_4: null,
        }),
      ),
    );

    renderApp('/m11/ket-qua?semester=all&status=not_started');

    const table = await screen.findByRole('table');
    expect(within(table).getByRole('img', { name: 'Chưa học' })).toBeInTheDocument();
    expect(screen.getByLabelText('Học kỳ')).toHaveValue('all');
    const last = callsTo(fetchMock, '/api/m11/grades').at(-1);
    expect(last.has('semester_id')).toBe(false);
    expect(last.get('status')).toBe('not_started');
  });

  it('không có dòng nào: trạng thái rỗng', async () => {
    m11Api('student', { 'GET /api/m11/grades': () => jsonResponse(200, gradesBody([])) });

    renderApp('/m11/ket-qua');

    expect(await screen.findByText('Không có môn nào phù hợp với bộ lọc.')).toBeInTheDocument();
  });

  it('lỗi tải bảng điểm', async () => {
    m11Api('student', { 'GET /api/m11/grades': () => apiError(500, 'INTERNAL_ERROR', 'Lỗi') });

    renderApp('/m11/ket-qua');

    expect(await screen.findByRole('alert')).toHaveTextContent('Không tải được bảng điểm');
  });

  it('phân trang', async () => {
    const fetchMock = m11Api('student', {
      'GET /api/m11/grades': (url) => {
        const page = parseInt(new URL(url, 'http://x').searchParams.get('page'), 10);
        return jsonResponse(200, gradesBody([gradeRow()], { page, total: 25 }));
      },
    });
    const user = userEvent.setup();

    renderApp('/m11/ket-qua');
    expect(await screen.findByText('Trang 1/2 · 25 môn')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Trang trước' })).toBeDisabled();

    await user.click(screen.getByRole('button', { name: 'Trang sau' }));

    expect(await screen.findByText('Trang 2/2 · 25 môn')).toBeInTheDocument();
    expect(callsTo(fetchMock, '/api/m11/grades').at(-1).get('page')).toBe('2');
    expect(screen.getByRole('button', { name: 'Trang sau' })).toBeDisabled();
    await user.click(screen.getByRole('button', { name: 'Trang trước' }));
    await waitFor(() => expect(search()).toBe('?page=1'));
  });

  it('chỉ có 1 trang: ẩn phân trang, vẫn ghi số môn', async () => {
    m11Api('student', {
      'GET /api/m11/grades': () => jsonResponse(200, gradesBody([gradeRow()], { total: 16 })),
    });

    renderApp('/m11/ket-qua');

    expect(await screen.findByText('16 môn')).toBeInTheDocument();
    expect(screen.queryByRole('navigation', { name: 'Phân trang bảng điểm' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Trang sau' })).toBeNull();
  });

  it('đúng 21 môn thì có 2 trang và có phân trang', async () => {
    m11Api('student', {
      'GET /api/m11/grades': () => jsonResponse(200, gradesBody([gradeRow()], { total: 21 })),
    });

    renderApp('/m11/ket-qua');

    expect(await screen.findByText('Trang 1/2 · 21 môn')).toBeInTheDocument();
    expect(screen.queryByText('21 môn')).toBeNull();
  });

  it('bảng điểm có lớp riêng cho thẻ di động', async () => {
    m11Api('student');

    renderApp('/m11/ket-qua');

    expect(await screen.findByRole('table')).toHaveClass('ui-table', 'grades-table');
  });

  it('trang trong URL không hợp lệ thì dùng trang 1', async () => {
    const fetchMock = m11Api('student');

    renderApp('/m11/ket-qua?page=abc');

    await screen.findByRole('table');
    expect(callsTo(fetchMock, '/api/m11/grades')[0].get('page')).toBe('1');
  });

  it('dòng học lại có nút, bấm mở panel lịch sử theo thứ tự kỳ', async () => {
    const fetchMock = m11Api('admin', {
      ...oneRow(
        gradeRow({
          course_id: 'MAU101',
          code: 'MAU101',
          name: 'Giải tích',
          has_retake: true,
        }),
      ),
      'GET /api/m11/grades/MAU101/attempts': () => jsonResponse(200, ATTEMPTS),
    });
    const user = userEvent.setup();

    renderApp('/m11/ket-qua?student=SV02');
    await user.click(await screen.findByRole('button', { name: /Xem lịch sử học lại Giải tích/ }));

    const dialog = await screen.findByRole('dialog');
    const items = await within(dialog).findAllByRole('listitem');
    expect(items.map((item) => item.querySelector('p').textContent)).toEqual([
      'Lần thứ 1 · HK1 2024-2025',
      'Lần thứ 2 · HK1 2025-2026',
      'Lần thứ 3 · HK1 2026-2027',
    ]);
    expect(within(items[0]).getByRole('img', { name: 'Chưa đạt' })).toBeInTheDocument();
    expect(within(items[0]).queryByText('Lần được tính')).not.toBeInTheDocument();
    expect(within(items[1]).getByText('Lần được tính')).toBeInTheDocument();
    expect(within(items[2]).getByRole('img', { name: 'Đang học' })).toBeInTheDocument();
    expect(callsTo(fetchMock, '/api/m11/grades/MAU101/attempts')[0].get('student_id')).toBe('SV02');

    await user.keyboard('{Escape}');
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('panel lịch sử rỗng', async () => {
    m11Api('student', {
      ...oneRow(gradeRow({ has_retake: true })),
      'GET /api/m11/grades/CNT101/attempts': () => jsonResponse(200, { ...ATTEMPTS, items: [] }),
    });
    const user = userEvent.setup();

    renderApp('/m11/ket-qua');
    await user.click(await screen.findByRole('button', { name: /Xem lịch sử/ }));

    expect(await screen.findByText('Chưa có lần học nào.')).toBeInTheDocument();
  });

  it('dòng không học lại thì không có nút lịch sử', async () => {
    m11Api('student');

    renderApp('/m11/ket-qua');

    await screen.findByRole('table');
    expect(screen.queryByRole('button', { name: /Xem lịch sử/ })).not.toBeInTheDocument();
  });

  it('sắp xếp điểm trong trang hiện tại, ô trống không thành 0', async () => {
    m11Api('student', {
      'GET /api/m11/grades': () =>
        jsonResponse(
          200,
          gradesBody([
            gradeRow({ course_id: 'A', name: 'Môn A', score_10: '8.50' }),
            gradeRow({ course_id: 'B', name: 'Môn B', score_10: '10.00' }),
            gradeRow({ course_id: 'C', name: 'Môn C', score_10: null }),
          ]),
        ),
    });
    const user = userEvent.setup();

    renderApp('/m11/ket-qua');
    const table = await screen.findByRole('table');
    await user.click(within(table).getByRole('button', { name: 'Điểm' }));

    const scores = within(table)
      .getAllByRole('row')
      .slice(1)
      .map((row) => within(row).getAllByRole('cell')[4].textContent);
    expect(scores).toEqual(['8,50', '10,00', '—']);
  });

  it('sắp xếp học kỳ theo thứ tự kỳ, không theo tên', async () => {
    m11Api('student', {
      'GET /api/m11/grades': () =>
        jsonResponse(
          200,
          gradesBody([
            gradeRow({ course_id: 'B', semester: { id: 'S3', name: 'Kỳ A', order: 3 } }),
            gradeRow({ course_id: 'A', semester: { id: 'S2', name: 'Kỳ Z', order: 2 } }),
          ]),
        ),
    });
    const user = userEvent.setup();

    renderApp('/m11/ket-qua');
    const table = await screen.findByRole('table');
    await user.click(within(table).getByRole('button', { name: 'Học kỳ' }));

    const names = within(table)
      .getAllByRole('row')
      .slice(1)
      .map((row) => within(row).getAllByRole('cell')[3].textContent);
    expect(names).toEqual(['Kỳ Z', 'Kỳ A']);
  });

  it('tìm môn thì về trang 1', async () => {
    m11Api('student');
    const user = userEvent.setup();

    renderApp('/m11/ket-qua?page=3');
    await user.type(await screen.findByLabelText('Tìm môn'), 'toán{Enter}');

    await waitFor(() => expect(search()).toBe('?q=to%C3%A1n'));
  });

  it('cảnh báo dữ liệu của cả bảng: có thì hiện, không có thì không có khối này', async () => {
    m11Api('student', {
      'GET /api/m11/grades': () =>
        jsonResponse(
          200,
          gradesBody([gradeRow()], {
            meta: {
              ...gradesBody([]).meta,
              data_warnings: [{ code: 'X', course_id: null, semester_id: null, message: 'Thiếu.' }],
            },
          }),
        ),
    });

    renderApp('/m11/ket-qua');

    expect(await screen.findByText('Cảnh báo dữ liệu (1)')).toBeInTheDocument();
    expect(screen.getByText('Thiếu.')).toBeInTheDocument();
  });

  it('không có cảnh báo dữ liệu thì không có khối cảnh báo', async () => {
    m11Api('student');

    renderApp('/m11/ket-qua');

    await screen.findByRole('table');
    expect(screen.queryByText(/Cảnh báo dữ liệu \(/)).not.toBeInTheDocument();
  });

  it('lỗi bảng điểm hiện cả nội dung lỗi của máy chủ', async () => {
    m11Api('student', {
      'GET /api/m11/grades': () => apiError(500, 'INTERNAL_ERROR', 'Hệ thống gặp lỗi.'),
    });

    renderApp('/m11/ket-qua');

    expect(await screen.findByRole('alert')).toHaveTextContent('Hệ thống gặp lỗi.');
  });

  it('dòng có cảnh báo dữ liệu hiện nhãn và tooltip gắn với nhãn', async () => {
    m11Api(
      'student',
      oneRow(gradeRow({ data_warnings: [{ code: 'MISSING_CODE', message: 'Môn chưa có mã.' }] })),
    );

    renderApp('/m11/ket-qua');

    const label = await screen.findByRole('button', { name: 'Cảnh báo dữ liệu' });
    expect(label).toHaveAccessibleDescription('Môn chưa có mã.');
  });

  it('môn tương đương ghi rõ nguồn; môn không tính GPA có ghi chú', async () => {
    m11Api(
      'student',
      oneRow(
        gradeRow({
          status: 'done_via_equivalency',
          counts_gpa: false,
          via_course: { course_id: 'B', code: null, name: 'B' },
        }),
      ),
    );

    renderApp('/m11/ket-qua');

    expect(await screen.findByText('Qua môn Chưa có mã')).toBeInTheDocument();
    expect(screen.getByText('Không tính GPA')).toBeInTheDocument();
  });
});

describe('Phân tích', () => {
  it('cả trang chỉ có 1 dòng kỳ tham chiếu chung, không nằm trong thẻ', async () => {
    m11Api('student');
    renderApp('/m11/phan-tich');

    await screen.findByText('Xu hướng GPA');
    const lines = await screen.findAllByText(/Kỳ tham chiếu/);
    await settled();
    expect(screen.getAllByText(/Kỳ tham chiếu/)).toHaveLength(1);
    expect(lines[0].closest('.ui-card, .card')).toBeNull();
  });

  it('mọi phần đều lỗi: không có dòng kỳ tham chiếu', async () => {
    const failed = () => apiError(500, 'INTERNAL_ERROR', 'Lỗi');
    m11Api('student', {
      'GET /api/m11/gpa-trend': failed,
      'GET /api/m11/credits': failed,
      'GET /api/m11/curriculum-check': failed,
      'GET /api/m11/strengths': failed,
    });
    renderApp('/m11/phan-tich');

    await screen.findAllByRole('alert');
    await settled();
    expect(screen.queryByText(/Kỳ tham chiếu/)).toBeNull();
  });

  it('biểu đồ có câu tóm tắt và bảng cho trình đọc màn hình, dùng chuỗi gốc', async () => {
    m11Api('student');

    renderApp('/m11/phan-tich');

    expect(await screen.findByText(TREND.summary)).toBeInTheDocument();
    const table = screen.getByRole('table', { name: 'GPA từng học kỳ' });
    expect(within(table).getByText('2,75')).toBeInTheDocument();
    expect(within(table).getByText('—')).toBeInTheDocument();
  });

  it('chỉ giá trị vẽ là số; kỳ không có GPA để trống, không thành 0', () => {
    const [first, second] = toChartData(TREND.points);

    expect(first).toMatchObject({ raw: '2.75', plotted: 2.75, label: 'HK2 25-26' });
    expect(second).toMatchObject({ raw: null, plotted: null });
    expect(shortSemesterName('Kỳ lạ')).toBe('Kỳ lạ');
  });

  it('tiến độ tín chỉ theo nhóm có số và thanh tiến độ', async () => {
    m11Api('student');

    renderApp('/m11/phan-tich');

    expect(await screen.findByText('15/60 tín chỉ')).toBeInTheDocument();
    expect(screen.getByRole('progressbar', { name: 'Bắt buộc' })).toHaveAttribute(
      'aria-valuenow',
      '25',
    );
    expect(screen.getByRole('progressbar', { name: 'Tự chọn A' })).toHaveAttribute(
      'aria-valuenow',
      '100',
    );
    expect(screen.getByText('vượt yêu cầu nhóm')).toBeInTheDocument();
  });

  it('khóa không có quy chế: tiến độ hiện gạch', async () => {
    m11Api('student', {
      'GET /api/m11/credits': () =>
        jsonResponse(200, {
          passed: null,
          debt: null,
          failed_courses: null,
          in_progress: 0,
          registered: 0,
          required: { total_credits: 60, passed_credits: null, missing_credits: null },
          elective_groups: [],
          meta: TREND.meta,
        }),
    });

    renderApp('/m11/phan-tich');

    expect(await screen.findByText('—/60 tín chỉ')).toBeInTheDocument();
    expect(screen.getByText(/Đạt — · Nợ —/)).toBeInTheDocument();
  });

  it('đối chiếu CTĐT: dùng mã môn, null hiện "Chưa có mã"', async () => {
    m11Api('student');

    renderApp('/m11/phan-tich');

    expect(await screen.findByText(/Chương trình: CTĐT mẫu/)).toBeInTheDocument();
    expect(screen.getByText(/Chưa có mã – Môn thiếu mã/)).toBeInTheDocument();
    expect(screen.getByText(/Tự chọn B: thiếu 6 tín chỉ/)).toBeInTheDocument();
    expect(screen.getByText(/Cần đạt trước: CNT301/)).toBeInTheDocument();
    expect(CURRICULUM.blocked_courses).toHaveLength(1);
  });

  it('điểm mạnh yếu: có nhãn chữ, "Chưa đủ dữ liệu", môn làm bằng chứng', async () => {
    m11Api('student');

    renderApp('/m11/phan-tich');

    expect(await screen.findByText('GPA nhóm 3,60')).toBeInTheDocument();
    expect(screen.getByText('Điểm mạnh')).toBeInTheDocument();
    expect(screen.getByText('Chưa đủ dữ liệu')).toBeInTheDocument();
    expect(screen.getByText('Môn làm bằng chứng: CNT101')).toBeInTheDocument();
    expect(screen.queryByText('GPA nhóm —')).not.toBeInTheDocument();
  });

  it('so sánh 2 kỳ: mặc định 2 kỳ có điểm, đổi kỳ thì gọi lại', async () => {
    const fetchMock = m11Api('student', TWO_GRADED);
    const user = userEvent.setup();

    renderApp('/m11/phan-tich');

    const region = await screen.findByRole('region', { name: 'So sánh hai kỳ' });
    expect(within(region).getByText('+0,25')).toBeInTheDocument();
    expect(within(region).getByText('+3')).toBeInTheDocument();
    expect(within(region).getByText('-1')).toBeInTheDocument();
    const first = callsTo(fetchMock, '/api/m11/compare')[0];
    expect([first.get('a'), first.get('b')]).toEqual(['S4', 'S5']);

    await user.selectOptions(screen.getByLabelText('Kỳ thứ hai'), 'S4');

    await waitFor(() => expect(callsTo(fetchMock, '/api/m11/compare').at(-1).get('b')).toBe('S4'));
  });

  it('so sánh mặc định lấy 2 kỳ gần nhất CÓ ĐIỂM, bỏ qua kỳ trống (SV04: S1 và S2)', async () => {
    const fetchMock = m11Api('student', {
      'GET /api/m11/semesters': () =>
        jsonResponse(200, {
          items: [
            { id: 'S0', name: 'Kỳ 0', order: 0, is_current: false },
            { id: 'S1', name: 'Kỳ 1', order: 1, is_current: false },
            { id: 'S2', name: 'Kỳ 2', order: 2, is_current: false },
            ...SEMESTERS.items,
          ],
          current_id: 'S5',
        }),
      'GET /api/m11/gpa-trend': () =>
        jsonResponse(200, {
          ...TREND,
          points: [
            { semester_id: 'S0', order: 0, name: 'Kỳ 0', value: '1.00' },
            { semester_id: 'S1', order: 1, name: 'Kỳ 1', value: '1.75' },
            { semester_id: 'S2', order: 2, name: 'Kỳ 2', value: '1.88' },
            { semester_id: 'S4', order: 4, name: 'Kỳ 4', value: null },
            { semester_id: 'S5', order: 5, name: 'Kỳ 5', value: null },
          ],
        }),
    });

    renderApp('/m11/phan-tich');

    await screen.findByRole('region', { name: 'So sánh hai kỳ' });
    const first = callsTo(fetchMock, '/api/m11/compare')[0];
    expect([first.get('a'), first.get('b')]).toEqual(['S1', 'S2']);
    expect(screen.getByLabelText('Kỳ thứ nhất')).toHaveValue('S1');
    expect(screen.getByLabelText('Kỳ thứ hai')).toHaveValue('S2');
  });

  it('so sánh: đổi kỳ thứ nhất thì gọi lại; đổi học kỳ của trang thì về mặc định', async () => {
    const fetchMock = m11Api('student', TWO_GRADED);
    const user = userEvent.setup();

    renderApp('/m11/phan-tich');
    await screen.findByRole('region', { name: 'So sánh hai kỳ' });

    await user.selectOptions(screen.getByLabelText('Kỳ thứ nhất'), 'S5');
    await waitFor(() => expect(callsTo(fetchMock, '/api/m11/compare').at(-1).get('a')).toBe('S5'));

    await user.selectOptions(screen.getByLabelText('Học kỳ'), 'S4');
    await waitFor(() => expect(screen.getByLabelText('Kỳ thứ nhất')).toHaveValue('S4'));
    expect(screen.getByLabelText('Kỳ thứ hai')).toHaveValue('S5');
  });

  it('so sánh: mỗi cột lấy đúng kỳ, chênh lệch có dấu', async () => {
    m11Api('student', {
      ...TWO_GRADED,
      'GET /api/m11/compare': () =>
        jsonResponse(200, {
          ...COMPARE,
          semester_a: { ...COMPARE.semester_a, credits: 11, passed_count: 21, failed_count: 31 },
          semester_b: { ...COMPARE.semester_b, credits: 12, passed_count: 22, failed_count: 32 },
          failed_delta: 1,
        }),
    });

    renderApp('/m11/phan-tich');

    const region = await screen.findByRole('region', { name: 'So sánh hai kỳ' });
    expect(cellsOf(region, 'Tín chỉ').slice(0, 2)).toEqual(['11', '12']);
    expect(cellsOf(region, 'Số môn đạt').slice(0, 2)).toEqual(['21', '22']);
    expect(cellsOf(region, 'Số môn chưa đạt')).toEqual(['31', '32', '+1']);
  });

  it('kỳ không có kết quả: ô hiện gạch, không hiện 0, chênh lệch cũng là gạch', async () => {
    const empty = { gpa: null, credits: 0, passed_count: 0, failed_count: 0 };
    m11Api('student', {
      ...TWO_GRADED,
      'GET /api/m11/compare': () =>
        jsonResponse(200, {
          ...COMPARE,
          semester_a: { ...COMPARE.semester_a, credits: 12, passed_count: 3, failed_count: 1 },
          semester_b: { ...COMPARE.semester_b, ...empty },
          gpa_delta: null,
          credit_delta: -12,
          passed_delta: -3,
          failed_delta: -1,
        }),
    });

    renderApp('/m11/phan-tich');

    const region = await screen.findByRole('region', { name: 'So sánh hai kỳ' });
    expect(cellsOf(region, 'GPA')).toEqual(['2,75', '—', '—']);
    expect(cellsOf(region, 'Tín chỉ')).toEqual(['12', '—', '—']);
    expect(cellsOf(region, 'Số môn đạt')).toEqual(['3', '—', '—']);
    expect(cellsOf(region, 'Số môn chưa đạt')).toEqual(['1', '—', '—']);
    expect(screen.queryByText('Cả hai kỳ này đều chưa có kết quả.')).toBeNull();
  });

  it('kỳ có tín chỉ nhưng không có GPA vẫn hiện số', async () => {
    m11Api('student', {
      ...TWO_GRADED,
      'GET /api/m11/compare': () =>
        jsonResponse(200, {
          ...COMPARE,
          semester_a: { ...COMPARE.semester_a, gpa: null, credits: 2 },
          gpa_delta: null,
        }),
    });

    renderApp('/m11/phan-tich');

    const region = await screen.findByRole('region', { name: 'So sánh hai kỳ' });
    expect(cellsOf(region, 'Tín chỉ')[0]).toBe('2');
  });

  it('người dùng chọn 2 kỳ đều chưa có kết quả thì nói rõ', async () => {
    const side = { gpa: null, credits: 0, passed_count: 0, failed_count: 0 };
    m11Api('student', {
      ...TWO_GRADED,
      'GET /api/m11/compare': () =>
        jsonResponse(200, {
          ...COMPARE,
          semester_a: { ...COMPARE.semester_a, ...side },
          semester_b: { ...COMPARE.semester_b, ...side },
          gpa_delta: null,
        }),
    });

    renderApp('/m11/phan-tich');

    expect(await screen.findByText('Cả hai kỳ này đều chưa có kết quả.')).toBeInTheDocument();
  });

  it.each([
    ['1 kỳ có điểm', [{ semester_id: 'S4', order: 4, name: 'Kỳ 4', value: '2.75' }]],
    ['0 kỳ có điểm', [{ semester_id: 'S4', order: 4, name: 'Kỳ 4', value: null }]],
  ])('%s: hiện EmptyState, không có bảng, không gọi API', async (_name, points) => {
    const fetchMock = m11Api('student', {
      'GET /api/m11/gpa-trend': () => jsonResponse(200, { ...TREND, points }),
    });

    renderApp('/m11/phan-tich');

    expect(await screen.findByText('Cần ít nhất 2 kỳ có kết quả để so sánh')).toBeInTheDocument();
    expect(screen.queryByRole('region', { name: 'So sánh hai kỳ' })).toBeNull();
    expect(screen.queryByLabelText('Kỳ thứ nhất')).toBeNull();
    expect(callsTo(fetchMock, '/api/m11/compare')).toEqual([]);
  });

  it('điểm mạnh yếu xếp: yếu, mạnh, bình thường; chưa đủ dữ liệu gộp cuối, thu gọn', async () => {
    const group = (id, level, value) => ({
      group_id: id,
      slug: id,
      name: `Nhóm ${id}`,
      level,
      value,
      numerator: '0',
      denominator: value ? 3 : 0,
      courses: [],
    });
    m11Api('student', {
      'GET /api/m11/strengths': () =>
        jsonResponse(200, {
          groups: [
            group('u1', 'insufficient_data', null),
            group('n', 'normal', '2.50'),
            group('s', 'strong', '3.60'),
            group('u2', 'insufficient_data', null),
            group('w1', 'weak', '1.00'),
            group('w2', 'weak', '1.20'),
          ],
          meta: TREND.meta,
        }),
    });

    renderApp('/m11/phan-tich');

    const summary = await screen.findByText('Chưa đủ dữ liệu (2)');
    const details = summary.closest('details');
    expect(details).not.toHaveAttribute('open');
    expect(within(details).getByText('Nhóm u1')).toBeInTheDocument();
    expect(within(details).getByText('Nhóm u2')).toBeInTheDocument();
    const list = document.querySelector('.strength-list');
    expect([...list.querySelectorAll('strong')].map((node) => node.textContent)).toEqual([
      'Nhóm w1',
      'Nhóm w2',
      'Nhóm s',
      'Nhóm n',
    ]);
  });

  it('điểm mạnh yếu: không có nhóm chưa đủ dữ liệu thì không có khối thu gọn', async () => {
    m11Api('student', {
      'GET /api/m11/strengths': () =>
        jsonResponse(200, { groups: [STRENGTHS.groups[0]], meta: TREND.meta }),
    });

    renderApp('/m11/phan-tich');

    await screen.findByText('GPA nhóm 3,60');
    expect(screen.queryByText(/Chưa đủ dữ liệu \(/)).toBeNull();
  });

  it('biểu đồ: ngưỡng lấy từ API cảnh báo, ghi rõ cho trình đọc màn hình', async () => {
    m11Api('student');

    renderApp('/m11/phan-tich');

    expect(await screen.findByText('Ngưỡng cảnh báo 2,00; ngưỡng chú ý 2,50.')).toBeInTheDocument();
  });

  it('không đọc được ngưỡng: biểu đồ vẫn hiện, không có câu ngưỡng', async () => {
    m11Api('student', { 'GET /api/m11/risks': () => apiError(500, 'INTERNAL_ERROR', 'Lỗi') });

    renderApp('/m11/phan-tich');

    expect(await screen.findByText(TREND.summary)).toBeInTheDocument();
    await settled();
    expect(screen.queryByText(/Ngưỡng cảnh báo/)).toBeNull();
  });

  it('gpaThresholds: khóa không có quy chế thì không có ngưỡng', () => {
    expect(gpaThresholds(RISKS.outcomes)).toEqual({ warning: '2.00', watch: '2.50' });
    expect(gpaThresholds([{ rule_code: 'gpa', evidence: {} }])).toBeNull();
    expect(gpaThresholds([{ rule_code: 'debt', evidence: { warning_below: '9' } }])).toBeNull();
  });

  it('một phần lỗi không làm hỏng phần còn lại', async () => {
    m11Api('student', { 'GET /api/m11/credits': () => apiError(500, 'INTERNAL_ERROR', 'Lỗi') });

    renderApp('/m11/phan-tich');

    expect(await screen.findByRole('alert')).toHaveTextContent('Không tải được tiến độ tín chỉ');
    expect(await screen.findByText(TREND.summary)).toBeInTheDocument();
  });

  it('đổi kỳ thì mọi phần gọi lại API', async () => {
    const fetchMock = m11Api('student');
    const user = userEvent.setup();

    renderApp('/m11/phan-tich');
    await screen.findByText(TREND.summary);
    await user.selectOptions(screen.getByLabelText('Học kỳ'), 'S4');

    await waitFor(() => {
      for (const name of ['gpa-trend', 'credits', 'curriculum-check', 'strengths']) {
        expect(callsTo(fetchMock, `/api/m11/${name}`).at(-1).get('semester_id')).toBe('S4');
      }
    });
  });
});

describe('Cảnh báo', () => {
  it('mỗi quy tắc có mức, lý do, bằng chứng, phiên bản; có câu tham khảo', async () => {
    m11Api('student');

    renderApp('/m11/canh-bao');

    expect(await screen.findByText(RISKS.outcomes[0].reason)).toBeInTheDocument();
    expect(
      screen.getByText('Cảnh báo tham khảo, không phải quyết định học vụ chính thức'),
    ).toBeInTheDocument();
    expect(screen.getByText('1,81 (43,50/24)')).toBeInTheDocument();
    expect(screen.getByText('dưới 2,50')).toBeInTheDocument();
    expect(screen.getByText('dưới 2,00')).toBeInTheDocument();
    expect(screen.getByText('3 tín chỉ nợ')).toBeInTheDocument();
    expect(screen.getByText('từ 6 tín chỉ')).toBeInTheDocument();
    expect(screen.getByText('0 tín chỉ đăng ký')).toBeInTheDocument();
    expect(screen.getByText('10–25 tín chỉ')).toBeInTheDocument();
    expect(screen.queryByText(/Phiên bản quy chế/)).toBeNull();
    expect(screen.getByText(/Quy chế K66-mau-v1/).closest('article')).toBeNull();
    expect(screen.getByText('Không áp dụng')).toBeInTheDocument();
    expect(screen.getByText('Chú ý')).toBeInTheDocument();
  });

  it('mức có chữ và biểu tượng, không chỉ dựa vào màu', async () => {
    m11Api('student');

    renderApp('/m11/canh-bao');

    await screen.findByText(RISKS.outcomes[0].reason);
    const chips = document.querySelectorAll('.status-text');
    expect(chips.length).toBeGreaterThan(0);
    for (const badge of chips) {
      expect(badge.textContent.trim().length).toBeGreaterThan(2);
      expect(badge.querySelector('svg[aria-hidden="true"]')).toBeInTheDocument();
    }
  });

  it('mức chung có nhãn; mỗi quy tắc có tên tiếng Việt', async () => {
    m11Api('student', {
      'GET /api/m11/risks': () =>
        jsonResponse(200, {
          ...RISKS,
          overall: 'insufficient_data',
          outcomes: [{ ...RISKS.outcomes[0], level: 'normal' }],
        }),
    });

    renderApp('/m11/canh-bao');

    expect(await screen.findByText('Chưa đủ dữ liệu')).toHaveClass('status-text');
    expect(screen.getByRole('heading', { name: 'GPA tích lũy' })).toBeInTheDocument();
  });

  const PLAN_API = 'GET /api/m12/improvement-plan';
  const plan = (extra) => () =>
    jsonResponse(200, {
      plan: null,
      active_rules: [{ rule_code: 'gpa', level: 'warning' }],
      new_rules: ['gpa'],
      disclaimer: 'x',
      ...extra,
    });

  it('nút Tạo kế hoạch hoạt động: gọi API rồi mở trang kế hoạch', async () => {
    const user = userEvent.setup();
    const fetchMock = m11Api('student', {
      [PLAN_API]: plan(),
      'POST /api/m12/improvement-plan': () => jsonResponse(201, {}),
    });
    renderApp('/m11/canh-bao');

    await user.click(await screen.findByRole('button', { name: 'Tạo kế hoạch cải thiện' }));

    expect(await screen.findByRole('heading', { name: 'Kế hoạch cải thiện' })).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([, options]) => options?.method === 'POST')).toBe(true);
  });

  it('tạo lỗi thì báo rõ, ở lại trang', async () => {
    const user = userEvent.setup();
    m11Api('student', {
      [PLAN_API]: plan(),
      'POST /api/m12/improvement-plan': () => apiError(422, 'NO_ACTIVE_RISK', 'Không có rủi ro'),
    });
    renderApp('/m11/canh-bao');

    await user.click(await screen.findByRole('button', { name: 'Tạo kế hoạch cải thiện' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Không có rủi ro');
  });

  it('đã có kế hoạch thì nút đổi thành Xem kế hoạch', async () => {
    m11Api('student', { [PLAN_API]: plan({ plan: { id: 'p', items: [] } }) });
    renderApp('/m11/canh-bao');

    expect(await screen.findByRole('link', { name: 'Xem kế hoạch' })).toHaveAttribute(
      'href',
      '/m11/canh-bao/ke-hoach',
    );
    expect(screen.queryByRole('button', { name: 'Tạo kế hoạch cải thiện' })).toBeNull();
  });

  it('không có rủi ro thì không có nút tạo', async () => {
    m11Api('student', { [PLAN_API]: plan({ active_rules: [] }) });
    renderApp('/m11/canh-bao');

    expect(
      await screen.findByText('Không có quy tắc nào cần lập kế hoạch cải thiện.'),
    ).toBeInTheDocument();
  });

  it('cố vấn không có nút tạo', async () => {
    m11Api('advisor', { [PLAN_API]: plan() });
    renderApp('/m11/canh-bao?student=SV04');

    expect(await screen.findByText('Sinh viên chưa tạo kế hoạch cải thiện.')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Tạo kế hoạch cải thiện' })).toBeNull();
  });

  it('khóa không có quy chế: quy tắc không có bằng chứng', async () => {
    m11Api('student', {
      'GET /api/m11/risks': () =>
        jsonResponse(200, {
          ...RISKS,
          overall: 'normal',
          outcomes: [
            {
              rule_code: 'gpa',
              level: 'insufficient_data',
              reason: 'Không tìm thấy quy chế của khóa.',
              evidence: {},
              rule_version: null,
            },
          ],
        }),
    });

    renderApp('/m11/canh-bao');

    expect(await screen.findByText('Không tìm thấy quy chế của khóa.')).toBeInTheDocument();
    expect(screen.queryByText('Giá trị thực tế')).not.toBeInTheDocument();
  });

  it('lỗi tải cảnh báo', async () => {
    m11Api('student', { 'GET /api/m11/risks': () => apiError(500, 'INTERNAL_ERROR', 'Lỗi') });

    renderApp('/m11/canh-bao');

    expect(await screen.findByRole('alert')).toHaveTextContent('Không tải được cảnh báo');
  });
});

describe('phạm vi xem trên điện thoại', () => {
  const STUDENTS = {
    items: [
      { id: 'SV04', student_code: 'SV04', full_name: 'Sinh viên 04', cohort: 'K66' },
      { id: 'SV07', student_code: 'SV07', full_name: 'Sinh viên 07', cohort: 'K66' },
    ],
    page: 1,
    page_size: 100,
    total: 2,
  };
  const chip = (name) => screen.findByRole('button', { name });

  it('quản trị: chip ghi sinh viên và kỳ; mở tấm chọn, đổi sinh viên và kỳ', async () => {
    m11Api('admin', { 'GET /api/admin/students': () => jsonResponse(200, STUDENTS) });
    const user = userEvent.setup();

    renderApp('/?student=SV04');
    const opener = await chip('Đang xem: SV04 · S5');
    expect(opener).toHaveAttribute('aria-haspopup', 'dialog');
    expect(opener).toHaveAttribute('title', 'Đang xem: SV04 · S5');
    await user.click(opener);

    const sheet = screen.getByRole('dialog', { name: 'Chọn phạm vi xem' });
    expect(within(sheet).getByRole('button', { name: 'Đóng' })).toHaveFocus();
    expect(within(sheet).getByRole('radio', { name: /SV04/ })).toBeChecked();

    await user.click(within(sheet).getByRole('radio', { name: /SV07/ }));
    expect(search()).toContain('student=SV07');
    await user.selectOptions(within(sheet).getByLabelText('Học kỳ'), 'S4');
    expect(search()).toContain('semester=S4');
    expect(await chip('Đang xem: SV07 · S4')).toBeInTheDocument();
  });

  it('Esc đóng tấm chọn và trả focus về chip; Tab không ra ngoài', async () => {
    m11Api('admin', { 'GET /api/admin/students': () => jsonResponse(200, STUDENTS) });
    const user = userEvent.setup();

    renderApp('/?student=SV04');
    const opener = await chip('Đang xem: SV04 · S5');
    opener.focus();
    await user.keyboard('{Enter}');
    const sheet = screen.getByRole('dialog');

    await user.keyboard('{Shift>}{Tab}{/Shift}');
    expect(within(sheet).getByRole('button', { name: 'Xong' })).toHaveFocus();
    await user.keyboard('{Tab}');
    expect(within(sheet).getByRole('button', { name: 'Đóng' })).toHaveFocus();

    await user.keyboard('{Escape}');
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(opener).toHaveFocus();
  });

  it('nút Xong và bấm nền đều đóng tấm chọn', async () => {
    m11Api('advisor');
    const user = userEvent.setup();

    renderApp('/m12/dinh-huong');
    await user.click(await chip('Đang xem: Chưa chọn'));
    await user.click(screen.getByRole('button', { name: 'Xong' }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

    await user.click(await chip('Đang xem: Chưa chọn'));
    await user.click(document.querySelector('.bottom-sheet__backdrop'));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('cố vấn tìm được trong tấm chọn, gửi q; không có kết quả thì nói rõ', async () => {
    const fetchMock = m11Api('advisor', {
      'GET /api/advisor/students': (url) =>
        jsonResponse(
          200,
          new URL(url, 'http://x').searchParams.get('q')
            ? { ...STUDENTS, items: [], total: 0 }
            : STUDENTS,
        ),
    });
    const user = userEvent.setup();

    renderApp('/m12/dinh-huong');
    await user.click(await chip('Đang xem: Chưa chọn'));
    await within(screen.getByRole('dialog')).findByRole('radio', { name: /SV04/ });
    await user.type(screen.getByLabelText('Tìm sinh viên'), 'zz');

    expect(await screen.findByText('Không có sinh viên phù hợp.')).toBeInTheDocument();
    expect(callsTo(fetchMock, '/api/advisor/students').at(-1).get('q')).toBe('zz');
  });

  it('sinh viên đang chọn không có trong kết quả tìm: vẫn thấy và giữ nguyên', async () => {
    m11Api('admin', {
      'GET /api/admin/students': () => jsonResponse(200, { ...STUDENTS, items: [], total: 0 }),
    });
    const user = userEvent.setup();

    renderApp('/?student=SV09');
    await user.click(await chip('Đang xem: SV09 · S5'));

    expect(screen.getByRole('radio', { name: 'SV09' })).toBeChecked();
  });

  it('trang Kết quả có "Tất cả các kỳ" trong tấm chọn, chip ghi rõ', async () => {
    m11Api('student');
    const user = userEvent.setup();

    renderApp('/m11/ket-qua');
    await user.click(await chip('Đang xem: S5'));
    const sheet = screen.getByRole('dialog');

    expect(within(sheet).queryByRole('radiogroup')).not.toBeInTheDocument();
    expect(within(sheet).queryByLabelText('Tìm sinh viên')).not.toBeInTheDocument();
    await user.selectOptions(within(sheet).getByLabelText('Học kỳ'), 'all');

    expect(search()).toBe('?semester=all');
    expect(await chip('Đang xem: Tất cả')).toBeInTheDocument();
  });

  it('trang ngoài M11: cố vấn có chip không có kỳ, sinh viên không có chip', async () => {
    m11Api('student');

    renderApp('/m12/dinh-huong?semester=all');

    await screen.findByRole('heading', { name: 'Định hướng nghề' });
    expect(screen.queryByRole('button', { name: /Đang xem/ })).not.toBeInTheDocument();
    expect(search()).toBe('?semester=all');
  });

  it('chỉ gọi danh sách học kỳ một lần cho cả thanh trên cùng và trang', async () => {
    const fetchMock = m11Api('student');

    renderApp('/m11/canh-bao');

    await screen.findByText(RISKS.outcomes[0].reason);
    expect(callsTo(fetchMock, '/api/m11/semesters')).toHaveLength(1);
  });

  it('đường dẫn có dấu / ở cuối vẫn là trang M11', async () => {
    m11Api('student');

    renderApp('/m11/canh-bao/');

    expect(await screen.findByText(RISKS.outcomes[0].reason)).toBeInTheDocument();
  });

  it('đổi sinh viên thì về trang 1 của bảng điểm', async () => {
    m11Api('admin', { 'GET /api/admin/students': () => jsonResponse(200, STUDENTS) });
    const user = userEvent.setup();

    renderApp('/m11/ket-qua?student=SV04&page=3');
    await user.click(await chip('Đang xem: SV04 · S5'));
    await user.click(screen.getByRole('radio', { name: /SV07/ }));

    expect(search()).toBe('?student=SV07');
  });

  it('nhân sự hỗ trợ ở trang chủ cũng không có chip', async () => {
    m11Api('support_staff');

    renderApp('/');

    await screen.findByText('Chào Người dùng support_staff');
    expect(screen.queryByRole('button', { name: /Đang xem/ })).not.toBeInTheDocument();
  });

  it('nhân sự hỗ trợ không có chip và không gọi học kỳ', async () => {
    const fetchMock = m11Api('support_staff');

    renderApp('/m12/hoc-lieu');

    await screen.findByRole('heading', { name: 'Học liệu' });
    expect(screen.queryByRole('button', { name: /Đang xem/ })).not.toBeInTheDocument();
    expect(callsTo(fetchMock, '/api/m11/semesters')).toEqual([]);
  });
});

describe('so sánh hai kỳ', () => {
  it('tên chỉ số là tiêu đề hàng', async () => {
    m11Api('student', TWO_GRADED);

    renderApp('/m11/phan-tich');

    const region = await screen.findByRole('region', { name: 'So sánh hai kỳ' });
    expect(within(region).getByRole('rowheader', { name: 'GPA' })).toBeInTheDocument();
    expect(within(region).getByRole('rowheader', { name: 'Số môn chưa đạt' })).toBeInTheDocument();
  });
});
