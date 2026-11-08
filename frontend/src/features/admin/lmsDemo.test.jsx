/** CR-11 (D-309): form LMS Demo của quản trị và cố vấn. */
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { apiError, jsonResponse, loggedInAs, renderApp } from '../../test/fakeApi';
import { m11Api } from '../m11/testData';

const OPTIONS = {
  today: '2026-10-26',
  semester: { id: 'S5', name: 'HK1 2026-2027', start_date: '2026-09-01', end_date: '2027-01-15' },
  students: [
    {
      id: 'NEU-KHMT-001',
      student_code: 'NEU-KHMT-001',
      full_name: 'Nguyễn Thiện Nhân',
      courses: [
        {
          id: 'CNTT1159',
          code: 'CNTT1159',
          name: 'Quản lý dự án Công nghệ thông tin',
          schedule: {
            weekday: 5,
            first_session_date: '2026-09-04',
            total_sessions: 15,
            current_week: { week_no: 8, start: '2026-10-23', end: '2026-10-29' },
            sessions_held: 8,
          },
        },
        { id: 'CNTT9999', code: 'CNTT9999', name: 'Môn chưa có lịch', schedule: null },
      ],
    },
  ],
};

const CALENDAR = {
  as_of: '2026-10-26',
  week: { week_no: 8, start: '2026-10-23', end: '2026-10-29' },
  sessions: [
    { session_no: 1, session_date: '2026-09-04' },
    { session_no: 2, session_date: '2026-09-11' },
    { session_no: 3, session_date: '2026-09-18' },
  ],
};

function snapshotBody(overrides = {}) {
  return {
    student: { id: 'NEU-KHMT-001', student_code: 'NEU-KHMT-001' },
    course: { id: 'CNTT1159', code: 'CNTT1159', name: 'Quản lý dự án Công nghệ thông tin' },
    as_of: '2026-10-26',
    week: CALENDAR.week,
    attendance: [
      { session_no: 1, session_date: '2026-09-04', status: 'present' },
      { session_no: 2, session_date: '2026-09-11', status: 'present' },
      { session_no: 3, session_date: '2026-09-18', status: 'absent' },
    ],
    assignments: [
      {
        code: 'BT1',
        name: 'Bài 1',
        due_date: '2026-09-10',
        submitted_on: '2026-09-12',
        score_10: '7.80',
        weight: '1.00',
        status: 'graded',
        late: true,
      },
      {
        code: 'BT2',
        name: 'Bài 2',
        due_date: '2026-09-17',
        submitted_on: null,
        score_10: null,
        weight: '1.00',
        status: 'overdue',
        late: false,
      },
    ],
    assessments: [],
    summary: {
      sessions_held: 3,
      present: 2,
      absent: 1,
      excused: 0,
      assignments_total: 2,
      submitted: 1,
      graded: 1,
      pending: 0,
      late: 1,
      overdue: 1,
      not_due: 0,
      completion: { numerator: 1, denominator: 2, value: '0.5000', percent: 50 },
      // D-313: BT1 7,8 (nộp muộn, không trừ) và BT2 quá hạn tính 0 → 3,90.
      assignment_score: '3.90',
      process_score: '3.90',
      assessment_average: null,
    },
    ...overrides,
  };
}

function lmsApi(role = 'admin', extra = {}) {
  return loggedInAs(role, {
    'GET /api/lms/form-options': () => jsonResponse(200, OPTIONS),
    'GET /api/lms/calendar': () => jsonResponse(200, CALENDAR),
    'GET /api/lms/snapshots/latest': () => jsonResponse(200, { snapshot: snapshotBody() }),
    'POST /api/lms/preview': () => jsonResponse(200, snapshotBody()),
    'POST /api/lms/sync': () => jsonResponse(200, snapshotBody({ id: 'lms-1' })),
    'GET /api/notifications': () =>
      jsonResponse(200, { items: [], unread_count: 0, page: 1, page_size: 20, total: 0, note: '' }),
    ...extra,
  });
}

async function choose(user) {
  renderApp('/quan-tri/lms-demo');
  await user.selectOptions(await screen.findByLabelText('Sinh viên nhận dữ liệu'), 'NEU-KHMT-001');
  await user.selectOptions(screen.getByLabelText('Môn đang học kỳ hiện tại'), 'CNTT1159');
}

const bodyOf = (fetchMock, path) =>
  fetchMock.mock.calls
    .filter(([url, options]) => String(url) === path && options?.method === 'POST')
    .map(([, options]) => JSON.parse(options.body));

beforeEach(() => window.localStorage.clear());
afterEach(() => window.localStorage.clear());

describe('LMS Demo', () => {
  it('tên rõ là giả lập; chọn sinh viên rồi môn thì mã, tên, lịch tự điền', async () => {
    const user = userEvent.setup();
    lmsApi();
    await choose(user);

    expect(
      screen.getByRole('heading', { level: 1, name: 'LMS Demo – giả lập dữ liệu LMS' }),
    ).toBeInTheDocument();
    const identity = screen.getByText('Mã SV').closest('dl');
    expect(identity).toHaveTextContent('NEU-KHMT-001');
    expect(identity).toHaveTextContent('Nguyễn Thiện Nhân');
    expect(identity).toHaveTextContent('CNTT1159 – Quản lý dự án Công nghệ thông tin');
    expect(identity).toHaveTextContent('Thứ 6, buổi đầu 04/09/2026, 15 buổi');
    expect(screen.getByLabelText('Giả lập ngày hôm nay')).toHaveValue('2026-10-26');
    expect(
      screen.getByRole('option', { name: /Môn chưa có lịch.*chưa có lịch học/ }),
    ).toBeDisabled();
  });

  it('điểm danh theo từng buổi, 3 trạng thái, nạp từ bản đã gửi', async () => {
    const user = userEvent.setup();
    lmsApi();
    await choose(user);

    const session3 = await screen.findByRole('group', { name: 'Buổi 3 · 18/09/2026' });
    expect(within(session3).getAllByRole('radio')).toHaveLength(3);
    // Bổ sung D-312 (commit đầu CR-13): nhãn "Vắng" thành "Vắng không phép".
    expect(within(session3).getByRole('radio', { name: 'Vắng không phép' })).toBeChecked();
    expect(screen.getByText('Dữ liệu đã gửi của tuần 8')).toBeInTheDocument();
    expect(screen.queryByText(/Điểm cộng tiến độ/)).toBeNull();
  });

  it('số tổng chỉ đọc lấy từ backend, trạng thái bằng icon kèm chữ, số kiểu Việt', async () => {
    const user = userEvent.setup();
    const fetchMock = lmsApi();
    await choose(user);

    const totals = await screen.findByText('Điểm bài tập hiện tại');
    const list = totals.closest('dl');
    await waitFor(() => expect(list).toHaveTextContent('3,9'));
    expect(list).toHaveTextContent('50% (1/2 bài đến hạn)');
    expect(within(list).queryAllByRole('textbox')).toEqual([]);
    expect(screen.getByLabelText('Điểm hệ 10', { selector: '#assignment-0-score' })).toHaveValue(
      '7,8',
    );
    const first = screen.getByRole('group', { name: 'Bài tập 1' });
    expect(within(first).getByText('Đã chấm')).toBeInTheDocument();
    expect(within(first).getByText('Nộp muộn')).toBeInTheDocument();
    const second = screen.getByRole('group', { name: 'Bài tập 2' });
    expect(within(second).getByText('Quá hạn chưa nộp')).toBeInTheDocument();
    expect(first.querySelector('.status-text')).not.toBeNull();
    const preview = bodyOf(fetchMock, '/api/lms/preview').at(-1);
    expect(preview).not.toHaveProperty('summary');
    expect(preview.assignments[0].score_10).toBe('7.8');
  });

  it('điểm sai định dạng: báo ở ô, không gửi được', async () => {
    const user = userEvent.setup();
    lmsApi();
    await choose(user);

    const score = await screen.findByLabelText('Điểm hệ 10', { selector: '#assignment-0-score' });
    await user.clear(score);
    await user.type(score, '11,5');
    expect(await screen.findByText(/Điểm từ 0 đến 10/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Gửi sang hệ thống cảnh báo' })).toBeDisabled();
  });

  it('Lưu tạm giữ nháp trên trình duyệt, chưa gửi; mở lại thì nạp nháp', async () => {
    const user = userEvent.setup();
    const fetchMock = lmsApi();
    await choose(user);

    const name = await screen.findByLabelText('Tên bài', { selector: '#assignment-1-name' });
    await user.clear(name);
    await user.type(name, 'Bài đã sửa');
    await user.click(screen.getByRole('button', { name: 'Lưu tạm' }));
    expect(await screen.findByText(/Đã lưu tạm trên trình duyệt này/)).toBeInTheDocument();
    expect(bodyOf(fetchMock, '/api/lms/sync')).toEqual([]);
    expect(window.localStorage.getItem('lms-draft:NEU-KHMT-001:CNTT1159:8')).toContain(
      'Bài đã sửa',
    );
  });

  it('Gửi gọi /api/lms/sync với dữ liệu gốc, xóa nháp, báo đã gửi', async () => {
    const user = userEvent.setup();
    const fetchMock = lmsApi();
    window.localStorage.setItem(
      'lms-draft:NEU-KHMT-001:CNTT1159:8',
      JSON.stringify({
        attendance: { 1: 'present', 2: 'excused', 3: 'present' },
        assignments: [],
        assessments: [],
        savedAt: 'hôm qua',
      }),
    );
    await choose(user);

    expect(await screen.findByText('Bản nháp lưu lúc hôm qua')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Gửi sang hệ thống cảnh báo' }));
    await waitFor(() => expect(bodyOf(fetchMock, '/api/lms/sync')).toHaveLength(1));
    const body = bodyOf(fetchMock, '/api/lms/sync')[0];
    expect(body).toMatchObject({
      student_id: 'NEU-KHMT-001',
      course_id: 'CNTT1159',
      as_of: '2026-10-26',
      source: 'demo_form',
    });
    expect(body.attendance[1]).toEqual({ session_no: 2, status: 'excused' });
    expect(body).not.toHaveProperty('summary');
    expect(body.sent_at).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    expect(await screen.findByText(/Đã gửi tuần 8 của CNTT1159/)).toBeInTheDocument();
    expect(window.localStorage.getItem('lms-draft:NEU-KHMT-001:CNTT1159:8')).toBeNull();
  });

  it('backend từ chối: hiện lỗi của từng trường', async () => {
    const user = userEvent.setup();
    lmsApi('admin', {
      'POST /api/lms/sync': () =>
        apiError(422, 'VALIDATION_ERROR', 'Dữ liệu không hợp lệ.', {
          fields: { attendance: ['Cần điểm danh đúng 3 buổi đã diễn ra, mỗi buổi một lần.'] },
        }),
    });
    await choose(user);
    await user.click(await screen.findByRole('button', { name: 'Gửi sang hệ thống cảnh báo' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('attendance: Cần điểm danh đúng 3');
  });

  it('ngày giả lập ngoài lịch của môn: báo lỗi, không có form', async () => {
    const user = userEvent.setup();
    lmsApi('admin', {
      'GET /api/lms/calendar': () =>
        apiError(422, 'COURSE_NOT_IN_SESSION', 'Ngày này môn chưa bắt đầu hoặc đã qua tuần cuối.'),
    });
    await choose(user);
    expect(await screen.findByText('Ngày này chưa nhập được')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Gửi sang hệ thống cảnh báo' })).toBeNull();
  });

  it('không có sinh viên trong phạm vi: trạng thái rỗng', async () => {
    lmsApi('advisor', {
      'GET /api/lms/form-options': () => jsonResponse(200, { ...OPTIONS, students: [] }),
    });
    renderApp('/quan-tri/lms-demo');
    expect(await screen.findByText('Chưa có sinh viên')).toBeInTheDocument();
  });

  it('sinh viên không thấy menu, mở thẳng thì không có quyền, không gọi API LMS', async () => {
    const fetchMock = m11Api('student');
    renderApp('/quan-tri/lms-demo');
    expect(await screen.findByText('Bạn không có quyền xem trang này')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'LMS Demo' })).toBeNull();
    expect(fetchMock.mock.calls.filter(([url]) => String(url).startsWith('/api/lms'))).toEqual([]);
  });
});
