import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { apiError, jsonResponse, pendingResponse, renderApp } from '../../../test/fakeApi';
import { callsTo } from '../../m11/testData';
import { AI, BACKEND, galleryBody, galleryItem, m12Api, progressBody, progress } from '../testData';

const PAGE = '/m12/dinh-huong/nghe/backend/gioi-thieu';
const LANDING_API = 'GET /api/m12/careers/slug/backend/landing';
const PROGRESS_API = 'GET /api/m12/progress/careers/slug/backend';
const FRAMEWORK_API = 'GET /api/m12/careers/slug/backend/framework';
const CERTIFICATES_API = 'GET /api/m12/certificates';
const CAVEAT =
  'Mức thu nhập thực tế phụ thuộc năng lực, nơi làm việc và khu vực; bảng này không phải mức cam kết.';
const NOTE =
  'Số liệu tham khảo từ báo cáo ITviec 2023–2024 (bài đăng 29/08/2024), có thể đã thay đổi. Bài gốc ghi đơn vị chưa thống nhất; nhóm hiểu là lương tháng.';
const WORKDAY_NOTE =
  'Các việc tiêu biểu tổng hợp từ khung năng lực của nền tảng, không phải lịch làm việc của một người cụ thể.';
const HEADINGS = [
  'Một ngày làm việc',
  'Backend khác Frontend, Full-stack, DevOps ở đâu',
  'Kỹ năng cần có',
  'Học ở NEU (KHMT)',
  'Sản phẩm nên có khi xin thực tập',
  'Thu nhập tham khảo',
  'Câu hỏi thường gặp',
];

const BACKEND_PROFILE = { ...BACKEND, has_landing: true, objective: 'Thiết kế API' };
const MODULES = Array.from({ length: 10 }, (_, index) => ({
  id: `module-${index + 1}`,
  order: index + 1,
  title: `Mô-đun mẫu ${index + 1}`,
  summary: `Mục tiêu đầu tiên ${index + 1}.`,
}));

function landingBody(landing = {}) {
  return {
    career: BACKEND_PROFILE,
    landing: {
      id: 'landing-1',
      version: 1,
      updated_at: '2026-11-09T07:00:00Z',
      is_mock: true,
      program: { id: 'prog-khmt', code: 'KHMT', name: 'Khoa học máy tính' },
      modules: MODULES,
      stages: [
        {
          id: 'node-1',
          order: 1,
          name: 'Logic + dữ liệu',
          deliverable: 'Viết chương trình CRUD.',
          courses: [
            {
              course_id: 'CNTT1128',
              code: 'CNTT1128',
              name: 'Cơ sở lập trình',
              credits: 3,
              requirement_type: 'elective',
              type_label: 'TC',
              planned_semester: 2,
              purpose: null,
            },
          ],
        },
        { id: 'node-5', order: 5, name: 'Ứng tuyển', deliverable: 'README rõ.', courses: [] },
      ],
      sources: [
        { id: 'CN-02', title: 'Cẩm nang', section: 'Nghề 02' },
        { id: 'KNL-m3', title: 'Khung năng lực', section: 'Mô-đun 3' },
      ],
      content: {
        intro: {
          summary: 'Lập trình viên Backend viết phần chạy trên máy chủ.',
          sources: ['CN-02'],
        },
        workday: {
          title: 'Một ngày làm việc',
          note: WORKDAY_NOTE,
          items: [
            { text: 'Viết migration (tệp ghi lại thay đổi cấu trúc bảng).', sources: ['KNL-m3'] },
            { text: 'Viết test API cho 401 (chưa đăng nhập).', sources: ['KNL-m3', 'CN-02'] },
          ],
        },
        comparison: {
          title: 'Backend khác Frontend, Full-stack, DevOps ở đâu',
          careers: [
            { slug: 'backend', name: 'Backend', name_en: 'Backend Developer' },
            { slug: 'frontend', name: 'Frontend', name_en: 'Frontend Developer' },
            { slug: 'fullstack', name: 'Full-stack', name_en: 'Full-stack Developer' },
            { slug: 'devops', name: 'DevOps', name_en: 'DevOps Engineer' },
          ],
          rows: [{ label: 'Ngành nên ưu tiên', cells: ['A', 'B', 'C', 'D'], sources: ['CN-02'] }],
        },
        modules: { title: 'Kỹ năng cần có', intro: '10 mô-đun.' },
        courses: {
          title: 'Học ở NEU',
          intro: 'BB là môn bắt buộc.',
          semester_note: 'HK là học kỳ phân bổ theo CTĐT.',
          other_programs_note: 'Ngành CNTT, KTPM, ATTT sẽ cập nhật sau.',
          sources: ['CN-02'],
        },
        projects: {
          title: 'Sản phẩm nên có khi xin thực tập',
          items: [
            {
              level: 'Thực tập sinh',
              name: 'API quản lý sinh viên',
              summary: 'CRUD.',
              module_orders: [3],
              modules: [{ order: 3, title: 'Mô-đun mẫu 3' }],
              sources: ['CN-02'],
            },
          ],
        },
        income: {
          title: 'Thu nhập tham khảo',
          caveat: CAVEAT,
          experience_label: 'Kinh nghiệm',
          amount_label: 'Thu nhập (triệu đồng/tháng)',
          rows: [
            { experience: 'Dưới 1 năm', amount: '10' },
            { experience: 'Trên 8 năm', amount: '60,5' },
          ],
          levels_title: 'Lộ trình cấp bậc',
          levels: ['Junior Backend Developer', 'Backend Architect'],
          note: NOTE,
          source: {
            publisher: 'ITviec Blog',
            title: 'Backend Developer là gì: Mô tả công việc và lộ trình sự nghiệp',
            author: 'Linh Trao',
            published: '29/08/2024',
            year: '2024',
            url: 'https://itviec.com/blog/backend-developer-la-gi/',
          },
        },
        faq: {
          title: 'Câu hỏi thường gặp',
          items: [{ question: 'Sinh viên KHMT có hợp không?', answer: 'Có.', sources: ['CN-02'] }],
        },
        progress: { title: 'Bạn đang ở đâu' },
        actions: { title: 'Bước tiếp theo' },
      },
      ...landing,
    },
  };
}

function quiz(state) {
  return { state, retry_at: null, certificate: null, can_review: false };
}

const FRAMEWORK = {
  modules: MODULES.map((module) => ({
    ...module,
    quiz: quiz(module.order <= 2 ? 'passed' : 'not_started'),
  })),
};
const CERTIFICATES = {
  items: [
    { code: 'C1', module_id: 'module-1', valid: true },
    { code: 'C2', module_id: 'module-2', valid: true },
    { code: 'X', module_id: 'module-khac', valid: true },
  ],
};

function studentApi(extra = {}) {
  return m12Api('student', {
    [LANDING_API]: () => jsonResponse(200, landingBody()),
    [PROGRESS_API]: () =>
      jsonResponse(
        200,
        progressBody({ career: BACKEND, is_primary: false, course_progress: progress(4, 11) }),
      ),
    [FRAMEWORK_API]: () => jsonResponse(200, FRAMEWORK),
    [CERTIFICATES_API]: () => jsonResponse(200, CERTIFICATES),
    ...extra,
  });
}

describe('CR-14: trang giới thiệu nghề', () => {
  it('sinh viên: đủ các phần theo thứ tự, có mục lục và phần Bạn đang ở đâu', async () => {
    studentApi();
    renderApp(PAGE);

    expect(
      await screen.findByRole('heading', { level: 1, name: BACKEND.display_name }),
    ).toBeInTheDocument();
    const headings = screen.getAllByRole('heading', { level: 2 }).map((node) => node.textContent);
    expect(headings).toEqual([...HEADINGS, 'Bạn đang ở đâu', 'Bước tiếp theo']);
    const toc = screen.getByRole('navigation', { name: 'Mục lục trang' });
    expect(within(toc).getByRole('link', { name: 'Bạn đang ở đâu' })).toHaveAttribute(
      'href',
      '#ban-o-dau',
    );
    expect(within(toc).getAllByRole('link')).toHaveLength(10);
  });

  it('phần Bạn đang ở đâu dùng số của API, mô-đun tiếp theo là mô-đun đầu tiên chưa đạt', async () => {
    studentApi();
    renderApp(PAGE);

    const section = await screen.findByRole('region', { name: 'Bạn đang ở đâu' });
    expect(await within(section).findByText('Học phần: 4/11 môn đã đạt')).toBeInTheDocument();
    expect(
      await within(section).findByText(
        'Mô-đun tiếp theo nên làm bài kiểm tra: Mô-đun 3 – Mô-đun mẫu 3',
      ),
    ).toBeInTheDocument();
    // Chứng chỉ của mô-đun nghề khác không tính.
    expect(within(section).getByText('Chứng chỉ mô-đun đã có: 2/10')).toBeInTheDocument();
    expect(within(section).getByText(/không phản ánh khả năng được tuyển dụng/)).toBeVisible();
  });

  it('3 nút cuối trang của sinh viên chưa đặt nghề này làm mục tiêu', async () => {
    studentApi();
    renderApp(PAGE);

    const actions = await screen.findByRole('region', { name: 'Bước tiếp theo' });
    expect(
      await within(actions).findByRole('button', { name: 'Đặt làm mục tiêu' }),
    ).toBeInTheDocument();
    expect(within(actions).getByRole('link', { name: 'Xem lộ trình học' })).toHaveAttribute(
      'href',
      '/m12/dinh-huong/nghe/backend?tab=roadmap',
    );
    expect(
      await within(actions).findByRole('link', { name: 'Làm bài kiểm tra mô-đun tiếp theo' }),
    ).toHaveAttribute('href', '/m12/dinh-huong/nghe/backend?tab=framework#module-3');
  });

  it('nghề đã là mục tiêu chính thì không có nút Đặt làm mục tiêu', async () => {
    studentApi({
      [PROGRESS_API]: () => jsonResponse(200, progressBody({ career: BACKEND, is_primary: true })),
    });
    renderApp(PAGE);

    const section = await screen.findByRole('region', { name: 'Bạn đang ở đâu' });
    await within(section).findByText(/Học phần:/);
    expect(screen.queryByRole('button', { name: 'Đặt làm mục tiêu' })).toBeNull();
  });

  it('cố vấn: không có phần cá nhân hóa, không gọi API tiến độ, liên kết giữ sinh viên đang xem', async () => {
    const fetchMock = m12Api('advisor', {
      [LANDING_API]: () => jsonResponse(200, landingBody()),
    });
    renderApp(`${PAGE}?student=SV02`);

    await screen.findByRole('heading', { level: 1, name: BACKEND.display_name });
    expect(screen.queryByRole('region', { name: 'Bạn đang ở đâu' })).toBeNull();
    expect(screen.queryByRole('link', { name: 'Bạn đang ở đâu' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Đặt làm mục tiêu' })).toBeNull();
    expect(screen.queryByRole('link', { name: 'Làm bài kiểm tra mô-đun tiếp theo' })).toBeNull();
    expect(screen.getByRole('link', { name: 'Xem lộ trình học' })).toHaveAttribute(
      'href',
      '/m12/dinh-huong/nghe/backend?student=SV02&tab=roadmap',
    );
    expect(screen.getByRole('link', { name: 'Quay lại trang nghề' })).toHaveAttribute(
      'href',
      '/m12/dinh-huong/nghe/backend?student=SV02',
    );
    expect(callsTo(fetchMock, '/api/m12/progress/careers/slug/backend')).toHaveLength(0);
    expect(callsTo(fetchMock, '/api/m12/certificates')).toHaveLength(0);
  });

  it('nhân viên hỗ trợ xem được nội dung, quay lại trang chủ, không có liên kết sang trang nghề', async () => {
    m12Api('support_staff', { [LANDING_API]: () => jsonResponse(200, landingBody()) });
    renderApp(PAGE);

    await screen.findByRole('heading', { level: 1, name: BACKEND.display_name });
    expect(screen.getByRole('link', { name: 'Về trang chủ' })).toHaveAttribute('href', '/');
    expect(screen.queryByRole('link', { name: 'Xem lộ trình học' })).toBeNull();
    expect(screen.queryByRole('link', { name: 'Mô-đun mẫu 1' })).toBeNull();
    expect(screen.getByText('Mô-đun mẫu 1')).toBeInTheDocument();
  });

  it('nghề chưa có nội dung: trang Đang cập nhật', async () => {
    m12Api('student', {
      [LANDING_API]: () => jsonResponse(200, { career: BACKEND, landing: null }),
    });
    renderApp(PAGE);

    expect(await screen.findByRole('heading', { name: 'Đang cập nhật' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1, name: BACKEND.display_name })).toBeVisible();
    expect(screen.queryByRole('heading', { name: 'Một ngày làm việc' })).toBeNull();
  });

  it('slug không có: Không tìm thấy nghề', async () => {
    m12Api('student', { [LANDING_API]: () => apiError(404, 'NOT_FOUND', 'Không tìm thấy') });
    renderApp(PAGE);

    expect(
      await screen.findByRole('heading', { level: 1, name: 'Không tìm thấy nghề' }),
    ).toBeInTheDocument();
  });

  it('đang tải rồi lỗi máy chủ, bấm Thử lại thì tải lại', async () => {
    const pending = pendingResponse();
    let calls = 0;
    m12Api('student', {
      [LANDING_API]: () => {
        calls += 1;
        return calls === 1 ? pending.handler() : jsonResponse(200, landingBody());
      },
      [PROGRESS_API]: () => jsonResponse(200, progressBody({ career: BACKEND })),
      [FRAMEWORK_API]: () => jsonResponse(200, FRAMEWORK),
      [CERTIFICATES_API]: () => jsonResponse(200, CERTIFICATES),
    });
    renderApp(PAGE);

    expect(await screen.findByText('Đang tải trang giới thiệu nghề...')).toBeInTheDocument();
    pending.resolve(apiError(500, 'INTERNAL', 'Lỗi máy chủ'));
    expect(
      await screen.findByRole('heading', { name: 'Không tải được trang giới thiệu nghề' }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Thử lại/ }));
    expect(
      await screen.findByRole('heading', { level: 1, name: BACKEND.display_name }),
    ).toBeInTheDocument();
  });

  it('khối thu nhập: câu lưu ý nằm trên bảng, chú thích dưới bảng, liên kết nguồn mở tab mới an toàn', async () => {
    studentApi();
    renderApp(PAGE);

    const section = await screen.findByRole('region', { name: 'Thu nhập tham khảo' });
    const caveat = within(section).getByText(CAVEAT);
    const table = within(section).getByRole('table');
    const note = within(section).getByText(NOTE);
    expect(
      caveat.compareDocumentPosition(table) & window.Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(
      table.compareDocumentPosition(note) & window.Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(within(table).getByRole('cell', { name: '60,5' })).toBeInTheDocument();
    const link = within(section).getByRole('link', { name: /Backend Developer là gì/ });
    expect(link).toHaveAttribute('href', 'https://itviec.com/blog/backend-developer-la-gi/');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    expect(within(section).getByRole('heading', { name: 'Lộ trình cấp bậc' })).toBeVisible();
  });

  it('không hiện mã nguồn của từng ý và không có mục Nguồn; chỉ còn nguồn ITviec ở khối thu nhập', async () => {
    studentApi();
    renderApp(PAGE);

    const section = await screen.findByRole('region', { name: 'Một ngày làm việc' });
    expect(within(section).getByText(WORKDAY_NOTE)).toBeVisible();
    expect(within(section).getAllByRole('listitem')).toHaveLength(2);
    expect(screen.queryByRole('link', { name: 'KNL-m3' })).toBeNull();
    expect(screen.queryByRole('heading', { name: 'Nguồn' })).toBeNull();
    expect(screen.getAllByText(/^Nguồn:/)).toHaveLength(1);
    expect(
      within(screen.getByRole('region', { name: 'Thu nhập tham khảo' })).getByText(/^Nguồn:/),
    ).toBeInTheDocument();
  });

  it('môn học có mã, BB/TC, HK; giai đoạn không có môn thì ghi rõ; có ghi chú ngành khác', async () => {
    studentApi();
    renderApp(PAGE);

    const section = await screen.findByRole('region', { name: 'Học ở NEU (KHMT)' });
    expect(within(section).getByText('CNTT1128')).toBeInTheDocument();
    expect(within(section).getByText('TC')).toHaveAttribute('title', 'Tự chọn');
    expect(within(section).getByText(/HK 2 · 3 tín chỉ/)).toBeInTheDocument();
    expect(
      within(section).getByText('Giai đoạn này là dự án, không có môn học riêng.'),
    ).toBeInTheDocument();
    expect(within(section).getByText('Ngành CNTT, KTPM, ATTT sẽ cập nhật sau.')).toBeVisible();
  });

  it('mô-đun liên kết sang tab Khung năng lực đúng mô-đun', async () => {
    studentApi();
    renderApp(PAGE);

    const section = await screen.findByRole('region', { name: 'Kỹ năng cần có' });
    expect(within(section).getAllByRole('listitem')).toHaveLength(10);
    expect(within(section).getByRole('link', { name: 'Mô-đun mẫu 4' })).toHaveAttribute(
      'href',
      '/m12/dinh-huong/nghe/backend?tab=framework#module-4',
    );
  });

  it('bảng so sánh cuộn ngang được bằng bàn phím', async () => {
    studentApi();
    renderApp(PAGE);

    const region = await screen.findByRole('region', {
      name: 'Backend khác Frontend, Full-stack, DevOps ở đâu',
    });
    const scroller = within(region).getByRole('region', { name: 'Bảng so sánh, cuộn ngang được' });
    expect(scroller).toHaveAttribute('tabindex', '0');
    expect(within(scroller).getAllByRole('columnheader')).toHaveLength(5);
  });

  it('nút Quay lại về trang nghề', async () => {
    studentApi();
    renderApp(PAGE);

    fireEvent.click(await screen.findByRole('link', { name: 'Quay lại trang nghề' }));
    await waitFor(() =>
      expect(screen.getByTestId('path')).toHaveTextContent('/m12/dinh-huong/nghe/backend'),
    );
  });
});

describe('CR-14: ảnh và phần Backend nằm ở đâu', () => {
  const IMAGE = { src: '/images/landing_page/may_chu_backend.jpg', alt: 'Minh họa máy chủ' };
  const OVERVIEW = {
    title: 'Backend nằm ở đâu trong một ứng dụng',
    text: 'Giao diện gửi yêu cầu qua API.',
    image: { src: '/images/landing_page/kien_truc_backend.jpg', alt: 'Sơ đồ luồng yêu cầu' },
    caption: 'Luồng một yêu cầu đi qua backend.',
    sources: ['CN-02'],
  };

  function withImages() {
    const body = landingBody();
    body.landing.content = {
      ...body.landing.content,
      intro: { ...body.landing.content.intro, image: IMAGE },
      overview: OVERVIEW,
    };
    return body;
  }

  it('ảnh đầu bài và sơ đồ có alt, chú thích; phần mới có trong mục lục', async () => {
    studentApi({ [LANDING_API]: () => jsonResponse(200, withImages()) });
    renderApp(PAGE);

    expect(await screen.findByRole('img', { name: 'Minh họa máy chủ' })).toHaveAttribute(
      'src',
      IMAGE.src,
    );
    const section = screen.getByRole('region', { name: OVERVIEW.title });
    expect(within(section).getByRole('img', { name: 'Sơ đồ luồng yêu cầu' })).toBeVisible();
    expect(within(section).getByText(OVERVIEW.caption).tagName).toBe('FIGCAPTION');
    const toc = screen.getByRole('navigation', { name: 'Mục lục trang' });
    expect(within(toc).getByRole('link', { name: 'Backend nằm ở đâu' })).toHaveAttribute(
      'href',
      '#tong-quan',
    );
  });

  it('chưa có ảnh thì dùng hình minh họa nghề, không có phần sơ đồ', async () => {
    studentApi();
    renderApp(PAGE);

    await screen.findByRole('heading', { level: 1, name: BACKEND.display_name });
    expect(document.querySelector('.landing-figure--hero .career-illustration')).not.toBeNull();
    expect(screen.queryByRole('link', { name: 'Backend nằm ở đâu' })).toBeNull();
  });
});

describe('CR-14: điểm vào trang giới thiệu', () => {
  const DETAIL = 'GET /api/m12/progress/careers/slug/ai';

  it('trang nghề có nội dung: nút Giới thiệu nghề cạnh các nút ở đầu trang', async () => {
    m12Api('student', {
      [DETAIL]: () =>
        jsonResponse(
          200,
          progressBody({ profile: { ...progressBody().profile, has_landing: true } }),
        ),
    });
    renderApp('/m12/dinh-huong/nghe/ai');

    const hero = await screen.findByRole('region', { name: AI.display_name });
    expect(within(hero).getByRole('link', { name: 'Giới thiệu nghề' })).toHaveAttribute(
      'href',
      '/m12/dinh-huong/nghe/ai/gioi-thieu',
    );
    expect(within(hero).getByRole('link', { name: 'Xem lộ trình theo học kỳ' })).toBeVisible();
  });

  it('trang nghề chưa có nội dung: không có nút', async () => {
    m12Api('student', {
      [DETAIL]: () =>
        jsonResponse(
          200,
          progressBody({ profile: { ...progressBody().profile, has_landing: false } }),
        ),
    });
    renderApp('/m12/dinh-huong/nghe/ai');

    const hero = await screen.findByRole('region', { name: AI.display_name });
    expect(within(hero).queryByRole('link', { name: 'Giới thiệu nghề' })).toBeNull();
  });

  it('lưới nghề: chỉ thẻ có nội dung có liên kết nhỏ, nằm ngoài liên kết của thẻ', async () => {
    m12Api('student', {
      'GET /api/m12/gallery': () =>
        jsonResponse(
          200,
          galleryBody([
            galleryItem({ ...BACKEND, has_landing: true }),
            galleryItem({ ...AI, has_landing: false }),
          ]),
        ),
    });
    renderApp('/m12/dinh-huong');

    const links = await screen.findAllByRole('link', { name: /^Giới thiệu nghề/ });
    expect(links).toHaveLength(1);
    expect(links[0]).toHaveAccessibleName(`Giới thiệu nghề ${BACKEND.display_name}`);
    expect(links[0]).toHaveAttribute('href', '/m12/dinh-huong/nghe/backend/gioi-thieu');
    expect(links[0].closest('.career-card')).toBeNull();
  });
});
