/** Nhãn luôn đi kèm biểu tượng và màu; ý nghĩa không chỉ nằm ở màu. */
export const GRADE_STATUSES = {
  done: { label: 'Đạt', icon: '✓', tone: 'success' },
  done_via_equivalency: { label: 'Đạt qua tương đương', icon: '✓', tone: 'success' },
  exempt: { label: 'Miễn', icon: '✓', tone: 'success' },
  in_progress: { label: 'Đang học', icon: '◔', tone: 'info' },
  failed: { label: 'Chưa đạt', icon: '✕', tone: 'error' },
  not_started: { label: 'Chưa học', icon: '○', tone: 'muted' },
};

export const RISK_LEVELS = {
  normal: { label: 'Bình thường', icon: '✓', tone: 'success' },
  watch: { label: 'Chú ý', icon: '!', tone: 'warning' },
  warning: { label: 'Cảnh báo', icon: '▲', tone: 'error' },
  insufficient_data: { label: 'Chưa đủ dữ liệu', icon: '?', tone: 'muted' },
  not_applicable: { label: 'Không áp dụng', icon: '–', tone: 'muted' },
};

export const GROUP_LEVELS = {
  strong: { label: 'Điểm mạnh', icon: '▲', tone: 'success' },
  normal: { label: 'Bình thường', icon: '–', tone: 'info' },
  weak: { label: 'Điểm yếu', icon: '▼', tone: 'warning' },
  insufficient_data: { label: 'Chưa đủ dữ liệu', icon: '?', tone: 'muted' },
};

export const ATTEMPT_STATUSES = {
  in_progress: GRADE_STATUSES.in_progress,
  exempt: GRADE_STATUSES.exempt,
};

export const RULE_NAMES = {
  gpa: 'GPA tích lũy',
  debt: 'Nợ tín chỉ',
  registration: 'Đăng ký tín chỉ',
};

export const DISCLAIMER = 'Cảnh báo tham khảo, không phải quyết định học vụ chính thức';
