export const NO_CODE = 'Chưa có mã';
export const NOT_IN_PROGRAM = 'Không có trong CTĐT ngành bạn';
export const METER_NOTE =
  'Cả thanh là toàn bộ môn của nghề: đoạn đậm là môn đã đạt, đoạn nhạt là môn còn lại trong CTĐT ngành bạn, đoạn sọc chéo là môn ngoài CTĐT ngành bạn. Số % lớn chỉ tính trên môn có trong CTĐT ngành bạn, nên có thể cao hơn phần đậm của thanh.';
export const NOT_RECRUITMENT = 'Tỷ lệ không phản ánh khả năng được tuyển dụng';
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

export function lowCoverageText(coverage) {
  return `Ngành bạn có ${coverage.numerator}/${coverage.denominator} môn của nghề`;
}

const GROUP_SHORT = {
  'Phát triển Web và phần mềm': 'Web & phần mềm',
  'Trí tuệ nhân tạo và dữ liệu': 'AI & dữ liệu',
  'Phân tích nghiệp vụ và sản phẩm số': 'Nghiệp vụ & sản phẩm',
  'Hạ tầng, Cloud và vận hành': 'Hạ tầng & Cloud',
  'An ninh mạng và bảo mật': 'An ninh mạng',
  'Kiểm thử và chất lượng phần mềm': 'Kiểm thử',
};

/** Tên trên chip lọc. Nhóm không có tên ngắn (profile test) giữ tên đầy đủ. */
export function groupShortLabel(group) {
  const full = groupLabel(group);
  return GROUP_SHORT[full] ?? full;
}

/** Tên đầy đủ của nhóm nghề: bỏ phần "Nhóm 1 – " và hậu tố mẫu của dữ liệu. */
export function groupLabel(group) {
  return group.replace(/^Nhóm \d+ – /, '').replace(/ \(mẫu\)$/, '');
}
