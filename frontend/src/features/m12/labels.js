export const NO_CODE = 'Chưa có mã';

/** Học phần giữ 6 trạng thái; kỹ năng, dự án chưa có minh chứng có nhãn riêng (D-220). */
export function chipStatus(kind, status) {
  return kind !== 'course' && status === 'not_started' ? 'no_evidence' : status;
}

export function kindLabel(kind) {
  return { course: 'Học phần', skill: 'Kỹ năng', project: 'Dự án' }[kind];
}

/** Chỉ để vẽ thanh tiến độ. Số hiển thị luôn là tử số/mẫu số từ API. */
export function percentOf(progress) {
  if (!progress.denominator) {
    return 0;
  }
  return Math.round((progress.numerator * 100) / progress.denominator);
}
