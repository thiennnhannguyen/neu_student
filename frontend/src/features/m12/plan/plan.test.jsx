import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { apiError, jsonResponse, renderApp } from '../../../test/fakeApi';
import { callsTo } from '../../m11/testData';
import { m12Api, progressBody } from '../testData';
import { alignmentLabel } from './labels';

const NOTE =
  'Lịch dự kiến, không phải lịch mở lớp chính thức. Tín chỉ và tiên quyết của CTĐT K68 là giả định.';
const CURRENT = 'GET /api/m12/roadmaps/current';
const PLAN = '/m12/ke-hoach';
const DIFF = '/m12/ke-hoach/khac-biet';

function item(id, name, extra = {}) {
  return {
    id,
    kind: 'course',
    course: { id, code: id, name, credits: 3 },
    confidence: 'du_kien',
    depends_on_pending_result: false,
    outside_curriculum: false,
    semester_alignment: null,
    reason: 'CTĐT không ghi học kỳ, xếp để cân bằng tín chỉ.',
    is_pinned: false,
    is_primary_career: false,
    assumed_position: false,
    prerequisites: [],
    ...extra,
  };
}

const MACHINE = item('CNTT1177', 'Học máy', {
  is_primary_career: true,
  confidence: 'confirmed',
  semester_alignment: { kind: 'on_time', offset: 0, planned_semester: 7 },
  reason: 'Đúng HK 7 của CTĐT, môn của nghề chính.',
  prerequisites: [
    { course_id: 'P1', code: 'P1', name: 'Toán', status: 'in_progress' },
    { course_id: 'P2', code: null, name: 'Tin', status: 'done' },
    { course_id: 'P3', code: 'P3', name: 'Lý', status: 'not_done' },
  ],
  depends_on_pending_result: true,
});
const LATE = item('CNTT1150', 'Mạng máy tính', {
  semester_alignment: { kind: 'late', offset: 1, planned_semester: 5 },
});
const EARLY = item('CNTT1151', 'Hệ điều hành', {
  semester_alignment: { kind: 'early', offset: -2, planned_semester: 8 },
});
const THESIS = item('CNTT1194', 'Khóa luận tốt nghiệp', {
  assumed_position: true,
  course: { id: 'CNTT1194', code: null, name: 'Khóa luận tốt nghiệp', credits: 10 },
});

function roadmap(extra = {}) {
  return {
    id: 'r1',
    career: {
      id: 'career-ai',
      slug: 'ai',
      name: 'AI',
      display_name: 'Kỹ sư Trí tuệ nhân tạo',
      illustration_key: 'ai',
    },
    version: { id: 'v1', version: 1, status: 'active', infeasible: false },
    stale: false,
    has_proposal: false,
    infeasible: false,
    unplaced: [],
    outside_curriculum: [],
    absent_subjects: [],
    totals: { credits_remaining: 22, semesters_remaining: 3 },
    semesters: [
      {
        id: 'S6',
        name: 'Học kỳ 6',
        order: 6,
        credits: 6,
        max_credits: 25,
        min_credits: 10,
        items: [LATE, EARLY],
        skills: [],
      },
      {
        id: 'S7',
        name: 'Học kỳ 7',
        order: 7,
        credits: 3,
        max_credits: 25,
        min_credits: 10,
        items: [MACHINE],
        skills: [
          {
            id: 'sk',
            kind: 'skill',
            skill: { id: 'sk', name: 'Viết API' },
            confidence: 'du_kien',
            reason: 'x',
          },
        ],
      },
      {
        id: 'S8',
        name: 'Học kỳ 8',
        order: 8,
        credits: 10,
        max_credits: 25,
        min_credits: 10,
        items: [THESIS],
        skills: [],
      },
    ],
    ...extra,
  };
}

function current(value = roadmap(), hasPrimary = true) {
  return () =>
    jsonResponse(200, {
      student_id: 'DEMO05',
      has_primary: hasPrimary,
      note: NOTE,
      roadmap: value,
    });
}

function planApi(role = 'student', extra = {}) {
  return m12Api(role, { [CURRENT]: current(), ...extra });
}

async function openPlan(role, extra) {
  const user = userEvent.setup();
  const fetchMock = planApi(role, extra);
  renderApp(PLAN);
  await screen.findByRole('group', { name: 'Lộ trình theo học kỳ' });
  return { user, fetchMock };
}

describe('alignmentLabel', () => {
  it('đúng, trễ, sớm, không có HK', () => {
    expect(alignmentLabel({ kind: 'on_time', offset: 0 })).toBe('Đúng HK CTĐT');
    expect(alignmentLabel({ kind: 'late', offset: 1 })).toBe('Lệch HK CTĐT (+1 kỳ)');
    expect(alignmentLabel({ kind: 'early', offset: -2 })).toBe('Lệch HK CTĐT (−2 kỳ)');
    expect(alignmentLabel(null)).toBeNull();
  });
});

describe('Kế hoạch học tập: trạng thái trống', () => {
  it('chưa có nghề chính: sinh viên có liên kết tới Định hướng nghề', async () => {
    planApi('student', { [CURRENT]: current(null, false) });
    renderApp(PLAN);

    expect(await screen.findByText('Bạn chưa có nghề chính')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Mở Định hướng nghề' })).toHaveAttribute(
      'href',
      '/m12/dinh-huong',
    );
    expect(screen.getByText(NOTE)).toBeInTheDocument();
  });

  it('chưa có lộ trình: bấm Tạo lộ trình thì gọi API rồi tải lại', async () => {
    const user = userEvent.setup();
    let created = false;
    const fetchMock = planApi('student', {
      [CURRENT]: () =>
        jsonResponse(200, {
          has_primary: true,
          note: NOTE,
          roadmap: created ? roadmap() : null,
        }),
      'POST /api/m12/roadmaps/generate': () => {
        created = true;
        return jsonResponse(201, { roadmap: roadmap() });
      },
    });
    renderApp(PLAN);

    await user.click(await screen.findByRole('button', { name: 'Tạo lộ trình' }));

    expect(await screen.findByRole('heading', { name: 'Học kỳ 6' })).toBeInTheDocument();
    expect(callsTo(fetchMock, '/api/m12/roadmaps/generate')).toHaveLength(1);
  });

  it('tạo lỗi thì báo rõ', async () => {
    const user = userEvent.setup();
    planApi('student', {
      [CURRENT]: current(null),
      'POST /api/m12/roadmaps/generate': () => apiError(422, 'NO_PRIMARY_CAREER', 'Chọn nghề'),
    });
    renderApp(PLAN);

    await user.click(await screen.findByRole('button', { name: 'Tạo lộ trình' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Chọn nghề');
  });

  it('cố vấn: sinh viên chưa có nghề, chưa có lộ trình, không có nút tạo', async () => {
    planApi('advisor', { [CURRENT]: current(null, false) });
    renderApp(`${PLAN}?student=DEMO05`);

    expect(await screen.findByText('Sinh viên chưa có nghề chính')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Tạo lộ trình' })).toBeNull();
  });

  it('cố vấn: có nghề nhưng chưa có lộ trình', async () => {
    planApi('advisor', { [CURRENT]: current(null, true) });
    renderApp(`${PLAN}?student=DEMO05`);

    expect(await screen.findByText('Sinh viên chưa tạo lộ trình')).toBeInTheDocument();
  });

  it('cố vấn chưa chọn sinh viên thì không gọi API', async () => {
    const fetchMock = planApi('advisor');
    renderApp(PLAN);

    expect(await screen.findByText('Chưa chọn sinh viên')).toBeInTheDocument();
    expect(callsTo(fetchMock, '/api/m12/roadmaps/current')).toHaveLength(0);
  });
});

describe('Kế hoạch học tập: các cột kỳ', () => {
  it('đầu trang có nghề, tổng tín chỉ, số kỳ; luôn có câu giới hạn', async () => {
    await openPlan();

    expect(screen.getByText('Kỹ sư Trí tuệ nhân tạo')).toBeInTheDocument();
    expect(screen.getByText(/Còn lại/)).toHaveTextContent('Còn lại 22 tín chỉ trong 3 kỳ');
    expect(screen.getByText(NOTE)).toBeInTheDocument();
  });

  it('mỗi cột có tổng tín chỉ / trần', async () => {
    await openPlan();

    const column = screen.getByRole('region', { name: 'Học kỳ 7' });
    expect(within(column).getByText('3/25 tín chỉ')).toBeInTheDocument();
    expect(within(column).getByText('Viết API')).toBeInTheDocument();
  });

  it('thẻ có tên, mã, tín chỉ, đủ chip và dấu nghề chính', async () => {
    await openPlan();

    const card = screen.getByRole('button', { name: /Học máy/ });
    expect(card).toHaveTextContent('CNTT1177');
    expect(card).toHaveTextContent('3 tín chỉ');
    expect(card).toHaveTextContent('Môn của nghề chính');
    expect(card).toHaveTextContent('Có lịch mở lớp');
    expect(card).toHaveTextContent('Phụ thuộc kết quả');
    expect(card).toHaveTextContent('Đúng HK CTĐT');

    const late = screen.getByRole('button', { name: /Mạng máy tính/ });
    expect(late).toHaveTextContent('Dự kiến – chưa xác minh lịch mở lớp');
    expect(late).toHaveTextContent('Lệch HK CTĐT (+1 kỳ)');
    expect(late).not.toHaveTextContent('Môn của nghề chính');
    expect(screen.getByRole('button', { name: /Hệ điều hành/ })).toHaveTextContent(
      'Lệch HK CTĐT (−2 kỳ)',
    );
  });

  it('khóa luận có chú thích giả định, môn không có HK thì không có chip HK', async () => {
    await openPlan();

    const card = screen.getByRole('button', { name: /Khóa luận tốt nghiệp/ });
    expect(card).toHaveTextContent('Vị trí theo giả định của nhóm – chờ xác minh');
    expect(card).toHaveTextContent('Chưa có mã');
    expect(card).not.toHaveTextContent('HK CTĐT');
  });

  it('cột trống ghi rõ', async () => {
    const empty = roadmap();
    empty.semesters[0] = { ...empty.semesters[0], items: [], credits: 0 };
    await openPlan('student', { [CURRENT]: current(empty) });

    expect(
      within(screen.getByRole('region', { name: 'Học kỳ 6' })).getByText('Không xếp môn nào.'),
    ).toBeInTheDocument();
  });

  it('không khả thi: liệt kê môn và lý do', async () => {
    await openPlan('student', {
      [CURRENT]: current(
        roadmap({
          infeasible: true,
          unplaced: [{ course_id: 'A', name: 'Môn A', reason: 'Chuỗi tiên quyết quá dài.' }],
        }),
      ),
    });

    const block = screen.getByRole('region', { name: 'Chưa xếp được toàn bộ' });
    expect(block).toHaveTextContent('Môn A: Chuỗi tiên quyết quá dài.');
  });

  it('môn ngoài CTĐT nằm trong khối thu gọn, có câu chỉ để tham khảo', async () => {
    await openPlan('student', {
      [CURRENT]: current(
        roadmap({
          outside_curriculum: [item('X', 'Môn ngoài', { outside_curriculum: true })],
          absent_subjects: [{ key: 'k', name: 'Môn ngành không có' }],
        }),
      ),
    });

    const details = screen.getByText(/Môn của nghề ngoài CTĐT ngành bạn \(2\)/).closest('details');
    expect(details).not.toHaveAttribute('open');
    expect(details).toHaveTextContent('Chỉ để tham khảo, không tính tín chỉ.');
    expect(details).toHaveTextContent('Môn ngoài');
    expect(details).toHaveTextContent('Môn ngành không có');
  });

  it('không có môn ngoài CTĐT thì không có khối đó', async () => {
    await openPlan();

    expect(screen.queryByText(/Môn của nghề ngoài CTĐT/)).toBeNull();
  });
});

describe('Kế hoạch học tập: panel và chuyển kỳ', () => {
  const MOVE = 'PATCH /api/m12/roadmaps/r1/items/CNTT1177';

  async function openPanel(extra, role) {
    const opened = await openPlan(role, extra);
    await opened.user.click(screen.getByRole('button', { name: /Học máy/ }));
    return { ...opened, panel: await screen.findByRole('dialog', { name: 'Học máy' }) };
  }

  it('panel có lý do, tiên quyết kèm trạng thái, Esc đóng và trả focus', async () => {
    const { user, panel } = await openPanel();

    expect(panel).toHaveTextContent('Đúng HK 7 của CTĐT, môn của nghề chính.');
    expect(panel).toHaveTextContent('Toán (P1): Đang học');
    expect(panel).toHaveTextContent('Tin (Chưa có mã): Đã đạt');
    expect(panel).toHaveTextContent('Lý (P3): Chưa đạt');

    await user.keyboard('{Escape}');
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(screen.getByRole('button', { name: /Học máy/ })).toHaveFocus();
  });

  it('môn không có tiên quyết ghi rõ, khóa luận có chú thích', async () => {
    const { user } = await openPlan();

    await user.click(screen.getByRole('button', { name: /Khóa luận/ }));
    const panel = await screen.findByRole('dialog', { name: 'Khóa luận tốt nghiệp' });

    expect(panel).toHaveTextContent('Không có tiên quyết chính thức.');
    expect(panel).toHaveTextContent('Vị trí theo giả định của nhóm');
  });

  it('chọn kỳ khác rồi chuyển: gọi PATCH đúng thân và tải lại', async () => {
    let body;
    const { user, fetchMock, panel } = await openPanel({
      [MOVE]: (_url, options) => {
        body = JSON.parse(options.body);
        return jsonResponse(200, { roadmap: roadmap() });
      },
    });

    const select = within(panel).getByLabelText('Chuyển sang kỳ…');
    expect(
      within(select)
        .getAllByRole('option')
        .map((o) => o.textContent),
    ).toEqual(['Học kỳ 6', 'Học kỳ 8']);
    await user.selectOptions(select, 'S8');
    await user.click(within(panel).getByRole('button', { name: 'Chuyển kỳ' }));

    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(body).toEqual({ semester_id: 'S8' });
    await waitFor(() =>
      expect(callsTo(fetchMock, '/api/m12/roadmaps/current').length).toBeGreaterThan(1),
    );
  });

  it('422 hiện từng vi phạm, panel vẫn mở', async () => {
    const { user, panel } = await openPanel({
      [MOVE]: () =>
        jsonResponse(422, {
          error: {
            code: 'ROADMAP_RULE_VIOLATION',
            message: 'x',
            details: {
              violations: [
                { code: 'PREREQUISITE', message: 'Học máy phải xếp sau môn tiên quyết Toán.' },
                { code: 'ABOVE_MAX_CREDITS', message: 'Học kỳ 6 có 27 tín chỉ, vượt trần 25.' },
              ],
            },
          },
        }),
    });

    await user.click(within(panel).getByRole('button', { name: 'Chuyển kỳ' }));

    const alert = await within(panel).findByRole('alert');
    expect(alert).toHaveTextContent('Không chuyển được');
    expect(alert).toHaveTextContent('Học máy phải xếp sau môn tiên quyết Toán.');
    expect(alert).toHaveTextContent('vượt trần 25');
    expect(screen.getByRole('dialog', { name: 'Học máy' })).toBeInTheDocument();
  });

  it('lỗi không có danh sách vi phạm thì hiện thông báo chung', async () => {
    const { user, panel } = await openPanel({
      [MOVE]: () => apiError(422, 'SEMESTER_OUT_OF_RANGE', 'Kỳ này nằm ngoài tầm lộ trình.'),
    });

    await user.click(within(panel).getByRole('button', { name: 'Chuyển kỳ' }));

    expect(await within(panel).findByRole('alert')).toHaveTextContent(
      'Kỳ này nằm ngoài tầm lộ trình.',
    );
  });

  it('cố vấn xem được lý do nhưng không có ô chuyển kỳ và nút Tạo lại', async () => {
    const user = userEvent.setup();
    planApi('advisor');
    renderApp(`${PLAN}?student=DEMO05`);
    await screen.findByRole('group', { name: 'Lộ trình theo học kỳ' });

    expect(screen.queryByRole('button', { name: 'Tạo lại' })).toBeNull();
    await user.click(screen.getByRole('button', { name: /Học máy/ }));
    const panel = await screen.findByRole('dialog', { name: 'Học máy' });

    expect(panel).toHaveTextContent('Lý do xếp');
    expect(within(panel).queryByLabelText('Chuyển sang kỳ…')).toBeNull();
  });
});

describe('Kế hoạch học tập: tạo lại', () => {
  it('có hộp xác nhận ghi rõ môn chuyển tay sẽ bị xếp lại; Hủy thì không gọi API', async () => {
    const { user, fetchMock } = await openPlan();

    await user.click(screen.getByRole('button', { name: 'Tạo lại' }));
    const dialog = await screen.findByRole('alertdialog');
    expect(dialog).toHaveTextContent('Các môn bạn đã chuyển tay sẽ bị xếp lại');

    await user.click(within(dialog).getByRole('button', { name: 'Hủy' }));
    expect(callsTo(fetchMock, '/api/m12/roadmaps/generate')).toHaveLength(0);
    expect(screen.getByRole('button', { name: 'Tạo lại' })).toHaveFocus();
  });

  it('xác nhận thì gọi API; lỗi thì giữ hộp', async () => {
    let fail = true;
    const { user, fetchMock } = await openPlan('student', {
      'POST /api/m12/roadmaps/generate': () =>
        fail ? apiError(500, 'X', 'Lỗi tạo') : jsonResponse(201, { roadmap: roadmap() }),
    });

    await user.click(screen.getByRole('button', { name: 'Tạo lại' }));
    const dialog = await screen.findByRole('alertdialog');
    await user.click(within(dialog).getByRole('button', { name: 'Tạo lại' }));
    expect(await within(dialog).findByRole('alert')).toHaveTextContent('Lỗi tạo');

    fail = false;
    await user.click(within(dialog).getByRole('button', { name: 'Tạo lại' }));
    await waitFor(() => expect(screen.queryByRole('alertdialog')).toBeNull());
    expect(callsTo(fetchMock, '/api/m12/roadmaps/generate')).toHaveLength(2);
  });
});

function proposal(extra = {}) {
  return {
    roadmap_id: 'r1',
    has_proposal: true,
    dismissed: false,
    stamp: 'st',
    note: NOTE,
    career_before: { id: 'career-ai', display_name: 'Kỹ sư AI' },
    career_after: { id: 'career-ai', display_name: 'Kỹ sư AI' },
    added: [{ kind: 'course', id: 'A', code: 'A', name: 'Môn thêm', semester: 'Học kỳ 6' }],
    removed: [{ kind: 'skill', id: 'B', code: null, name: 'Kỹ năng bớt', semester: null }],
    moved: [
      {
        kind: 'course',
        id: 'C',
        code: null,
        name: 'Môn chuyển',
        from_semester: 'Học kỳ 6',
        to_semester: 'Học kỳ 7',
      },
    ],
    infeasible: false,
    unplaced: [],
    ...extra,
  };
}

describe('Khác biệt của lộ trình', () => {
  const GET = 'GET /api/m12/roadmaps/r1/proposal';

  function diffApi(role, extra) {
    return planApi(role, { [GET]: () => jsonResponse(200, proposal()), ...extra });
  }

  it('không có đề xuất thì không có banner', async () => {
    await openPlan();

    expect(screen.queryByText('Lộ trình có thay đổi')).toBeNull();
  });

  it('banner có nút Xem khác biệt', async () => {
    await openPlan('student', { [CURRENT]: current(roadmap({ has_proposal: true })) });

    expect(screen.getByText('Lộ trình có thay đổi')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Xem khác biệt' })).toHaveAttribute('href', DIFF);
  });

  it('hai cột: bớt ở bản hiện tại, thêm ở bản đề xuất, chuyển kỳ ở cả hai, có chữ kèm icon', async () => {
    diffApi();
    renderApp(DIFF);

    const before = await screen.findByRole('region', { name: 'Bản hiện tại' });
    const after = screen.getByRole('region', { name: 'Bản đề xuất' });

    expect(before).toHaveTextContent('Bớt');
    expect(before).toHaveTextContent('Kỹ năng bớt');
    expect(before).toHaveTextContent('Không xếp kỳ');
    expect(before).toHaveTextContent('Môn chuyển');
    expect(before).toHaveTextContent('Học kỳ 6');
    expect(after).toHaveTextContent('Thêm');
    expect(after).toHaveTextContent('Môn thêm (A)');
    expect(after).toHaveTextContent('Chuyển kỳ');
    expect(within(after).getByText('Học kỳ 7')).toBeInTheDocument();
    expect(screen.getByText('Thêm 1 · Bớt 1 · Chuyển kỳ 1')).toBeInTheDocument();
    expect(screen.getByText(NOTE)).toBeInTheDocument();
    expect(document.querySelector('.plan-diff__row--added svg')).not.toBeNull();
  });

  it('đổi nghề thì ghi nghề cũ, nghề mới; bản đề xuất không khả thi thì báo', async () => {
    diffApi('student', {
      [GET]: () =>
        jsonResponse(
          200,
          proposal({
            career_after: { id: 'career-be', display_name: 'Backend' },
            infeasible: true,
            unplaced: [{ course_id: 'X', name: 'Môn X', reason: 'Hết chỗ.' }],
          }),
        ),
    });
    renderApp(DIFF);

    expect(await screen.findByText(/Nghề chính đổi từ/)).toHaveTextContent(
      'Nghề chính đổi từ Kỹ sư AI sang Backend.',
    );
    expect(screen.getByText('Môn X: Hết chỗ.')).toBeInTheDocument();
  });

  it.each([
    ['Áp dụng', 'accept'],
    ['Giữ bản cũ', 'dismiss'],
  ])('%s gửi đúng stamp rồi về trang kế hoạch', async (name, action) => {
    const user = userEvent.setup();
    let body;
    diffApi('student', {
      [`POST /api/m12/roadmaps/r1/proposal/${action}`]: (_url, options) => {
        body = JSON.parse(options.body);
        return jsonResponse(200, { roadmap: roadmap() });
      },
    });
    renderApp(DIFF);

    await user.click(await screen.findByRole('button', { name }));

    expect(await screen.findByRole('group', { name: 'Lộ trình theo học kỳ' })).toBeInTheDocument();
    expect(body).toEqual({ stamp: 'st' });
  });

  it('409 thì báo và ở lại trang', async () => {
    const user = userEvent.setup();
    diffApi('student', {
      'POST /api/m12/roadmaps/r1/proposal/accept': () =>
        apiError(409, 'PROPOSAL_OUTDATED', 'Dữ liệu vừa thay đổi.'),
    });
    renderApp(DIFF);

    await user.click(await screen.findByRole('button', { name: 'Áp dụng' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Dữ liệu vừa thay đổi.');
    expect(screen.getByRole('region', { name: 'Bản hiện tại' })).toBeInTheDocument();
  });

  it('cố vấn xem được khác biệt, không có nút áp dụng', async () => {
    diffApi('advisor');
    renderApp(`${DIFF}?student=DEMO05`);

    await screen.findByRole('region', { name: 'Bản hiện tại' });
    expect(screen.queryByRole('button', { name: 'Áp dụng' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Giữ bản cũ' })).toBeNull();
  });

  it('không có đề xuất, chưa có lộ trình, chưa chọn sinh viên', async () => {
    diffApi('student', {
      [GET]: () => jsonResponse(200, { roadmap_id: 'r1', has_proposal: false, note: NOTE }),
    });
    const { unmount } = renderApp(DIFF);
    expect(await screen.findByText('Không có thay đổi')).toBeInTheDocument();
    unmount();

    planApi('student', { [CURRENT]: current(null) });
    const second = renderApp(DIFF);
    expect(await screen.findByText('Chưa có lộ trình')).toBeInTheDocument();
    second.unmount();

    planApi('advisor');
    renderApp(DIFF);
    expect(await screen.findByText('Chưa chọn sinh viên')).toBeInTheDocument();
  });
});

describe('nút từ trang chi tiết nghề', () => {
  it('nghề chính có nút Xem lộ trình theo học kỳ', async () => {
    m12Api();
    renderApp('/m12/dinh-huong/nghe/ai');

    expect(await screen.findByRole('link', { name: 'Xem lộ trình theo học kỳ' })).toHaveAttribute(
      'href',
      PLAN,
    );
  });

  it('nghề khác không có nút này; cố vấn giữ student trong liên kết', async () => {
    m12Api('student', {
      'GET /api/m12/progress/careers/slug/ai': () =>
        jsonResponse(200, progressBody({ is_primary: false })),
    });
    const first = renderApp('/m12/dinh-huong/nghe/ai');
    await screen.findByRole('tab', { name: 'Lộ trình học' });
    expect(screen.queryByRole('link', { name: 'Xem lộ trình theo học kỳ' })).toBeNull();
    first.unmount();

    m12Api('advisor');
    renderApp('/m12/dinh-huong/nghe/ai?student=DEMO05');
    expect(await screen.findByRole('link', { name: 'Xem lộ trình theo học kỳ' })).toHaveAttribute(
      'href',
      `${PLAN}?student=DEMO05`,
    );
  });
});
