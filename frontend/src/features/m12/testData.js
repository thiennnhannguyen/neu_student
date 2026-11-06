import { jsonResponse } from '../../test/fakeApi';
import { m11Api } from '../m11/testData';

export const DISCLAIMER = 'Tỷ lệ này không phản ánh khả năng được tuyển dụng';

export function progress(numerator, denominator, label = 'học phần') {
  return {
    numerator,
    denominator,
    value: denominator ? '0.2222' : null,
    formula: `${numerator}/${denominator} ${label}`,
  };
}

const SKILL_LABEL = 'kỹ năng & dự án';

export function career(id, name, field = 'Dữ liệu và AI (mẫu)') {
  return { id, slug: id, name, field };
}

export const AI = career('career-ai_engineer', 'AI Engineer (mẫu)');
export const ANALYST = career('career-data_analyst', 'Data Analyst (mẫu)');
export const ML = career('career-ml_engineer', 'Machine Learning Engineer (mẫu)');
export const BACKEND = career('career-backend', 'Backend Developer (mẫu)', 'Phần mềm (mẫu)');

export function relatedItem(item, shared = 9, union = 14, done = 1, total = 8) {
  return {
    career: item,
    closeness: { numerator: shared, denominator: union, value: '0.6429' },
    course_progress: progress(done, total),
    skill_progress: progress(1, 3, SKILL_LABEL),
  };
}

export const MY_CAREERS = {
  student_id: 'SV01',
  primary: {
    career: AI,
    course_progress: progress(2, 9),
    skill_progress: progress(1, 3, SKILL_LABEL),
    outside_curriculum_count: 4,
  },
  related: [relatedItem(ML), relatedItem(ANALYST, 6, 15, 1, 7), relatedItem(BACKEND, 3, 18, 2, 8)],
  disclaimer: DISCLAIMER,
};

export const NO_PRIMARY = {
  student_id: 'SV01',
  primary: null,
  related: [],
  disclaimer: DISCLAIMER,
};

export function relatedBody(items = MY_CAREERS.related, extra = {}) {
  return {
    items,
    page: 1,
    page_size: 12,
    total: items.length,
    student_id: 'SV01',
    sort: 'closeness',
    primary_career: AI,
    fields: ['Dữ liệu và AI (mẫu)', 'Phần mềm (mẫu)'],
    disclaimer: DISCLAIMER,
    data_warnings: [],
    ...extra,
  };
}

export function child(id, title, status, extra = {}) {
  return {
    id,
    kind: 'course',
    title,
    short_desc: `Mô tả ${title}`,
    course_id: id,
    code: id,
    skill_id: null,
    weight: '1.00',
    status,
    outside_curriculum: false,
    via_course: null,
    ...extra,
  };
}

export const NODES = [
  {
    id: 'n1',
    kind: 'group',
    title: 'Nền tảng (mẫu)',
    short_desc: 'Mô tả nhóm',
    order: 1,
    children: [
      child('CNT102', 'Lập trình Python (mẫu)', 'done'),
      child('CNT202', 'Giải thuật (mẫu)', 'done_via_equivalency', {
        via_course: { course_id: 'CNT201', code: 'CNT201' },
      }),
      child('MAU105', 'Tiếng Anh (mẫu)', 'exempt'),
      child('MAU102', 'Đại số (mẫu)', 'in_progress'),
      child('KDL301', 'Học máy (mẫu)', 'failed', { outside_curriculum: true }),
      child('course-cd-a', 'Chuyên đề (mẫu)', 'not_started', { code: null }),
    ],
  },
  {
    id: 'n2',
    kind: 'group',
    title: 'Thực hành (mẫu)',
    short_desc: null,
    order: 2,
    children: [
      child('sk-git', 'Git (mẫu)', 'done', { kind: 'skill', course_id: null, code: null }),
      child('sk-eval', 'Đánh giá mô hình (mẫu)', 'not_started', {
        kind: 'skill',
        course_id: null,
        code: null,
      }),
      child('prj-data', 'Dự án dữ liệu (mẫu)', 'pending', {
        kind: 'project',
        course_id: null,
        code: null,
      }),
    ],
  },
];

export function progressBody(extra = {}) {
  return {
    student_id: 'SV01',
    career: AI,
    version: { id: 'cv', version: 1, published_at: '2026-08-20T09:00:00Z' },
    is_primary: true,
    course_progress: progress(2, 9),
    skill_progress: progress(1, 3, SKILL_LABEL),
    disclaimer: DISCLAIMER,
    outside_curriculum_count: 4,
    computed_at: '2026-11-07T03:00:00Z',
    data_warnings: [],
    nodes: NODES,
    ...extra,
  };
}

export const REQUIREMENT = {
  id: 'CNT202',
  code: 'CNT202',
  credits: 3,
  short_desc: 'Môn thuật toán của CTĐT mới.',
  prerequisites: [{ course_id: 'CNT102', code: 'CNT102', name: 'Lập trình Python (mẫu)' }],
  other_careers: [{ id: 'career-backend', name: 'Backend Developer (mẫu)' }],
  resources: [],
};

const respond = (body) => () => jsonResponse(200, body);

export function m12Api(role = 'student', extra = {}) {
  return m11Api(role, {
    'GET /api/m12/my-careers': respond(MY_CAREERS),
    'GET /api/m12/related': respond(relatedBody()),
    'GET /api/m12/requirements/CNT202': respond(REQUIREMENT),
    [`GET /api/m12/progress/careers/${AI.id}`]: respond(progressBody()),
    'GET /api/m12/careers': respond({
      items: [AI, ANALYST],
      page: 1,
      page_size: 12,
      total: 2,
    }),
    ...extra,
  });
}
