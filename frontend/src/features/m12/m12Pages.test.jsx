import { act, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { apiError, jsonResponse, pendingResponse, renderApp } from '../../test/fakeApi';
import { callsTo } from '../m11/testData';
import {
  chipStatus,
  groupLabel,
  groupShortLabel,
  percentText,
  priorityLabel,
  typeLabel,
} from './labels';
import {
  AI,
  ANALYST,
  BACKEND,
  child,
  DISCLAIMER,
  galleryBody,
  galleryItem,
  m12Api,
  NODES,
  PRIMARY_ITEM,
  progress,
  progressBody,
  REQUIREMENT,
} from './testData';

const DETAIL_PATH = '/m12/dinh-huong/nghe/ai';
const DETAIL_API = 'GET /api/m12/progress/careers/slug/ai';
const GALLERY_API = 'GET /api/m12/gallery';
const search = () => screen.getByTestId('search').textContent;
const settled = () => new Promise((resolve) => window.setTimeout(resolve, 20));

function cardLink(name) {
  return screen.getByRole('link', { name: new RegExp(name) });
}

function cardNames() {
  return [...document.querySelectorAll('.career-card__name')].map((node) => node.textContent);
}

async function openRoadmap(pathname = DETAIL_PATH) {
  renderApp(pathname);
  return screen.findByRole('tree', { name: /Lộ trình/ });
}

function stubPushLayout() {
  vi.stubGlobal(
    'matchMedia',
    vi.fn(() => ({
      matches: true,
      addEventListener: () => {},
      removeEventListener: () => {},
    })),
  );
}

describe('nhãn', () => {
  it('kỹ năng chưa có minh chứng khác với học phần chưa học', () => {
    expect(chipStatus('course', 'not_started')).toBe('not_started');
    expect(chipStatus('skill', 'not_started')).toBe('no_evidence');
    expect(chipStatus('project', 'not_started')).toBe('no_evidence');
    expect(chipStatus('skill', 'pending')).toBe('pending');
  });

  it('% lấy từ API, mẫu số 0 thì hiện gạch ngang chứ không phải 0%', () => {
    expect(percentText(22)).toBe('22%');
    expect(percentText(0)).toBe('0%');
    expect(percentText(null)).toBe('—');
  });

  it('mức ưu tiên, BB/TC và tên nhóm nghề', () => {
    expect(priorityLabel('very_important')).toBe('Rất quan trọng');
    expect(priorityLabel(null)).toBeNull();
    expect(typeLabel('required')).toBe('BB');
    expect(typeLabel('elective')).toBe('TC');
    expect(typeLabel(null)).toBeNull();
    expect(groupLabel('Nhóm 2 – Trí tuệ nhân tạo và dữ liệu')).toBe('Trí tuệ nhân tạo và dữ liệu');
    expect(groupLabel('Phần mềm')).toBe('Phần mềm');
    expect(groupShortLabel('Nhóm 4 – Hạ tầng, Cloud và vận hành')).toBe('Hạ tầng & Cloud');
    expect(groupShortLabel('Phần mềm')).toBe('Phần mềm');
  });
});

describe('lưới thẻ nghề', () => {
  it('nghề chính đứng đầu với ngôi sao "Mục tiêu chính của bạn" (D-305) và viền nhấn; hợp ngành có chip', async () => {
    m12Api();
    renderApp('/m12/dinh-huong');

    const first = (await screen.findAllByRole('link', { name: /Mục tiêu chính của bạn/ }))[0];
    expect(cardNames()[0]).toBe(AI.display_name);
    expect(first).toHaveClass('career-card--primary');
    expect(within(first).getByText('Hợp ngành KHMT')).toBeInTheDocument();
    expect(cardLink(BACKEND.display_name)).not.toHaveClass('career-card--primary');
    expect(within(cardLink(BACKEND.display_name)).queryByText(/Hợp ngành/)).toBeNull();
  });

  it('thẻ có tên Việt, tên Anh, "" ở nhãn nhỏ, không có ở tiêu đề', async () => {
    m12Api();
    renderApp('/m12/dinh-huong');

    await screen.findAllByRole('link', { name: /Kỹ sư/ });
    const card = cardLink(AI.display_name);
    expect(card.querySelector('.career-card__name').textContent).toBe('Kỹ sư Trí tuệ nhân tạo');
    expect(card.querySelector('.career-card__en').textContent).toBe('AI Engineer');
    expect(card.querySelector('.career-illustration')).toHaveAttribute('aria-hidden', 'true');
  });

  it('số lớn là % học phần, dòng nhỏ là % kỹ năng; không hiện phân số và câu miễn trừ ở thẻ', async () => {
    m12Api();
    renderApp('/m12/dinh-huong');

    await screen.findAllByRole('link', { name: /Kỹ sư/ });
    const card = cardLink(AI.display_name);
    expect(within(card).getByText('22%')).toHaveClass('career-card__percent');
    expect(within(card).getByText('Kỹ năng & dự án 33%')).toBeInTheDocument();
    expect(card).not.toHaveTextContent('2/9');
    expect(within(card).getByRole('progressbar')).toHaveAttribute('aria-valuenow', '2');
    expect(document.querySelector('main, body')).not.toHaveTextContent(DISCLAIMER);
  });

  it('InfoPopover giải thích tỷ lệ và có câu miễn trừ', async () => {
    const user = userEvent.setup();
    m12Api();
    renderApp('/m12/dinh-huong');

    await user.click(await screen.findByRole('button', { name: 'Giải thích tỷ lệ' }));
    expect(document.querySelector('.info-popover__content')).toHaveTextContent(
      'khả năng được tuyển dụng',
    );
  });

  it('mẫu số 0 hiện "—" cho cả 2 tỷ lệ, thanh vẫn hợp lệ', async () => {
    m12Api('student', {
      [GALLERY_API]: () =>
        jsonResponse(
          200,
          galleryBody([
            galleryItem(AI, {
              course_progress: progress(0, 0),
              skill_progress: progress(0, 0, 'kỹ năng & dự án'),
              coverage: { numerator: 0, denominator: 0, percent: null },
            }),
          ]),
        ),
    });
    renderApp('/m12/dinh-huong');

    const card = await screen.findByRole('link', { name: /Kỹ sư/ });
    expect(within(card).getByText('—')).toBeInTheDocument();
    expect(within(card).getByText('Kỹ năng & dự án —')).toBeInTheDocument();
    const bar = within(card).getByRole('progressbar');
    expect(bar).toHaveAttribute('aria-valuenow', '0');
    expect(bar).toHaveAttribute('aria-valuetext', '—');
  });

  it('coverage dưới 50% ghi số cụ thể ở đúng 1 thẻ, đủ thì không có', async () => {
    m12Api('student', {
      [GALLERY_API]: () =>
        jsonResponse(
          200,
          galleryBody([
            galleryItem(AI),
            galleryItem(BACKEND, {
              low_coverage: true,
              coverage: { numerator: 5, denominator: 12, percent: 42 },
            }),
          ]),
        ),
    });
    renderApp('/m12/dinh-huong');

    await screen.findAllByRole('link', { name: /Kỹ sư/ });
    expect(screen.getAllByText('Ngành bạn có 5/12 môn của nghề')).toHaveLength(1);
    expect(cardLink(BACKEND.display_name)).toHaveTextContent('Ngành bạn có 5/12 môn của nghề');
    expect(cardLink(AI.display_name)).not.toHaveTextContent('Ngành bạn có');
  });

  it('thanh 3 đoạn: dài theo y, đậm là đã đạt, nhạt là còn lại, sọc là ngoài CTĐT', async () => {
    m12Api('student', {
      [GALLERY_API]: () =>
        jsonResponse(
          200,
          galleryBody([
            galleryItem(AI, {
              course_progress: progress(5, 5),
              coverage: { numerator: 5, denominator: 12, percent: 42 },
            }),
            galleryItem(BACKEND, {
              course_progress: progress(7, 9),
              coverage: { numerator: 9, denominator: 12, percent: 75 },
            }),
          ]),
        ),
    });
    renderApp('/m12/dinh-huong');
    await screen.findAllByRole('link', { name: /Kỹ sư/ });

    // Số % giữ theo Q92 dù thanh chỉ đậm 5/12.
    const full = cardLink(AI.display_name);
    expect(within(full).getByText('100%')).toBeInTheDocument();
    expect(full.querySelector('.career-meter__segment--done').style.flexGrow).toBe('5');
    expect(full.querySelector('.career-meter__segment--remaining')).toBeNull();
    expect(full.querySelector('.career-meter__segment--outside').style.flexGrow).toBe('7');

    const card = cardLink(BACKEND.display_name);
    expect(card.querySelector('.career-meter__segment--done').style.flexGrow).toBe('7');
    expect(card.querySelector('.career-meter__segment--remaining').style.flexGrow).toBe('2');
    expect(card.querySelector('.career-meter__segment--outside').style.flexGrow).toBe('3');
    const bar = within(card).getByRole('progressbar');
    expect(bar).toHaveAttribute('aria-valuemax', '12');
    expect(bar).toHaveAttribute(
      'aria-valuetext',
      '7 môn đã đạt, 2 môn còn lại trong CTĐT, 3 môn ngoài CTĐT ngành bạn',
    );
  });

  it('InfoPopover và chú giải giải thích đủ 3 đoạn', async () => {
    const user = userEvent.setup();
    m12Api();
    renderApp('/m12/dinh-huong');

    await user.click(await screen.findByRole('button', { name: 'Giải thích tỷ lệ' }));
    const note = document.querySelector('.info-popover__content');
    expect(note).toHaveTextContent('đoạn đậm là môn đã đạt');
    expect(note).toHaveTextContent('đoạn nhạt là môn còn lại trong CTĐT ngành bạn');
    expect(note).toHaveTextContent('đoạn sọc chéo là môn ngoài CTĐT ngành bạn');
    const legend = document.querySelector('.career-meter-legend');
    expect(legend).toHaveTextContent('Đã đạt');
    expect(legend).toHaveTextContent('Còn lại trong CTĐT');
    expect(legend).toHaveTextContent('Ngoài CTĐT ngành bạn');
  });

  it('chip nhóm dùng tên ngắn, tên đầy đủ ở title và aria-label', async () => {
    const full = 'Nhóm 2 – Trí tuệ nhân tạo và dữ liệu';
    m12Api('student', {
      [GALLERY_API]: () => jsonResponse(200, galleryBody(undefined, { groups: [full] })),
    });
    renderApp('/m12/dinh-huong');

    const chip = await screen.findByRole('button', { name: /Trí tuệ nhân tạo và dữ liệu$/ });
    expect(chip).toHaveTextContent(/^AI & dữ liệu$/);
    expect(chip).toHaveAttribute('title', 'Trí tuệ nhân tạo và dữ liệu');
  });

  it('cả thẻ là một liên kết tới trang chi tiết theo slug, nhận được focus', async () => {
    const user = userEvent.setup();
    m12Api();
    renderApp('/m12/dinh-huong');

    const card = await screen.findByRole('link', { name: /Lập trình viên Backend/ });
    expect(card).toHaveAttribute('href', '/m12/dinh-huong/nghe/backend');
    card.focus();
    expect(card).toHaveFocus();
    await user.keyboard('{Tab}');
    expect(card).not.toHaveFocus();
  });

  it('chip lọc có Tất cả và các nhóm; bấm chip gửi group, lưu vào URL, còn bấm lại Tất cả', async () => {
    const user = userEvent.setup();
    const fetchMock = m12Api();
    renderApp('/m12/dinh-huong');

    const chips = await screen.findByRole('group', { name: 'Lọc theo nhóm nghề' });
    const all = within(chips).getByRole('button', { name: 'Tất cả' });
    expect(all).toHaveAttribute('aria-pressed', 'true');

    const data = within(chips).getByRole('button', { name: /Trí tuệ nhân tạo và dữ liệu$/ });
    await user.click(data);
    await waitFor(() => expect(data).toHaveAttribute('aria-pressed', 'true'));
    expect(decodeURIComponent(search().replaceAll('+', ' '))).toContain(
      'group=Nhóm 2 – Trí tuệ nhân tạo và dữ liệu',
    );
    await waitFor(() =>
      expect(callsTo(fetchMock, '/api/m12/gallery').some((query) => query.get('group'))).toBe(true),
    );

    await user.click(all);
    await waitFor(() => expect(search()).not.toContain('group='));
  });

  it('ô tìm gửi q; không có kết quả thì báo trống và vẫn đổi được bộ lọc', async () => {
    const user = userEvent.setup();
    const fetchMock = m12Api('student', {
      [GALLERY_API]: (url) =>
        jsonResponse(200, galleryBody(String(url).includes('q=') ? [] : undefined)),
    });
    renderApp('/m12/dinh-huong');

    await screen.findAllByRole('link', { name: /Kỹ sư/ });
    await user.type(screen.getByRole('searchbox', { name: 'Tìm nghề' }), 'xyz');

    expect(await screen.findByText('Không có nghề phù hợp')).toBeInTheDocument();
    expect(callsTo(fetchMock, '/api/m12/gallery').some((query) => query.get('q') === 'xyz')).toBe(
      true,
    );
    expect(screen.getByRole('group', { name: 'Lọc theo nhóm nghề' })).toBeInTheDocument();
  });

  it('sinh viên chưa có nghề chính vẫn thấy lưới và có dải nhắc', async () => {
    m12Api('student', {
      [GALLERY_API]: () =>
        jsonResponse(
          200,
          galleryBody([galleryItem(AI, { closeness: null })], { has_primary: false }),
        ),
    });
    renderApp('/m12/dinh-huong');

    expect(await screen.findByText(/Chọn một nghề làm mục tiêu/)).toBeInTheDocument();
    expect(cardLink(AI.display_name)).toBeInTheDocument();
    expect(screen.queryByRole('img', { name: 'Mục tiêu chính của bạn' })).toBeNull();
  });

  it('đang tải, rồi lỗi có nút thử lại', async () => {
    const user = userEvent.setup();
    const pending = pendingResponse();
    let calls = 0;
    m12Api('student', {
      [GALLERY_API]: () => {
        calls += 1;
        return calls === 1 ? pending.handler() : jsonResponse(200, galleryBody());
      },
    });
    renderApp('/m12/dinh-huong');

    expect(await screen.findByText('Đang tải định hướng nghề...')).toBeInTheDocument();
    await act(async () => pending.resolve(apiError(500, 'SERVER', 'Máy chủ lỗi.')));
    expect(await screen.findByText('Không tải được định hướng nghề')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /Thử lại/ }));
    expect(await screen.findByRole('link', { name: /Kỹ sư/ })).toBeInTheDocument();
  });

  it('cố vấn xem: gửi student_id, liên kết giữ sinh viên đang chọn', async () => {
    const fetchMock = m12Api('advisor');
    renderApp('/m12/dinh-huong?student=DEMO05');

    const card = await screen.findByRole('link', { name: /Lập trình viên Backend/ });
    expect(card).toHaveAttribute('href', '/m12/dinh-huong/nghe/backend?student=DEMO05');
    expect(callsTo(fetchMock, '/api/m12/gallery')[0].get('student_id')).toBe('DEMO05');
  });

  it('cố vấn chưa chọn sinh viên: hướng dẫn, không gọi API', async () => {
    const fetchMock = m12Api('advisor');
    renderApp('/m12/dinh-huong');

    expect(await screen.findByText('Chưa chọn sinh viên')).toBeInTheDocument();
    await settled();
    expect(callsTo(fetchMock, '/api/m12/gallery')).toHaveLength(0);
  });

  it('nhân sự hỗ trợ không vào được', async () => {
    m12Api('support_staff');
    renderApp('/m12/dinh-huong');

    expect(await screen.findByRole('heading', { name: /không có quyền/i })).toBeInTheDocument();
  });
});

describe('trang lưới thẻ thay trang Xem tất cả (TC10)', () => {
  it('đường dẫn cũ chuyển về lưới thẻ và giữ sinh viên đang chọn', async () => {
    m12Api('advisor');
    renderApp('/m12/dinh-huong/tat-ca?student=DEMO05');

    await screen.findByRole('link', { name: /Lập trình viên Backend/ });
    expect(screen.getByTestId('path').textContent).toBe('/m12/dinh-huong');
    expect(search()).toContain('student=DEMO05');
  });

  it('chọn "Gần nghề chính": gọi lại API với sort, thứ tự đổi theo kết quả', async () => {
    const user = userEvent.setup();
    const fetchMock = m12Api('student', {
      [GALLERY_API]: (url) =>
        jsonResponse(
          200,
          galleryBody(
            String(url).includes('sort=closeness')
              ? [PRIMARY_ITEM, galleryItem(BACKEND), galleryItem(ANALYST)]
              : [PRIMARY_ITEM, galleryItem(ANALYST), galleryItem(BACKEND)],
          ),
        ),
    });
    renderApp('/m12/dinh-huong');

    await screen.findAllByRole('link', { name: /Kỹ sư/ });
    expect(cardNames()).toEqual([AI.display_name, ANALYST.display_name, BACKEND.display_name]);

    await user.selectOptions(screen.getByRole('combobox', { name: 'Sắp xếp' }), 'closeness');

    await waitFor(() =>
      expect(cardNames()).toEqual([AI.display_name, BACKEND.display_name, ANALYST.display_name]),
    );
    expect(search()).toContain('sort=closeness');
    expect(
      callsTo(fetchMock, '/api/m12/gallery').some((query) => query.get('sort') === 'closeness'),
    ).toBe(true);

    await user.selectOptions(screen.getByRole('combobox', { name: 'Sắp xếp' }), 'default');
    await waitFor(() => expect(search()).not.toContain('sort='));
  });
});

describe('trang chi tiết nghề: Hero', () => {
  it('có tên Việt, Anh, nhóm, tagline, mục tiêu đầu ra, chip phù hợp, câu định hướng', async () => {
    m12Api();
    renderApp(DETAIL_PATH);

    expect(await screen.findByRole('heading', { level: 1, name: AI.display_name })).toBeVisible();
    const hero = screen.getByRole('region', { name: AI.display_name });
    expect(within(hero).getByText('Trí tuệ nhân tạo và dữ liệu')).toBeInTheDocument();
    expect(hero).toHaveTextContent('AI Engineer');
    expect(within(hero).getByText(AI.tagline)).toBeInTheDocument();
    expect(hero).toHaveTextContent('Mục tiêu đầu ra: Đóng gói mô hình AI');
    expect(within(hero).getByText('Phù hợp với ngành của bạn: KHMT')).toBeInTheDocument();
    expect(within(hero).getByText('Ưu tiên KHMT.')).toBeInTheDocument();
  });

  it('2 vòng % tách riêng, luôn hiện độ phủ x/y; phân số chỉ nằm trong InfoPopover', async () => {
    const user = userEvent.setup();
    m12Api();
    renderApp(DETAIL_PATH);

    const hero = await screen.findByRole('region', { name: AI.display_name });
    expect(within(hero).getByText('22%')).toBeInTheDocument();
    expect(within(hero).getByText('33%')).toBeInTheDocument();
    expect(hero).toHaveTextContent('Ngành của bạn có 12/14 môn của nghề');
    expect(hero.querySelector('.career-meter__segment--outside').style.flexGrow).toBe('2');
    expect(hero.querySelector('.career-meter-legend')).toHaveTextContent('Ngoài CTĐT ngành bạn');
    expect(hero).not.toHaveTextContent('2/9 học phần');

    await user.click(within(hero).getByRole('button', { name: 'Giải thích tỷ lệ' }));
    const popover = hero.querySelector('.info-popover__content');
    expect(popover).toHaveTextContent('2/9 học phần');
    expect(popover).toHaveTextContent('1/3 kỹ năng & dự án');
    expect(popover).toHaveTextContent(DISCLAIMER);
  });

  it('D-325: cuối trang không còn câu về tuyển dụng và câu về danh mục CTĐT', async () => {
    m12Api();
    renderApp(DETAIL_PATH);

    await screen.findByRole('heading', { level: 1 });
    expect(screen.queryByText('Tỷ lệ không phản ánh khả năng được tuyển dụng.')).toBeNull();
    expect(screen.queryByText(/Danh mục theo CTĐT K68/)).toBeNull();
    expect(document.querySelector('.career-disclaimer')).toBeNull();
  });

  it('profile test: không có chip phù hợp, câu định hướng, câu K68 (D-325: bỏ câu tuyển dụng)', async () => {
    m12Api('student', {
      [DETAIL_API]: () =>
        jsonResponse(
          200,
          progressBody({
            fits_major: null,
            profile: { ...progressBody().profile, major_fit: null, objective: null, tagline: null },
          }),
        ),
    });
    renderApp(DETAIL_PATH);

    await screen.findByRole('heading', { level: 1 });
    expect(screen.queryByText('Tỷ lệ không phản ánh khả năng được tuyển dụng.')).toBeNull();
    expect(screen.queryByText(/Phù hợp với ngành của bạn/)).toBeNull();
    expect(screen.queryByText(/Danh mục theo CTĐT K68/)).toBeNull();
    expect(screen.queryByText(/Mục tiêu đầu ra/)).toBeNull();
  });

  it('có cảnh báo dữ liệu thì hiện', async () => {
    m12Api('student', {
      [DETAIL_API]: () =>
        jsonResponse(
          200,
          progressBody({
            data_warnings: [{ code: 'NO_SKILL_REQUIREMENTS', message: 'Chưa có yêu cầu kỹ năng.' }],
          }),
        ),
    });
    renderApp(DETAIL_PATH);

    expect(await screen.findByText(/Cảnh báo dữ liệu/)).toBeInTheDocument();
  });

  it('liên kết cũ theo id nghề chuyển sang slug', async () => {
    m12Api();
    renderApp('/m12/dinh-huong/nghe/career-ai');

    expect(await screen.findByRole('heading', { level: 1, name: AI.display_name })).toBeVisible();
  });

  it('nghề không tồn tại: báo lỗi', async () => {
    m12Api('student', { [DETAIL_API]: () => apiError(404, 'NOT_FOUND', 'Không tìm thấy.') });
    renderApp(DETAIL_PATH);

    expect(await screen.findByText('Không tải được nghề')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1, name: 'Chi tiết nghề' })).toBeVisible();
  });

  it('cố vấn chưa chọn sinh viên: hướng dẫn, không gọi API', async () => {
    const fetchMock = m12Api('advisor');
    renderApp(DETAIL_PATH);

    expect(await screen.findByText('Chưa chọn sinh viên')).toBeInTheDocument();
    await settled();
    expect(callsTo(fetchMock, '/api/m12/progress/careers/slug/ai')).toHaveLength(0);
  });

  it('có đường dẫn phân cấp về Định hướng nghề và mục sidebar vẫn sáng', async () => {
    m12Api();
    renderApp(DETAIL_PATH);

    await screen.findByRole('heading', { level: 1, name: AI.display_name });
    const trail = screen.getByRole('navigation', { name: 'Vị trí trang' });
    expect(within(trail).getByRole('link', { name: 'Định hướng nghề' })).toHaveAttribute(
      'href',
      '/m12/dinh-huong',
    );
    expect(within(trail).getByText('Chi tiết nghề')).toBeInTheDocument();
  });
});

describe('tab Lộ trình học', () => {
  it('tab mặc định; không còn dòng chú thích học kỳ chính thức và thứ tự khuyến nghị (D-317)', async () => {
    m12Api();
    await openRoadmap();

    expect(screen.getByRole('tab', { name: 'Lộ trình học' })).toHaveAttribute(
      'aria-selected',
      'true',
    );
    // D-317: quản lý dự án yêu cầu xóa dòng chú thích phía trên lộ trình.
    expect(screen.queryByText('Học kỳ chính thức theo CTĐT:')).toBeNull();
    expect(screen.queryByText('Thứ tự học khuyến nghị:')).toBeNull();
  });

  it('timeline: mỗi giai đoạn có %, sản phẩm cần đạt; mẫu số 0 hiện "—" và ghi là dự án', async () => {
    m12Api();
    const tree = await openRoadmap();

    const stage = within(tree).getByRole('treeitem', { name: /^Toán \+ lập trình/ });
    expect(within(stage).getByText('67%')).toBeInTheDocument();
    expect(stage).toHaveTextContent('Sản phẩm cần đạt: Python, NumPy');
    expect(stage).toHaveAccessibleName(/Toán \+ lập trình 67% Sản phẩm cần đạt/);
    expect(stage).not.toHaveAccessibleName(/Cơ sở lập trình/);
    const last = within(tree).getByRole('treeitem', { name: /^Portfolio/ });
    expect(within(last).getByText('—')).toBeInTheDocument();
    expect(last.closest('li')).toHaveTextContent('Giai đoạn này là dự án, không có học phần.');
  });

  it('chỉ có học phần trong timeline; mã theo ngành, BB/TC, HK n, mức ưu tiên và chip luôn thấy', async () => {
    m12Api();
    const tree = await openRoadmap();

    const row = within(tree).getByRole('treeitem', { name: /Cơ sở lập trình/ });
    expect(row).toHaveTextContent('CNTT1128');
    expect(row).toHaveTextContent('BB');
    expect(row).toHaveTextContent('HK 3');
    expect(row).toHaveTextContent('Cốt lõi');
    expect(within(row).getByRole('img', { name: 'Đạt' })).toBeInTheDocument();
    expect(within(tree).queryByRole('treeitem', { name: /Lập baseline/ })).toBeNull();
  });

  it('môn thiếu mã, TC, không có HK; môn ngoài ngành có nhãn và không có mã', async () => {
    m12Api();
    const tree = await openRoadmap();

    const noCode = within(tree).getByRole('treeitem', { name: /Môn chưa có mã/ });
    expect(noCode).toHaveTextContent('Chưa có mã');
    expect(noCode).toHaveTextContent('TC');
    expect(noCode).not.toHaveTextContent('HK');
    const absent = within(tree).getByRole('treeitem', { name: /Học máy/ });
    expect(absent).toHaveTextContent('Không có trong CTĐT ngành bạn');
    expect(absent).not.toHaveTextContent('Chưa có mã');
    expect(absent).toHaveClass('roadmap__item--absent');
  });

  it('có role tree, aria-expanded, chỉ một điểm dừng Tab', async () => {
    m12Api();
    const tree = await openRoadmap();

    const items = within(tree).getAllByRole('treeitem');
    expect(items[0]).toHaveAttribute('aria-expanded', 'true');
    expect(items.filter((item) => item.tabIndex === 0)).toHaveLength(1);
  });

  it('phím mũi tên, Home, End di chuyển và mở, đóng giai đoạn', async () => {
    const user = userEvent.setup();
    m12Api();
    const tree = await openRoadmap();
    const first = within(tree).getByRole('treeitem', { name: /^Toán \+ lập trình/ });
    first.focus();

    await user.keyboard('{ArrowDown}');
    expect(within(tree).getByRole('treeitem', { name: /Cơ sở lập trình/ })).toHaveFocus();
    await user.keyboard('{ArrowLeft}');
    expect(first).toHaveFocus();
    await user.keyboard('{ArrowLeft}');
    expect(first).toHaveAttribute('aria-expanded', 'false');
    expect(within(tree).queryByRole('treeitem', { name: /Cơ sở lập trình/ })).toBeNull();
    await user.keyboard('{ArrowRight}');
    expect(first).toHaveAttribute('aria-expanded', 'true');
    await user.keyboard('{ArrowRight}');
    expect(within(tree).getByRole('treeitem', { name: /Cơ sở lập trình/ })).toHaveFocus();
    await user.keyboard('{ArrowRight}');
    expect(within(tree).getByRole('treeitem', { name: /Cơ sở lập trình/ })).toHaveFocus();
    await user.keyboard('{End}');
    expect(within(tree).getByRole('treeitem', { name: /^Portfolio/ })).toHaveFocus();
    await user.keyboard('{ArrowUp}');
    expect(within(tree).getByRole('treeitem', { name: /Học máy/ })).toHaveFocus();
    await user.keyboard('{Home}');
    expect(first).toHaveFocus();
    await user.keyboard('{Enter}');
    expect(first).toHaveAttribute('aria-expanded', 'false');
    await user.keyboard(' ');
    expect(first).toHaveAttribute('aria-expanded', 'true');
  });

  it('bấm chuột vào giai đoạn thì đóng, mở', async () => {
    const user = userEvent.setup();
    m12Api();
    const tree = await openRoadmap();
    const first = within(tree).getByRole('treeitem', { name: /^Toán \+ lập trình/ });

    await user.click(first.querySelector('.roadmap__title'));
    expect(first).toHaveAttribute('aria-expanded', 'false');
  });
});

describe('SidePanel của môn', () => {
  async function openPanel(name = /Trí tuệ nhân tạo/) {
    const user = userEvent.setup();
    const tree = await openRoadmap();
    const row = within(tree).getByRole('treeitem', { name });
    await user.click(row);
    return { user, row };
  }

  it('Enter trên môn mở panel', async () => {
    const user = userEvent.setup();
    m12Api();
    const tree = await openRoadmap();
    within(tree)
      .getByRole('treeitem', { name: /^Toán \+ lập trình/ })
      .focus();

    await user.keyboard('{ArrowDown}{Enter}');
    expect(await screen.findByRole('dialog', { name: 'Cơ sở lập trình' })).toBeInTheDocument();
  });

  it('panel đủ: mục đích, tương đương, thứ tự khuyến nghị, nghề khác; đóng thì trả focus', async () => {
    m12Api();
    const { user, row } = await openPanel();

    const panel = await screen.findByRole('dialog', { name: 'Trí tuệ nhân tạo' });
    await within(panel).findByText('Thứ tự học khuyến nghị');
    expect(panel).toHaveTextContent('Học để làm gì? Học Trí tuệ nhân tạo');
    expect(panel).toHaveTextContent('Đạt qua tương đương: X1');
    expect(panel).toHaveTextContent('Tiên quyết');
    expect(panel).toHaveTextContent('Không có');
    expect(panel).toHaveTextContent('Nên học trước: TOKT1145 Xác suất');
    expect(panel).toHaveTextContent('không phải tiên quyết chính thức');
    expect(panel).toHaveTextContent('EP17.CNTT1140 Trí tuệ nhân tạo');
    expect(panel).toHaveTextContent('Học kỳ chính thức theo CTĐT');
    expect(panel).toHaveTextContent('HK 3');
    expect(within(panel).getByRole('link', { name: 'Phân tích dữ liệu' })).toHaveAttribute(
      'href',
      '/m12/dinh-huong/nghe/data',
    );

    await user.keyboard('{Escape}');
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(row).toHaveFocus();
  });

  it('tiên quyết chính thức tách khỏi thứ tự khuyến nghị; không có nghề khác, không có tương đương', async () => {
    const detail = {
      ...REQUIREMENT,
      prerequisites: [
        { course_id: 'A', code: null, name: 'Môn A', kind: 'prerequisite', source: null },
      ],
      equivalents: [],
      other_careers: [],
      short_desc: 'Mô tả ngắn',
    };
    m12Api('student', {
      'GET /api/m12/requirements/CNTT1140': () => jsonResponse(200, detail),
    });
    await openPanel();

    const panel = await screen.findByRole('dialog');
    await within(panel).findByText('Chỉ có ở nghề này.');
    expect(panel).toHaveTextContent('Chưa có mã Môn A');
    expect(panel).not.toHaveTextContent('Thứ tự học khuyến nghị');
    expect(panel).not.toHaveTextContent('Tương đương');
    expect(panel).toHaveTextContent('Mô tả ngắn');
  });

  it('môn có cảnh báo dữ liệu, thiếu mã, không ghi học kỳ', async () => {
    m12Api('student', {
      'GET /api/m12/requirements/NOCODE': () =>
        jsonResponse(200, { ...REQUIREMENT, code: null, prerequisites: [], equivalents: [] }),
    });
    await openPanel(/Môn chưa có mã/);

    const panel = await screen.findByRole('dialog');
    await within(panel).findByText('Nguồn ghi trùng mã.');
    expect(panel).toHaveTextContent('Không ghi');
    expect(panel).toHaveTextContent('Chưa có mã');
    expect(panel).toHaveTextContent('TC');
  });

  it('môn ngoài ngành: không gọi API, có nhãn, mục đích và không tính vào tỷ lệ', async () => {
    const fetchMock = m12Api();
    await openPanel(/Học máy/);

    const panel = await screen.findByRole('dialog', { name: 'Học máy' });
    expect(panel).toHaveTextContent('không tính vào tỷ lệ học phần');
    expect(panel).toHaveTextContent('Mức ưu tiên: Bổ trợ');
    expect(callsTo(fetchMock, '/api/m12/requirements/absent-s9')).toHaveLength(0);
  });

  it('panel lỗi có thông báo', async () => {
    m12Api('student', {
      'GET /api/m12/requirements/CNTT1140': () => apiError(500, 'SERVER', 'Máy chủ lỗi.'),
    });
    await openPanel();

    expect(await screen.findByText('Không tải được chi tiết')).toBeInTheDocument();
  });

  it('từ 1280px panel đẩy nội dung: không phải hộp thoại, không có nền che, Esc đóng và trả focus', async () => {
    stubPushLayout();
    m12Api();
    const { user, row } = await openPanel();

    const panel = await screen.findByRole('complementary', { name: 'Trí tuệ nhân tạo' });
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(document.querySelector('.side-panel__backdrop')).toBeNull();
    expect(document.querySelector('.career-detail')).toHaveClass('career-detail--with-panel');
    expect(within(panel).getByRole('button', { name: 'Đóng' })).toHaveFocus();

    await user.keyboard('a');
    expect(panel).toBeInTheDocument();
    await user.keyboard('{Escape}');
    await waitFor(() =>
      expect(screen.queryByRole('complementary', { name: /Trí tuệ/ })).toBeNull(),
    );
    expect(row).toHaveFocus();
    expect(document.querySelector('.career-detail')).not.toHaveClass('career-detail--with-panel');
  });

  it('nút Đóng của panel đẩy nội dung', async () => {
    stubPushLayout();
    m12Api();
    const { user } = await openPanel();

    const panel = await screen.findByRole('complementary', { name: 'Trí tuệ nhân tạo' });
    await user.click(within(panel).getByRole('button', { name: 'Đóng' }));
    expect(screen.queryByRole('complementary', { name: /Trí tuệ/ })).toBeNull();
  });
});

describe('tab Môn học NEU', () => {
  async function openTab() {
    const user = userEvent.setup();
    m12Api();
    await openRoadmap();
    await user.click(screen.getByRole('tab', { name: 'Môn học NEU' }));
    return { user, table: screen.getByRole('region', { name: 'Môn học NEU của nghề' }) };
  }

  it('bảng có đủ môn, mã, BB/TC, HK; môn ngoài ngành không có mã', async () => {
    const { table } = await openTab();
    const rows = within(table).getAllByRole('row');

    expect(rows).toHaveLength(5);
    expect(rows[1]).toHaveTextContent('Cơ sở lập trình');
    expect(rows[1]).toHaveTextContent('CNTT1128');
    expect(rows[1]).toHaveTextContent('HK 3');
    expect(rows[3]).toHaveTextContent('Chưa có mã');
    expect(rows[4]).toHaveTextContent('Không có trong CTĐT ngành bạn');
  });

  it('lọc theo Cốt lõi, Rất quan trọng, Nên chọn, Bổ trợ và BB/TC', async () => {
    const { user, table } = await openTab();
    const priority = screen.getByRole('group', { name: 'Lọc theo mức ưu tiên' });

    for (const name of ['Cốt lõi', 'Rất quan trọng', 'Nên chọn', 'Bổ trợ']) {
      await user.click(within(priority).getByRole('button', { name }));
      expect(within(table).getAllByRole('row')).toHaveLength(2);
    }
    await user.click(within(priority).getByRole('button', { name: 'Tất cả' }));

    const type = screen.getByRole('group', { name: 'Lọc theo BB/TC' });
    await user.click(within(type).getByRole('button', { name: 'TC' }));
    expect(within(table).getAllByRole('row')).toHaveLength(2);
    await user.click(within(type).getByRole('button', { name: 'BB' }));
    expect(within(table).getAllByRole('row')).toHaveLength(3);
  });

  it('bấm tên môn mở panel', async () => {
    const { user, table } = await openTab();

    await user.click(within(table).getByRole('button', { name: 'Trí tuệ nhân tạo' }));
    expect(await screen.findByRole('dialog', { name: 'Trí tuệ nhân tạo' })).toBeInTheDocument();
  });
});

describe('tab Kỹ năng & dự án', () => {
  async function openTab(extra) {
    const user = userEvent.setup();
    m12Api('student', extra);
    await openRoadmap();
    await user.click(screen.getByRole('tab', { name: 'Kỹ năng & dự án' }));
  }

  it('checklist có trạng thái minh chứng', async () => {
    await openTab();

    const list = screen.getByRole('region', { name: 'Checklist sẵn sàng thực tập' });
    const row = (name) => within(list).getByText(name).parentElement;
    expect(within(row('Lập baseline')).getByRole('img', { name: 'Đạt' })).toBeInTheDocument();
    expect(
      within(row('Giải thích metric')).getByRole('img', { name: 'Chờ duyệt' }),
    ).toBeInTheDocument();
    expect(
      within(row('Viết báo cáo')).getByRole('img', { name: 'Chưa có minh chứng' }),
    ).toBeInTheDocument();
  });

  it('3 dự án xếp Starter, Intermediate, Job-ready, có tiêu chí', async () => {
    await openTab();

    const section = screen.getByRole('region', { name: 'Dự án portfolio' });
    const projects = within(section).getAllByRole('article');
    expect(projects.map((item) => item.querySelector('h3').textContent)).toEqual([
      'Dự án nhỏ',
      'Dự án vừa',
      'Dự án lớn',
    ]);
    expect(projects[0]).toHaveTextContent('Starter');
    expect(projects[0]).toHaveTextContent('Tiêu chí Dự án nhỏ');
    expect(
      within(projects[0]).getByRole('img', { name: 'Chưa có minh chứng' }),
    ).toBeInTheDocument();
  });

  it('câu lưu ý nằm dưới khối Tự học, không phải một mục trong danh sách', async () => {
    const body = progressBody();
    await openTab({
      [DETAIL_API]: () =>
        jsonResponse(200, {
          ...body,
          profile: { ...body.profile, self_study_note: 'chỉ thực hành trên hệ thống được phép' },
        }),
    });

    const block = screen.getByRole('region', { name: 'Tự học ngoài chương trình' });
    const note = within(block).getByText(/chỉ thực hành trên hệ thống được phép/);
    expect(note.tagName).toBe('P');
    expect(
      within(block)
        .getAllByRole('listitem')
        .map((item) => item.textContent),
    ).toEqual(['PyTorch', 'FastAPI']);
  });

  it('khối Tự học có ghi chú không phải học phần chính thức', async () => {
    await openTab();

    const block = screen.getByRole('region', { name: 'Tự học ngoài chương trình' });
    expect(block).toHaveTextContent('Không phải học phần chính thức của NEU');
    expect(within(block).getByText('PyTorch')).toBeInTheDocument();
  });

  it('nghề không có kỹ năng, dự án, tự học: không có khối trống', async () => {
    await openTab({
      [DETAIL_API]: () =>
        jsonResponse(
          200,
          progressBody({
            nodes: [{ ...NODES[0], children: [child('CNTT1128', 'Cơ sở lập trình', 'done')] }],
            profile: { ...progressBody().profile, self_study: [] },
          }),
        ),
    });

    expect(screen.queryByRole('region', { name: 'Checklist sẵn sàng thực tập' })).toBeNull();
    expect(screen.queryByRole('region', { name: 'Dự án portfolio' })).toBeNull();
    expect(screen.queryByRole('region', { name: 'Tự học ngoài chương trình' })).toBeNull();
  });
});

describe('đặt làm mục tiêu chính (TC08)', () => {
  const NOT_PRIMARY = () =>
    jsonResponse(200, progressBody({ is_primary: false, fits_major: null }));

  it('nghề chính có ngôi sao (D-305), không có nút', async () => {
    m12Api();
    renderApp(DETAIL_PATH);

    const hero = await screen.findByRole('region', { name: AI.display_name });
    expect(within(hero).getByRole('img', { name: 'Mục tiêu chính của bạn' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Đặt làm mục tiêu chính' })).toBeNull();
  });

  it('cố vấn, quản trị không có nút', async () => {
    m12Api('advisor', { [DETAIL_API]: NOT_PRIMARY });
    renderApp(`${DETAIL_PATH}?student=DEMO05`);

    await screen.findByRole('region', { name: AI.display_name });
    expect(screen.queryByRole('button', { name: 'Đặt làm mục tiêu chính' })).toBeNull();
  });

  it('hộp xác nhận ghi rõ không mất lịch sử; Hủy thì không gọi API, trả focus', async () => {
    const user = userEvent.setup();
    const fetchMock = m12Api('student', { [DETAIL_API]: NOT_PRIMARY });
    renderApp(DETAIL_PATH);

    const button = await screen.findByRole('button', { name: 'Đặt làm mục tiêu chính' });
    await user.click(button);
    const dialog = screen.getByRole('alertdialog', { name: /Đặt làm mục tiêu chính/ });
    expect(dialog).toHaveTextContent('Lịch sử học tập và tiến độ không bị mất');
    expect(dialog).toHaveTextContent(AI.display_name);

    await user.click(within(dialog).getByRole('button', { name: 'Hủy' }));
    expect(screen.queryByRole('alertdialog')).toBeNull();
    expect(button).toHaveFocus();
    expect(fetchMock.mock.calls.some(([, options]) => options?.method === 'PUT')).toBe(false);
  });

  it('xác nhận: PUT, báo thành công, tải lại nên thành nghề chính', async () => {
    const user = userEvent.setup();
    let primary = false;
    const fetchMock = m12Api('student', {
      [DETAIL_API]: () => jsonResponse(200, progressBody({ is_primary: primary })),
      'PUT /api/m12/career-goal': () => {
        primary = true;
        return jsonResponse(200, { career: AI });
      },
    });
    renderApp(DETAIL_PATH);

    await user.click(await screen.findByRole('button', { name: 'Đặt làm mục tiêu chính' }));
    await user.click(screen.getByRole('button', { name: 'Xác nhận' }));

    expect(await screen.findByText(`Đã đặt ${AI.display_name} làm mục tiêu chính.`)).toBeVisible();
    await waitFor(() =>
      expect(screen.queryByRole('button', { name: 'Đặt làm mục tiêu chính' })).toBeNull(),
    );
    const [, options] = fetchMock.mock.calls.find(([, item]) => item?.method === 'PUT');
    expect(JSON.parse(options.body)).toEqual({ career_id: AI.id });
  });

  it('lỗi: giữ hộp xác nhận và hiện thông báo', async () => {
    const user = userEvent.setup();
    m12Api('student', {
      [DETAIL_API]: NOT_PRIMARY,
      'PUT /api/m12/career-goal': () => apiError(422, 'INVALID', 'Không đổi được nghề.'),
    });
    renderApp(DETAIL_PATH);

    await user.click(await screen.findByRole('button', { name: 'Đặt làm mục tiêu chính' }));
    await user.click(screen.getByRole('button', { name: 'Xác nhận' }));

    expect(await screen.findByText('Không đổi được nghề.')).toBeInTheDocument();
    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
  });
});
