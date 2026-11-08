/** CR-08 (D-306): Tổng quan theo ảnh mẫu – dải hồ sơ, thẻ 2×2, biểu đồ tròn tín chỉ, biểu đồ cột GPA. */
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { apiError, jsonResponse, renderApp } from '../../test/fakeApi';
import {
  creditPieData,
  formatTenths,
  gpaBarData,
  PIE_PARTS,
  pieRadius,
  roundTenths,
} from './OverviewCharts';
import { callsTo, CREDITS, m11Api, overviewBody, TREND } from './testData';

/** Số thật của thiennhan (demo-k68) qua /api/m11/credits và /api/m11/gpa-trend, ngày 08/11/2026. */
const THIENNHAN_CREDITS = {
  S5: {
    passed: 77,
    debt: 3,
    in_progress: 9,
    required: { total_credits: 76, passed_credits: 44, missing_credits: 32 },
    elective_groups: [
      { min_credits: 12, passed_credits: 12, missing_credits: 0 },
      { min_credits: 12, passed_credits: 12, missing_credits: 0 },
      { min_credits: 30, passed_credits: 9, missing_credits: 21 },
    ],
  },
  S3: {
    passed: 56,
    debt: 6,
    in_progress: 0,
    required: { total_credits: 76, passed_credits: 35, missing_credits: 41 },
    elective_groups: [
      { min_credits: 12, passed_credits: 9, missing_credits: 3 },
      { min_credits: 12, passed_credits: 12, missing_credits: 0 },
      { min_credits: 30, passed_credits: 0, missing_credits: 30 },
    ],
  },
};

const THIENNHAN_POINTS = [
  { semester_id: 'S1', order: 1, name: 'HK1 2024-2025', value: '3.23' },
  { semester_id: 'S2', order: 2, name: 'HK2 2024-2025', value: '2.78' },
  { semester_id: 'S3', order: 3, name: 'HK1 2025-2026', value: '2.84' },
  { semester_id: 'S4', order: 4, name: 'HK2 2025-2026', value: '3.50' },
  { semester_id: 'S5', order: 5, name: 'HK1 2026-2027', value: null },
];

const sumTenths = (data) => data.parts.reduce((sum, part) => sum + part.tenths, 0);
const sumCredits = (data) => data.parts.reduce((sum, part) => sum + part.credits, 0);

describe('dữ liệu biểu đồ tròn tín chỉ', () => {
  it('thiennhan kỳ hiện tại: tổng 130 tín chỉ CTĐT, 77 đạt, 3 chưa đạt, 50 chưa học (gồm 9 đang học)', () => {
    const data = creditPieData(THIENNHAN_CREDITS.S5);

    expect(data.total).toBe(130);
    expect(data.parts.map((part) => [part.key, part.credits, part.percent])).toEqual([
      ['passed', 77, '59,2%'],
      ['failed', 3, '2,3%'],
      ['remaining', 50, '38,5%'],
    ]);
    expect(sumCredits(data)).toBe(130);
    expect(sumTenths(data)).toBe(1000);
  });

  it('thiennhan kỳ đã qua HK1 2025-2026: 56 đạt, 6 chưa đạt, 68 chưa học, cộng đúng 100%', () => {
    const data = creditPieData(THIENNHAN_CREDITS.S3);

    expect(data.parts.map((part) => [part.credits, part.percent])).toEqual([
      [56, '43,1%'],
      [6, '4,6%'],
      [68, '52,3%'],
    ]);
    expect(sumTenths(data)).toBe(1000);
  });

  it('chỉ tính tín chỉ đáp ứng CTĐT: phần vượt nhóm tự chọn không làm tổng vượt 100%', () => {
    // CREDITS: nhóm tự chọn đạt 9/6 (vượt 3), passed = 19 nhưng chỉ 15 + 6 = 21 tín chỉ đáp ứng CTĐT.
    const data = creditPieData(CREDITS);

    expect(data.total).toBe(66);
    expect(data.parts[0].credits).toBe(21);
    expect(sumCredits(data)).toBe(66);
    expect(sumTenths(data)).toBe(1000);
  });

  it('tín chỉ nợ lớn hơn phần CTĐT còn thiếu (môn nợ ngoài CTĐT): phần chưa đạt không vượt phần còn thiếu', () => {
    const credits = {
      ...THIENNHAN_CREDITS.S5,
      debt: 60,
    };
    const data = creditPieData(credits);

    expect(data.parts.map((part) => part.credits)).toEqual([77, 53, 0]);
    expect(sumCredits(data)).toBe(130);
  });

  it('khóa không có quy chế (số đạt null) hoặc CTĐT không có tín chỉ: không vẽ', () => {
    const noRule = {
      ...CREDITS,
      passed: null,
      debt: null,
      required: { total_credits: 60, passed_credits: null, missing_credits: null },
    };
    const empty = {
      ...CREDITS,
      required: { total_credits: 0, passed_credits: 0, missing_credits: 0 },
      elective_groups: [],
    };

    expect(creditPieData(noRule)).toBeNull();
    expect(creditPieData(empty)).toBeNull();
  });

  it('ba phần theo đúng màu ảnh mẫu: xanh lá đạt, đỏ chưa đạt, xanh dương chưa học', () => {
    expect(PIE_PARTS.map((part) => [part.key, part.color])).toEqual([
      ['passed', 'var(--chart-passed)'],
      ['failed', 'var(--chart-failed)'],
      ['remaining', 'var(--chart-remaining)'],
    ]);
  });
});

describe('làm tròn phần trăm', () => {
  it('ba phần bằng nhau: phần đứng trước nhận 0,1% còn thiếu', () => {
    expect(roundTenths([1, 1, 1], 3)).toEqual([334, 333, 333]);
    expect(roundTenths([1, 1, 1], 3).map(formatTenths)).toEqual(['33,4%', '33,3%', '33,3%']);
  });

  it('mọi cách chia tổng 1–200 tín chỉ thành 3 phần đều cộng đúng 100,0%, mỗi phần lệch dưới 0,1%', () => {
    for (let total = 1; total <= 200; total += 1) {
      for (let first = 0; first <= total; first += 7) {
        for (let second = 0; second <= total - first; second += 5) {
          const amounts = [first, second, total - first - second];
          const tenths = roundTenths(amounts, total);
          expect(tenths.reduce((sum, item) => sum + item, 0)).toBe(1000);
          amounts.forEach((amount, index) => {
            expect(Math.abs(tenths[index] * total - amount * 1000)).toBeLessThan(total);
          });
        }
      }
    }
  });

  it('phần 0 tín chỉ là 0,0%; một phần chiếm hết là 100,0%', () => {
    expect(roundTenths([0, 0, 130], 130).map(formatTenths)).toEqual(['0,0%', '0,0%', '100,0%']);
  });
});

describe('dữ liệu biểu đồ cột Điểm trung bình', () => {
  it('thiennhan kỳ hiện tại: không có cột cho HK1 2026-2027 (đang học), tên kỳ đầy đủ', () => {
    const bars = gpaBarData(THIENNHAN_POINTS);

    expect(bars.map((bar) => bar.name)).toEqual([
      'HK1 2024-2025',
      'HK2 2024-2025',
      'HK1 2025-2026',
      'HK2 2025-2026',
    ]);
    expect(bars.map((bar) => bar.raw)).toEqual(['3.23', '2.78', '2.84', '3.50']);
  });

  it('kỳ đã qua: chỉ các kỳ tính đến kỳ đang chọn (API trả tới HK1 2025-2026)', () => {
    expect(gpaBarData(THIENNHAN_POINTS.slice(0, 3)).map((bar) => bar.name)).toEqual([
      'HK1 2024-2025',
      'HK2 2024-2025',
      'HK1 2025-2026',
    ]);
  });

  it('kỳ có GPA giữa chừng bị trống (chỉ có môn không tính GPA) thì không có cột', () => {
    const points = [
      THIENNHAN_POINTS[0],
      { ...THIENNHAN_POINTS[1], value: null },
      THIENNHAN_POINTS[2],
    ];
    expect(gpaBarData(points).map((bar) => bar.name)).toEqual(['HK1 2024-2025', 'HK1 2025-2026']);
  });
});

describe('bán kính biểu đồ tròn', () => {
  it('chừa chỗ cho nhãn hai bên, không nhỏ hơn 40, không lớn hơn 100', () => {
    expect(pieRadius(290)).toBe(73);
    expect(pieRadius(120)).toBe(40);
    expect(pieRadius(800)).toBe(100);
  });
});

describe('trang Tổng quan CR-08', () => {
  it('dải hồ sơ: "Mã SV - Họ tên", "Khóa · Ngành", bộ chọn kỳ; không còn "Đang xem", "Kỳ hiện tại"', async () => {
    m11Api('student');

    renderApp('/');

    const band = await screen.findByRole('region', { name: 'Lời chào' });
    expect(await within(band).findByText('SV01 - Sinh viên 01')).toBeInTheDocument();
    expect(within(band).getByText('K66 · CNTT')).toBeInTheDocument();
    expect(within(band).getByLabelText('Học kỳ')).toHaveValue('S5');
    expect(
      within(band).getByRole('option', { name: 'HK1 2026-2027 – hiện tại' }),
    ).toBeInTheDocument();
    expect(band.textContent).not.toMatch(/Đang xem|Kỳ hiện tại|Kỳ đã qua|Chào /);
  });

  it('4 thẻ chỉ có nhãn, nút "i" và số; không có dòng phụ, mức cảnh báo, dòng thời gian', async () => {
    const fetchMock = m11Api('student');

    renderApp('/');
    await screen.findByText('3,11');

    const cards = screen.getAllByRole('article');
    expect(cards).toHaveLength(4);
    for (const card of cards) {
      expect(card.querySelectorAll('.metric-card__detail')).toHaveLength(0);
      expect(card.className).toBe('metric-card');
      expect(within(card).getAllByRole('button', { name: /^Giải thích: / })).toHaveLength(1);
    }
    const main = document.querySelector('.m11-page');
    expect(main.textContent).not.toMatch(
      /Mức cảnh báo chung|Tính lúc|Điểm cập nhật|Quy chế|Kỳ tham chiếu|Cảnh báo dữ liệu|Riêng |Tính đến /,
    );
    expect(callsTo(fetchMock, '/api/m11/risks')).toEqual([]);
  });

  it('GPA học kỳ trống: chỉ có gạch, không có dòng Q80', async () => {
    const fetchMock = m11Api('student', {
      'GET /api/m11/overview': () => {
        const body = overviewBody({ gpa: null });
        body.metrics.semester_gpa.denominator = 0;
        return jsonResponse(200, body);
      },
    });

    renderApp('/');

    const card = (await screen.findByRole('link', { name: 'GPA học kỳ' })).closest('article');
    await waitFor(() => expect(within(card).getByText('—')).toBeInTheDocument());
    expect(card.textContent).not.toMatch(/Kỳ này chưa có kết quả|Gần nhất/);
    expect(callsTo(fetchMock, '/api/m11/gpa-trend')).toHaveLength(1);
  });

  it('hai biểu đồ gọi /credits và /gpa-trend theo kỳ đang chọn; bảng số cho trình đọc màn hình', async () => {
    const fetchMock = m11Api('student', {
      'GET /api/m11/credits': () => jsonResponse(200, { ...CREDITS, ...THIENNHAN_CREDITS.S3 }),
      'GET /api/m11/gpa-trend': () =>
        jsonResponse(200, { ...TREND, points: THIENNHAN_POINTS.slice(0, 3) }),
    });

    renderApp('/?semester=S4');

    const pie = await screen.findByRole('table', { name: 'Tín chỉ theo CTĐT' });
    expect(
      within(pie)
        .getAllByRole('row')
        .slice(1)
        .map((row) => row.textContent),
    ).toEqual(['Tín chỉ đã đạt5643,1%', 'Tín chỉ chưa đạt64,6%', 'Tín chỉ chưa học6852,3%']);
    const bars = screen.getByRole('table', { name: 'Điểm trung bình theo kỳ' });
    expect(within(bars).getAllByRole('row')).toHaveLength(4);
    expect(bars.textContent).not.toContain('HK1 2026-2027');
    expect(callsTo(fetchMock, '/api/m11/credits').at(-1).get('semester_id')).toBe('S4');
    expect(callsTo(fetchMock, '/api/m11/gpa-trend').at(-1).get('semester_id')).toBe('S4');
    expect(screen.getByText(/Tổng 130 tín chỉ theo CTĐT: đã đạt 56 \(43,1%\)/)).toBeInTheDocument();
    expect(
      screen.getByText(/Điểm trung bình hệ 4 các kỳ đã có điểm: HK1 2024-2025: 3,23/),
    ).toBeInTheDocument();
  });

  it('chưa có kỳ nào có điểm, khóa không có quy chế: hai biểu đồ có trạng thái rỗng', async () => {
    m11Api('student', {
      'GET /api/m11/credits': () =>
        jsonResponse(200, {
          ...CREDITS,
          passed: null,
          debt: null,
          required: { total_credits: 60, passed_credits: null, missing_credits: null },
        }),
      'GET /api/m11/gpa-trend': () =>
        jsonResponse(200, { ...TREND, points: [THIENNHAN_POINTS[4]] }),
    });

    renderApp('/');

    expect(await screen.findByText('Chưa vẽ được biểu đồ tín chỉ')).toBeInTheDocument();
    expect(await screen.findByText('Chưa có kỳ nào có điểm')).toBeInTheDocument();
  });

  it('biểu đồ lỗi: thẻ số liệu vẫn hiện, biểu đồ báo lỗi và thử lại được', async () => {
    let calls = 0;
    m11Api('student', {
      'GET /api/m11/credits': () => {
        calls += 1;
        return calls === 1
          ? apiError(500, 'INTERNAL_ERROR', 'Lỗi')
          : jsonResponse(200, { ...CREDITS, ...THIENNHAN_CREDITS.S5 });
      },
    });
    const user = userEvent.setup();

    renderApp('/');

    expect(await screen.findByText('Không tải được biểu đồ tín chỉ')).toBeInTheDocument();
    expect(screen.getByText('3,11')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /Thử lại/ }));
    expect(await screen.findByRole('table', { name: 'Tín chỉ theo CTĐT' })).toBeInTheDocument();
  });

  it('cố vấn: dải hồ sơ là sinh viên đang chọn, lấy từ /api/students/<id>', async () => {
    m11Api('advisor', {
      'GET /api/students/SV04': () =>
        jsonResponse(200, {
          id: 'SV04',
          student_code: 'SV04',
          full_name: 'Sinh viên 04',
          cohort: 'K66',
          program: { name: 'CNTT' },
        }),
    });

    renderApp('/?student=SV04');

    const band = await screen.findByRole('region', { name: 'Lời chào' });
    expect(await within(band).findByText('SV04 - Sinh viên 04')).toBeInTheDocument();
    expect(within(band).getByText('K66 · CNTT')).toBeInTheDocument();
  });

  it('cố vấn chưa chọn sinh viên: dải ghi lời chào và vai trò, không gọi API hồ sơ', async () => {
    const fetchMock = m11Api('advisor');

    renderApp('/');

    const band = await screen.findByRole('region', { name: 'Lời chào' });
    expect(within(band).getByText('Chào Người dùng advisor')).toBeInTheDocument();
    expect(fetchMock.mock.calls.filter(([url]) => String(url).startsWith('/api/students'))).toEqual(
      [],
    );
  });

  it('lối tắt: 4 liên kết Kết quả, Phân tích, Định hướng nghề, Yêu cầu hỗ trợ, có mô tả', async () => {
    m11Api('student');

    renderApp('/');

    const shortcuts = await screen.findByRole('region', { name: 'Lối tắt' });
    const links = within(shortcuts).getAllByRole('link');
    expect(links.map((link) => link.querySelector('strong').textContent)).toEqual([
      'Kết quả',
      'Phân tích',
      'Định hướng nghề',
      'Yêu cầu hỗ trợ',
    ]);
    expect(links[0]).toHaveTextContent('Xem bảng điểm và lịch sử học lại');
  });
});
