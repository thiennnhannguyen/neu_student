import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { apiError, jsonResponse, pendingResponse, renderApp } from '../../test/fakeApi';
import { callsTo } from '../m11/testData';
import { chipStatus, percentOf } from './labels';
import {
  AI,
  BACKEND,
  DISCLAIMER,
  m12Api,
  MY_CAREERS,
  NO_PRIMARY,
  progress,
  progressBody,
  relatedBody,
  relatedItem,
  REQUIREMENT,
} from './testData';

const TREE_PATH = `/m12/dinh-huong/nghe/${AI.id}`;
const PROGRESS_API = `GET /api/m12/progress/careers/${AI.id}`;
const search = () => screen.getByTestId('search').textContent;

const settled = () => new Promise((resolve) => window.setTimeout(resolve, 20));

async function openTree(groupName = /Nền tảng/) {
  renderApp(TREE_PATH);
  const tree = await screen.findByRole('tree', { name: /Cây nghề/ });
  return { tree, group: within(tree).getByRole('treeitem', { name: groupName }) };
}

function primaryCard() {
  return screen.getByRole('region', { name: AI.name });
}

describe('nhãn', () => {
  it('kỹ năng chưa có minh chứng khác với học phần chưa học', () => {
    expect(chipStatus('course', 'not_started')).toBe('not_started');
    expect(chipStatus('skill', 'not_started')).toBe('no_evidence');
    expect(chipStatus('project', 'not_started')).toBe('no_evidence');
    expect(chipStatus('skill', 'pending')).toBe('pending');
  });

  it('phần trăm chỉ để vẽ, mẫu số 0 thì 0', () => {
    expect(percentOf(progress(2, 9))).toBe(22);
    expect(percentOf(progress(0, 0))).toBe(0);
  });
});

describe('trang Định hướng nghề', () => {
  it('thẻ nghề chính có lĩnh vực, 2 thanh tiến độ tách riêng, số môn ngoài CTĐT', async () => {
    m12Api();
    renderApp('/m12/dinh-huong');

    await screen.findByRole('heading', { name: AI.name });
    const card = primaryCard();
    expect(within(card).getByText('Dữ liệu và AI (mẫu)')).toBeInTheDocument();
    expect(within(card).getByText('2/9 học phần')).toBeInTheDocument();
    expect(within(card).getByText('1/3 kỹ năng & dự án')).toBeInTheDocument();
    expect(within(card).getAllByRole('progressbar')).toHaveLength(2);
    expect(within(card).getByText(/4 học phần/)).toBeInTheDocument();
    expect(within(card).getByRole('link', { name: 'Xem cây nghề' })).toHaveAttribute(
      'href',
      TREE_PATH,
    );
  });

  it('InfoPopover giải thích tử số, mẫu số và câu miễn trừ', async () => {
    const user = userEvent.setup();
    m12Api();
    renderApp('/m12/dinh-huong');

    await user.click(await screen.findByRole('button', { name: 'Giải thích tỷ lệ' }));

    const note = screen.getByText(/Tử số/);
    expect(note).toHaveTextContent('Tử số');
    expect(note).toHaveTextContent('Mẫu số');
    expect(note).toHaveTextContent(DISCLAIMER);
  });

  it('có 3 thẻ nghề liên quan, mỗi thẻ có tỷ lệ riêng, và nút Xem tất cả', async () => {
    m12Api();
    renderApp('/m12/dinh-huong');

    await screen.findByRole('heading', { name: 'Nghề liên quan' });
    const cards = screen.getAllByRole('article');
    expect(cards).toHaveLength(3);
    expect(within(cards[0]).getByText('1/8 học phần')).toBeInTheDocument();
    expect(within(cards[1]).getByText('1/7 học phần')).toBeInTheDocument();
    expect(within(cards[2]).getByText('2/8 học phần')).toBeInTheDocument();
    expect(within(cards[0]).getByText(/9\/14 yêu cầu trùng/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Xem tất cả' })).toHaveAttribute(
      'href',
      '/m12/dinh-huong/tat-ca',
    );
    expect(screen.getByText(`${DISCLAIMER}.`)).toBeInTheDocument();
  });

  it('không có môn ngoài CTĐT thì không có dòng đó', async () => {
    m12Api('student', {
      'GET /api/m12/my-careers': () =>
        jsonResponse(200, {
          ...MY_CAREERS,
          primary: { ...MY_CAREERS.primary, outside_curriculum_count: 0 },
        }),
    });
    renderApp('/m12/dinh-huong');

    await screen.findByRole('heading', { name: AI.name });
    expect(within(primaryCard()).queryByText('Ngoài CTĐT')).not.toBeInTheDocument();
  });

  it('nghề không có yêu cầu kỹ năng hiện "Chưa có yêu cầu", không hiện 0%', async () => {
    m12Api('student', {
      'GET /api/m12/my-careers': () =>
        jsonResponse(200, {
          ...MY_CAREERS,
          primary: { ...MY_CAREERS.primary, skill_progress: progress(0, 0) },
        }),
    });
    renderApp('/m12/dinh-huong');

    await screen.findByRole('heading', { name: AI.name });
    expect(within(primaryCard()).getByText('Chưa có yêu cầu')).toBeInTheDocument();
  });

  it('đang tải, rồi lỗi có nút thử lại', async () => {
    const user = userEvent.setup();
    const pending = pendingResponse();
    const fetchMock = m12Api('student', { 'GET /api/m12/my-careers': pending.handler });
    renderApp('/m12/dinh-huong');

    expect(await screen.findByText('Đang tải định hướng nghề...')).toBeInTheDocument();
    pending.resolve(apiError(500, 'INTERNAL_ERROR', 'Hệ thống gặp lỗi.'));

    expect(await screen.findByText('Không tải được định hướng nghề')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /Thử lại/ }));
    await waitFor(() => expect(callsTo(fetchMock, '/api/m12/my-careers')).toHaveLength(2));
  });

  it.each(['advisor', 'admin'])(
    '%s chưa chọn sinh viên: hướng dẫn, không gọi API',
    async (role) => {
      const fetchMock = m12Api(role);
      renderApp('/m12/dinh-huong');

      expect(await screen.findByText(/Chọn sinh viên ở ô/)).toBeInTheDocument();
      expect(callsTo(fetchMock, '/api/m12/my-careers')).toEqual([]);
    },
  );

  it('cố vấn xem: gửi student_id, liên kết giữ sinh viên đang chọn', async () => {
    const fetchMock = m12Api('advisor');
    renderApp('/m12/dinh-huong?student=SV07');

    await screen.findByRole('heading', { name: AI.name });
    expect(callsTo(fetchMock, '/api/m12/my-careers')[0].get('student_id')).toBe('SV07');
    expect(screen.getByRole('link', { name: 'Xem tất cả' })).toHaveAttribute(
      'href',
      '/m12/dinh-huong/tat-ca?student=SV07',
    );
  });

  it('nhân sự hỗ trợ không vào được', async () => {
    const fetchMock = m12Api('support_staff');
    renderApp('/m12/dinh-huong');

    expect(await screen.findByText('Bạn không có quyền xem trang này')).toBeInTheDocument();
    expect(callsTo(fetchMock, '/api/m12/my-careers')).toEqual([]);
  });
});

describe('sinh viên chưa có nghề chính', () => {
  function noPrimary(extra = {}) {
    return m12Api('student', {
      'GET /api/m12/my-careers': () => jsonResponse(200, NO_PRIMARY),
      ...extra,
    });
  }

  it('hiện danh mục nghề và nút chọn', async () => {
    noPrimary();
    renderApp('/m12/dinh-huong');

    expect(await screen.findByText(/Bạn chưa chọn nghề chính/)).toBeInTheDocument();
    expect(await screen.findByRole('link', { name: AI.name })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Chọn nghề này' })).toHaveLength(2);
  });

  it('tìm kiếm gửi q lên API và về trang 1', async () => {
    const user = userEvent.setup();
    const fetchMock = noPrimary();
    renderApp('/m12/dinh-huong');

    await user.type(await screen.findByRole('searchbox'), 'ai{Enter}');

    await waitFor(() =>
      expect(callsTo(fetchMock, '/api/m12/careers').some((query) => query.get('q') === 'ai')).toBe(
        true,
      ),
    );
  });

  it('không có nghề phù hợp thì báo trống', async () => {
    noPrimary({
      'GET /api/m12/careers': () =>
        jsonResponse(200, { items: [], page: 1, page_size: 12, total: 0 }),
    });
    renderApp('/m12/dinh-huong');

    expect(await screen.findByText('Không có nghề phù hợp')).toBeInTheDocument();
  });

  it('chọn nghề: xác nhận rồi PUT và tải lại', async () => {
    const user = userEvent.setup();
    let saved = false;
    const fetchMock = noPrimary({
      'GET /api/m12/my-careers': () => jsonResponse(200, saved ? MY_CAREERS : NO_PRIMARY),
      'PUT /api/m12/career-goal': () => {
        saved = true;
        return jsonResponse(200, { student_id: 'SV01', current: null });
      },
    });
    renderApp('/m12/dinh-huong');

    const buttons = await screen.findAllByRole('button', { name: 'Chọn nghề này' });
    await user.click(buttons[0]);
    await user.click(
      within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Xác nhận' }),
    );

    expect(await screen.findByRole('heading', { name: AI.name })).toBeInTheDocument();
    const put = fetchMock.mock.calls.find(([, options]) => options?.method === 'PUT');
    expect(JSON.parse(put[1].body)).toEqual({ career_id: AI.id });
  });

  it('cố vấn xem sinh viên chưa có nghề: chỉ thông báo, không có trang chọn', async () => {
    const fetchMock = m12Api('advisor', {
      'GET /api/m12/my-careers': () => jsonResponse(200, NO_PRIMARY),
    });
    renderApp('/m12/dinh-huong?student=SV05');

    expect(await screen.findByText('Sinh viên này chưa chọn nghề chính')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Chọn nghề này' })).not.toBeInTheDocument();
    expect(callsTo(fetchMock, '/api/m12/careers')).toEqual([]);
  });
});

describe('trang Xem tất cả (TC10)', () => {
  it('mặc định xếp theo Gần nghề chính, liệt kê lĩnh vực từ API', async () => {
    const fetchMock = m12Api();
    renderApp('/m12/dinh-huong/tat-ca');

    await screen.findAllByRole('article');
    expect(callsTo(fetchMock, '/api/m12/related')[0].get('sort')).toBe('closeness');
    expect(screen.getByLabelText('Sắp xếp')).toHaveValue('closeness');
    expect(screen.getByRole('option', { name: 'Phần mềm (mẫu)' })).toBeInTheDocument();
  });

  it('chuyển sang Phù hợp hồ sơ: gọi lại API, thứ tự đổi theo kết quả', async () => {
    const user = userEvent.setup();
    const fit = [relatedItem(BACKEND, 3, 18, 2, 8), relatedItem(AI, 9, 14, 1, 8)];
    const fetchMock = m12Api('student', {
      'GET /api/m12/related': (url) => {
        const sort = new URL(url, 'http://x').searchParams.get('sort');
        return jsonResponse(
          200,
          sort === 'profile_fit' ? relatedBody(fit, { sort }) : relatedBody(),
        );
      },
    });
    renderApp('/m12/dinh-huong/tat-ca');

    await screen.findAllByRole('article');
    await user.selectOptions(screen.getByLabelText('Sắp xếp'), 'profile_fit');

    await waitFor(() => expect(screen.getAllByRole('article')).toHaveLength(2));
    const first = screen.getAllByRole('article')[0];
    expect(within(first).getByRole('link', { name: BACKEND.name })).toBeInTheDocument();
    expect(search()).toContain('sort=profile_fit');
    expect(callsTo(fetchMock, '/api/m12/related').at(-1).get('sort')).toBe('profile_fit');
  });

  it('lọc lĩnh vực, mức tiến độ, tìm kiếm: lưu vào URL và gửi đúng tham số', async () => {
    const user = userEvent.setup();
    const fetchMock = m12Api();
    renderApp('/m12/dinh-huong/tat-ca');

    await screen.findAllByRole('article');
    await user.selectOptions(screen.getByLabelText('Lĩnh vực'), 'Phần mềm (mẫu)');
    await user.selectOptions(screen.getByLabelText('Mức tiến độ'), '50');
    await user.type(screen.getByRole('searchbox'), 'dev{Enter}');

    await waitFor(() => {
      const query = callsTo(fetchMock, '/api/m12/related').at(-1);
      expect(query.get('field')).toBe('Phần mềm (mẫu)');
      expect(query.get('min_progress')).toBe('50');
      expect(query.get('q')).toBe('dev');
    });
  });

  it('không có kết quả thì báo trống, vẫn đổi được bộ lọc', async () => {
    m12Api('student', { 'GET /api/m12/related': () => jsonResponse(200, relatedBody([])) });
    renderApp('/m12/dinh-huong/tat-ca');

    expect(await screen.findByText('Không có nghề phù hợp với bộ lọc')).toBeInTheDocument();
    expect(screen.getByLabelText('Lĩnh vực')).toBeEnabled();
  });

  it('nhiều trang thì có phân trang, ít thì không', async () => {
    const user = userEvent.setup();
    const fetchMock = m12Api('student', {
      'GET /api/m12/related': () =>
        jsonResponse(200, relatedBody(MY_CAREERS.related, { total: 13 })),
    });
    renderApp('/m12/dinh-huong/tat-ca');

    await user.click(await screen.findByRole('button', { name: 'Trang sau' }));

    await waitFor(() =>
      expect(callsTo(fetchMock, '/api/m12/related').at(-1).get('page')).toBe('2'),
    );
  });

  it('chưa có nghề chính: hiện cảnh báo, thẻ không có dòng trùng yêu cầu', async () => {
    const user = userEvent.setup();
    m12Api('student', {
      'GET /api/m12/related': () =>
        jsonResponse(
          200,
          relatedBody([{ ...relatedItem(BACKEND), closeness: null }], {
            primary_career: null,
            data_warnings: [
              { code: 'NO_PRIMARY_CAREER', message: 'Sinh viên chưa có nghề chính.' },
            ],
          }),
        ),
    });
    renderApp('/m12/dinh-huong/tat-ca');

    await user.click(await screen.findByText('Cảnh báo dữ liệu (1)'));
    expect(screen.getByText('Sinh viên chưa có nghề chính.')).toBeInTheDocument();
    expect(screen.queryByText(/yêu cầu trùng/)).not.toBeInTheDocument();
  });

  it('cố vấn chưa chọn sinh viên: hướng dẫn, không gọi API', async () => {
    const fetchMock = m12Api('advisor');
    renderApp('/m12/dinh-huong/tat-ca');

    expect(await screen.findByText(/Chọn sinh viên ở ô/)).toBeInTheDocument();
    expect(callsTo(fetchMock, '/api/m12/related')).toEqual([]);
  });

  it('lỗi có thông báo', async () => {
    m12Api('student', {
      'GET /api/m12/related': () => apiError(500, 'INTERNAL_ERROR', 'Hệ thống gặp lỗi.'),
    });
    renderApp('/m12/dinh-huong/tat-ca');

    expect(await screen.findByText('Không tải được danh sách nghề')).toBeInTheDocument();
  });
});

describe('cây nghề', () => {
  it('mặc định thu gọn, có role tree, aria-expanded, chỉ một điểm dừng Tab', async () => {
    m12Api();
    const { tree, group } = await openTree();

    expect(group).toHaveAttribute('aria-expanded', 'false');
    expect(within(tree).queryByText('Lập trình Python (mẫu)')).not.toBeInTheDocument();
    const items = within(tree).getAllByRole('treeitem');
    expect(items).toHaveLength(2);
    expect(items.filter((item) => item.tabIndex === 0)).toEqual([group]);
  });

  it('mọi trạng thái có đủ biểu tượng và chữ; có nhãn Ngoài CTĐT, Chưa có mã', async () => {
    const user = userEvent.setup();
    m12Api();
    const { tree, group } = await openTree();
    const second = within(tree).getByRole('treeitem', { name: /Thực hành/ });

    await user.click(group);
    await user.click(second);

    for (const label of [
      'Đạt qua tương đương',
      'Miễn',
      'Đang học',
      'Chưa đạt',
      'Chưa học',
      'Chờ duyệt',
      'Chưa có minh chứng',
    ]) {
      const chip = within(tree).getByText(label);
      expect(chip.querySelector('svg')).not.toBeNull();
    }
    expect(within(tree).getAllByText('Đạt')).toHaveLength(2);
    expect(within(tree).getByText('Ngoài CTĐT')).toBeInTheDocument();
    expect(within(tree).getByText('Chưa có mã')).toBeInTheDocument();
    expect(within(tree).queryByText('course-cd-a')).not.toBeInTheDocument();
  });

  it('phím mũi tên, Home, End di chuyển và mở, đóng nhóm', async () => {
    const user = userEvent.setup();
    m12Api();
    const { tree, group } = await openTree();
    const second = within(tree).getByRole('treeitem', { name: /Thực hành/ });

    group.focus();
    await user.keyboard('{ArrowDown}');
    expect(second).toHaveFocus();
    await user.keyboard('{ArrowUp}');
    expect(group).toHaveFocus();

    await user.keyboard('{ArrowRight}');
    expect(group).toHaveAttribute('aria-expanded', 'true');
    expect(group).toHaveFocus();

    await user.keyboard('{ArrowRight}');
    const python = within(tree).getByRole('treeitem', { name: /Lập trình Python/ });
    expect(python).toHaveFocus();
    expect(python).toHaveAttribute('tabindex', '0');

    await user.keyboard('{ArrowRight}');
    expect(python).toHaveFocus();

    await user.keyboard('{ArrowLeft}');
    expect(group).toHaveFocus();
    await user.keyboard('{ArrowLeft}');
    expect(group).toHaveAttribute('aria-expanded', 'false');
    await user.keyboard('{ArrowLeft}');
    expect(group).toHaveFocus();

    await user.keyboard('{End}');
    expect(second).toHaveFocus();
    await user.keyboard('{ArrowDown}');
    expect(second).toHaveFocus();
    await user.keyboard('{Home}');
    expect(group).toHaveFocus();
    await user.keyboard('{ArrowUp}');
    expect(group).toHaveFocus();
    await user.keyboard('{Enter}');
    expect(group).toHaveAttribute('aria-expanded', 'true');
    await user.keyboard(' ');
    expect(group).toHaveAttribute('aria-expanded', 'false');
  });

  it('phím mũi tên phải không làm gì ở nhóm rỗng đã mở', async () => {
    const user = userEvent.setup();
    m12Api('student', {
      [PROGRESS_API]: () =>
        jsonResponse(
          200,
          progressBody({
            nodes: [
              { id: 'n', kind: 'group', title: 'Rỗng', short_desc: null, order: 1, children: [] },
            ],
          }),
        ),
    });
    const { group } = await openTree(/Rỗng/);

    group.focus();
    await user.keyboard('{ArrowRight}{ArrowRight}');

    expect(group).toHaveFocus();
  });

  it('Enter trên môn mở SidePanel đủ chi tiết; đóng thì trả focus về đúng nút', async () => {
    const user = userEvent.setup();
    m12Api();
    const { tree, group } = await openTree();

    group.focus();
    await user.keyboard('{ArrowRight}{ArrowRight}{ArrowDown}');
    const item = within(tree).getByRole('treeitem', { name: /Giải thuật/ });
    expect(item).toHaveFocus();
    await user.keyboard('{Enter}');

    const panel = await screen.findByRole('dialog', { name: 'Giải thuật (mẫu)' });
    expect(await within(panel).findByText('CNT202')).toBeInTheDocument();
    expect(within(panel).getByText('Đạt qua tương đương: CNT201')).toBeInTheDocument();
    expect(within(panel).getByText('3')).toBeInTheDocument();
    expect(within(panel).getByText('CNT102 Lập trình Python (mẫu)')).toBeInTheDocument();
    expect(within(panel).getByText(REQUIREMENT.short_desc)).toBeInTheDocument();
    expect(within(panel).getByRole('link', { name: BACKEND.name })).toHaveAttribute(
      'href',
      `/m12/dinh-huong/nghe/${BACKEND.id}`,
    );

    await user.keyboard('{Escape}');
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(item).toHaveFocus();
  });

  it('bấm chuột vào môn thiếu mã: panel ghi "Chưa có mã", tiên quyết thiếu mã cũng vậy', async () => {
    const user = userEvent.setup();
    m12Api('student', {
      'GET /api/m12/requirements/course-cd-a': () =>
        jsonResponse(200, {
          ...REQUIREMENT,
          code: null,
          short_desc: null,
          prerequisites: [{ course_id: 'x', code: null, name: 'Môn X (mẫu)' }],
          other_careers: [],
        }),
    });
    const { tree, group } = await openTree();

    await user.click(group);
    await user.click(within(tree).getByRole('treeitem', { name: /Chuyên đề/ }));

    const panel = await screen.findByRole('dialog');
    expect(await within(panel).findByText('Chưa có mã')).toBeInTheDocument();
    expect(within(panel).getByText('Chưa có mã Môn X (mẫu)')).toBeInTheDocument();
    expect(within(panel).getByText('Chỉ có ở nghề này.')).toBeInTheDocument();
    expect(within(panel).queryByText('Mô tả')).not.toBeInTheDocument();
    expect(within(panel).queryByText(/Đạt qua tương đương/)).not.toBeInTheDocument();
  });

  it('panel của môn không tiên quyết ghi "Không có"; của kỹ năng không có mã, tín chỉ', async () => {
    const user = userEvent.setup();
    m12Api('student', {
      'GET /api/m12/requirements/sk-git': () =>
        jsonResponse(200, { ...REQUIREMENT, code: null, credits: null, prerequisites: [] }),
      'GET /api/m12/requirements/MAU105': () =>
        jsonResponse(200, { ...REQUIREMENT, prerequisites: [] }),
    });
    const { tree, group } = await openTree();

    await user.click(within(tree).getByRole('treeitem', { name: /Thực hành/ }));
    await user.click(within(tree).getByRole('treeitem', { name: /Git/ }));
    let panel = await screen.findByRole('dialog');
    await within(panel).findByText('Kỹ năng');
    expect(within(panel).queryByText('Mã')).not.toBeInTheDocument();
    expect(within(panel).queryByText('Tín chỉ')).not.toBeInTheDocument();
    await user.keyboard('{Escape}');

    await user.click(group);
    await user.click(within(tree).getByRole('treeitem', { name: /Tiếng Anh/ }));
    panel = await screen.findByRole('dialog');
    expect(await within(panel).findByText('Không có')).toBeInTheDocument();
  });

  it('panel lỗi có thông báo', async () => {
    const user = userEvent.setup();
    m12Api('student', {
      'GET /api/m12/requirements/CNT102': () => apiError(404, 'NOT_FOUND', 'Không tìm thấy.'),
    });
    const { tree, group } = await openTree();

    await user.click(group);
    await user.click(within(tree).getByRole('treeitem', { name: /Lập trình Python/ }));

    expect(await screen.findByText('Không tải được chi tiết')).toBeInTheDocument();
  });

  it('nghề không tồn tại: báo lỗi', async () => {
    m12Api('student', {
      'GET /api/m12/progress/careers/khong': () => apiError(404, 'NOT_FOUND', 'Không tìm thấy.'),
    });
    renderApp('/m12/dinh-huong/nghe/khong');

    expect(await screen.findByText('Không tải được cây nghề')).toBeInTheDocument();
  });

  it('cố vấn chưa chọn sinh viên: hướng dẫn, không gọi API', async () => {
    const fetchMock = m12Api('advisor');
    renderApp(TREE_PATH);

    expect(await screen.findByText(/Chọn sinh viên ở ô/)).toBeInTheDocument();
    expect(callsTo(fetchMock, `/api/m12/progress/careers/${AI.id}`)).toEqual([]);
  });

  it('có đường dẫn phân cấp về Định hướng nghề và mục sidebar vẫn sáng', async () => {
    m12Api();
    renderApp(TREE_PATH);

    await screen.findByRole('tree');
    expect(screen.getByRole('navigation', { name: 'Vị trí trang' })).toHaveTextContent('Cây nghề');
    const menu = screen.getByRole('navigation', { name: 'Menu chính' });
    expect(within(menu).getByRole('link', { name: 'Định hướng nghề' })).toHaveAttribute(
      'aria-current',
      'page',
    );
  });
});

describe('đặt làm mục tiêu chính (TC08)', () => {
  const NOT_PRIMARY = {
    [PROGRESS_API]: () => jsonResponse(200, progressBody({ is_primary: false })),
  };

  it('nghề chính có nhãn, không có nút', async () => {
    m12Api();
    await openTree();

    expect(screen.getByText('Nghề chính')).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: 'Đặt làm mục tiêu chính' }),
    ).not.toBeInTheDocument();
  });

  it.each(['advisor', 'admin'])('%s chỉ xem, không có nút', async (role) => {
    m12Api(role, NOT_PRIMARY);
    renderApp(`${TREE_PATH}?student=SV07`);

    await screen.findByRole('tree');
    expect(
      screen.queryByRole('button', { name: 'Đặt làm mục tiêu chính' }),
    ).not.toBeInTheDocument();
    await settled();
  });

  it('hộp xác nhận ghi rõ không mất lịch sử; Hủy thì không gọi API, trả focus', async () => {
    const user = userEvent.setup();
    const fetchMock = m12Api('student', NOT_PRIMARY);
    await openTree();
    const button = screen.getByRole('button', { name: 'Đặt làm mục tiêu chính' });

    await user.click(button);

    const dialog = screen.getByRole('alertdialog');
    expect(dialog).toHaveTextContent('Lịch sử học tập và tiến độ không bị mất');
    const cancel = within(dialog).getByRole('button', { name: 'Hủy' });
    expect(cancel).toHaveFocus();
    await user.click(cancel);

    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
    expect(button).toHaveFocus();
    expect(fetchMock.mock.calls.filter(([, options]) => options?.method === 'PUT')).toEqual([]);
  });

  it('Esc đóng hộp xác nhận', async () => {
    const user = userEvent.setup();
    m12Api('student', NOT_PRIMARY);
    await openTree();

    await user.click(screen.getByRole('button', { name: 'Đặt làm mục tiêu chính' }));
    await user.keyboard('{Escape}');

    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
  });

  it('xác nhận: PUT, báo thành công, tải lại nên thành nghề chính', async () => {
    const user = userEvent.setup();
    let primary = false;
    const fetchMock = m12Api('student', {
      [PROGRESS_API]: () => jsonResponse(200, progressBody({ is_primary: primary })),
      'PUT /api/m12/career-goal': () => {
        primary = true;
        return jsonResponse(200, { student_id: 'SV01', current: null });
      },
    });
    await openTree();

    await user.click(screen.getByRole('button', { name: 'Đặt làm mục tiêu chính' }));
    await user.click(screen.getByRole('button', { name: 'Xác nhận' }));

    expect(await screen.findByText('Nghề chính')).toBeInTheDocument();
    expect(await screen.findByText(`Đã đặt ${AI.name} làm mục tiêu chính.`)).toBeInTheDocument();
    const put = fetchMock.mock.calls.find(([, options]) => options?.method === 'PUT');
    expect(JSON.parse(put[1].body)).toEqual({ career_id: AI.id });
    expect(put[1].headers['X-Requested-With']).toBe('fetch');
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
  });

  it('lỗi: giữ hộp xác nhận và hiện thông báo', async () => {
    const user = userEvent.setup();
    m12Api('student', {
      ...NOT_PRIMARY,
      'PUT /api/m12/career-goal': () =>
        apiError(422, 'CAREER_NOT_PUBLISHED', 'Nghề này chưa được công bố.'),
    });
    await openTree();

    await user.click(screen.getByRole('button', { name: 'Đặt làm mục tiêu chính' }));
    await user.click(screen.getByRole('button', { name: 'Xác nhận' }));

    const dialog = screen.getByRole('alertdialog');
    expect(await within(dialog).findByRole('alert')).toHaveTextContent(
      'Nghề này chưa được công bố.',
    );
  });
});
