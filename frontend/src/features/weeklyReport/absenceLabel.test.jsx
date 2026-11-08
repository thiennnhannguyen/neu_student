/** Bổ sung D-312 (commit đầu CR-13): "Vắng" thành "Vắng không phép", giá trị lưu giữ nguyên. */
import { screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { jsonResponse, renderApp } from '../../test/fakeApi';
import { ATTENDANCE_OPTIONS } from '../admin/lmsForm';
import { m11Api } from '../m11/testData';
import { QUESTIONS } from './questions';

const OPEN = {
  course: { id: 'CNTT1180', code: 'CNTT1180', name: 'Môn CNTT1180' },
  week: { week_no: 7, start: '2026-10-19', end: '2026-10-25' },
  opens_on: '2026-10-25',
  due_on: '2026-10-26',
  status: 'open',
  postponed: false,
  can_postpone: true,
  submitted_on: null,
  answers: null,
};

describe('Vắng không phép (bổ sung D-312)', () => {
  it('câu 1 có 3 lựa chọn: Có mặt, Vắng có phép, Vắng không phép; không còn "Vắng" trơn', async () => {
    m11Api('student', {
      'GET /api/weekly-reports/open': () =>
        jsonResponse(200, { today: '2026-10-26', items: [OPEN] }),
    });
    renderApp('/');
    const dialog = await screen.findByRole('dialog');
    const group = within(dialog).getByRole('group', { name: /1\. Đi học tuần này/ });
    expect(
      within(group)
        .getAllByRole('radio')
        .map((radio) => radio.labels[0].textContent),
    ).toEqual(['Có mặt', 'Vắng có phép', 'Vắng không phép']);
    expect(within(group).queryByRole('radio', { name: 'Vắng' })).toBeNull();
  });

  it('giá trị gửi API giữ nguyên, trùng trạng thái của LMS; form LMS Demo dùng cùng nhãn', () => {
    const attendance = QUESTIONS.find((question) => question.name === 'attendance').options;
    const label = (options, value) => options.find((option) => option.value === value).label;
    expect(attendance.map((option) => option.value).sort()).toEqual(
      ATTENDANCE_OPTIONS.map((option) => option.value).sort(),
    );
    for (const value of ['present', 'absent', 'excused']) {
      expect(label(attendance, value)).toBe(label(ATTENDANCE_OPTIONS, value));
    }
    expect(label(attendance, 'absent')).toBe('Vắng không phép');
  });
});
