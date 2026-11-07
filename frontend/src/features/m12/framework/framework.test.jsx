import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { apiError, jsonResponse, pendingResponse, renderApp } from '../../../test/fakeApi';
import { m12Api, progressBody } from '../testData';

const NOTICE =
  'Chứng nhận hoàn thành bài kiểm tra trên nền tảng bài tập lớn – không phải chứng chỉ của Trường Đại học Kinh tế Quốc dân.';
const CERTIFICATE = {
  code: 'ma-kho-doan-123456789',
  module_id: 'm1',
  student_name: 'Nguyễn Thiện Nhân',
  module_title: 'Cơ sở dữ liệu và SQL',
  correct_count: 9,
  total: 10,
  percent: 90,
  issued_at: '2026-10-10T09:12:00Z',
  valid: true,
  notice: NOTICE,
};

function moduleBody(extra = {}) {
  return {
    id: 'm3',
    order: 3,
    title: 'Cơ sở dữ liệu và SQL',
    objectives: ['Viết truy vấn JOIN 3 bảng.'],
    extra_knowledge: ['N+1 query.'],
    practice: ['Viết migration.'],
    skill_id: 'sk-m3',
    skill_done: false,
    courses_done: 1,
    courses: [
      {
        course_id: 'TIKT1130',
        code: 'TIKT1130',
        name: 'Cơ sở dữ liệu',
        credits: 3,
        requirement_type: 'elective',
        curriculum_group: 'Học phần của lĩnh vực (chọn 4/6)',
        planned_semester: 2,
        status: 'done',
        takeaways: ['Vẽ ERD, chuyển thành bảng.'],
      },
    ],
    quiz: {
      state: 'not_started',
      attempt_count: 0,
      open_attempt_id: null,
      retry_at: null,
      question_count: 15,
      can_review: false,
      certificate: null,
    },
    ...extra,
  };
}

function frameworkBody(module = moduleBody()) {
  return {
    source: 'Nhóm biên soạn',
    modules: [module],
    program_note:
      'Theo CTĐT do Trường công bố (nguồn: courses.neu.edu.vn) – dữ liệu sinh viên là mẫu',
    milestones: [
      {
        name: 'Thực tập sinh',
        projects: ['API quản lý sinh viên'],
        modules: [{ order: 3, title: 'Cơ sở dữ liệu và SQL' }],
        modules_done: 0,
      },
    ],
    electives: {
      suggested: [
        { ...module.courses[0], course_id: 'CNTT1114', code: 'CNTT1114', name: 'Mạng máy tính' },
      ],
      replaced: [
        {
          chosen: { course_id: 'CNTT1174', code: 'CNTT1174', name: 'Đồ họa máy tính' },
          instead_of: { course_id: 'CNTT1159', code: 'CNTT1159', name: 'Quản lý dự án' },
        },
      ],
      allocation: { suggested: { 4: 9, 5: 9, 6: 6, 7: 6 }, curriculum: { 4: 6, 5: 6, 6: 9, 7: 9 } },
    },
  };
}

const QUESTION = {
  id: 'q1',
  order: 1,
  kind: 'code',
  prompt: 'Câu sau trả về gì?',
  code: 'SELECT 1;',
  options: [
    { id: 'a', text: 'Một' },
    { id: 'b', text: 'Hai' },
  ],
  selected_option_ids: [],
};

function openAttempt(extra = {}) {
  return {
    id: 'att1',
    status: 'in_progress',
    module: { id: 'm3', order: 3, title: 'Cơ sở dữ liệu và SQL' },
    attempt_no: 1,
    started_at: '2026-11-07T01:00:00Z',
    deadline_at: '2026-11-07T01:15:00Z',
    remaining_seconds: 900,
    total: 2,
    author_label: 'Câu hỏi do nhóm biên soạn',
    questions: [
      QUESTION,
      { ...QUESTION, id: 'q2', order: 2, kind: 'multi', prompt: 'Chọn các câu đúng', code: null },
    ],
    ...extra,
  };
}

function resultBody(extra = {}) {
  return {
    id: 'att1',
    status: 'submitted',
    module: { id: 'm3', order: 3, title: 'Cơ sở dữ liệu và SQL' },
    attempt_no: 1,
    correct_count: 9,
    total: 10,
    percent: 90,
    pass_percent: 80,
    passed: true,
    auto_submitted: false,
    submitted_at: '2026-11-07T01:10:00Z',
    retry_at: null,
    certificate: CERTIFICATE,
    author_label: 'Câu hỏi do nhóm biên soạn',
    questions: [
      {
        ...QUESTION,
        options: [
          { id: 'a', text: 'Một', is_correct: true },
          { id: 'b', text: 'Hai', is_correct: false },
        ],
        selected_option_ids: ['a'],
        is_correct: true,
        explanation: 'Trả về 1.',
      },
    ],
    ...extra,
  };
}

const CAREER = '/m12/dinh-huong/nghe/ai?tab=framework';

function careerApi(framework, extra = {}) {
  return m12Api('student', {
    'GET /api/m12/progress/careers/slug/ai': () => jsonResponse(200, progressBody()),
    'GET /api/m12/careers/slug/ai/framework': () => jsonResponse(200, framework),
    ...extra,
  });
}

async function openFramework(framework, extra) {
  const fetchMock = careerApi(framework, extra);
  renderApp(CAREER);
  await screen.findByRole('heading', { name: '10 mô-đun năng lực' });
  return fetchMock;
}

describe('tab Khung năng lực', () => {
  it('không có mô-đun thì không có tab', async () => {
    careerApi({ modules: [], milestones: [], electives: null, source: 'Nhóm biên soạn' });
    renderApp('/m12/dinh-huong/nghe/ai');

    await screen.findByRole('tab', { name: 'Lộ trình học' });
    await waitFor(() => expect(screen.queryByRole('tab', { name: 'Khung năng lực' })).toBeNull());
  });

  it('có mô-đun: mốc nghề, môn, phần cần nắm, nhãn nhóm biên soạn, nguồn CTĐT', async () => {
    await openFramework(frameworkBody());

    expect(screen.getByRole('tab', { name: 'Khung năng lực' })).toHaveAttribute(
      'aria-selected',
      'true',
    );
    expect(screen.getByText(/Nhóm biên soạn\. Câu chữ về từng môn/)).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Thực tập sinh' })).toBeInTheDocument();
    expect(screen.getByText('Môn đã đạt: 1/1')).toBeInTheDocument();
    expect(screen.getByText('Phần cần nắm từ môn này cho Backend:')).toBeInTheDocument();
    expect(screen.getByText('Vẽ ERD, chuyển thành bảng.')).toBeInTheDocument();
    expect(
      screen.getByText(/3 TC · Học phần của lĩnh vực \(chọn 4\/6\) · HK 2/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        'Theo CTĐT do Trường công bố (nguồn: courses.neu.edu.vn) – dữ liệu sinh viên là mẫu',
      ),
    ).toBeInTheDocument();
  });

  it('bộ tự chọn đề xuất có môn bị thay và chênh lệch phân bổ', async () => {
    await openFramework(frameworkBody());

    expect(screen.getByText(/CNTT1174 Đồ họa máy tính thay cho/)).toBeInTheDocument();
    expect(
      screen.getByText(
        /bộ đề xuất HK4: 9, HK5: 9, HK6: 6, HK7: 6;\s+PDF ghi HK4: 6, HK5: 6, HK6: 9, HK7: 9/,
      ),
    ).toBeInTheDocument();
  });

  it('bấm Làm bài kiểm tra: mở bài', async () => {
    const fetchMock = await openFramework(frameworkBody(), {
      'POST /api/m12/modules/m3/attempts': () => jsonResponse(201, openAttempt()),
      'GET /api/m12/attempts/att1': () => jsonResponse(200, openAttempt()),
    });

    await userEvent.click(screen.getByRole('button', { name: 'Làm bài kiểm tra' }));

    expect(await screen.findByText(/Câu 1\. Câu sau trả về gì\?/)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalled();
  });

  it('lỗi khi mở bài: hiện thông báo', async () => {
    await openFramework(frameworkBody(), {
      'POST /api/m12/modules/m3/attempts': () =>
        apiError(409, 'QUIZ_COOLDOWN', 'Chưa đến lúc làm lại bài kiểm tra.'),
    });

    await userEvent.click(screen.getByRole('button', { name: 'Làm bài kiểm tra' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Chưa đến lúc');
  });

  it.each([
    ['cooldown', { retry_at: '2026-11-07T02:00:00Z' }, /Chưa đạt, chờ tới lượt làm lại/],
    ['in_progress', { open_attempt_id: 'att1' }, /Đang làm dở/],
    ['retry', { can_review: true }, /Chưa đạt, có thể làm lại/],
  ])('trạng thái %s', async (state, extra, text) => {
    const module = moduleBody({ quiz: { ...moduleBody().quiz, state, ...extra } });
    await openFramework(frameworkBody(module));

    expect(screen.getByText(text)).toBeInTheDocument();
    if (state === 'cooldown') {
      expect(screen.getByRole('button', { name: 'Làm bài kiểm tra' })).toBeDisabled();
    }
    if (state === 'in_progress') {
      expect(screen.getByRole('link', { name: 'Làm tiếp' })).toHaveAttribute(
        'href',
        '/m12/lam-bai/att1',
      );
    }
    if (state === 'retry') {
      expect(screen.getByRole('link', { name: 'Ôn tập' })).toHaveAttribute(
        'href',
        '/m12/on-tap/m3',
      );
    }
  });

  it('đã đạt: có chứng chỉ và Ôn tập, không có nút làm bài', async () => {
    const quiz = {
      ...moduleBody().quiz,
      state: 'passed',
      can_review: true,
      certificate: CERTIFICATE,
    };
    await openFramework(frameworkBody(moduleBody({ quiz })));

    expect(screen.getByRole('link', { name: 'Xem chứng chỉ' })).toHaveAttribute(
      'href',
      `/m12/chung-chi/${CERTIFICATE.code}`,
    );
    expect(screen.getByRole('link', { name: 'Ôn tập' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Làm bài kiểm tra' })).toBeNull();
  });
});

describe('làm bài', () => {
  function attemptApi(extra = {}) {
    return m12Api('student', {
      'GET /api/m12/attempts/att1': () => jsonResponse(200, openAttempt()),
      'PUT /api/m12/attempts/att1/answers/q1': () =>
        jsonResponse(200, { question_id: 'q1', selected_option_ids: ['a'] }),
      'PUT /api/m12/attempts/att1/answers/q2': () =>
        jsonResponse(200, { question_id: 'q2', selected_option_ids: ['a', 'b'] }),
      'POST /api/m12/attempts/att1/submit': () => jsonResponse(200, resultBody()),
      ...extra,
    });
  }

  it('đang tải rồi có câu hỏi, đồng hồ, 1 tiêu đề chính', async () => {
    const pending = pendingResponse();
    attemptApi({ 'GET /api/m12/attempts/att1': pending.handler });
    renderApp('/m12/lam-bai/att1');

    expect(await screen.findByText('Đang tải bài kiểm tra...')).toBeInTheDocument();
    pending.resolve(jsonResponse(200, openAttempt()));

    expect(await screen.findByLabelText('Thời gian còn lại 15:00')).toBeInTheDocument();
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1);
    expect(screen.getByText(/Câu hỏi do nhóm biên soạn/)).toBeInTheDocument();
    expect(screen.getByText('SELECT 1;')).toBeInTheDocument();
  });

  it('chọn đáp án thì lưu, câu nhiều đáp án gửi đủ lựa chọn, nộp rồi hiện giải thích', async () => {
    const fetchMock = attemptApi();
    renderApp('/m12/lam-bai/att1');
    const first = await screen.findByRole('group', { name: /Câu 1/ });
    const second = screen.getByRole('group', { name: /Câu 2/ });

    await userEvent.click(within(first).getByRole('radio', { name: 'Một' }));
    await userEvent.click(within(second).getByRole('checkbox', { name: 'Một' }));
    await userEvent.click(within(second).getByRole('checkbox', { name: 'Hai' }));
    await userEvent.click(within(second).getByRole('checkbox', { name: 'Một' }));

    expect(screen.getByText('Đã trả lời 2/2')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Nộp bài' }));
    const dialog = screen.getByRole('alertdialog');
    await userEvent.click(within(dialog).getByRole('button', { name: 'Nộp bài' }));

    expect(await screen.findByText('9/10 câu đúng (90%)')).toBeInTheDocument();
    expect(screen.getByText(/Trả về 1\./)).toBeInTheDocument();
    expect(screen.getByText('(bạn chọn)', { exact: false })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Xem chứng chỉ' })).toBeInTheDocument();
    const calls = fetchMock.mock.calls.filter(([url]) => url.includes('/answers/q2'));
    expect(JSON.parse(calls.at(-1)[1].body)).toEqual({ option_ids: ['b'] });
  });

  it('hết giờ: tự nộp', async () => {
    const fetchMock = attemptApi({
      'GET /api/m12/attempts/att1': () => jsonResponse(200, openAttempt({ remaining_seconds: 1 })),
      'POST /api/m12/attempts/att1/submit': () =>
        jsonResponse(200, resultBody({ status: 'expired', auto_submitted: true })),
    });
    renderApp('/m12/lam-bai/att1');

    expect(
      await screen.findByText(/Hết giờ: hệ thống tự nộp/, {}, { timeout: 4000 }),
    ).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([url]) => url.endsWith('/submit'))).toBe(true);
  });

  it('lượt đã đóng ở nơi khác: đọc lại kết quả', async () => {
    let reads = 0;
    attemptApi({
      'GET /api/m12/attempts/att1': () => {
        reads += 1;
        return jsonResponse(
          200,
          reads === 1
            ? openAttempt()
            : resultBody({ passed: false, certificate: null, retry_at: '2026-11-07T02:00:00Z' }),
        );
      },
      'POST /api/m12/attempts/att1/submit': () =>
        apiError(409, 'ATTEMPT_CLOSED', 'Lượt làm bài đã kết thúc.'),
    });
    renderApp('/m12/lam-bai/att1');
    await screen.findByRole('group', { name: /Câu 1/ });

    await userEvent.click(screen.getByRole('button', { name: 'Nộp bài' }));
    await userEvent.click(
      within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Nộp bài' }),
    );

    expect(await screen.findByText(/Chưa đạt, cần từ 80%/)).toBeInTheDocument();
    expect(screen.getByText(/Làm lại từ/)).toBeInTheDocument();
  });

  it('nộp lỗi: báo lỗi, giữ nguyên bài', async () => {
    attemptApi({
      'POST /api/m12/attempts/att1/submit': () => apiError(500, 'INTERNAL', 'Lỗi máy chủ.'),
    });
    renderApp('/m12/lam-bai/att1');
    await screen.findByRole('group', { name: /Câu 1/ });

    await userEvent.click(screen.getByRole('button', { name: 'Nộp bài' }));
    await userEvent.click(
      within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Nộp bài' }),
    );

    expect(await screen.findAllByText('Lỗi máy chủ.')).not.toHaveLength(0);
  });

  it('không lưu được đáp án: báo cho người làm', async () => {
    attemptApi({
      'PUT /api/m12/attempts/att1/answers/q1': () => apiError(500, 'INTERNAL', 'Lỗi máy chủ.'),
    });
    renderApp('/m12/lam-bai/att1');
    const first = await screen.findByRole('group', { name: /Câu 1/ });

    await userEvent.click(within(first).getByRole('radio', { name: 'Một' }));

    expect(await screen.findByText(/Không lưu được đáp án/)).toBeInTheDocument();
  });

  it('mở lại lượt đã nộp: hiện kết quả', async () => {
    attemptApi({ 'GET /api/m12/attempts/att1': () => jsonResponse(200, resultBody()) });
    renderApp('/m12/lam-bai/att1');

    expect(await screen.findByText('9/10 câu đúng (90%)')).toBeInTheDocument();
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1);
  });

  it('lỗi tải: có Thử lại và 1 tiêu đề chính', async () => {
    attemptApi({ 'GET /api/m12/attempts/att1': () => apiError(500, 'INTERNAL', 'Lỗi máy chủ.') });
    renderApp('/m12/lam-bai/att1');

    expect(await screen.findByRole('button', { name: 'Thử lại' })).toBeInTheDocument();
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1);
  });
});

describe('dấu mã', () => {
  it('đoạn trong dấu ` thành thẻ code, không còn dấu `', async () => {
    const question = { ...QUESTION, prompt: 'Lệnh `COUNT(*)` đếm gì?', code: null };
    m12Api('student', {
      'GET /api/m12/attempts/att1': () => jsonResponse(200, openAttempt({ questions: [question] })),
    });
    renderApp('/m12/lam-bai/att1');

    const group = await screen.findByRole('group', { name: /Câu 1/ });
    expect(within(group).getByText('COUNT(*)').tagName).toBe('CODE');
    expect(group.textContent).not.toContain('`');
  });
});

describe('ôn tập', () => {
  it('hiện đáp án, giải thích, không chấm', async () => {
    m12Api('student', {
      'GET /api/m12/modules/m3/review': () =>
        jsonResponse(200, {
          module: { id: 'm3', order: 3, title: 'Cơ sở dữ liệu và SQL' },
          author_label: 'Câu hỏi do nhóm biên soạn',
          questions: resultBody().questions,
        }),
    });
    renderApp('/m12/on-tap/m3');

    expect(
      await screen.findByRole('heading', { level: 1, name: /Ôn tập: Cơ sở dữ liệu/ }),
    ).toBeInTheDocument();
    expect(screen.getByText(/không chấm điểm/)).toBeInTheDocument();
    expect(screen.getByText(/Trả về 1\./)).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'Đáp án đúng' })).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'Đáp án sai' })).toBeInTheDocument();
  });
});

describe('chứng chỉ', () => {
  it('danh sách của tôi', async () => {
    m12Api('student', {
      'GET /api/m12/certificates': () =>
        jsonResponse(200, { items: [CERTIFICATE], notice: NOTICE }),
    });
    renderApp('/m12/chung-chi');

    expect(
      await screen.findByRole('heading', { level: 2, name: 'Cơ sở dữ liệu và SQL' }),
    ).toBeInTheDocument();
    expect(screen.getByText(NOTICE)).toBeInTheDocument();
  });

  it('chưa có chứng chỉ: trạng thái rỗng', async () => {
    m12Api('student', {
      'GET /api/m12/certificates': () => jsonResponse(200, { items: [], notice: NOTICE }),
    });
    renderApp('/m12/chung-chi');

    expect(await screen.findByText(/Chưa có chứng chỉ nào/)).toBeInTheDocument();
  });

  it('cố vấn chưa chọn sinh viên: không gọi API', async () => {
    m12Api('advisor');
    renderApp('/m12/chung-chi');

    expect(await screen.findByText('Chưa chọn sinh viên')).toBeInTheDocument();
  });

  it('trang chứng chỉ có tên, điểm, mã, QR, câu miễn trừ, không có ảnh logo', async () => {
    m12Api('student', {
      [`GET /api/m12/certificates/${CERTIFICATE.code}`]: () => jsonResponse(200, CERTIFICATE),
    });
    renderApp(`/m12/chung-chi/${CERTIFICATE.code}`);

    const name = await screen.findByRole('heading', { name: 'Nguyễn Thiện Nhân' });
    const certificate = name.closest('article');
    expect(certificate).toHaveTextContent('9/10 (90%)');
    expect(certificate).toHaveTextContent(CERTIFICATE.code);
    expect(certificate).toHaveTextContent(NOTICE);
    expect(certificate).toHaveTextContent(`/xac-thuc/${CERTIFICATE.code}`);
    expect(
      within(certificate).getByRole('img', { name: 'Mã QR tới trang xác thực' }),
    ).toBeInTheDocument();
    expect(certificate.querySelector('image, img')).toBeNull();
    expect(screen.getByRole('button', { name: 'In hoặc lưu PDF' })).toBeInTheDocument();
  });

  it('bấm in gọi hộp thoại in của trình duyệt', async () => {
    const printed = [];
    window.print = () => printed.push(1);
    m12Api('student', {
      [`GET /api/m12/certificates/${CERTIFICATE.code}`]: () => jsonResponse(200, CERTIFICATE),
    });
    renderApp(`/m12/chung-chi/${CERTIFICATE.code}`);
    await screen.findByRole('heading', { name: 'Nguyễn Thiện Nhân' });

    await userEvent.click(screen.getByRole('button', { name: 'In hoặc lưu PDF' }));

    expect(printed).toEqual([1]);
  });
});

describe('xác thực công khai', () => {
  const VERIFY = `GET /api/public/certificates/abc`;

  it('chưa đăng nhập vẫn xem được, chỉ có tên, mô-đun, ngày cấp, hiệu lực', async () => {
    m12Api('student', {
      'GET /api/auth/me': () => apiError(401, 'UNAUTHORIZED', 'Chưa đăng nhập.'),
      [VERIFY]: () =>
        jsonResponse(200, {
          student_name: 'Nguyễn Thiện Nhân',
          module_title: 'Cơ sở dữ liệu và SQL',
          issued_at: '2026-10-10T09:12:00Z',
          valid: true,
          notice: NOTICE,
        }),
    });
    renderApp('/xac-thuc/abc');

    expect(await screen.findByText('Còn hiệu lực')).toBeInTheDocument();
    expect(screen.getByText('Nguyễn Thiện Nhân')).toBeInTheDocument();
    expect(screen.getByText(NOTICE)).toBeInTheDocument();
    expect(screen.getByText('Dữ liệu mẫu')).toBeInTheDocument();
    expect(screen.getByText(/không phải hệ thống chính thức/)).toBeInTheDocument();
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1);
    expect(screen.queryByRole('img')).toBeNull();
  });

  it('đã thu hồi', async () => {
    m12Api('student', {
      [VERIFY]: () =>
        jsonResponse(200, {
          student_name: 'A',
          module_title: 'B',
          issued_at: '2026-10-10T09:12:00Z',
          valid: false,
          notice: NOTICE,
        }),
    });
    renderApp('/xac-thuc/abc');

    expect(await screen.findByText('Đã thu hồi')).toBeInTheDocument();
  });

  it('mã sai: báo không tìm thấy', async () => {
    m12Api('student', { [VERIFY]: () => apiError(404, 'NOT_FOUND', 'Không tìm thấy.') });
    renderApp('/xac-thuc/abc');

    expect(await screen.findByText('Không tìm thấy chứng chỉ với mã này')).toBeInTheDocument();
  });
});
