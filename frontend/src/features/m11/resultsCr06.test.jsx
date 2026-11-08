/** CR-06: trang Kết quả theo ảnh mẫu – cột Chi tiết, dòng Tổng kết học kì, không còn nút Học lại. */
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { jsonResponse, renderApp } from '../../test/fakeApi';
import { ATTEMPTS, callsTo, gradeRow, gradesBody, m11Api } from './testData';

const SUMMARY = { credits: 14, score_10: '7.40', grade_4: '3.18' };

function grades(items, overrides = {}) {
  return { 'GET /api/m11/grades': () => jsonResponse(200, gradesBody(items, overrides)) };
}

const columnHeaders = (table) =>
  within(table)
    .getAllByRole('columnheader')
    .map((cell) => cell.textContent);

describe('CR-06 Kết quả', () => {
  it('đủ cột như ảnh mẫu, cột cuối là Chi tiết', async () => {
    m11Api('student');
    renderApp('/m11/ket-qua');
    const table = await screen.findByRole('table');
    expect(columnHeaders(table)).toEqual([
      'Mã môn',
      'Tên môn',
      'Tín chỉ',
      'Học kỳ',
      'Điểm hệ 10',
      'Điểm chữ',
      'Hệ 4',
      'Trạng thái',
      'Chi tiết',
    ]);
  });

  it('dòng học lại trông như dòng thường: không có nút Học lại trong ô tên môn', async () => {
    m11Api('student', grades([gradeRow({ name: 'Giải tích', has_retake: true })]));
    renderApp('/m11/ket-qua');
    const table = await screen.findByRole('table');
    expect(within(table).queryByRole('button', { name: /Học lại|lịch sử học lại/ })).toBeNull();
    expect(within(table).queryByText('Học lại')).toBeNull();
  });

  it('dòng có cảnh báo dữ liệu không còn biểu tượng Cảnh báo dữ liệu trong ô tên môn', async () => {
    m11Api(
      'student',
      grades([gradeRow({ data_warnings: [{ code: 'MISSING_CODE', message: 'Môn chưa có mã.' }] })]),
    );
    renderApp('/m11/ket-qua');
    const table = await screen.findByRole('table');
    expect(within(table).queryByRole('button', { name: 'Cảnh báo dữ liệu' })).toBeNull();
    expect(within(table).queryByText('Môn chưa có mã.')).toBeNull();
  });

  it('mọi dòng có nút Chi tiết; bấm thì mở bảng điểm thành phần theo từng lần học, bấm lại thì đóng', async () => {
    const fetchMock = m11Api('admin', {
      ...grades([
        gradeRow({ course_id: 'MAU101', code: 'MAU101', name: 'Giải tích', has_retake: true }),
        gradeRow({ course_id: 'CNT101', code: 'CNT101', name: 'Nhập môn' }),
      ]),
      'GET /api/m11/grades/MAU101/attempts': () => jsonResponse(200, ATTEMPTS),
    });
    const user = userEvent.setup();
    renderApp('/m11/ket-qua?student=SV02');
    const table = await screen.findByRole('table');

    expect(
      within(table).getByRole('button', { name: 'Chi tiết Nhập môn (CNT101)' }),
    ).toHaveAttribute('aria-expanded', 'false');
    const toggle = within(table).getByRole('button', { name: 'Chi tiết Giải tích (MAU101)' });
    await user.click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'true');

    const region = await screen.findByRole('region', {
      name: 'Chi tiết học phần: MAU101 - Giải tích',
    });
    expect(toggle).toHaveAttribute('aria-controls', region.closest('td').id);
    const detail = await within(region).findByRole('table');
    const rows = within(detail)
      .getAllByRole('row')
      .map((row) => [...row.children].map((cell) => cell.textContent));
    expect(rows[0].slice(0, 3)).toEqual(['STT', 'Tên thành phần', 'Trọng số']);
    expect(rows[0].slice(3).map((text) => text.slice(0, 10))).toEqual([
      'Điểm lần 1',
      'Điểm lần 2',
      'Điểm lần 3',
    ]);
    expect(rows[0][4]).toContain('HK1 2025-2026');
    expect(rows[0][4]).toContain('Lần được tính');
    expect(rows.slice(1)).toEqual([
      ['1', 'Điểm Chuyên cần', '10%', '', '10', ''],
      ['2', 'Điểm Kiểm tra thường xuyên 1', '40%', '', '8', ''],
      ['3', 'Điểm thi kết thúc học phần', '50%', '', '8,75', ''],
    ]);
    expect(detail.querySelector('tfoot')).toBeNull();
    expect(callsTo(fetchMock, '/api/m11/grades/MAU101/attempts')[0].get('student_id')).toBe('SV02');
    expect(callsTo(fetchMock, '/api/m11/grades/CNT101/attempts')).toHaveLength(0);

    await user.click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByRole('region', { name: /Chi tiết học phần/ })).toBeNull();
  });

  it('dòng Tổng kết học kì: tổng tín chỉ, điểm hệ 10, hệ 4 đúng dưới cột', async () => {
    m11Api('student', grades([gradeRow()], { semester_summary: SUMMARY }));
    renderApp('/m11/ket-qua?semester=S4');
    const table = await screen.findByRole('table');
    const footer = table.querySelector('tfoot tr');
    expect(within(footer).getByRole('rowheader')).toHaveTextContent('Tổng kết học kì');
    const headers = columnHeaders(table);
    const cells = [...footer.children];
    const at = (header) => {
      let column = 0;
      for (const cell of cells) {
        const span = Number(cell.getAttribute('colspan') ?? 1);
        if (column === headers.indexOf(header)) {
          return cell.textContent;
        }
        column += span;
      }
      return null;
    };
    expect(at('Tín chỉ')).toBe('14');
    expect(at('Điểm hệ 10')).toBe('7,40');
    expect(at('Hệ 4')).toBe('3,18');
  });

  it('không có dòng tổng kết khi xem tất cả các kỳ', async () => {
    m11Api('student', grades([gradeRow()], { semester_summary: null }));
    renderApp('/m11/ket-qua');
    const table = await screen.findByRole('table');
    expect(table.querySelector('tfoot')).toBeNull();
  });

  it('kỳ hiện tại chưa có điểm: vẫn có dòng Tổng kết học kì, các ô để trống', async () => {
    m11Api(
      'student',
      grades([gradeRow()], { semester_summary: { credits: 0, score_10: null, grade_4: null } }),
    );
    renderApp('/m11/ket-qua?semester=S5');
    const table = await screen.findByRole('table');
    const footer = table.querySelector('tfoot tr');
    expect(within(footer).getByRole('rowheader')).toHaveTextContent('Tổng kết học kì');
    const values = [...footer.querySelectorAll('td')].map((cell) => cell.textContent);
    expect(values.every((value) => value === '')).toBe(true);
  });

  it('không còn câu mô tả, chú thích trạng thái, Cảnh báo dữ liệu, dòng số môn và dòng kỳ tham chiếu ở mọi kỳ', async () => {
    const meta = {
      reference_semester: 'S5',
      computed_at: '2026-11-06T03:00:00Z',
      rule_version: 'K66-mau-v1',
      data_warnings: [
        { code: 'MISSING_CODE', course_id: 'X', semester_id: null, message: 'Môn X chưa có mã.' },
      ],
    };
    for (const semester of ['S3', 'S5', 'all']) {
      m11Api('student', grades([gradeRow()], { meta }));
      const { unmount } = renderApp(`/m11/ket-qua?semester=${semester}`);
      await screen.findByRole('table');
      expect(screen.queryByText(/gồm cả môn chưa học/)).toBeNull();
      expect(document.querySelector('.status-legend')).toBeNull();
      expect(screen.queryByText(/^Cảnh báo dữ liệu \(/)).toBeNull();
      expect(screen.queryByText(/^\d+ môn$/)).toBeNull();
      expect(screen.queryByText(/Kỳ tham chiếu/)).toBeNull();
      expect(screen.getByText(/không phải hệ thống chính thức/)).toBeInTheDocument();
      unmount();
    }
  });

  it('kỳ có điểm nhưng không môn nào tính GPA: hệ 4 hiện gạch ngang', async () => {
    m11Api(
      'student',
      grades([gradeRow()], { semester_summary: { credits: 2, score_10: '8.00', grade_4: null } }),
    );
    renderApp('/m11/ket-qua?semester=S1');
    const table = await screen.findByRole('table');
    const footer = table.querySelector('tfoot tr');
    expect(footer.textContent).toContain('8,00');
    expect(footer.textContent).toContain('—');
  });
});
