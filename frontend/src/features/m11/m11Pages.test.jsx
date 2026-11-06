import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { apiError, jsonResponse, pendingResponse, renderApp } from '../../test/fakeApi';
import { shortSemesterName, toChartData } from './GpaTrendChart';
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
  TREND,
} from './testData';

const search = () => screen.getByTestId('search').textContent;
const path = () => screen.getByTestId('path').textContent;

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
          items: [
            { id: 'SV04', student_code: 'SV04', full_name: 'Sinh viên 04 (mẫu)', cohort: 'K66' },
          ],
          page: 1,
          page_size: 100,
          total: 1,
        }),
    });
    const user = userEvent.setup();

    renderApp('/');
    await screen.findByRole('option', { name: 'SV04 – Sinh viên 04 (mẫu)' });
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

    expect(await screen.findByText('Backend đang hoạt động.')).toBeInTheDocument();
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
      within(screen.getByRole('navigation')).getByRole('link', { name: 'Cảnh báo' }),
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
      within(screen.getByRole('navigation')).getByRole('link', { name: 'Phân tích' }),
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
    expect(screen.getByRole('link', { name: /Mức cảnh báo chung/ })).toHaveTextContent('Cảnh báo');
    expect(screen.getByRole('link', { name: /Mức cảnh báo chung/ })).toHaveTextContent('tham khảo');
  });

  it('dưới thẻ ghi kỳ tham chiếu và thời điểm cập nhật', async () => {
    m11Api('student');

    renderApp('/');

    await screen.findByText('3,11');
    expect(
      within(card('GPA học kỳ')).getByText(/Kỳ tham chiếu Kỳ S5 · Cập nhật \d\d\/11\/2026/),
    ).toBeInTheDocument();
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
    'trạng thái %s có chữ "%s" và biểu tượng, không chỉ màu',
    async (status, label) => {
      m11Api('student', oneRow(gradeRow({ status })));

      renderApp('/m11/ket-qua');

      const table = await screen.findByRole('table');
      const badge = within(table).getByText(label);
      expect(badge).toHaveClass('level-badge');
      expect(badge.querySelector('[aria-hidden="true"]').textContent.trim()).not.toBe('');
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
    expect(table.querySelectorAll('td.grades-table__blank')).toHaveLength(4);
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
    expect(within(table).getByText('Chưa học')).toBeInTheDocument();
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
          name: 'Giải tích (mẫu)',
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
      'Lần thứ 1 · HK1 2024-2025 (mẫu)',
      'Lần thứ 2 · HK1 2025-2026 (mẫu)',
      'Lần thứ 3 · HK1 2026-2027 (mẫu)',
    ]);
    expect(within(items[0]).getByText('Chưa đạt')).toBeInTheDocument();
    expect(within(items[1]).getByText('Lần được tính')).toBeInTheDocument();
    expect(within(items[2]).getByText('Đang học')).toBeInTheDocument();
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
  });

  it('so sánh 2 kỳ: mặc định kỳ trước và kỳ đang chọn, đổi kỳ thì gọi lại', async () => {
    const fetchMock = m11Api('student');
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

  it('so sánh mặc định lấy đúng kỳ liền trước kỳ đang chọn', async () => {
    const fetchMock = m11Api('student', {
      'GET /api/m11/semesters': () =>
        jsonResponse(200, {
          items: [{ id: 'S1', name: 'Kỳ 1', order: 1, is_current: false }, ...SEMESTERS.items],
          current_id: 'S5',
        }),
    });

    renderApp('/m11/phan-tich');

    await screen.findByRole('region', { name: 'So sánh hai kỳ' });
    const first = callsTo(fetchMock, '/api/m11/compare')[0];
    expect([first.get('a'), first.get('b')]).toEqual(['S4', 'S5']);
  });

  it('cả hai kỳ chưa có kết quả thì nói rõ', async () => {
    const side = { gpa: null, credits: 0, passed_count: 0, failed_count: 0 };
    m11Api('student', {
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

  it('chỉ có 1 kỳ thì không so sánh, không gọi API', async () => {
    const fetchMock = m11Api('student', {
      'GET /api/m11/semesters': () =>
        jsonResponse(200, { items: [SEMESTERS.items[1]], current_id: 'S5' }),
    });

    renderApp('/m11/phan-tich');

    expect(await screen.findByText('Chưa đủ 2 học kỳ để so sánh.')).toBeInTheDocument();
    expect(callsTo(fetchMock, '/api/m11/compare')).toEqual([]);
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
    expect(screen.getAllByText('Phiên bản quy chế: K66-mau-v1')).toHaveLength(3);
    expect(screen.getByText('Không áp dụng')).toBeInTheDocument();
    expect(screen.getByText('Chú ý')).toBeInTheDocument();
  });

  it('mức có chữ và biểu tượng, không chỉ dựa vào màu', async () => {
    m11Api('student');

    renderApp('/m11/canh-bao');

    await screen.findByText(RISKS.outcomes[0].reason);
    for (const badge of document.querySelectorAll('.level-badge')) {
      expect(badge.textContent.trim().length).toBeGreaterThan(2);
      expect(badge.querySelector('[aria-hidden="true"]').textContent.trim()).not.toBe('');
    }
  });

  it('nút tạo kế hoạch bị khóa, có ghi chú', async () => {
    m11Api('student');

    renderApp('/m11/canh-bao');

    expect(await screen.findByRole('button', { name: 'Tạo kế hoạch cải thiện' })).toBeDisabled();
    expect(screen.getByText('Có ở giai đoạn sau')).toBeInTheDocument();
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
    expect(screen.getByText('Phiên bản quy chế: Không xác định')).toBeInTheDocument();
    expect(screen.queryByText('Giá trị thực tế')).not.toBeInTheDocument();
  });

  it('lỗi tải cảnh báo', async () => {
    m11Api('student', { 'GET /api/m11/risks': () => apiError(500, 'INTERNAL_ERROR', 'Lỗi') });

    renderApp('/m11/canh-bao');

    expect(await screen.findByRole('alert')).toHaveTextContent('Không tải được cảnh báo');
  });
});
