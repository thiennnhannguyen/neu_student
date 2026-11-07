import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { apiError, jsonResponse, renderApp } from '../../test/fakeApi';
import { formatDateTime } from '../m11/format';
import { callsTo, m11Api } from '../m11/testData';
import { m12Api, NODES, progressBody } from './testData';

const PDF = new window.File(['%PDF-1.7'], 'bai-lam.pdf', { type: 'application/pdf' });

function sentBody(fetchMock, path) {
  const call = fetchMock.mock.calls.find(([url, options]) => url === path && options?.body);
  return call[1].body;
}

// --- Minh chứng: nộp ---

const SKILL = {
  id: 'r1',
  kind: 'skill',
  title: 'Viết API',
  skill_id: 'sk-api',
  status: 'not_started',
};

function detailWith(child) {
  return progressBody({ nodes: [{ ...NODES[0], children: [child] }] });
}

function evidence(extra = {}) {
  return {
    id: 'e1',
    student_id: 'DEMO05',
    skill: { id: 'sk-api', name: 'Viết API', kind: 'skill' },
    description: 'Kho mã',
    link: null,
    status: 'pending',
    review_note: null,
    attachments: [],
    ...extra,
  };
}

async function openSkillTab(user, child = SKILL, extra = {}, role = 'student', query = '') {
  const fetchMock = m12Api(role, {
    'GET /api/m12/progress/careers/slug/ai': () => jsonResponse(200, detailWith(child)),
    'GET /api/m12/evidences': () => jsonResponse(200, { student_id: 'DEMO05', items: [] }),
    ...extra,
  });
  renderApp(`/m12/dinh-huong/nghe/ai${query}`);
  await user.click(await screen.findByRole('tab', { name: 'Kỹ năng & dự án' }));
  return fetchMock;
}

describe('nộp minh chứng', () => {
  it('kỹ năng chưa có minh chứng có nút Nộp, form đủ trường, gửi multipart đúng dữ liệu', async () => {
    const user = userEvent.setup();
    const fetchMock = await openSkillTab(user, SKILL, {
      'POST /api/m12/evidences': () => jsonResponse(201, evidence()),
    });

    await user.click(screen.getByRole('button', { name: 'Nộp minh chứng' }));
    const panel = await screen.findByRole('dialog', { name: 'Viết API' });
    await user.type(await within(panel).findByLabelText('Mô tả'), 'Kho mã nhóm');
    await user.type(within(panel).getByLabelText(/Liên kết/), 'https://example.test/kho');
    await user.upload(within(panel).getByLabelText(/Tệp đính kèm/), PDF);
    await user.click(within(panel).getByRole('button', { name: 'Nộp minh chứng' }));

    await waitFor(() => expect(callsTo(fetchMock, '/api/m12/evidences').length).toBeGreaterThan(1));
    const body = sentBody(fetchMock, '/api/m12/evidences');
    expect(body.get('skill_id')).toBe('sk-api');
    expect(body.get('description')).toBe('Kho mã nhóm');
    expect(body.get('link')).toBe('https://example.test/kho');
    expect(body.get('files').name).toBe('bai-lam.pdf');
    const call = fetchMock.mock.calls.find(([, options]) => options?.body === body);
    expect(call[1].headers['Content-Type']).toBeUndefined();
    expect(call[1].headers['X-Requested-With']).toBe('fetch');
  });

  it('mô tả giới hạn 1.000 ký tự, tệp chỉ nhận đúng loại', async () => {
    const user = userEvent.setup();
    await openSkillTab(user);

    await user.click(screen.getByRole('button', { name: 'Nộp minh chứng' }));
    const panel = await screen.findByRole('dialog');
    const description = await within(panel).findByLabelText('Mô tả');

    expect(description).toHaveAttribute('maxlength', '1000');
    expect(within(panel).getByLabelText(/Tệp đính kèm/)).toHaveAttribute(
      'accept',
      '.pdf,.png,.jpg,.jpeg,.docx',
    );
  });

  it('tệp sai bị từ chối thì hiện đúng lý do', async () => {
    const user = userEvent.setup();
    await openSkillTab(user, SKILL, {
      'POST /api/m12/evidences': () =>
        apiError(422, 'ATTACHMENT_INVALID', 'x', {
          fields: { files: ['virus.pdf: nội dung không đúng định dạng pdf.'] },
        }),
    });

    await user.click(screen.getByRole('button', { name: 'Nộp minh chứng' }));
    const panel = await screen.findByRole('dialog');
    await user.type(await within(panel).findByLabelText('Mô tả'), 'A');
    await user.click(within(panel).getByRole('button', { name: 'Nộp minh chứng' }));

    expect(await within(panel).findByRole('alert')).toHaveTextContent(
      'virus.pdf: nội dung không đúng định dạng pdf.',
    );
  });

  it('lỗi không có chi tiết trường thì hiện thông báo chung', async () => {
    const user = userEvent.setup();
    await openSkillTab(user, SKILL, {
      'POST /api/m12/evidences': () => apiError(409, 'EVIDENCE_EXISTS', 'Đã có minh chứng'),
    });

    await user.click(screen.getByRole('button', { name: 'Nộp minh chứng' }));
    const panel = await screen.findByRole('dialog');
    await user.type(await within(panel).findByLabelText('Mô tả'), 'A');
    await user.click(within(panel).getByRole('button', { name: 'Nộp minh chứng' }));

    expect(await within(panel).findByRole('alert')).toHaveTextContent('Đã có minh chứng');
  });

  it('đang chờ duyệt thì xem lịch sử, không có form', async () => {
    const user = userEvent.setup();
    await openSkillTab(
      user,
      { ...SKILL, status: 'pending' },
      {
        'GET /api/m12/evidences': () =>
          jsonResponse(200, {
            items: [
              evidence({
                link: 'https://example.test/a',
                attachments: [
                  {
                    id: 'a1',
                    original_name: 'bai.pdf',
                    size_bytes: 2048,
                    url: '/api/m12/evidences/e1/attachments/a1',
                  },
                ],
              }),
            ],
          }),
      },
    );

    await user.click(screen.getByRole('button', { name: 'Xem minh chứng' }));
    const panel = await screen.findByRole('dialog');

    expect(await within(panel).findByText('Kho mã')).toBeInTheDocument();
    expect(within(panel).getByText('Chờ duyệt')).toBeInTheDocument();
    expect(within(panel).getByRole('link', { name: 'bai.pdf' })).toHaveAttribute(
      'href',
      '/api/m12/evidences/e1/attachments/a1',
    );
    expect(within(panel).getByText('2 KB')).toBeInTheDocument();
    expect(within(panel).queryByLabelText('Mô tả')).toBeNull();
  });

  it('bị từ chối: có lý do, vẫn nộp lại được và giữ lịch sử', async () => {
    const user = userEvent.setup();
    await openSkillTab(user, SKILL, {
      'GET /api/m12/evidences': () =>
        jsonResponse(200, {
          items: [evidence({ status: 'rejected', review_note: 'Thiếu liên kết' })],
        }),
    });

    await user.click(screen.getByRole('button', { name: 'Nộp minh chứng' }));
    const panel = await screen.findByRole('dialog');

    expect(await within(panel).findByText('Thiếu liên kết')).toBeInTheDocument();
    expect(within(panel).getByText('Bị từ chối')).toBeInTheDocument();
    expect(within(panel).getByLabelText('Mô tả')).toBeInTheDocument();
  });

  it('đã duyệt thì không nộp thêm', async () => {
    const user = userEvent.setup();
    await openSkillTab(
      user,
      { ...SKILL, status: 'done' },
      {
        'GET /api/m12/evidences': () =>
          jsonResponse(200, { items: [evidence({ status: 'approved' })] }),
      },
    );

    await user.click(screen.getByRole('button', { name: 'Xem minh chứng' }));
    const panel = await screen.findByRole('dialog');

    expect(await within(panel).findByText('Đã duyệt')).toBeInTheDocument();
    expect(within(panel).queryByLabelText('Mô tả')).toBeNull();
  });

  it('cố vấn chỉ xem, truy vấn đúng sinh viên', async () => {
    const user = userEvent.setup();
    const fetchMock = await openSkillTab(user, SKILL, {}, 'advisor', '?student=DEMO05');

    await user.click(screen.getByRole('button', { name: 'Xem minh chứng' }));
    const panel = await screen.findByRole('dialog');

    expect(await within(panel).findByText('Chưa có minh chứng.')).toBeInTheDocument();
    expect(within(panel).queryByLabelText('Mô tả')).toBeNull();
    expect(callsTo(fetchMock, '/api/m12/evidences')[0].get('student_id')).toBe('DEMO05');
  });
});

// --- Minh chứng: duyệt ---

const REVIEWS = 'GET /api/m12/evidence-reviews';

function reviewRow(extra = {}) {
  return evidence({
    student: { id: 'DEMO05', code: 'DEMO05', name: 'Sinh viên 5' },
    careers: [{ id: 'c-ai', name: 'AI Engineer', group: 'Nền tảng' }],
    submitted_at: '2026-03-02T01:30:00Z',
    previous_submissions: 0,
    ...extra,
  });
}

function reviewList(items = [reviewRow()]) {
  return () => jsonResponse(200, { items, page: 1, page_size: 20, total: items.length });
}

async function openReview(role = 'advisor', extra = {}) {
  const user = userEvent.setup();
  const fetchMock = m11Api(role, { [REVIEWS]: reviewList(), ...extra });
  renderApp('/m12/duyet-minh-chung');
  await user.click(await screen.findByRole('button', { name: 'Xem' }));
  return { user, fetchMock, panel: await screen.findByRole('dialog', { name: 'Viết API' }) };
}

describe('Duyệt minh chứng', () => {
  it('danh sách lọc mặc định chờ duyệt, đổi bộ lọc thì gọi lại API', async () => {
    const user = userEvent.setup();
    const fetchMock = m11Api('advisor', { [REVIEWS]: reviewList() });
    renderApp('/m12/duyet-minh-chung');

    expect(await screen.findByRole('rowheader', { name: /Sinh viên 5/ })).toBeInTheDocument();
    expect(callsTo(fetchMock, '/api/m12/evidence-reviews')[0].get('status')).toBe('pending');

    await user.selectOptions(screen.getByLabelText('Lọc theo trạng thái'), 'rejected');
    await waitFor(() =>
      expect(callsTo(fetchMock, '/api/m12/evidence-reviews').at(-1).get('status')).toBe('rejected'),
    );
  });

  it('bảng có nghề, nhóm năng lực, ngày nộp, tệp tải được và số lần nộp trước', async () => {
    m11Api('advisor', {
      [REVIEWS]: reviewList([
        reviewRow({
          previous_submissions: 2,
          careers: [
            { id: 'c-ai', name: 'AI Engineer', group: 'Nền tảng' },
            { id: 'c-da', name: 'Data Analyst', group: 'Công cụ' },
          ],
          attachments: [{ id: 'a1', original_name: 'bai.pdf', size_bytes: 2048, url: '/tep/a1' }],
        }),
      ]),
    });
    renderApp('/m12/duyet-minh-chung');

    const row = (await screen.findByRole('rowheader', { name: /Sinh viên 5/ })).closest('tr');
    expect(within(row).getByText('AI Engineer: Nền tảng')).toBeInTheDocument();
    expect(within(row).getByText('Data Analyst: Công cụ')).toBeInTheDocument();
    expect(row).toHaveTextContent(formatDateTime('2026-03-02T01:30:00Z'));
    expect(within(row).getByRole('link', { name: 'bai.pdf' })).toHaveAttribute('href', '/tep/a1');
    expect(screen.getByRole('columnheader', { name: 'Số lần nộp trước' })).toBeInTheDocument();
    expect(within(row).getByRole('cell', { name: '2' })).toBeInTheDocument();
  });

  it('bảng ghi rõ khi thiếu ngày nộp, tệp đính kèm hoặc nghề', async () => {
    m11Api('advisor', {
      [REVIEWS]: reviewList([reviewRow({ submitted_at: null, careers: [] })]),
    });
    renderApp('/m12/duyet-minh-chung');

    const row = (await screen.findByRole('rowheader', { name: /Sinh viên 5/ })).closest('tr');
    expect(row).toHaveTextContent('Chưa ghi nhận');
    expect(row).toHaveTextContent('Không có');
    expect(row).toHaveTextContent('Không thuộc nghề nào');
  });

  it('panel có nghề, nhóm năng lực, ngày nộp, tệp tải được và số lần nộp trước', async () => {
    const { panel } = await openReview('advisor', {
      [REVIEWS]: reviewList([
        reviewRow({
          previous_submissions: 1,
          attachments: [{ id: 'a1', original_name: 'bai.pdf', size_bytes: 2048, url: '/tep/a1' }],
        }),
      ]),
    });

    expect(within(panel).getByText('AI Engineer: Nền tảng')).toBeInTheDocument();
    expect(panel).toHaveTextContent(`Ngày nộp: ${formatDateTime('2026-03-02T01:30:00Z')}`);
    expect(panel).toHaveTextContent('Số lần nộp trước: 1');
    expect(within(panel).getByRole('link', { name: 'bai.pdf' })).toHaveAttribute('href', '/tep/a1');
    expect(panel).not.toHaveTextContent('Không có tệp đính kèm.');
  });

  it('panel ghi rõ khi không có tệp đính kèm', async () => {
    const { panel } = await openReview();

    expect(panel).toHaveTextContent('Không có tệp đính kèm.');
    expect(panel).toHaveTextContent('Số lần nộp trước: 0');
  });

  it('không có minh chứng thì ghi rõ; chọn Tất cả thì không gửi status', async () => {
    const user = userEvent.setup();
    const fetchMock = m11Api('advisor', { [REVIEWS]: reviewList([]) });
    renderApp('/m12/duyet-minh-chung');

    expect(await screen.findByText('Không có minh chứng nào')).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText('Lọc theo trạng thái'), '');
    await waitFor(() =>
      expect(callsTo(fetchMock, '/api/m12/evidence-reviews').at(-1).get('status')).toBeNull(),
    );
  });

  it('duyệt gọi đúng API rồi đóng panel, tải lại', async () => {
    const { user, fetchMock, panel } = await openReview('advisor', {
      'POST /api/m12/evidence-reviews/e1/approve': () => jsonResponse(200, {}),
    });

    expect(panel).toHaveTextContent('Sinh viên 5 (DEMO05)');
    await user.click(within(panel).getByRole('button', { name: 'Duyệt' }));

    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(callsTo(fetchMock, '/api/m12/evidence-reviews/e1/approve')).toHaveLength(1);
    await waitFor(() =>
      expect(callsTo(fetchMock, '/api/m12/evidence-reviews').length).toBeGreaterThan(1),
    );
  });

  it('từ chối gửi lý do', async () => {
    let body;
    const { user, panel } = await openReview('advisor', {
      'POST /api/m12/evidence-reviews/e1/reject': (_url, options) => {
        body = JSON.parse(options.body);
        return jsonResponse(200, {});
      },
    });

    await user.type(within(panel).getByLabelText('Lý do, nhận xét'), 'Thiếu liên kết');
    await user.click(within(panel).getByRole('button', { name: 'Từ chối' }));

    await waitFor(() => expect(body).toEqual({ note: 'Thiếu liên kết' }));
  });

  it('từ chối không lý do: hiện lỗi 422 của trường, panel vẫn mở', async () => {
    const { user, panel } = await openReview('advisor', {
      'POST /api/m12/evidence-reviews/e1/reject': () =>
        apiError(422, 'VALIDATION_ERROR', 'x', { fields: { note: ['Trường này là bắt buộc.'] } }),
    });

    await user.click(within(panel).getByRole('button', { name: 'Từ chối' }));

    expect(await within(panel).findByRole('alert')).toHaveTextContent('Trường này là bắt buộc.');
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('409 khi đã được xử lý thì hiện thông báo', async () => {
    const { user, panel } = await openReview('advisor', {
      'POST /api/m12/evidence-reviews/e1/approve': () =>
        apiError(409, 'EVIDENCE_REVIEWED', 'Đã được xử lý'),
    });

    await user.click(within(panel).getByRole('button', { name: 'Duyệt' }));

    expect(await within(panel).findByRole('alert')).toHaveTextContent('Đã được xử lý');
  });

  it('quản trị viên chỉ xem, không có nút duyệt', async () => {
    const { panel } = await openReview('admin');

    expect(within(panel).queryByRole('button', { name: 'Duyệt' })).toBeNull();
  });

  it('bản đã xử lý không có nút, có nhận xét và liên kết', async () => {
    const { panel } = await openReview('advisor', {
      [REVIEWS]: reviewList([
        reviewRow({
          status: 'approved',
          review_note: 'Tốt',
          link: 'https://example.test/a',
        }),
      ]),
    });

    expect(panel).toHaveTextContent('Tốt');
    expect(within(panel).getByRole('link', { name: 'https://example.test/a' })).toBeInTheDocument();
    expect(within(panel).queryByRole('button', { name: 'Duyệt' })).toBeNull();
  });

  it('sinh viên không có trang này', async () => {
    m11Api('student');
    renderApp('/m12/duyet-minh-chung');

    expect(await screen.findByRole('heading', { name: /quyền/i })).toBeInTheDocument();
  });
});

// --- Yêu cầu hỗ trợ ---

const LIST = 'GET /api/m12/support-requests';
const CATEGORIES = 'GET /api/m12/support-categories';

function ticket(extra = {}) {
  return {
    id: 't1',
    code: 'HT-202611-0001',
    title: 'Xin hỏi đăng ký',
    status: 'new',
    category: { id: 'cat-hocvu', name: 'Học vụ' },
    student: { code: 'SV01', name: 'Sinh viên 1' },
    created_at: '2026-11-01T09:00:00Z',
    updated_at: '2026-11-01T09:00:00Z',
    description: 'Nội dung',
    messages: [
      {
        id: 'm1',
        author: 'Sinh viên 1',
        is_mine: true,
        body: 'Nội dung',
        created_at: '2026-11-01T09:00:00Z',
        attachments: [
          {
            id: 'a1',
            original_name: 'don.pdf',
            size_bytes: 1024,
            url: '/api/m12/support-requests/t1/attachments/a1',
          },
        ],
      },
      {
        id: 'm2',
        author: 'Nhân sự hỗ trợ',
        is_mine: false,
        body: 'Đã nhận',
        created_at: '2026-11-01T10:00:00Z',
        attachments: [],
      },
    ],
    timeline: [
      {
        from_status: 'new',
        to_status: 'in_progress',
        to_label: 'Đang xử lý',
        actor: 'Nhân sự hỗ trợ',
        created_at: '2026-11-01T10:00:00Z',
      },
    ],
    can_reply: false,
    next_statuses: [],
    ...extra,
  };
}

function ticketPage(items = [ticket()]) {
  return () => jsonResponse(200, { items, page: 1, page_size: 20, total: items.length });
}

function supportApi(role = 'student', extra = {}) {
  return m11Api(role, {
    [LIST]: ticketPage(),
    [CATEGORIES]: () =>
      jsonResponse(200, {
        items: [
          { id: 'cat-hocvu', name: 'Học vụ' },
          { id: 'cat-kythuat', name: 'Kỹ thuật' },
        ],
      }),
    'GET /api/m12/support-requests/t1': () => jsonResponse(200, ticket()),
    ...extra,
  });
}

describe('danh sách yêu cầu hỗ trợ', () => {
  it('sinh viên thấy mã, tiêu đề, trạng thái, liên kết tới chi tiết; không lọc nhóm', async () => {
    supportApi();
    renderApp('/m12/yeu-cau-ho-tro');

    const link = await screen.findByRole('link', { name: /HT-202611-0001/ });
    expect(link).toHaveAttribute('href', '/m12/yeu-cau-ho-tro/t1');
    expect(link).toHaveTextContent('Xin hỏi đăng ký');
    expect(link).toHaveTextContent('Mới');
    expect(link).not.toHaveTextContent('Sinh viên 1');
    expect(screen.queryByLabelText('Lọc theo nhóm vấn đề')).toBeNull();
  });

  it('nhân viên có hàng đợi, thấy sinh viên, lọc theo nhóm và trạng thái; không có nút tạo', async () => {
    const user = userEvent.setup();
    const fetchMock = supportApi('support_staff');
    renderApp('/m12/yeu-cau-ho-tro');

    expect(await screen.findByRole('heading', { name: 'Hàng đợi hỗ trợ' })).toBeInTheDocument();
    expect(await screen.findByRole('link', { name: /HT-202611/ })).toHaveTextContent('SV01');
    expect(screen.queryByRole('button', { name: 'Tạo yêu cầu' })).toBeNull();

    await user.selectOptions(await screen.findByLabelText('Lọc theo nhóm vấn đề'), 'cat-kythuat');
    await waitFor(() =>
      expect(callsTo(fetchMock, '/api/m12/support-requests').at(-1).get('category_id')).toBe(
        'cat-kythuat',
      ),
    );
    await user.selectOptions(screen.getByLabelText('Lọc theo trạng thái'), 'done');
    await waitFor(() =>
      expect(callsTo(fetchMock, '/api/m12/support-requests').at(-1).get('status')).toBe('done'),
    );
    await user.selectOptions(screen.getByLabelText('Lọc theo trạng thái'), '');
    await waitFor(() =>
      expect(callsTo(fetchMock, '/api/m12/support-requests').at(-1).get('status')).toBeNull(),
    );
  });

  it('không có yêu cầu thì ghi rõ', async () => {
    supportApi('student', { [LIST]: ticketPage([]) });
    renderApp('/m12/yeu-cau-ho-tro');

    expect(await screen.findByText('Chưa có yêu cầu nào')).toBeInTheDocument();
  });

  it('tạo yêu cầu gửi multipart rồi mở trang chi tiết', async () => {
    const user = userEvent.setup();
    const fetchMock = supportApi('student', {
      'POST /api/m12/support-requests': () => jsonResponse(201, ticket()),
    });
    renderApp('/m12/yeu-cau-ho-tro');

    await user.click(await screen.findByRole('button', { name: 'Tạo yêu cầu' }));
    const panel = await screen.findByRole('dialog');
    await user.type(within(panel).getByLabelText('Tiêu đề'), 'Tiêu đề A');
    await user.selectOptions(within(panel).getByLabelText('Nhóm vấn đề'), 'cat-kythuat');
    await user.type(within(panel).getByLabelText('Mô tả'), 'Mô tả A');
    await user.upload(within(panel).getByLabelText(/Tệp đính kèm/), PDF);
    await user.click(within(panel).getByRole('button', { name: 'Gửi yêu cầu' }));

    expect(await screen.findByRole('heading', { name: 'Chi tiết yêu cầu' })).toBeInTheDocument();
    const body = sentBody(fetchMock, '/api/m12/support-requests');
    expect(body.get('title')).toBe('Tiêu đề A');
    expect(body.get('category_id')).toBe('cat-kythuat');
    expect(body.get('description')).toBe('Mô tả A');
    expect(body.get('files').name).toBe('bai-lam.pdf');
  });

  it('tạo lỗi thì hiện lý do, form vẫn mở', async () => {
    const user = userEvent.setup();
    supportApi('student', {
      'POST /api/m12/support-requests': () =>
        apiError(422, 'ATTACHMENT_INVALID', 'x', { fields: { files: ['lon.pdf: tối đa 5 MB.'] } }),
    });
    renderApp('/m12/yeu-cau-ho-tro');

    await user.click(await screen.findByRole('button', { name: 'Tạo yêu cầu' }));
    const panel = await screen.findByRole('dialog');
    await user.type(within(panel).getByLabelText('Tiêu đề'), 'A');
    await user.type(within(panel).getByLabelText('Mô tả'), 'B');
    await user.click(within(panel).getByRole('button', { name: 'Gửi yêu cầu' }));

    expect(await within(panel).findByRole('alert')).toHaveTextContent('lon.pdf: tối đa 5 MB.');
  });
});

describe('chi tiết yêu cầu hỗ trợ', () => {
  const REPLY = 'POST /api/m12/support-requests/t1/messages';
  const STATUS = 'POST /api/m12/support-requests/t1/status';

  function open(role, value, extra) {
    const fetchMock = supportApi(role, {
      'GET /api/m12/support-requests/t1': () => jsonResponse(200, value),
      ...extra,
    });
    renderApp('/m12/yeu-cau-ho-tro/t1');
    return fetchMock;
  }

  it('có luồng tin nhắn, tệp, timeline; tin của mình phân biệt được', async () => {
    open('student', ticket());

    const first = (await screen.findByText('Đã nhận')).closest('li');
    expect(first).not.toHaveClass('ticket-message--mine');
    expect(screen.getByText('Nội dung').closest('li')).toHaveClass('ticket-message--mine');
    expect(screen.getByRole('link', { name: 'don.pdf' })).toHaveAttribute(
      'href',
      '/api/m12/support-requests/t1/attachments/a1',
    );
    const side = screen.getByRole('complementary', { name: 'Trạng thái yêu cầu' });
    expect(side).toHaveTextContent('Tạo yêu cầu');
    expect(side).toHaveTextContent('Đang xử lý');
    expect(side).toHaveTextContent('Nhân sự hỗ trợ');
  });

  it('sinh viên không ở trạng thái cần bổ sung: không có ô trả lời, có giải thích', async () => {
    open('student', ticket());

    expect(
      await screen.findByText('Bạn chỉ trả lời được khi yêu cầu ở trạng thái Cần bổ sung.'),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText('Trả lời')).toBeNull();
  });

  it('trả lời gửi đúng nội dung rồi tải lại', async () => {
    const user = userEvent.setup();
    const fetchMock = open('student', ticket({ status: 'need_info', can_reply: true }), {
      [REPLY]: () => jsonResponse(201, ticket()),
    });

    await user.type(await screen.findByLabelText('Trả lời'), 'Em bổ sung');
    await user.upload(screen.getByLabelText(/Tệp đính kèm/), PDF);
    await user.click(screen.getByRole('button', { name: 'Gửi' }));

    await waitFor(() =>
      expect(callsTo(fetchMock, '/api/m12/support-requests/t1').length).toBeGreaterThan(1),
    );
    const body = sentBody(fetchMock, '/api/m12/support-requests/t1/messages');
    expect(body.get('body')).toBe('Em bổ sung');
    expect(body.get('files').name).toBe('bai-lam.pdf');
  });

  it('trả lời lỗi thì báo rõ', async () => {
    const user = userEvent.setup();
    open('student', ticket({ status: 'need_info', can_reply: true }), {
      [REPLY]: () => apiError(409, 'TICKET_NOT_NEED_INFO', 'Không trả lời được'),
    });

    await user.type(await screen.findByLabelText('Trả lời'), 'A');
    await user.click(screen.getByRole('button', { name: 'Gửi' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Không trả lời được');
  });

  it('nhân viên đổi trạng thái theo danh sách API trả về', async () => {
    const user = userEvent.setup();
    let body;
    open(
      'support_staff',
      ticket({ status: 'in_progress', can_reply: true, next_statuses: ['done', 'need_info'] }),
      {
        [STATUS]: (_url, options) => {
          body = JSON.parse(options.body);
          return jsonResponse(200, ticket());
        },
      },
    );

    expect(
      await screen.findByRole('button', { name: 'Chuyển sang Hoàn thành' }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Chuyển sang Cần bổ sung' }));

    await waitFor(() => expect(body).toEqual({ status: 'need_info' }));
  });

  it('chuyển sai bị 409 thì báo rõ', async () => {
    const user = userEvent.setup();
    open('support_staff', ticket({ next_statuses: ['in_progress'] }), {
      [STATUS]: () => apiError(409, 'INVALID_TRANSITION', 'Không chuyển được'),
    });

    await user.click(await screen.findByRole('button', { name: 'Chuyển sang Đang xử lý' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Không chuyển được');
  });

  it('hoàn thành: không trả lời được, ghi cách tạo yêu cầu mới', async () => {
    open('student', ticket({ status: 'done' }));

    expect(await screen.findByText(/Cần hỗ trợ thêm thì tạo yêu cầu mới/)).toBeInTheDocument();
    expect(screen.queryByLabelText('Trả lời')).toBeNull();
  });

  it('ngoài phạm vi: API 404 thì báo không tải được, không hiện nội dung', async () => {
    open('student', ticket(), {
      'GET /api/m12/support-requests/t1': () => apiError(404, 'NOT_FOUND', 'Không tìm thấy'),
    });

    expect(await screen.findByText('Không tải được yêu cầu')).toBeInTheDocument();
    expect(screen.queryByText('Xin hỏi đăng ký')).toBeNull();
  });
});

// --- Kế hoạch cải thiện ---

const PLAN = 'GET /api/m12/improvement-plan';
const DISCLAIMER = 'Khuyến nghị tham khảo, không thay thế quyết định của cố vấn và nhà trường';

function planItem(id, title, extra = {}) {
  return { id, title, due_date: null, done: false, order: 1, ...extra };
}

function planBody(extra = {}) {
  return {
    student_id: 'SV04',
    active_rules: [{ rule_code: 'gpa', level: 'warning' }],
    new_rules: [],
    disclaimer: DISCLAIMER,
    plan: {
      id: 'p1',
      title: 'Kế hoạch',
      source_rule_codes: ['gpa'],
      items: [planItem('i1', 'Gặp cố vấn', { due_date: '2027-01-15' }), planItem('i2', 'Ôn tập')],
    },
    ...extra,
  };
}

function openPlan(role = 'student', extra = {}, query = '') {
  const fetchMock = m11Api(role, { [PLAN]: () => jsonResponse(200, planBody()), ...extra });
  renderApp(`/m11/canh-bao/ke-hoach${query}`);
  return fetchMock;
}

describe('Kế hoạch cải thiện', () => {
  const ITEM = 'PATCH /api/m12/improvement-plan/p1/items/i1';

  it('có checklist, luôn có câu khuyến nghị', async () => {
    openPlan();

    expect(await screen.findByDisplayValue('Gặp cố vấn')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Ôn tập')).toBeInTheDocument();
    expect(screen.getByDisplayValue('2027-01-15')).toBeInTheDocument();
    expect(screen.getByText(`${DISCLAIMER}.`)).toBeInTheDocument();
  });

  it('đánh dấu xong, sửa nội dung, đặt hạn đều gọi PATCH đúng', async () => {
    const user = userEvent.setup();
    const bodies = [];
    openPlan('student', {
      [ITEM]: (_url, options) => {
        bodies.push(JSON.parse(options.body));
        return jsonResponse(200, planBody());
      },
    });

    await user.click(await screen.findByRole('checkbox', { name: 'Đánh dấu xong: Gặp cố vấn' }));
    await waitFor(() => expect(bodies).toContainEqual({ done: true }));

    const title = await screen.findByLabelText('Nội dung: Gặp cố vấn');
    await user.type(title, ' sớm');
    await user.tab();
    await waitFor(() => expect(bodies).toContainEqual({ title: 'Gặp cố vấn sớm' }));

    const date = await screen.findByLabelText('Hạn: Gặp cố vấn');
    await user.clear(date);
    await waitFor(() => expect(bodies).toContainEqual({ due_date: null }));
  });

  it('thêm và xóa mục', async () => {
    const user = userEvent.setup();
    let added;
    const fetchMock = openPlan('student', {
      'POST /api/m12/improvement-plan/p1/items': (_url, options) => {
        added = JSON.parse(options.body);
        return jsonResponse(201, planBody());
      },
      'DELETE /api/m12/improvement-plan/p1/items/i2': () => jsonResponse(200, planBody()),
    });

    await user.type(await screen.findByLabelText('Mục mới'), 'Mục tự thêm');
    await user.click(screen.getByRole('button', { name: 'Thêm' }));
    await waitFor(() => expect(added).toEqual({ title: 'Mục tự thêm' }));

    await user.click(await screen.findByRole('button', { name: 'Xóa: Ôn tập' }));
    await waitFor(() =>
      expect(callsTo(fetchMock, '/api/m12/improvement-plan/p1/items/i2')).toHaveLength(1),
    );
  });

  it('có rủi ro mới thì có nút thêm mục', async () => {
    const user = userEvent.setup();
    const fetchMock = openPlan('student', {
      [PLAN]: () => jsonResponse(200, planBody({ new_rules: ['debt'] })),
      'POST /api/m12/improvement-plan/p1/new-risks': () => jsonResponse(200, planBody()),
    });

    await user.click(await screen.findByRole('button', { name: 'Thêm mục cho rủi ro mới' }));

    await waitFor(() =>
      expect(callsTo(fetchMock, '/api/m12/improvement-plan/p1/new-risks')).toHaveLength(1),
    );
  });

  it('thao tác lỗi thì báo rõ', async () => {
    const user = userEvent.setup();
    openPlan('student', { [ITEM]: () => apiError(422, 'VALIDATION_ERROR', 'Hạn không hợp lệ') });

    await user.click(await screen.findByRole('checkbox', { name: /Gặp cố vấn/ }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Hạn không hợp lệ');
  });

  it('cố vấn chỉ xem: không có ô sửa, nút thêm, nút xóa', async () => {
    openPlan(
      'advisor',
      {
        [PLAN]: () =>
          jsonResponse(
            200,
            planBody({
              new_rules: ['debt'],
              plan: {
                id: 'p1',
                items: [
                  planItem('i1', 'Gặp cố vấn', { done: true, due_date: '2027-01-15' }),
                  planItem('i2', 'Ôn tập'),
                ],
              },
            }),
          ),
      },
      '?student=SV04',
    );

    expect(await screen.findByText('Gặp cố vấn')).toBeInTheDocument();
    expect(screen.getByText('Đã xong')).toBeInTheDocument();
    expect(screen.getByText('Hạn 2027-01-15')).toBeInTheDocument();
    expect(screen.getByText('Chưa đặt hạn')).toBeInTheDocument();
    expect(screen.queryByRole('checkbox')).toBeNull();
    expect(screen.queryByLabelText('Mục mới')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Thêm mục cho rủi ro mới' })).toBeNull();
  });

  it('chưa có kế hoạch: sinh viên tạo được, báo tạo lỗi', async () => {
    const user = userEvent.setup();
    let created = false;
    openPlan('student', {
      [PLAN]: () => jsonResponse(200, planBody({ plan: created ? planBody().plan : null })),
      'POST /api/m12/improvement-plan': () => {
        created = true;
        return jsonResponse(201, planBody());
      },
    });

    await user.click(await screen.findByRole('button', { name: 'Tạo kế hoạch cải thiện' }));

    expect(await screen.findByDisplayValue('Gặp cố vấn')).toBeInTheDocument();
  });

  it('tạo thất bại hiện lỗi', async () => {
    const user = userEvent.setup();
    openPlan('student', {
      [PLAN]: () => jsonResponse(200, planBody({ plan: null })),
      'POST /api/m12/improvement-plan': () => apiError(409, 'PLAN_EXISTS', 'Đã có kế hoạch'),
    });

    await user.click(await screen.findByRole('button', { name: 'Tạo kế hoạch cải thiện' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Đã có kế hoạch');
  });

  it('không có rủi ro; cố vấn chưa có kế hoạch; chưa chọn sinh viên', async () => {
    const first = m11Api('student', {
      [PLAN]: () => jsonResponse(200, planBody({ plan: null, active_rules: [] })),
    });
    const view = renderApp('/m11/canh-bao/ke-hoach');
    expect(await screen.findByText(/Không có quy tắc nào/)).toBeInTheDocument();
    expect(first).toBeDefined();
    view.unmount();

    m11Api('advisor', { [PLAN]: () => jsonResponse(200, planBody({ plan: null })) });
    const second = renderApp('/m11/canh-bao/ke-hoach?student=SV04');
    expect(await screen.findByText('Sinh viên chưa tạo kế hoạch cải thiện')).toBeInTheDocument();
    second.unmount();

    m11Api('advisor');
    renderApp('/m11/canh-bao/ke-hoach');
    expect(await screen.findByText('Chưa chọn sinh viên')).toBeInTheDocument();
  });
});

// --- Thông báo ---

const NOTICES = 'GET /api/notifications';
const NOTE = 'Thông báo lộ trình cập nhật khi bạn mở ứng dụng.';

function notice(id, extra = {}) {
  return {
    id,
    kind: 'ticket_update',
    title: `Thông báo ${id}`,
    body: 'Nội dung',
    link: '/m12/ke-hoach/khac-biet',
    read: false,
    created_at: '2026-11-01T10:00:00Z',
    ...extra,
  };
}

function noticeBody(items, unread) {
  return { items, unread_count: unread, note: NOTE, page: 1, page_size: 20, total: items.length };
}

async function bell(items = [notice(1), notice(2, { read: true })], unread = 1, extra = {}) {
  const user = userEvent.setup();
  const fetchMock = m11Api('student', {
    [NOTICES]: () => jsonResponse(200, noticeBody(items, unread)),
    'GET /api/m12/roadmaps/current': () =>
      jsonResponse(200, { has_primary: false, roadmap: null, note: 'x' }),
    ...extra,
  });
  renderApp('/m11/ket-qua');
  const button = await screen.findByRole('button', {
    name: unread > 0 ? `Thông báo, ${unread} chưa đọc` : 'Thông báo',
  });
  return { user, fetchMock, button };
}

describe('chuông thông báo', () => {
  it('có số chưa đọc; mở panel thấy danh sách và chú thích', async () => {
    const { user, button } = await bell();

    expect(button).toHaveTextContent('1');
    expect(button).toHaveAttribute('aria-expanded', 'false');
    await user.click(button);
    const panel = screen.getByRole('region', { name: 'Danh sách thông báo' });

    expect(button).toHaveAttribute('aria-expanded', 'true');
    expect(within(panel).getByRole('link', { name: /Thông báo 1/ })).toHaveAttribute(
      'href',
      '/m12/ke-hoach/khac-biet',
    );
    expect(within(panel).getAllByText('Chưa đọc')).toHaveLength(1);
    expect(panel).toHaveTextContent(NOTE);
  });

  it('không có chưa đọc: không có số, không có nút đọc tất cả', async () => {
    const { user, button } = await bell([notice(2, { read: true })], 0);

    expect(button.querySelector('.notification-bell__count')).toBeNull();
    await user.click(button);
    expect(screen.queryByRole('button', { name: 'Đọc tất cả' })).toBeNull();
  });

  it('danh sách rỗng ghi rõ; quá 99 hiện 99+', async () => {
    const { user, button } = await bell([], 120);

    expect(button).toHaveTextContent('99+');
    await user.click(button);
    expect(screen.getByText('Chưa có thông báo.')).toBeInTheDocument();
  });

  it('đọc tất cả gọi API rồi tải lại', async () => {
    const { user, fetchMock, button } = await bell(undefined, 1, {
      'POST /api/notifications/read-all': () => jsonResponse(200, { unread_count: 0 }),
    });

    await user.click(button);
    await user.click(screen.getByRole('button', { name: 'Đọc tất cả' }));

    await waitFor(() => expect(callsTo(fetchMock, '/api/notifications/read-all')).toHaveLength(1));
    await waitFor(() => expect(callsTo(fetchMock, '/api/notifications').length).toBeGreaterThan(1));
  });

  it('đọc tất cả lỗi thì báo', async () => {
    const { user, button } = await bell(undefined, 1, {
      'POST /api/notifications/read-all': () => apiError(500, 'X', 'Lỗi đọc'),
    });

    await user.click(button);
    await user.click(screen.getByRole('button', { name: 'Đọc tất cả' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Lỗi đọc');
  });

  it('bấm thông báo chưa đọc thì đánh dấu đã đọc và chuyển trang, panel đóng', async () => {
    const { user, fetchMock, button } = await bell(undefined, 1, {
      'POST /api/notifications/1/read': () => jsonResponse(200, { unread_count: 0 }),
    });

    await user.click(button);
    await user.click(screen.getByRole('link', { name: /Thông báo 1/ }));

    await waitFor(() => expect(callsTo(fetchMock, '/api/notifications/1/read')).toHaveLength(1));
    await waitFor(() => expect(screen.queryByRole('region', { name: /Danh sách/ })).toBeNull());
  });

  it('bấm thông báo đã đọc thì không gọi API đọc', async () => {
    const { user, fetchMock, button } = await bell([notice(2, { read: true })], 0);

    await user.click(button);
    await user.click(screen.getByRole('link', { name: /Thông báo 2/ }));

    expect(callsTo(fetchMock, '/api/notifications/2/read')).toHaveLength(0);
  });

  it('Esc đóng và trả focus; bấm ra ngoài đóng', async () => {
    const { user, button } = await bell();

    await user.click(button);
    await user.keyboard('{Escape}');
    expect(screen.queryByRole('region', { name: /Danh sách/ })).toBeNull();
    expect(button).toHaveFocus();

    await user.click(button);
    await user.click(document.body);
    expect(screen.queryByRole('region', { name: /Danh sách/ })).toBeNull();
  });

  it('đổi trang thì tải lại thông báo; lỗi tải thì không chặn trang', async () => {
    const user = userEvent.setup();
    const fetchMock = m11Api('student', {
      [NOTICES]: () => apiError(500, 'X', 'Lỗi'),
    });
    renderApp('/m11/ket-qua');

    expect(await screen.findByRole('button', { name: 'Thông báo' })).toBeInTheDocument();
    const before = callsTo(fetchMock, '/api/notifications').length;
    await user.click(screen.getByRole('link', { name: 'Cảnh báo' }));
    await waitFor(() =>
      expect(callsTo(fetchMock, '/api/notifications').length).toBeGreaterThan(before),
    );
  });
});

describe('hộp tài khoản demo', () => {
  it('có nhãn của nhân viên hỗ trợ', async () => {
    const { stubApi } = await import('../../test/fakeApi');
    stubApi({
      'GET /api/auth/me': () => apiError(401, 'UNAUTHENTICATED', 'x'),
      'GET /api/health': () => jsonResponse(200, { status: 'ok' }),
      'GET /api/auth/demo-accounts': () =>
        jsonResponse(200, {
          accounts: [{ username: 'ht1', full_name: 'Nhân sự hỗ trợ 1', role: 'support_staff' }],
        }),
    });
    renderApp('/login');

    expect(await screen.findByText('Hỗ trợ')).toBeInTheDocument();
  });
});
