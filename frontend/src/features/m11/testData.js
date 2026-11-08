import { jsonResponse, loggedInAs } from '../../test/fakeApi';

const META = {
  reference_semester: 'S5',
  computed_at: '2026-11-06T03:00:00Z',
  rule_version: 'K66-mau-v1',
  data_warnings: [],
};

export const SEMESTERS = {
  items: [
    { id: 'S4', name: 'HK2 2025-2026', order: 4, is_current: false },
    { id: 'S5', name: 'HK1 2026-2027', order: 5, is_current: true },
  ],
  current_id: 'S5',
};

function metric(value, extra = {}) {
  return { value, ...META, ...extra };
}

const SEMESTER_SCOPE = { scope: 'semester', scope_label: 'Riêng' };
const AS_OF_SCOPE = { scope: 'as_of', scope_label: 'Tính đến' };

export function overviewBody({ gpa = '3.11', cumulative = '2.88', semester = 'S5', ...rest } = {}) {
  return {
    semester: { id: semester, name: `Kỳ ${semester}` },
    metrics: {
      semester_gpa: metric(gpa, { numerator: '10.00', denominator: 3, ...SEMESTER_SCOPE }),
      cumulative_gpa: metric(cumulative, { numerator: '20.00', denominator: 7, ...AS_OF_SCOPE }),
      credits_passed: metric(19, AS_OF_SCOPE),
      credits_debt: metric(6, AS_OF_SCOPE),
      credits_in_progress: metric(15, SEMESTER_SCOPE),
      failed_course_count: metric(2, AS_OF_SCOPE),
      risk_level: metric('warning', AS_OF_SCOPE),
    },
    grades_updated_at: '2026-06-19T00:00:00Z',
    meta: META,
    ...rest,
  };
}

export const EMPTY_OVERVIEW = {
  semester: { id: 'S5', name: 'Kỳ S5' },
  metrics: {
    semester_gpa: metric(null, { numerator: '0', denominator: 0, ...SEMESTER_SCOPE }),
    cumulative_gpa: metric(null, { numerator: '0', denominator: 0, ...AS_OF_SCOPE }),
    credits_passed: metric(0, AS_OF_SCOPE),
    credits_debt: metric(0, AS_OF_SCOPE),
    credits_in_progress: metric(0, SEMESTER_SCOPE),
    failed_course_count: metric(0, AS_OF_SCOPE),
    risk_level: metric('normal', AS_OF_SCOPE),
  },
  grades_updated_at: null,
  meta: {
    ...META,
    data_warnings: [
      { code: 'NO_RESULTS', course_id: null, semester_id: null, message: 'Chưa có kết quả.' },
    ],
  },
};

export function gradeRow(overrides = {}) {
  return {
    course_id: 'CNT101',
    code: 'CNT101',
    name: 'Nhập môn',
    credits: 3,
    counts_gpa: true,
    semester: { id: 'S4', name: 'HK2 2025-2026', order: 4 },
    score_10: '8.60',
    letter: 'A',
    grade_4: '4.00',
    status: 'done',
    via_course: null,
    has_retake: false,
    data_warnings: [],
    ...overrides,
  };
}

export function gradesBody(items, overrides = {}) {
  return {
    items,
    page: 1,
    page_size: 20,
    total: items.length,
    semester_summary: null,
    meta: META,
    ...overrides,
  };
}

export const COMPONENTS = [
  { key: 'attendance_score', name: 'Điểm Chuyên cần', weight: 10 },
  { key: 'midterm_score', name: 'Điểm Kiểm tra thường xuyên 1', weight: 40 },
  { key: 'final_score', name: 'Điểm thi kết thúc học phần', weight: 50 },
];

export const ATTEMPTS = {
  course: { course_id: 'MAU101', code: 'MAU101', name: 'Giải tích' },
  components: COMPONENTS,
  items: [
    {
      ordinal: 1,
      semester: { id: 'S1', name: 'HK1 2024-2025', order: 1 },
      status: 'final',
      score_10: '3.00',
      letter: 'F',
      grade_4: '0.00',
      passed: false,
      is_effective: false,
      component_scores: null,
    },
    {
      ordinal: 2,
      semester: { id: 'S3', name: 'HK1 2025-2026', order: 3 },
      status: 'final',
      score_10: '8.60',
      letter: 'A',
      grade_4: '4.00',
      passed: true,
      is_effective: true,
      component_scores: { attendance_score: '10.00', midterm_score: '8.00', final_score: '8.75' },
    },
    {
      ordinal: 3,
      semester: { id: 'S5', name: 'HK1 2026-2027', order: 5 },
      status: 'in_progress',
      score_10: null,
      letter: null,
      grade_4: null,
      passed: null,
      is_effective: false,
      component_scores: null,
    },
  ],
  meta: META,
};

export const TREND = {
  points: [
    { semester_id: 'S4', order: 4, name: 'HK2 2025-2026', value: '2.75' },
    { semester_id: 'S5', order: 5, name: 'HK1 2026-2027', value: null },
  ],
  direction: 'stable',
  summary: 'GPA kỳ S4 ổn định so với kỳ S3, chênh 0,05.',
  stable_delta: '0.10',
  meta: META,
};

export const CREDITS = {
  passed: 19,
  debt: 6,
  failed_courses: 2,
  in_progress: 15,
  registered: 15,
  required: { total_credits: 60, passed_credits: 15, missing_credits: 45 },
  elective_groups: [
    {
      group_id: 'eg',
      name: 'Tự chọn A',
      min_credits: 6,
      passed_credits: 9,
      missing_credits: 0,
      exceeded_credits: 3,
      label: 'vượt yêu cầu nhóm',
    },
  ],
  meta: META,
};

export const CURRICULUM = {
  program: { program_version_id: 'pv', name: 'CTĐT mẫu', effective_cohort: 'K66' },
  missing_required: [{ course_id: 'c1', code: null, name: 'Môn thiếu mã', credits: 3 }],
  unmet_elective_groups: [
    {
      group_id: 'eg',
      name: 'Tự chọn B',
      min_credits: 6,
      passed_credits: 0,
      missing_credits: 6,
      exceeded_credits: 0,
      label: null,
    },
  ],
  blocked_courses: [
    {
      course_id: 'c2',
      code: 'CNT303',
      name: 'Hệ thống',
      credits: 3,
      missing_prerequisites: [{ course_id: 'c3', code: 'CNT301', name: 'Web', credits: 3 }],
    },
  ],
  meta: META,
};

export const STRENGTHS = {
  groups: [
    {
      group_id: 'g1',
      slug: 'a',
      name: 'Nhóm lập trình',
      level: 'strong',
      value: '3.60',
      numerator: '36.00',
      denominator: 10,
      courses: [{ course_id: 'c', code: 'CNT101', name: 'A', credits: 3 }],
    },
    {
      group_id: 'g2',
      slug: 'b',
      name: 'Nhóm toán',
      level: 'insufficient_data',
      value: null,
      numerator: '0',
      denominator: 0,
      courses: [],
    },
  ],
  meta: META,
};

export const COMPARE = {
  semester_a: {
    semester_id: 'S4',
    name: 'HK2 2025-2026',
    gpa: '2.75',
    credits: 12,
    passed_count: 3,
    failed_count: 1,
  },
  semester_b: {
    semester_id: 'S5',
    name: 'HK1 2026-2027',
    gpa: '3.00',
    credits: 15,
    passed_count: 5,
    failed_count: 0,
  },
  gpa_delta: '0.25',
  credit_delta: 3,
  passed_delta: 2,
  failed_delta: -1,
  meta: META,
};

export const RISKS = {
  overall: 'warning',
  outcomes: [
    {
      rule_code: 'gpa',
      level: 'warning',
      reason: 'GPA tích lũy 1,81 dưới ngưỡng cảnh báo 2,00.',
      summary: 'GPA tích lũy 1,81, dưới ngưỡng 2,00',
      evidence: {
        numerator: '43.50',
        denominator: 24,
        value: '1.81',
        watch_below: '2.50',
        warning_below: '2.00',
      },
      rule_version: 'K66-mau-v1',
    },
    {
      rule_code: 'debt',
      level: 'watch',
      reason: 'Đang nợ 3 tín chỉ.',
      summary: 'Nợ 3 tín chỉ',
      evidence: { debt_credits: 3, watch_from: 3, warning_from: 6 },
      rule_version: 'K66-mau-v1',
    },
    {
      rule_code: 'registration',
      level: 'not_applicable',
      reason: 'Chỉ xét đăng ký ở kỳ hiện tại.',
      summary: null,
      evidence: { registered_credits: 0, min_credits: 10, max_credits: 25 },
      rule_version: 'K66-mau-v1',
    },
  ],
  disclaimer: 'Cảnh báo tham khảo, không phải quyết định học vụ chính thức',
  meta: META,
};

export const GLOSSARY = {
  items: [
    {
      key: 'failed_course_count',
      name: 'Số môn chưa đạt',
      formula: 'Số nhóm môn có lần hiệu lực trượt.',
      source: 'Kết quả các lần học',
      rule_version: 'K66-mau-v1',
      note: 'Có thể lớn hơn số dòng "Chưa đạt".',
    },
  ],
};

const respond = (body) => () => jsonResponse(200, body);

/** Đủ API đọc của M11; extra ghi đè từng đường dẫn. */
export function m11Api(role = 'student', extra = {}) {
  return loggedInAs(role, {
    'GET /api/students/me': respond({
      cohort: 'K66',
      program: { name: 'CNTT' },
      current_semester: { name: 'HK1' },
    }),
    'GET /api/m11/semesters': respond(SEMESTERS),
    'GET /api/m11/overview': respond(overviewBody()),
    'GET /api/m11/grades': respond(gradesBody([gradeRow()])),
    'GET /api/m11/gpa-trend': respond(TREND),
    'GET /api/m11/credits': respond(CREDITS),
    'GET /api/m11/curriculum-check': respond(CURRICULUM),
    'GET /api/m11/strengths': respond(STRENGTHS),
    'GET /api/m11/risks': respond(RISKS),
    'GET /api/m11/compare': respond(COMPARE),
    'GET /api/m11/metrics-glossary': respond(GLOSSARY),
    ...extra,
  });
}

export function callsTo(fetchMock, path) {
  return fetchMock.mock.calls
    .map(([url]) => String(url))
    .filter((url) => url.split('?')[0] === path)
    .map((url) => new URL(url, 'http://x').searchParams);
}
