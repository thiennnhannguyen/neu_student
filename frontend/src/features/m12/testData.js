import { jsonResponse } from '../../test/fakeApi';
import { m11Api } from '../m11/testData';

export const DISCLAIMER = 'Tỷ lệ này không phản ánh khả năng được tuyển dụng';

export function progress(numerator, denominator, label = 'học phần') {
  return {
    numerator,
    denominator,
    value: denominator ? '0.2222' : null,
    percent: denominator ? Math.round((numerator * 100) / denominator) : null,
    formula: `${numerator}/${denominator} ${label}`,
  };
}

const SKILL_LABEL = 'kỹ năng & dự án';

export function card(id, display_name, name_en, group, extra = {}) {
  return {
    id: `career-${id}`,
    slug: id,
    name: `${display_name}`,
    field: group,
    display_name,
    name_en,
    group,
    illustration_key: id,
    tagline: `Tagline ${display_name}`,
    is_mock: true,
    ...extra,
  };
}

const WEB = 'Nhóm 1 – Phát triển Web và phần mềm';
const DATA = 'Nhóm 2 – Trí tuệ nhân tạo và dữ liệu';
export const AI = card('ai', 'Kỹ sư Trí tuệ nhân tạo', 'AI Engineer', DATA);
export const ANALYST = card('data', 'Chuyên viên Phân tích dữ liệu', 'Data Analyst', DATA);
export const BACKEND = card('backend', 'Lập trình viên Backend', 'Backend Developer', WEB);

export function galleryItem(career, extra = {}) {
  return {
    career,
    is_primary: false,
    fits_major: null,
    course_progress: progress(1, 8),
    skill_progress: progress(0, 9, SKILL_LABEL),
    coverage: { numerator: 8, denominator: 12, percent: 67 },
    low_coverage: false,
    closeness: { numerator: 3, denominator: 14, value: '0.2143' },
    ...extra,
  };
}

export const PRIMARY_ITEM = galleryItem(AI, {
  is_primary: true,
  fits_major: { id: 'prog-khmt', code: 'KHMT' },
  course_progress: progress(2, 9),
  skill_progress: progress(1, 3, SKILL_LABEL),
  closeness: null,
});

export function galleryBody(items, extra = {}) {
  return {
    student_id: 'DEMO05',
    sort: 'default',
    has_primary: true,
    groups: [WEB, DATA],
    items: items ?? [
      PRIMARY_ITEM,
      galleryItem(ANALYST, { fits_major: { id: 'prog-khmt', code: 'KHMT' } }),
      galleryItem(BACKEND, { low_coverage: true }),
    ],
    disclaimer: DISCLAIMER,
    ...extra,
  };
}

export function child(id, title, status, extra = {}) {
  return {
    id,
    kind: 'course',
    title,
    short_desc: null,
    course_id: id,
    code: id,
    skill_id: null,
    level: null,
    criteria: null,
    weight: '1.00',
    program_id: 'prog-khmt',
    subject_key: `s-${id}`,
    priority: 'core',
    purpose: `Học ${title}`,
    status,
    outside_curriculum: false,
    not_in_program: false,
    via_course: null,
    requirement_type: 'required',
    planned_semester: 3,
    data_warning: null,
    ...extra,
  };
}

function skillChild(id, title, status, extra = {}) {
  return child(id, title, status, {
    kind: 'skill',
    course_id: null,
    code: null,
    skill_id: id,
    program_id: null,
    subject_key: null,
    priority: null,
    purpose: null,
    requirement_type: null,
    planned_semester: null,
    ...extra,
  });
}

function projectChild(id, title, level) {
  return skillChild(id, title, 'not_started', {
    kind: 'project',
    level,
    criteria: `Tiêu chí ${title}`,
  });
}

export const NODES = [
  {
    id: 'n1',
    kind: 'group',
    title: 'Toán + lập trình',
    short_desc: null,
    order: 1,
    deliverable: 'Python, NumPy',
    course_progress: progress(2, 3),
    children: [
      child('CNTT1128', 'Cơ sở lập trình', 'done'),
      child('CNTT1140', 'Trí tuệ nhân tạo', 'done_via_equivalency', {
        via_course: { course_id: 'X1', code: 'X1' },
        priority: 'very_important',
      }),
      child('NOCODE', 'Môn chưa có mã', 'in_progress', {
        code: null,
        requirement_type: 'elective',
        planned_semester: null,
        priority: 'recommended',
        data_warning: 'Nguồn ghi trùng mã.',
      }),
      child('absent-s9', 'Học máy', 'not_in_program', {
        course_id: null,
        code: null,
        not_in_program: true,
        requirement_type: null,
        planned_semester: null,
        priority: 'supporting',
      }),
    ],
  },
  {
    id: 'n2',
    kind: 'group',
    title: 'Portfolio',
    short_desc: null,
    order: 2,
    deliverable: 'Có metric',
    course_progress: progress(0, 0),
    children: [
      skillChild('sk-a', 'Lập baseline', 'done'),
      skillChild('sk-b', 'Giải thích metric', 'pending'),
      skillChild('sk-c', 'Viết báo cáo', 'not_started'),
      projectChild('pj-3', 'Dự án lớn', 'Job-ready'),
      projectChild('pj-1', 'Dự án nhỏ', 'Starter'),
      projectChild('pj-2', 'Dự án vừa', 'Intermediate'),
    ],
  },
];

export function progressBody(extra = {}) {
  return {
    student_id: 'DEMO05',
    career: AI,
    version: { id: 'cv', version: 1, published_at: '2026-08-20T09:00:00Z' },
    is_primary: true,
    course_progress: progress(2, 9),
    skill_progress: progress(1, 3, SKILL_LABEL),
    coverage: { numerator: 12, denominator: 14, percent: 86 },
    fits_major: { id: 'prog-khmt', code: 'KHMT' },
    profile: {
      ...AI,
      objective: 'Đóng gói mô hình AI',
      major_fit: { programs: [{ id: 'prog-khmt', code: 'KHMT' }], note: 'Ưu tiên KHMT.' },
      self_study: ['PyTorch', 'FastAPI'],
    },
    disclaimer: DISCLAIMER,
    outside_curriculum_count: 0,
    computed_at: '2026-11-07T03:00:00Z',
    data_warnings: [],
    nodes: NODES,
    ...extra,
  };
}

export const REQUIREMENT = {
  id: 'CNTT1140',
  code: 'CNTT1140',
  credits: 3,
  short_desc: null,
  prerequisites: [
    {
      course_id: 'TOKT1145',
      code: 'TOKT1145',
      name: 'Xác suất',
      kind: 'recommended_order',
      source: 'Thứ tự sư phạm khuyến nghị – không phải tiên quyết chính thức',
    },
  ],
  equivalents: [{ course_id: 'E1', code: 'EP17.CNTT1140', name: 'Trí tuệ nhân tạo', source: 'x' }],
  other_careers: [{ id: 'career-data', slug: 'data', name: 'Phân tích dữ liệu' }],
  resources: [],
};

const respond = (body) => () => jsonResponse(200, body);

export function m12Api(role = 'student', extra = {}) {
  return m11Api(role, {
    'GET /api/m12/gallery': respond(galleryBody()),
    'GET /api/m12/requirements/CNTT1140': respond(REQUIREMENT),
    'GET /api/m12/progress/careers/slug/ai': respond(progressBody()),
    ...extra,
  });
}
