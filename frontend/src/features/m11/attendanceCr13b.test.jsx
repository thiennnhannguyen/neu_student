/** CR-13b (D-316): dòng Chuyên cần "10 − 3 (vắng 2 buổi không phép) = 7" ở trang chi tiết môn. */
import { screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { jsonResponse, renderApp } from '../../test/fakeApi';
import { attendanceBasis, shortDecimal } from './CourseDetailPage';
import { COURSE_DETAIL, m11Api } from './testData';

const component = (deduction, value, counted, excusedDeducts = false) => ({
  key: 'attendance',
  weight: '0.10',
  value,
  kind: 'actual',
  deduction,
  deducted_absences: counted,
  excused_deducts: excusedDeducts,
});

describe('công thức chuyên cần trên trang chi tiết (D-316)', () => {
  it.each([
    ['7.00', '7'],
    ['7.50', '7,5'],
    ['10.00', '10'],
    ['0.00', '0'],
    ['10', '10'],
  ])('shortDecimal(%s) = %s', (value, text) => {
    expect(shortDecimal(value)).toBe(text);
  });

  it('2 buổi không phép: 10 − 3 = 7, không ngoại suy', () => {
    expect(attendanceBasis(component('3.00', '7.00', 2), { excused: 0 })).toBe(
      'Số thật: 10 − 3 (vắng 2 buổi không phép) = 7; không ngoại suy tới cuối kỳ.',
    );
  });

  it('vắng có phép không trừ thì ghi rõ', () => {
    expect(attendanceBasis(component('1.00', '9.00', 1), { excused: 2 })).toBe(
      'Số thật: 10 − 1 (vắng 1 buổi không phép) = 9; không ngoại suy tới cuối kỳ. Vắng có phép (2 buổi) tạm thời không trừ điểm.',
    );
  });

  it('cấu hình cho vắng có phép bị trừ: không ghi "không phép", không có câu tạm thời', () => {
    expect(attendanceBasis(component('3.00', '7.00', 2, true), { excused: 1 })).toBe(
      'Số thật: 10 − 3 (vắng 2 buổi) = 7; không ngoại suy tới cuối kỳ.',
    );
  });

  it('CNTT1159 trên trang: bảng thành phần có dòng trừ điểm', async () => {
    const detail = {
      ...COURSE_DETAIL,
      prediction: {
        ...COURSE_DETAIL.prediction,
        components: [component('3.00', '7.00', 2), ...COURSE_DETAIL.prediction.components.slice(1)],
        attendance: { held: 8, present: 6, absent: 2, excused: 0, total_sessions: 15 },
      },
    };
    m11Api('student', {
      'GET /api/m11/courses/CNTT1188/prediction': () => jsonResponse(200, detail),
    });
    renderApp('/m11/phan-tich/mon/CNTT1188');
    const table = await screen.findByRole('table', { name: 'Thành phần điểm dự kiến' });
    expect(within(table).getAllByRole('row')[1]).toHaveTextContent(
      'Chuyên cần10%7,00Số thật: 10 − 3 (vắng 2 buổi không phép) = 7',
    );
  });
});
