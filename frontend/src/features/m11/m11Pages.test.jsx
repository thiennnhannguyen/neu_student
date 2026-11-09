import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { apiError, jsonResponse, pendingResponse, renderApp } from '../../test/fakeApi';
import {
  ATTEMPTS,
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

/** Chờ các lời gọi đang chạy trả về, để kiểm "không xuất hiện" không qua sớm. */
const settled = () => new Promise((resolve) => window.setTimeout(resolve, 20));

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

    // D-306: bảng số của biểu đồ cột cũng có "2,75", nên tìm trong thẻ GPA học kỳ.
    expect(await within(card('GPA học kỳ')).findByText('2,75')).toBeInTheDocument();
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
        name: 'Phân tích & Cảnh báo',
      }),
    );

    // D-310: Cảnh báo gộp vào Phân tích & Cảnh báo.
    expect(path()).toBe('/m11/phan-tich');
    expect(search()).toBe('?student=SV04&semester=S4');
  });

  it('chuyển từ Kết quả sang trang khác, sidebar không mang all', async () => {
    m11Api('admin');
    const user = userEvent.setup();

    renderApp('/m11/ket-qua?student=SV07&semester=all&status=failed');
    await screen.findByRole('table');

    await user.click(
      within(screen.getByRole('navigation', { name: 'Menu chính' })).getByRole('link', {
        name: 'Phân tích & Cảnh báo',
      }),
    );

    expect(path()).toBe('/m11/phan-tich');
    expect(search()).toBe('?student=SV07');
  });
});

describe('Tổng quan', () => {
  it('đang tải rồi 4 thẻ số liệu (D-306 bỏ dải cảnh báo và dòng phụ)', async () => {
    const overview = pendingResponse();
    m11Api('student', { 'GET /api/m11/overview': overview.handler });

    renderApp('/');

    expect(await screen.findByText('Đang tải tổng quan...')).toBeInTheDocument();
    overview.resolve(jsonResponse(200, overviewBody()));
    expect(await screen.findByText('3,11')).toBeInTheDocument();
    expect(screen.getAllByRole('article')).toHaveLength(4);
    expect(within(card('GPA tích lũy')).getByText('2,88')).toBeInTheDocument();
    expect(within(card('Tín chỉ đạt')).getByText('19')).toBeInTheDocument();
    expect(within(card('Số môn chưa đạt')).getByText('2')).toBeInTheDocument();
  });

  // D-306 bỏ khỏi Tổng quan: dòng "Tính lúc … · Điểm cập nhật lần cuối …" (D-293), viền và nhãn mức
  // trên thẻ GPA tích lũy, dòng lý do của khối "Mức cảnh báo chung" (D-187, D-294). Tổng quan không
  // gọi /api/m11/risks nữa. Test thay thế: overviewCr08.test.jsx "4 thẻ chỉ có nhãn…".

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

  it('bộ lọc kỳ nằm trong thẻ chào mừng', async () => {
    m11Api('student');

    renderApp('/');

    const welcome = await screen.findByRole('region', { name: 'Lời chào' });
    expect(await within(welcome).findByLabelText('Học kỳ')).toHaveValue('S5');
  });

  it.each([
    ['GPA học kỳ', '/m11/phan-tich', '?semester=S4'],
    ['Tín chỉ đạt', '/m11/phan-tich', '?semester=S4'],
    ['Số môn chưa đạt', '/m11/ket-qua', '?semester=S4&view=failed'],
  ])('bấm thẻ %s sang trang chi tiết, giữ tham số', async (title, target, query) => {
    m11Api('student');
    const user = userEvent.setup();

    renderApp('/?semester=S4');
    await screen.findByText('3,11');
    await user.click(screen.getByRole('link', { name: title }));

    expect(path()).toBe(target);
    expect(search()).toBe(query);
  });

  it('không lặp các khối của trang Phân tích (D-306: biểu đồ cột dùng /gpa-trend theo ảnh mẫu)', async () => {
    const fetchMock = m11Api('student');

    renderApp('/');

    await screen.findByText('3,11');
    await screen.findByRole('table', { name: 'Điểm trung bình theo kỳ' });
    for (const path of ['/api/m11/curriculum-check', '/api/m11/strengths', '/api/m11/compare']) {
      expect(callsTo(fetchMock, path)).toEqual([]);
    }
    expect(document.querySelector('.trend-chart')).toBeNull();
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
    expect(within(dialog).getByText('Kết quả các lần học')).toBeInTheDocument();
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

// D-306 thay D-292 ở Tổng quan: GPA học kỳ trống chỉ còn gạch, không có dòng "Kỳ này chưa có kết quả ·
// Kỳ gần nhất có điểm …". Test thay thế: overviewCr08.test.jsx "GPA học kỳ trống: chỉ có gạch…".

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

  it('chỉ có 1 trang: ẩn phân trang, số dòng bằng số môn API trả', async () => {
    const items = ['A', 'B', 'C'].map((id) =>
      gradeRow({ course_id: id, code: id, name: `Môn ${id}` }),
    );
    const body = gradesBody(items, { total: items.length });
    m11Api('student', { 'GET /api/m11/grades': () => jsonResponse(200, body) });

    renderApp('/m11/ket-qua');

    const table = await screen.findByRole('table');
    expect(table.querySelectorAll('tbody > tr')).toHaveLength(body.items.length);
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

  it('Chi tiết của môn học lại: các lần học theo thứ tự kỳ, chỉ lần 1 Chưa đạt, chỉ lần 2 được tính', async () => {
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
    await user.click(await screen.findByRole('button', { name: 'Chi tiết Giải tích (MAU101)' }));

    const region = await screen.findByRole('region', {
      name: 'Chi tiết học phần: MAU101 - Giải tích',
    });
    const headers = within(await within(region).findByRole('table'))
      .getAllByRole('columnheader')
      .slice(3);
    expect(headers.map((header) => header.textContent)).toEqual([
      'Điểm lần 1HK1 2024-2025 · Chưa đạt',
      'Điểm lần 2HK1 2025-2026 · Lần được tính',
      'Điểm lần 3HK1 2026-2027 · đang học',
    ]);
    expect(
      headers.map((header) => header.querySelector('.component-table__failed svg') !== null),
    ).toEqual([true, false, false]);
    expect(callsTo(fetchMock, '/api/m11/grades/MAU101/attempts')[0].get('student_id')).toBe('SV02');
  });

  it('nút Chi tiết dùng được bằng bàn phím: Enter và Space mở/đóng, focus ở lại nút', async () => {
    m11Api('student', {
      ...oneRow(gradeRow({ course_id: 'MAU101', code: 'MAU101', name: 'Giải tích' })),
      'GET /api/m11/grades/MAU101/attempts': () => jsonResponse(200, ATTEMPTS),
    });
    const user = userEvent.setup();
    const regionName = 'Chi tiết học phần: MAU101 - Giải tích';

    renderApp('/m11/ket-qua');
    const toggle = await screen.findByRole('button', { name: 'Chi tiết Giải tích (MAU101)' });
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    toggle.focus();

    await user.keyboard('{Enter}');
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    const region = await screen.findByRole('region', { name: regionName });
    expect(document.getElementById(toggle.getAttribute('aria-controls'))).toContainElement(region);
    expect(toggle).toHaveFocus();

    await user.keyboard(' ');
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByRole('region', { name: regionName })).toBeNull();
    expect(toggle).toHaveFocus();

    await user.keyboard(' ');
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(await screen.findByRole('region', { name: regionName })).toBeInTheDocument();

    await user.keyboard('{Enter}');
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    expect(toggle).toHaveFocus();
  });

  it('môn có 4 lần học: bảng Chi tiết thêm cột Điểm lần 4, cuộn ngang được', async () => {
    const [first, effective, inProgress] = ATTEMPTS.items;
    const items = [
      first,
      { ...first, ordinal: 2, semester: { id: 'S2', name: 'HK2 2024-2025', order: 2 } },
      { ...effective, ordinal: 3 },
      { ...inProgress, ordinal: 4 },
    ];
    m11Api('student', {
      ...oneRow(gradeRow({ course_id: 'MAU101', code: 'MAU101', name: 'Giải tích' })),
      'GET /api/m11/grades/MAU101/attempts': () => jsonResponse(200, { ...ATTEMPTS, items }),
    });
    const user = userEvent.setup();

    renderApp('/m11/ket-qua');
    await user.click(await screen.findByRole('button', { name: 'Chi tiết Giải tích (MAU101)' }));

    const scroller = await screen.findByRole('region', { name: 'Bảng điểm thành phần' });
    expect(scroller).toHaveAttribute('tabindex', '0');
    const headers = within(within(scroller).getByRole('table'))
      .getAllByRole('columnheader')
      .slice(3)
      .map((header) => header.textContent);
    expect(headers).toEqual([
      'Điểm lần 1HK1 2024-2025 · Chưa đạt',
      'Điểm lần 2HK2 2024-2025 · Chưa đạt',
      'Điểm lần 3HK1 2025-2026 · Lần được tính',
      'Điểm lần 4HK1 2026-2027 · đang học',
    ]);
  });

  it('Chi tiết của môn chưa có lần học nào', async () => {
    m11Api('student', {
      ...oneRow(gradeRow()),
      'GET /api/m11/grades/CNT101/attempts': () => jsonResponse(200, { ...ATTEMPTS, items: [] }),
    });
    const user = userEvent.setup();

    renderApp('/m11/ket-qua');
    await user.click(await screen.findByRole('button', { name: /^Chi tiết / }));

    const region = await screen.findByRole('region', { name: /^Chi tiết học phần: / });
    expect(await within(region).findByText('Chưa có lần học nào.')).toBeInTheDocument();
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
    await user.click(within(table).getByRole('button', { name: 'Điểm hệ 10' }));

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

  it('cảnh báo dữ liệu chung hiện ở trang Cảnh báo (D-300 bỏ khỏi trang Kết quả)', async () => {
    m11Api('student', {
      'GET /api/m11/risks': () =>
        jsonResponse(200, {
          ...RISKS,
          meta: {
            ...RISKS.meta,
            data_warnings: [{ code: 'X', course_id: null, semester_id: null, message: 'Thiếu.' }],
          },
        }),
    });

    renderApp('/m11/canh-bao');

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

  it('cảnh báo dữ liệu của từng môn hiện ở trang Cảnh báo (D-300 bỏ khỏi ô tên môn)', async () => {
    m11Api('student', {
      'GET /api/m11/risks': () =>
        jsonResponse(200, {
          ...RISKS,
          meta: {
            ...RISKS.meta,
            data_warnings: [
              {
                code: 'MISSING_CODE',
                course_id: 'NN3',
                semester_id: null,
                message: 'Môn chưa có mã.',
              },
            ],
          },
        }),
    });

    renderApp('/m11/canh-bao');

    expect(await screen.findByText('Cảnh báo dữ liệu (1)')).toBeInTheDocument();
    expect(screen.getByText('Môn chưa có mã.')).toBeInTheDocument();
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

// D-310: bỏ khỏi giao diện Xu hướng GPA, Tiến độ tín chỉ, Đối chiếu CTĐT, Điểm mạnh/yếu, So sánh
// hai kỳ (M11-04 đến M11-08); test API của các khối này vẫn giữ ở backend/tests/api/m11.
// Trang gộp Phân tích & Cảnh báo có test ở features/m11/analysisCr11.test.jsx.

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

    // D-314: bảng môn đang học cũng có "Chưa đủ dữ liệu" (điểm dự kiến), nên tìm trong khối cảnh báo.
    const risks = (await screen.findByRole('heading', { name: 'Cảnh báo học vụ' })).parentElement;
    expect(await within(risks).findByText('Chưa đủ dữ liệu')).toHaveClass('status-text');
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
    const opener = await chip('Đang xem: SV04 · HK1 2026-2027');
    expect(opener).toHaveAttribute('aria-haspopup', 'dialog');
    expect(opener).toHaveAttribute('title', 'Đang xem: SV04 · HK1 2026-2027');
    await user.click(opener);

    const sheet = screen.getByRole('dialog', { name: 'Chọn phạm vi xem' });
    expect(within(sheet).getByRole('button', { name: 'Đóng' })).toHaveFocus();
    expect(within(sheet).getByRole('radio', { name: /SV04/ })).toBeChecked();

    await user.click(within(sheet).getByRole('radio', { name: /SV07/ }));
    expect(search()).toContain('student=SV07');
    await user.selectOptions(within(sheet).getByLabelText('Học kỳ'), 'S4');
    expect(search()).toContain('semester=S4');
    expect(await chip('Đang xem: SV07 · HK2 2025-2026')).toBeInTheDocument();
  });

  it('Esc đóng tấm chọn và trả focus về chip; Tab không ra ngoài', async () => {
    m11Api('admin', { 'GET /api/admin/students': () => jsonResponse(200, STUDENTS) });
    const user = userEvent.setup();

    renderApp('/?student=SV04');
    const opener = await chip('Đang xem: SV04 · HK1 2026-2027');
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
    await user.click(await chip('Đang xem: SV09 · HK1 2026-2027'));

    expect(screen.getByRole('radio', { name: 'SV09' })).toBeChecked();
  });

  it('trang Kết quả có "Tất cả các kỳ" trong tấm chọn, chip ghi rõ', async () => {
    m11Api('student');
    const user = userEvent.setup();

    renderApp('/m11/ket-qua');
    await user.click(await chip('Đang xem: HK1 2026-2027'));
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
    await user.click(await chip('Đang xem: SV04 · HK1 2026-2027'));
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
