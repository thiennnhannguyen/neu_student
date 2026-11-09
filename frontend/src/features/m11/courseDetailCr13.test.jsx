/** CR-13 (D-314): bảng 2 cột Môn học · Điểm dự kiến và trang chi tiết môn. */
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { apiError, jsonResponse, renderApp } from '../../test/fakeApi';
import { percentText } from './CourseDetailPage';
import { COURSE_DETAIL, CURRENT_COURSES, callsTo, m11Api } from './testData';

const prediction = (level, score = null, letter = null, reasons = []) => ({
  level,
  score,
  letter,
  range: score ? { low: '5.00', high: '8.00' } : null,
  confidence: score ? 'medium' : null,
  reasons,
});

function course(id, code, name, value) {
  return {
    course: { id, code, name, credits: 3 },
    schedule: null,
    latest: null,
    prediction: value,
  };
}

const FIVE = {
  ...CURRENT_COURSES,
  items: [
    course('A', 'CNTT0001', 'Môn cấm thi', prediction('barred')),
    course('B', 'CNTT0002', 'Môn nguy cơ', prediction('high', '6.78', 'C+')),
    course('C', 'CNTT0003', 'Môn chú ý', prediction('watch', '7.68', 'B')),
    course('D', 'CNTT0004', 'Môn ổn', prediction('ok', '8.98', 'A')),
    course('E', null, 'Môn chưa có dữ liệu', prediction('insufficient')),
  ],
};

async function courseTable() {
  return screen.findByRole('table', { name: 'Môn đang học và điểm dự kiến' });
}

describe('Bảng "Môn đang học kỳ này" (D-314)', () => {
  it('đúng 2 cột; tên đậm, mã chữ nhỏ; giữ thứ tự của API', async () => {
    m11Api('student', {
      'GET /api/m11/current-courses': () => jsonResponse(200, FIVE),
    });
    renderApp('/m11/phan-tich');
    const table = await courseTable();
    expect(
      within(table)
        .getAllByRole('columnheader')
        .map((cell) => cell.textContent),
    ).toEqual(['Môn học', 'Điểm dự kiến']);
    const rows = within(table).getAllByRole('row').slice(1);
    expect(rows.map((row) => within(row).getAllByRole('cell').length + 1)).toEqual([2, 2, 2, 2, 2]);
    expect(rows.map((row) => row.querySelector('.course-row__name').textContent)).toEqual([
      'Môn cấm thi',
      'Môn nguy cơ',
      'Môn chú ý',
      'Môn ổn',
      'Môn chưa có dữ liệu',
    ]);
    expect(rows[1].querySelector('.course-row__code')).toHaveTextContent('CNTT0002');
    expect(rows[4].querySelector('.course-row__code')).toHaveTextContent('Chưa có mã');
  });

  it('ô điểm: số và điểm chữ; icon kèm chữ chỉ khi có cảnh báo; không đủ điều kiện, chưa đủ dữ liệu', async () => {
    m11Api('student', {
      'GET /api/m11/current-courses': () => jsonResponse(200, FIVE),
    });
    renderApp('/m11/phan-tich');
    const rows = within(await courseTable())
      .getAllByRole('row')
      .slice(1);
    const score = (row) => within(row).getByRole('cell');
    expect(score(rows[0])).toHaveTextContent('Không đủ điều kiện dự thi');
    expect(score(rows[0])).not.toHaveTextContent(/\d/);
    expect(score(rows[1])).toHaveTextContent('6,78 C+Nguy cơ cao');
    expect(score(rows[2])).toHaveTextContent('7,68 BCần chú ý');
    expect(score(rows[3])).toHaveTextContent(/^8,98 A$/);
    expect(score(rows[4])).toHaveTextContent(/^Chưa đủ dữ liệu$/);
    for (const row of rows.slice(0, 3)) {
      expect(score(row).querySelector('.level-mark svg')).not.toBeNull();
    }
    expect(score(rows[3]).querySelector('.level-mark')).toBeNull();
    // Không có khối màu: chỉ chữ và icon.
    expect(score(rows[1]).querySelector('.status-icon--danger')).toHaveClass('level-mark');
  });

  it('cả dòng là một liên kết sang trang chi tiết, có mũi tên, giữ ?student= cho cố vấn', async () => {
    const user = userEvent.setup();
    const fetchMock = m11Api('advisor');
    renderApp('/m11/phan-tich?student=SV04');
    const table = await courseTable();
    const link = within(table).getByRole('link', {
      name: 'Lập trình Web CNTT1188: điểm dự kiến 6,78 C+ · Nguy cơ cao',
    });
    expect(link).toHaveAttribute('href', '/m11/phan-tich/mon/CNTT1188?student=SV04');
    expect(link.closest('tr').querySelector('.course-row__arrow')).not.toBeNull();
    // Bấm ô điểm (ngoài liên kết) cũng mở trang chi tiết: cả dòng bấm được.
    await user.click(within(link.closest('tr')).getByRole('cell'));
    expect(await screen.findByRole('heading', { level: 1, name: 'Lập trình Web' })).toBeVisible();
    const query = callsTo(fetchMock, '/api/m11/courses/CNTT1188/prediction').at(-1);
    expect(query.get('student_id')).toBe('SV04');
  });

  it('khối Cảnh báo học vụ phía trên vẫn giữ; có dòng tham khảo', async () => {
    m11Api('student');
    renderApp('/m11/phan-tich');
    await courseTable();
    expect(screen.getByRole('heading', { name: 'Cảnh báo học vụ' })).toBeInTheDocument();
    expect(
      screen.getByText(/Dự kiến chỉ mang tính tham khảo, dựa trên dữ liệu mô phỏng\./),
    ).toBeInTheDocument();
  });
});

describe('Trang chi tiết môn (D-314)', () => {
  async function openDetail(extra = {}) {
    const fetchMock = m11Api('student', extra);
    renderApp('/m11/phan-tich/mon/CNTT1188');
    await screen.findByRole('heading', { level: 1, name: 'Lập trình Web' });
    return fetchMock;
  }

  it('a) điểm dự kiến, khoảng, độ tin cậy, mức và lý do', async () => {
    await openDetail();
    const summary = document.querySelector('.prediction-summary');
    expect(summary).toHaveTextContent('6,78C+');
    expect(summary).toHaveTextContent('Khoảng dự kiến5,32–8,25');
    expect(summary).toHaveTextContent('Độ tin cậyTrung bình');
    expect(summary).toHaveTextContent('Mức cảnh báoNguy cơ cao');
    const reasons = within(summary).getByRole('list', { name: 'Lý do' });
    expect(
      within(reasons)
        .getAllByRole('listitem')
        .map((item) => item.textContent),
    ).toEqual(['Nguy cơ caoThiếu 3/7 bài đã quá hạn']);
  });

  it('b) thành phần 10/40/50, phần nào là số thật, phần nào ước lượng; điều chỉnh cuối kỳ', async () => {
    await openDetail();
    const table = screen.getByRole('table', { name: 'Thành phần điểm dự kiến' });
    const rows = within(table).getAllByRole('row').slice(1);
    expect(rows.map((row) => row.textContent)).toEqual([
      expect.stringMatching(/^Chuyên cần10%10,00Ước lượng từ số thật: có mặt 8\/8 buổi đã học/),
      expect.stringMatching(
        /^Quá trình40%5,37Số thật và ước lượng: điểm quá trình hiện tại 4,81 trên 8 bài tập, bài kiểm tra; kéo về mức nền 7,58/,
      ),
      expect.stringMatching(
        /^Cuối kỳ50%7,28Ước lượng: mức nền 7,58 – trung bình các môn đã học \(28 môn\), điều chỉnh -0,30\./,
      ),
    ]);
    const adjustments = document.querySelector('.adjustment-list');
    expect(adjustments).toHaveTextContent('Tự học khoảng 0,50 giờ/tuần-0,30');
    expect(adjustments).toHaveTextContent('Mức hiểu bài trung bình 4,00 (4 báo cáo gần nhất)+0,50');
  });

  it('c) cuối kỳ cần bao nhiêu: số, "Không đạt được", "Đã chắc chắn"', async () => {
    await openDetail({
      'GET /api/m11/courses/CNTT1188/prediction': () =>
        jsonResponse(200, {
          ...COURSE_DETAIL,
          prediction: {
            ...COURSE_DETAIL.prediction,
            targets: [
              { letter: 'C', score: '5.50', status: 'secured', needed: null },
              ...COURSE_DETAIL.prediction.targets.slice(1),
            ],
          },
        }),
    });
    const section = screen.getByRole('heading', {
      name: 'Cuối kỳ cần bao nhiêu điểm',
    }).parentElement;
    expect(section).toHaveTextContent('Đạt C (5,5)Đã chắc chắn');
    expect(section).toHaveTextContent('Đạt B (7,0)7,71');
    expect(section).toHaveTextContent('Đạt A (8,5)Không đạt được');
  });

  it('d) chuyên cần, điểm hiện tại từ LMS, bài tập, bài kiểm tra, báo cáo tuần, lịch học', async () => {
    await openDetail();
    const heading = (name) => screen.getByRole('heading', { name }).parentElement;
    expect(heading('Chuyên cần')).toHaveTextContent('Buổi đã học8/15');
    expect(heading('Chuyên cần')).toHaveTextContent('Vắng không phép0');
    expect(heading('Chuyên cần')).toHaveTextContent('Vắng có phép0');
    expect(heading(/Điểm hiện tại từ LMS/)).toHaveTextContent('Điểm bài tập hiện tại4,43');
    expect(heading(/Điểm hiện tại từ LMS/)).toHaveTextContent('Điểm quá trình hiện tại4,81');
    const assignments = screen.getByRole('table', { name: 'Bài tập của môn' });
    expect(within(assignments).getAllByRole('row')).toHaveLength(4);
    expect(within(assignments).getByText('Quá hạn chưa nộp')).toBeVisible();
    expect(within(assignments).getByText('Nộp muộn')).toBeVisible();
    expect(screen.getByRole('table', { name: 'Bài kiểm tra của môn' })).toHaveTextContent(
      'Kiểm tra 1',
    );
    expect(heading('Báo cáo tuần')).toHaveTextContent('Đã nộp 7/7 · gần nhất tuần 7 (20/10/2026)');
    expect(heading('Lịch học')).toHaveTextContent('Thứ 4, buổi đầu 02/09/2026, 15 buổi');
    expect(heading('Lịch học')).toHaveTextContent('Tuần 8 (21/10/2026–27/10/2026)');
  });

  it('d) nút Xem mở báo cáo tuần chỉ đọc của đúng môn', async () => {
    const user = userEvent.setup();
    const fetchMock = await openDetail({
      'GET /api/weekly-reports': () =>
        jsonResponse(200, { today: '2026-10-26', course: COURSE_DETAIL.course, items: [] }),
    });
    await user.click(screen.getByRole('button', { name: 'Xem báo cáo tuần môn CNTT1188' }));
    expect(await screen.findByRole('dialog', { name: /Báo cáo tuần CNTT1188/ })).toBeVisible();
    expect(callsTo(fetchMock, '/api/weekly-reports').at(-1).get('course_id')).toBe('CNTT1188');
  });

  it('e) biểu đồ nhỏ theo tuần có nhãn và bảng cho trình đọc màn hình', async () => {
    await openDetail();
    // D-315 (CR-13b): biểu đồ vẽ bằng Recharts; jsdom không có kích thước nên không có SVG để đếm
    // điểm. Trục 0–10, ngưỡng và nhãn tuần kiểm ở e2e (predictionCr13.spec.mjs).
    expect(
      screen.getByRole('img', { name: /^Điểm dự kiến theo tuần: tuần 1: 8,07;/ }),
    ).toBeInTheDocument();
    const table = screen.getByRole('table', { name: 'Điểm dự kiến theo tuần' });
    expect(within(table).getAllByRole('row')).toHaveLength(9);
    expect(table).toHaveTextContent('Tuần 86,78');
  });

  it('f) Lộ trình cải thiện – sắp có; g) dòng tham khảo', async () => {
    await openDetail();
    expect(screen.getByRole('heading', { name: 'Lộ trình cải thiện – sắp có' })).toBeVisible();
    expect(
      screen.getByText(/^Dự kiến chỉ mang tính tham khảo, dựa trên dữ liệu mô phỏng\./),
    ).toBeVisible();
  });

  it('không đủ điều kiện dự thi: không hiện điểm, không có thành phần và mốc cần đạt', async () => {
    await openDetail({
      'GET /api/m11/courses/CNTT1188/prediction': () =>
        jsonResponse(200, {
          ...COURSE_DETAIL,
          prediction: {
            ...COURSE_DETAIL.prediction,
            ...prediction('barred', null, null, [
              {
                code: 'attendance_absent',
                level: 'barred',
                text: 'Vắng 3 buổi không phép – không đủ điều kiện dự thi',
              },
            ]),
            targets: [],
            weekly: [],
          },
        }),
    });
    const summary = document.querySelector('.prediction-summary');
    expect(summary).toHaveTextContent('Không đủ điều kiện dự thi');
    expect(summary).toHaveTextContent('Vắng 3 buổi không phép – không đủ điều kiện dự thi');
    expect(summary).not.toHaveTextContent('6,78');
    expect(screen.queryByRole('table', { name: 'Thành phần điểm dự kiến' })).toBeNull();
    expect(screen.queryByRole('heading', { name: 'Cuối kỳ cần bao nhiêu điểm' })).toBeNull();
  });

  it('chưa đủ dữ liệu', async () => {
    await openDetail({
      'GET /api/m11/courses/CNTT1188/prediction': () =>
        jsonResponse(200, {
          ...COURSE_DETAIL,
          latest: null,
          prediction: { ...COURSE_DETAIL.prediction, ...prediction('insufficient'), weekly: [] },
        }),
    });
    expect(document.querySelector('.prediction-summary')).toHaveTextContent('Chưa đủ dữ liệu');
    expect(screen.getByText('Chưa có dữ liệu LMS của môn này.')).toBeVisible();
    expect(screen.queryByRole('img', { name: /Điểm dự kiến theo tuần/ })).toBeNull();
  });

  it('môn không thuộc sinh viên: báo lỗi của máy chủ, có liên kết quay lại', async () => {
    m11Api('student', {
      'GET /api/m11/courses/KHAC/prediction': () =>
        apiError(404, 'NOT_FOUND', 'Không tìm thấy dữ liệu.'),
    });
    renderApp('/m11/phan-tich/mon/KHAC');
    expect(await screen.findByText('Không tải được môn học')).toBeVisible();
    expect(screen.getByText(/Không tìm thấy dữ liệu\./)).toBeVisible();
    expect(document.querySelector('.back-link')).toHaveAttribute('href', '/m11/phan-tich');
  });

  it('liên kết quay lại giữ ?student=', async () => {
    m11Api('advisor');
    renderApp('/m11/phan-tich/mon/CNTT1188?student=SV04');
    await screen.findByRole('heading', { level: 1, name: 'Lập trình Web' });
    expect(document.querySelector('.back-link')).toHaveAttribute(
      'href',
      expect.stringMatching(/^\/m11\/phan-tich\?student=SV04/),
    );
  });
});

describe('percentText: trọng số thành phần trăm, không qua số (Q78)', () => {
  it.each([
    ['0.10', '10%'],
    ['0.40', '40%'],
    ['0.05', '5%'],
    ['1.00', '100%'],
    ['0.00', '0%'],
    ['0.45', '45%'],
  ])('%s → %s', (weight, text) => {
    expect(percentText(weight)).toBe(text);
  });
});
