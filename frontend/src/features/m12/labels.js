export const NO_CODE = 'Chưa có mã';
export const NOT_IN_PROGRAM = 'Không có trong CTĐT ngành bạn';
export const LOW_COVERAGE = 'Ngành bạn có ít môn cho nghề này';
export const NOT_RECRUITMENT = 'Tỷ lệ không phản ánh khả năng được tuyển dụng';
export const K68_NOTE =
  'Danh mục theo CTĐT K68 – 2026 do nhóm tổng hợp; tín chỉ, tiên quyết là giả định.';
export const RATE_NOTE =
  'Tử số là số học phần đã đạt, gồm cả đạt qua tương đương và miễn; môn đang học không được tính. Kỹ năng và dự án chỉ tính khi minh chứng đã được duyệt. Hai tỷ lệ luôn tách riêng. Môn không có trong CTĐT ngành bạn không vào mẫu số.';

/** Học phần giữ 6 trạng thái; kỹ năng, dự án chưa có minh chứng có nhãn riêng (D-220). */
export function chipStatus(kind, status) {
  return kind !== 'course' && status === 'not_started' ? 'no_evidence' : status;
}

export function kindLabel(kind) {
  return { course: 'Học phần', skill: 'Kỹ năng', project: 'Dự án' }[kind];
}

/** Giá trị % do API tính; mẫu số 0 thì API trả null và giao diện hiện gạch ngang. */
export function percentText(percent) {
  return percent === null || percent === undefined ? '—' : `${percent}%`;
}

export const PRIORITIES = [
  { id: 'core', label: 'Cốt lõi' },
  { id: 'very_important', label: 'Rất quan trọng' },
  { id: 'recommended', label: 'Nên chọn' },
  { id: 'supporting', label: 'Bổ trợ' },
];

export function priorityLabel(priority) {
  return PRIORITIES.find((item) => item.id === priority)?.label ?? null;
}

export function typeLabel(requirementType) {
  return { required: 'BB', elective: 'TC' }[requirementType] ?? null;
}

/** Nhãn ngắn của nhóm nghề: bỏ phần "Nhóm 1 – " và hậu tố mẫu của dữ liệu. */
export function groupLabel(group) {
  return group.replace(/^Nhóm \d+ – /, '').replace(/ \(mẫu\)$/, '');
}
