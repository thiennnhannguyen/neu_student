/** CR-12b (D-313): "Điểm bài tập hiện tại", "Điểm quá trình hiện tại", cách tính trong ⓘ. */
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { jsonResponse, renderApp } from '../../test/fakeApi';
import { CURRENT_COURSES, m11Api } from './testData';

function withScores(summary) {
  const [first, second] = CURRENT_COURSES.items;
  return {
    ...CURRENT_COURSES,
    items: [
      { ...first, latest: { ...first.latest, summary: { ...first.latest.summary, ...summary } } },
      second,
    ],
  };
}

describe('Điểm bài tập và điểm quá trình (D-313)', () => {
  it('bảng có đủ 3 cột điểm đúng tên, mỗi cột đúng trường của API', async () => {
    m11Api('student', {
      'GET /api/m11/current-courses': () =>
        jsonResponse(
          200,
          withScores({
            assignment_score: '4.43',
            assessment_average: '7.50',
            process_score: '4.81',
          }),
        ),
    });
    renderApp('/m11/phan-tich');
    const table = await screen.findByRole('table', { name: /Môn đang học/ });
    const headers = within(table)
      .getAllByRole('columnheader')
      .map((cell) => cell.textContent);
    expect(headers).toEqual(
      expect.arrayContaining(['Điểm bài tập hiện tại', 'Điểm kiểm tra', 'Điểm quá trình hiện tại']),
    );
    expect(headers).not.toContain('Điểm TB bài tập');
    const cells = within(within(table).getAllByRole('row')[1]).getAllByRole('cell');
    const valueOf = (name) => cells[headers.indexOf(name) - 1]?.textContent;
    // Cột đầu (Tên môn) là ô tiêu đề hàng nên lệch 1 với các ô thường.
    const rowHeaderIndex = headers.indexOf('Tên môn');
    const at = (name) =>
      headers.indexOf(name) > rowHeaderIndex
        ? valueOf(name)
        : cells[headers.indexOf(name)]?.textContent;
    expect(at('Điểm bài tập hiện tại')).toBe('4,43');
    expect(at('Điểm kiểm tra')).toBe('7,50');
    expect(at('Điểm quá trình hiện tại')).toBe('4,81');
  });

  it('ⓘ ghi cách tính: quá hạn = 0, chưa tới hạn và chờ chấm không tính, nộp muộn, gộp kiểm tra', async () => {
    const user = userEvent.setup();
    m11Api('student');
    renderApp('/m11/phan-tich');
    await screen.findByRole('table', { name: /Môn đang học/ });
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
