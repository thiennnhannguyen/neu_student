/** CR-12 (D-312): màn hình báo cáo tuần toàn trang và cột "Báo cáo tuần". */
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { apiError, jsonResponse, renderApp } from '../../test/fakeApi';
import { COURSE_DETAIL, callsTo, m11Api } from '../m11/testData';
import { PRIVACY_NOTE } from './questions';

function report(code, weekNo, due, extra = {}) {
  return {
    course: { id: code, code, name: `Môn ${code}` },
    week: { week_no: weekNo, start: '2026-10-19', end: '2026-10-25' },
    opens_on: '2026-10-25',
    due_on: due,
    status: 'open',
    postponed: false,
    can_postpone: true,
    submitted_on: null,
    answers: null,
    ...extra,
  };
}

const TWO_OPEN = [report('CNTT1180', 7, '2026-10-26'), report('CNTT1117', 8, '2026-10-27')];

const NOTIFICATIONS = { items: [], unread_count: 0, page: 1, page_size: 20, total: 0, note: '' };

function api({ items = TWO_OPEN, role = 'student', extra = {} } = {}) {
  return m11Api(role, {
    'GET /api/weekly-reports/open': () => jsonResponse(200, { today: '2026-10-26', items }),
    'POST /api/weekly-reports/CNTT1180/7/submit': () => jsonResponse(200, {}),
    'POST /api/weekly-reports/CNTT1180/7/postpone': () => jsonResponse(200, {}),
    'POST /api/weekly-reports/CNTT1117/8/submit': () => jsonResponse(200, {}),
    'POST /api/weekly-reports/CNTT1117/8/postpone': () => jsonResponse(200, {}),
    'POST /api/auth/logout': () => new Response(null, { status: 204 }),
    'GET /api/notifications': () => jsonResponse(200, NOTIFICATIONS),
    'GET /api/m12/support-requests': () =>
      jsonResponse(200, { items: [], page: 1, page_size: 20, total: 0 }),
    ...extra,
  });
}

const posts = (fetchMock, path) =>
  fetchMock.mock.calls
    .filter(([url, options]) => String(url) === path && options?.method === 'POST')
    .map(([, options]) => (options.body ? JSON.parse(options.body) : null));

async function answerAll(user, dialog) {
  for (const [group, option] of [
    ['1. Đi học tuần này', 'Có mặt'],
    ['2. Thời gian tự học', '1–2 giờ'],
    ['3. Mức hiểu bài tuần này', '4'],
    ['5. Bài tập tuần này', 'Xong'],
    ['6. Mức tự tin nếu thi ngay bây giờ', '3'],
    ['7. Cản trở nhiều nhất', 'Bài khó'],
    ['8. Tuần tới định làm gì', 'Ôn lại bài'],
  ]) {
    const fieldset = within(dialog).getByRole('group', { name: new RegExp(group) });
    await user.click(within(fieldset).getByRole('radio', { name: option }));
  }
}

describe('Màn hình báo cáo tuần', () => {
  it('hiện toàn trang khi đăng nhập, theo thứ tự API (hạn gần nhất trước), có "Môn 1/2"', async () => {
    api();
    renderApp('/');
    const dialog = await screen.findByRole('dialog', { name: 'CNTT1180 – Môn CNTT1180' });
    expect(dialog).toHaveTextContent('Báo cáo tuần · Môn 1/2');
    expect(dialog).toHaveTextContent('Hạn nộp hết ngày 26/10/2026');
    expect(within(dialog).getByText(PRIVACY_NOTE)).toBeInTheDocument();
    expect(within(dialog).getAllByRole('group')).toHaveLength(7);
    expect(within(dialog).getByLabelText(/4\. Nội dung chưa hiểu/)).toBeInTheDocument();
    // Phần còn lại của trang bị khóa; focus ở tiêu đề môn.
    expect(document.querySelector('.app-frame')).toHaveAttribute('inert');
    expect(screen.getByRole('heading', { name: 'CNTT1180 – Môn CNTT1180' })).toHaveFocus();
  });

  it('thiếu câu thì báo, đủ thì nộp đúng dữ liệu rồi sang môn 2/2, nộp xong thì đóng', async () => {
    const user = userEvent.setup();
    const fetchMock = api();
    renderApp('/');
    let dialog = await screen.findByRole('dialog');
    await user.click(within(dialog).getByRole('button', { name: 'Nộp báo cáo' }));
    expect(within(dialog).getByRole('alert')).toHaveTextContent('Còn 7 câu chưa trả lời.');
    expect(within(dialog).getByRole('radio', { name: 'Có mặt' })).toHaveFocus();
    expect(posts(fetchMock, '/api/weekly-reports/CNTT1180/7/submit')).toEqual([]);

    await answerAll(user, dialog);
    await user.type(within(dialog).getByLabelText(/Nội dung chưa hiểu/), '  Chưa hiểu vòng lặp  ');
    await user.click(within(dialog).getByRole('button', { name: 'Nộp báo cáo' }));
    await waitFor(() =>
      expect(posts(fetchMock, '/api/weekly-reports/CNTT1180/7/submit')).toEqual([
        {
          attendance: 'present',
          self_study: '1_2h',
          understanding: 4,
          unclear_note: 'Chưa hiểu vòng lặp',
          assignment: 'done',
          confidence: 3,
          obstacle: 'hard_content',
          next_plan: 'review',
        },
      ]),
    );
    dialog = await screen.findByRole('dialog', { name: 'CNTT1117 – Môn CNTT1117' });
    expect(dialog).toHaveTextContent('Môn 2/2');
    // Môn mới bắt đầu với form trống.
    expect(within(dialog).getByRole('radio', { name: 'Có mặt' })).not.toBeChecked();
    await answerAll(user, dialog);
    await user.click(within(dialog).getByRole('button', { name: 'Nộp báo cáo' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(posts(fetchMock, '/api/weekly-reports/CNTT1117/8/submit')[0].unclear_note).toBeNull();
    expect(document.querySelector('.app-frame')).not.toHaveAttribute('inert');
  });

  it('"Làm sau": gọi API, sang môn sau; chuyển trang trong lần dùng này không hiện lại', async () => {
    const user = userEvent.setup();
    const fetchMock = api();
    renderApp('/');
    await screen.findByRole('dialog', { name: /CNTT1180/ });
    await user.click(screen.getByRole('button', { name: 'Làm sau' }));
    await screen.findByRole('dialog', { name: /CNTT1117/ });
    await user.click(screen.getByRole('button', { name: 'Làm sau' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(posts(fetchMock, '/api/weekly-reports/CNTT1180/7/postpone')).toHaveLength(1);
    expect(posts(fetchMock, '/api/weekly-reports/CNTT1117/8/postpone')).toHaveLength(1);

    // API vẫn trả 2 báo cáo đang mở (đã làm sau); chuyển trang không hiện lại trong lần dùng này.
    const before = callsTo(fetchMock, '/api/weekly-reports/open').length;
    await user.click(
      within(screen.getByRole('navigation', { name: 'Menu chính' })).getByRole('link', {
        name: 'Phân tích & Cảnh báo',
      }),
    );
    await waitFor(() =>
      expect(callsTo(fetchMock, '/api/weekly-reports/open').length).toBeGreaterThan(before),
    );
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('tải lại trang sau khi "Làm sau": hiện lại, không còn nút "Làm sau", Esc không đóng', async () => {
    const user = userEvent.setup();
    const fetchMock = api({
      items: [report('CNTT1117', 8, '2026-10-27', { postponed: true, can_postpone: false })],
    });
    renderApp('/');
    const dialog = await screen.findByRole('dialog', { name: /CNTT1117/ });
    expect(within(dialog).queryByRole('button', { name: 'Làm sau' })).toBeNull();
    expect(dialog).toHaveTextContent('Bạn đã chọn “Làm sau” một lần cho báo cáo này.');
    await user.keyboard('{Escape}');
    expect(screen.getByRole('dialog', { name: /CNTT1117/ })).toBeInTheDocument();
    expect(posts(fetchMock, '/api/weekly-reports/CNTT1117/8/postpone')).toEqual([]);
  });

  it('Esc khi còn được "Làm sau" thì giống bấm "Làm sau"', async () => {
    const user = userEvent.setup();
    const fetchMock = api({ items: [report('CNTT1117', 8, '2026-10-27')] });
    renderApp('/');
    await screen.findByRole('dialog', { name: /CNTT1117/ });
    await user.keyboard('{Escape}');
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(posts(fetchMock, '/api/weekly-reports/CNTT1117/8/postpone')).toHaveLength(1);
  });

  it('Tab không ra khỏi màn hình báo cáo', async () => {
    const user = userEvent.setup();
    api({ items: [report('CNTT1117', 8, '2026-10-27')] });
    renderApp('/');
    const dialog = await screen.findByRole('dialog');
    const submit = within(dialog).getByRole('button', { name: 'Nộp báo cáo' });
    submit.focus();
    await user.tab();
    expect(dialog).toContainElement(document.activeElement);
    expect(within(dialog).getByRole('button', { name: 'Yêu cầu hỗ trợ' })).toHaveFocus();
    await user.tab({ shift: true });
    expect(submit).toHaveFocus();
  });

  it('không chặn Yêu cầu hỗ trợ: sang trang hỗ trợ thì màn hình đóng', async () => {
    const user = userEvent.setup();
    api();
    renderApp('/');
    const dialog = await screen.findByRole('dialog');
    await user.click(within(dialog).getByRole('button', { name: 'Yêu cầu hỗ trợ' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(screen.getByTestId('path')).toHaveTextContent('/m12/yeu-cau-ho-tro');
  });

  it('không chặn Đăng xuất', async () => {
    const user = userEvent.setup();
    const fetchMock = api();
    renderApp('/');
    const dialog = await screen.findByRole('dialog');
    await user.click(within(dialog).getByRole('button', { name: 'Đăng xuất' }));
    await waitFor(() => expect(posts(fetchMock, '/api/auth/logout')).toHaveLength(1));
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
  });

  it('lỗi khi nộp: báo lỗi, giữ câu trả lời; 409 thì báo và sang môn tiếp theo', async () => {
    const user = userEvent.setup();
    api({
      extra: {
        'POST /api/weekly-reports/CNTT1180/7/submit': () =>
          apiError(500, 'INTERNAL_ERROR', 'Hệ thống gặp lỗi.'),
        'POST /api/weekly-reports/CNTT1117/8/submit': () =>
          apiError(409, 'REPORT_CLOSED', 'Báo cáo tuần này đã quá hạn.'),
      },
    });
    renderApp('/');
    let dialog = await screen.findByRole('dialog', { name: /CNTT1180/ });
    await answerAll(user, dialog);
    await user.click(within(dialog).getByRole('button', { name: 'Nộp báo cáo' }));
    expect(await within(dialog).findByText('Hệ thống gặp lỗi.')).toBeInTheDocument();
    expect(within(dialog).getByRole('radio', { name: 'Có mặt' })).toBeChecked();
    await user.click(within(dialog).getByRole('button', { name: 'Làm sau' }));
    dialog = await screen.findByRole('dialog', { name: /CNTT1117/ });
    await answerAll(user, dialog);
    await user.click(within(dialog).getByRole('button', { name: 'Nộp báo cáo' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(await screen.findByText('Báo cáo tuần này đã quá hạn.')).toBeInTheDocument();
  });

  it('không có báo cáo đang mở, hoặc không tải được: không chặn', async () => {
    api({
      extra: { 'GET /api/weekly-reports/open': () => apiError(500, 'INTERNAL_ERROR', 'Lỗi') },
    });
    renderApp('/m11/phan-tich');
    expect(await screen.findByRole('heading', { level: 1 })).toBeInTheDocument();
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it.each(['advisor', 'admin', 'support_staff'])(
    'vai trò %s không có màn hình báo cáo',
    async (role) => {
      const fetchMock = api({ role });
      renderApp('/');
      await screen.findByRole('navigation', { name: 'Menu chính' });
      expect(callsTo(fetchMock, '/api/weekly-reports/open')).toEqual([]);
      expect(screen.queryByRole('dialog')).toBeNull();
    },
  );
});

const HISTORY = {
  today: '2026-10-26',
  course: { id: 'CNTT1188', code: 'CNTT1188', name: 'Lập trình Web' },
  items: [
    {
      ...report('CNTT1188', 1, '2026-09-09'),
      week: { week_no: 1, start: '2026-09-02', end: '2026-09-08' },
      status: 'submitted',
      can_postpone: false,
      submitted_on: '2026-09-08',
      answers: {
        attendance: 'present',
        self_study: 'under_1h',
        understanding: 4,
        unclear_note: null,
        assignment: 'not_started',
        confidence: 3,
        obstacle: 'outside_work',
        next_plan: 'finish_assignments',
      },
      mismatch: { attendance: false, assignment: true },
    },
    {
      ...report('CNTT1188', 2, '2026-09-16'),
      week: { week_no: 2, start: '2026-09-09', end: '2026-09-15' },
      status: 'missed',
      can_postpone: false,
    },
  ],
};

// D-314: cột "Báo cáo tuần" của bảng chuyển vào mục "Báo cáo tuần" của trang chi tiết môn.
function withWeekly(summary) {
  return { ...COURSE_DETAIL, weekly_reports: summary };
}

const DETAIL = 'GET /api/m11/courses/CNTT1188/prediction';

function weeklySection() {
  return screen.getByRole('heading', { name: 'Báo cáo tuần' }).parentElement;
}

describe('Báo cáo tuần ở trang chi tiết môn (D-312, chuyển chỗ theo D-314)', () => {
  it('đã nộp x/y, lần gần nhất, số đang mở; "Xem" mở bản chỉ đọc', async () => {
    const user = userEvent.setup();
    const fetchMock = api({
      items: [],
      role: 'advisor',
      extra: {
        [DETAIL]: () =>
          jsonResponse(
            200,
            withWeekly({
              submitted: 5,
              expected: 7,
              missed: 2,
              open: 1,
              latest: { week_no: 6, submitted_on: '2026-10-14' },
            }),
          ),
        'GET /api/weekly-reports': () => jsonResponse(200, HISTORY),
      },
    });
    renderApp('/m11/phan-tich/mon/CNTT1188?student=SV04');
    await screen.findByRole('heading', { level: 1, name: 'Lập trình Web' });
    const section = weeklySection();
    expect(section).toHaveTextContent('Đã nộp 5/7 · gần nhất tuần 6 (14/10/2026) · 1 đang mở');

    await user.click(
      within(section).getByRole('button', { name: 'Xem báo cáo tuần môn CNTT1188' }),
    );
    const panel = await screen.findByRole('dialog', { name: /Báo cáo tuần CNTT1188/ });
    const query = callsTo(fetchMock, '/api/weekly-reports').at(-1);
    expect([query.get('student_id'), query.get('course_id')]).toEqual(['SV04', 'CNTT1188']);
    expect(panel).toHaveTextContent('Chỉ xem, không sửa được báo cáo đã nộp.');
    expect(panel).toHaveTextContent('Không nộp');
    expect(panel).toHaveTextContent('Đã nộp ngày 08/09/2026');
    expect(panel).toHaveTextContent('Chưa làm');
    expect(panel).toHaveTextContent('Việc ngoài trường');
    expect(within(panel).getAllByText('Không khớp dữ liệu LMS')).toHaveLength(1);
    // Chỉ đọc: không có ô nhập hay nút nộp.
    expect(within(panel).queryByRole('radio')).toBeNull();
    expect(within(panel).queryByRole('textbox')).toBeNull();
    expect(within(panel).queryByRole('button', { name: /Nộp/ })).toBeNull();
  });

  it('chưa có báo cáo đến hạn: không có nút "Xem"', async () => {
    api({
      items: [],
      extra: {
        [DETAIL]: () =>
          jsonResponse(
            200,
            withWeekly({ submitted: 0, expected: 0, missed: 0, open: 1, latest: null }),
          ),
      },
    });
    renderApp('/m11/phan-tich/mon/CNTT1188');
    await screen.findByRole('heading', { level: 1, name: 'Lập trình Web' });
    expect(weeklySection()).toHaveTextContent('Đã nộp 0/0 · 1 đang mở');
    expect(within(weeklySection()).queryByRole('button', { name: /Xem báo cáo/ })).toBeNull();
  });
});
