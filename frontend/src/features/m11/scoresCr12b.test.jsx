/** CR-12b (D-313): "Điểm bài tập hiện tại", "Điểm quá trình hiện tại", cách tính trong ⓘ. */
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { jsonResponse, renderApp } from '../../test/fakeApi';
import { COURSE_DETAIL, CURRENT_COURSES, m11Api } from './testData';

// D-314: bảng môn đang học chỉ còn 2 cột; 3 điểm của D-313 và ⓘ chuyển sang mục "Điểm hiện tại
// từ LMS" của trang chi tiết môn.
function withScores(summary) {
  return {
    ...COURSE_DETAIL,
    latest: { ...COURSE_DETAIL.latest, summary: { ...COURSE_DETAIL.latest.summary, ...summary } },
  };
}

async function lmsScores() {
  await screen.findByRole('heading', { level: 1, name: 'Lập trình Web' });
  return screen.getByRole('heading', { name: /Điểm hiện tại từ LMS/ }).parentElement;
}

describe('Điểm bài tập và điểm quá trình (D-313)', () => {
  it('trang chi tiết môn có đủ 3 điểm đúng tên, mỗi điểm đúng trường của API', async () => {
    m11Api('student', {
      'GET /api/m11/courses/CNTT1188/prediction': () =>
        jsonResponse(
          200,
          withScores({
            assignment_score: '4.43',
            assessment_average: '7.50',
            process_score: '4.81',
          }),
        ),
    });
    renderApp('/m11/phan-tich/mon/CNTT1188');
    const list = (await lmsScores()).querySelector('dl');
    const value = (name) => within(list).getByText(name).nextElementSibling.textContent;
    expect(value('Điểm bài tập hiện tại')).toBe('4,43');
    expect(value('Điểm kiểm tra')).toBe('7,50');
    expect(value('Điểm quá trình hiện tại')).toBe('4,81');
    expect(list).not.toHaveTextContent('Điểm TB bài tập');
  });

  it('ⓘ ghi cách tính: quá hạn = 0, chưa tới hạn và chờ chấm không tính, nộp muộn, gộp kiểm tra', async () => {
    const user = userEvent.setup();
    m11Api('student');
    renderApp('/m11/phan-tich/mon/CNTT1188');
    await lmsScores();
    await user.click(
      screen.getByRole('button', { name: 'Cách tính điểm bài tập và điểm quá trình' }),
    );
    const help = screen.getByText(/quá hạn chưa nộp \(tính 0 điểm\)/).closest('.info-popover');
    expect(help).toHaveTextContent('chưa tới hạn');
    expect(help).toHaveTextContent('chờ chấm chưa tính');
    expect(help).toHaveTextContent('nộp muộn giữ điểm');
    expect(help).toHaveTextContent('bài kiểm tra, giữa kỳ đã có điểm');
  });
});

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
          id: 'CNTT1188',
          code: 'CNTT1188',
          name: 'Lập trình Web',
          schedule: {
            weekday: 3,
            first_session_date: '2026-09-02',
            total_sessions: 15,
            current_week: { week_no: 8, start: '2026-10-21', end: '2026-10-27' },
            sessions_held: 8,
          },
        },
      ],
    },
  ],
};

const PREVIEW = {
  week: { week_no: 8, start: '2026-10-21', end: '2026-10-27' },
  attendance: [],
  assignments: [],
  assessments: [],
  summary: {
    ...CURRENT_COURSES.items[0].latest.summary,
    assignment_score: '4.43',
    assessment_average: '7.50',
    process_score: '4.81',
  },
};

describe('Form LMS Demo (D-313)', () => {
  it('số tổng chỉ đọc có Điểm bài tập hiện tại, Điểm kiểm tra, Điểm quá trình hiện tại và ⓘ', async () => {
    const user = userEvent.setup();
    m11Api('admin', {
      'GET /api/lms/form-options': () => jsonResponse(200, OPTIONS),
      'GET /api/lms/calendar': () =>
        jsonResponse(200, { as_of: '2026-10-26', week: PREVIEW.week, sessions: [] }),
      'GET /api/lms/snapshots/latest': () => jsonResponse(200, { snapshot: null }),
      'POST /api/lms/preview': () => jsonResponse(200, PREVIEW),
      'GET /api/notifications': () =>
        jsonResponse(200, {
          items: [],
          unread_count: 0,
          page: 1,
          page_size: 20,
          total: 0,
          note: '',
        }),
    });
    renderApp('/quan-tri/lms-demo');
    await user.selectOptions(
      await screen.findByLabelText('Sinh viên nhận dữ liệu'),
      'NEU-KHMT-001',
    );
    await user.selectOptions(screen.getByLabelText('Môn đang học kỳ hiện tại'), 'CNTT1188');
    const list = (await screen.findByText('Điểm quá trình hiện tại')).closest('dl');
    const value = (name) => within(list).getByText(name).nextElementSibling.textContent;
    expect(value('Điểm bài tập hiện tại')).toBe('4,43');
    expect(value('Điểm kiểm tra')).toBe('7,50');
    expect(value('Điểm quá trình hiện tại')).toBe('4,81');
    expect(
      screen.getByRole('button', { name: 'Cách tính điểm bài tập và điểm quá trình' }),
    ).toBeInTheDocument();
  });
});
