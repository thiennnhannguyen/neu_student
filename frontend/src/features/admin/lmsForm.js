/**
 * Hàm thuần của form LMS Demo (D-309). Form không tự tính số tổng: các số chỉ đọc lấy từ
 * POST /api/lms/preview, cùng phép tính với lúc gửi thật, nên chỉ có một nguồn số liệu.
 */

export const ATTENDANCE_OPTIONS = [
  { value: 'present', label: 'Có mặt' },
  { value: 'absent', label: 'Vắng không phép' },
  { value: 'excused', label: 'Vắng có phép' },
];

export const ASSESSMENT_KINDS = [
  { value: 'quiz', label: 'Kiểm tra' },
  { value: 'midterm', label: 'Giữa kỳ' },
];

const SCORE = /^\d{1,2}(?:[.,]\d{1,2})?$/;

/**
 * Điểm gõ kiểu Việt ("7,8") hoặc có dấu chấm thành chuỗi gửi API ("7.8"); không đổi sang số.
 * Ô trống là null. Sai định dạng trả undefined để form báo lỗi.
 */
export function scoreToApi(text) {
  const value = (text ?? '').trim();
  if (value === '') {
    return null;
  }
  return SCORE.test(value) ? value.replace(',', '.') : undefined;
}

/** Chuỗi điểm của API ("7.80") thành chữ kiểu Việt để sửa trong ô ("7,8"). */
export function scoreFromApi(value) {
  if (value === null || value === undefined) {
    return '';
  }
  return String(value)
    .replace(/(\.\d*?)0+$/, '$1')
    .replace(/\.$/, '')
    .replace('.', ',');
}

/** Điểm hệ 10 trong khoảng 0–10, so trên chuỗi đã chuẩn hóa ("7.8"), không đổi sang số thực. */
export function scoreInRange(apiText) {
  const [whole, fraction = ''] = apiText.split('.');
  const units = parseInt(whole, 10);
  return units < 10 || (units === 10 && /^0*$/.test(fraction));
}

export function draftKey(studentId, courseId, weekNo) {
  return `lms-draft:${studentId}:${courseId}:${weekNo}`;
}

export function emptyAssignment(index) {
  return {
    code: `BT${index}`,
    name: '',
    due_date: '',
    submitted_on: '',
    score: '',
    weight: '1',
  };
}

export function emptyAssessment(index) {
  return { kind: 'quiz', code: `KT${index}`, name: '', taken_on: '', score: '', weight: '1' };
}

/** Điểm danh mặc định "Có mặt" cho các buổi đã diễn ra; giữ trạng thái đã chọn của buổi cũ. */
export function attendanceFor(sessions, current = {}) {
  return Object.fromEntries(
    sessions.map((session) => [session.session_no, current[session.session_no] ?? 'present']),
  );
}

/** Nạp form từ bản chụp đã gửi (API latest) để sửa tiếp. */
export function formFromSnapshot(snapshot) {
  return {
    attendance: Object.fromEntries(snapshot.attendance.map((row) => [row.session_no, row.status])),
    assignments: snapshot.assignments.map((row) => ({
      code: row.code,
      name: row.name,
      due_date: row.due_date,
      submitted_on: row.submitted_on ?? '',
      score: scoreFromApi(row.score_10),
      weight: scoreFromApi(row.weight),
    })),
    assessments: snapshot.assessments.map((row) => ({
      kind: row.kind,
      code: row.code,
      name: row.name,
      taken_on: row.taken_on,
      score: scoreFromApi(row.score_10),
      weight: scoreFromApi(row.weight),
    })),
  };
}

/** Lỗi định dạng phía form: điểm và trọng số. Trả { "assignments.0.score": "…" }. */
export function formErrors(form) {
  const errors = {};
  for (const key of ['assignments', 'assessments']) {
    form[key].forEach((row, index) => {
      const score = scoreToApi(row.score);
      if (score === undefined || (score !== null && !scoreInRange(score))) {
        errors[`${key}.${index}.score`] = 'Điểm từ 0 đến 10, tối đa 2 chữ số thập phân, vd 7,8.';
      }
      const weight = scoreToApi(row.weight);
      if (weight === undefined || weight === null || /^0+(?:\.0+)?$/.test(weight)) {
        errors[`${key}.${index}.weight`] = 'Trọng số lớn hơn 0, vd 1.';
      }
    });
  }
  return errors;
}

/** Payload gửi /api/lms/sync và /api/lms/preview. Không có số tổng nào. */
export function toPayload({ studentId, courseId, asOf, form, sentAt }) {
  return {
    student_id: studentId,
    course_id: courseId,
    as_of: asOf,
    source: 'demo_form',
    sent_at: sentAt,
    attendance: Object.entries(form.attendance).map(([sessionNo, status]) => ({
      session_no: parseInt(sessionNo, 10),
      status,
    })),
    assignments: form.assignments.map((row) => ({
      code: row.code.trim(),
      name: row.name.trim(),
      due_date: row.due_date,
      submitted_on: row.submitted_on || null,
      score_10: scoreToApi(row.score),
      weight: scoreToApi(row.weight),
    })),
    assessments: form.assessments.map((row) => ({
      kind: row.kind,
      code: row.code.trim(),
      name: row.name.trim(),
      taken_on: row.taken_on,
      score_10: scoreToApi(row.score),
      weight: scoreToApi(row.weight),
    })),
  };
}

export function readDraft(storage, key) {
  try {
    const text = storage?.getItem(key);
    return text ? JSON.parse(text) : null;
  } catch {
    return null;
  }
}

export function writeDraft(storage, key, form, savedAt) {
  try {
    storage?.setItem(key, JSON.stringify({ ...form, savedAt }));
    return true;
  } catch {
    return false;
  }
}

export function removeDraft(storage, key) {
  try {
    storage?.removeItem(key);
  } catch {
    // Không xóa được nháp thì bỏ qua: lần sau người dùng vẫn chọn được bản đã gửi.
  }
}
