/** CR-13b (D-316), D-330: dòng Chuyên cần "10 − 3 (vắng 2 buổi không phép) = 7" ở trang chi tiết môn. */
import { screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { jsonResponse, renderApp } from '../../test/fakeApi';
import { attendanceBasis, shortDecimal } from './CourseDetailPage';
import { COURSE_DETAIL, m11Api } from './testData';

// D-330: thành phần Chuyên cần có số buổi và mức trừ riêng từng loại vắng.
const component = (
  value,
  absent = 0,
  absentDeduction = '0.00',
  excused = 0,
  excusedDeduction = '0.00',
) => ({
  key: 'attendance',
  weight: '0.10',
  value,
  kind: 'actual',
  deduction: '0.00',
  absent,
  absent_deduction: absentDeduction,
  excused,
  excused_deduction: excusedDeduction,
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
    expect(attendanceBasis(component('7.00', 2, '3.00'))).toBe(
      'Số thật: 10 − 3 (vắng 2 buổi không phép) = 7; không ngoại suy tới cuối kỳ.',
    );
  });

  it('D-330: trộn hai loại vắng ghi đủ phép tính', () => {
    expect(attendanceBasis(component('8.00', 1, '1.00', 2, '1.00'))).toBe(
      'Số thật: 10 − 1 (vắng 1 buổi không phép) − 1 (vắng 2 buổi có phép) = 8; không ngoại suy tới cuối kỳ.',
    );
  });

  it('D-330: chỉ vắng có phép, kể cả 1 buổi trừ 0, vẫn ghi', () => {
    expect(attendanceBasis(component('10.00', 0, '0.00', 1, '0.00'))).toBe(
      'Số thật: 10 − 0 (vắng 1 buổi có phép) = 10; không ngoại suy tới cuối kỳ.',
    );
  });

  it('chưa vắng buổi nào', () => {
    expect(attendanceBasis(component('10.00'))).toBe(
      'Số thật: 10 − 0 (chưa vắng buổi nào) = 10; không ngoại suy tới cuối kỳ.',
    );
  });

  it('CNTT1159 trên trang: bảng thành phần có dòng trừ điểm', async () => {
    const detail = {
      ...COURSE_DETAIL,
      prediction: {
        ...COURSE_DETAIL.prediction,
        components: [component('7.00', 2, '3.00'), ...COURSE_DETAIL.prediction.components.slice(1)],
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
