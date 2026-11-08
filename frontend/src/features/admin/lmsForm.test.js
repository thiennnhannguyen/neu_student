/** D-309: hàm thuần của form LMS Demo. */
import { describe, expect, it } from 'vitest';
import {
  attendanceFor,
  draftKey,
  formErrors,
  formFromSnapshot,
  readDraft,
  removeDraft,
  scoreFromApi,
  scoreInRange,
  scoreToApi,
  toPayload,
  writeDraft,
} from './lmsForm';

describe('điểm kiểu Việt', () => {
  it.each([
    ['7,8', '7.8'],
    ['7.8', '7.8'],
    ['10', '10'],
    [' 8,25 ', '8.25'],
    ['', null],
    ['  ', null],
  ])('%s gửi lên API là %s', (text, value) => {
    expect(scoreToApi(text)).toBe(value);
  });

  it.each(['7,555', 'abc', '7,8,1', '-1', '100'])('%s sai định dạng', (text) => {
    expect(scoreToApi(text)).toBeUndefined();
  });

  it.each([
    ['0', true],
    ['9.99', true],
    ['10', true],
    ['10.0', true],
    ['10.5', false],
    ['11', false],
  ])('khoảng 0–10: %s là %s', (text, ok) => {
    expect(scoreInRange(text)).toBe(ok);
  });

  it.each([
    ['7.80', '7,8'],
    ['8.00', '8'],
    ['10.00', '10'],
    ['7.25', '7,25'],
    [null, ''],
  ])('API %s hiện trong ô là %s', (value, text) => {
    expect(scoreFromApi(value)).toBe(text);
  });
});

describe('form', () => {
  const form = {
    attendance: { 1: 'present', 2: 'absent' },
    assignments: [
      {
        code: ' BT1 ',
        name: 'Bài 1',
        due_date: '2026-09-10',
        submitted_on: '',
        score: '',
        weight: '1',
      },
    ],
    assessments: [
      {
        kind: 'quiz',
        code: 'KT1',
        name: 'KT',
        taken_on: '2026-09-25',
        score: '7,5',
        weight: '1',
      },
    ],
  };

  it('payload chỉ có dữ liệu gốc, không có số tổng', () => {
    const payload = toPayload({
      studentId: 'SV',
      courseId: 'C',
      asOf: '2026-10-26',
      form,
      sentAt: 'x',
    });
    expect(Object.keys(payload).sort()).toEqual(
      [
        'as_of',
        'assessments',
        'assignments',
        'attendance',
        'course_id',
        'sent_at',
        'source',
        'student_id',
      ].sort(),
    );
    expect(payload.attendance).toEqual([
      { session_no: 1, status: 'present' },
      { session_no: 2, status: 'absent' },
    ]);
    expect(payload.assignments[0]).toEqual({
      code: 'BT1',
      name: 'Bài 1',
      due_date: '2026-09-10',
      submitted_on: null,
      score_10: null,
      weight: '1',
    });
    expect(payload.assessments[0].score_10).toBe('7.5');
  });

  it('lỗi điểm và trọng số theo từng dòng', () => {
    const bad = {
      ...form,
      assignments: [{ ...form.assignments[0], score: '11,5', weight: '0' }],
    };
    expect(formErrors(bad)).toEqual({
      'assignments.0.score': expect.stringContaining('0 đến 10'),
      'assignments.0.weight': expect.stringContaining('lớn hơn 0'),
    });
    expect(formErrors(form)).toEqual({});
  });

  it('điểm danh đúng các buổi đã diễn ra, giữ trạng thái đã chọn, buổi mới là Có mặt', () => {
    const sessions = [1, 2, 3].map((n) => ({ session_no: n, session_date: '' }));
    expect(attendanceFor(sessions, { 2: 'excused', 9: 'absent' })).toEqual({
      1: 'present',
      2: 'excused',
      3: 'present',
    });
  });

  it('nạp lại từ bản chụp đã gửi', () => {
    const snapshot = {
      attendance: [{ session_no: 1, status: 'absent' }],
      assignments: [
        {
          code: 'BT1',
          name: 'B',
          due_date: '2026-09-10',
          submitted_on: null,
          score_10: null,
          weight: '1.00',
        },
      ],
      assessments: [],
    };
    expect(formFromSnapshot(snapshot)).toEqual({
      attendance: { 1: 'absent' },
      assignments: [
        {
          code: 'BT1',
          name: 'B',
          due_date: '2026-09-10',
          submitted_on: '',
          score: '',
          weight: '1',
        },
      ],
      assessments: [],
    });
  });
});

describe('bản nháp trong trình duyệt', () => {
  function memory() {
    const data = new Map();
    return {
      getItem: (key) => data.get(key) ?? null,
      setItem: (key, value) => data.set(key, value),
      removeItem: (key) => data.delete(key),
    };
  }
  const broken = {
    getItem: () => {
      throw new Error('blocked');
    },
    setItem: () => {
      throw new Error('blocked');
    },
    removeItem: () => {
      throw new Error('blocked');
    },
  };

  it('khóa theo sinh viên, môn, tuần của môn', () => {
    expect(draftKey('SV', 'C', 8)).toBe('lms-draft:SV:C:8');
  });

  it('lưu, đọc, xóa', () => {
    const store = memory();
    expect(writeDraft(store, 'k', { a: 1 }, 'lúc')).toBe(true);
    expect(readDraft(store, 'k')).toEqual({ a: 1, savedAt: 'lúc' });
    removeDraft(store, 'k');
    expect(readDraft(store, 'k')).toBeNull();
  });

  it('trình duyệt chặn lưu trữ: không làm hỏng form', () => {
    expect(writeDraft(broken, 'k', {}, 'x')).toBe(false);
    expect(readDraft(broken, 'k')).toBeNull();
    expect(() => removeDraft(broken, 'k')).not.toThrow();
    expect(readDraft(null, 'k')).toBeNull();
  });
});
