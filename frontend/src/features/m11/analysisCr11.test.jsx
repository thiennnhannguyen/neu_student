/** CR-11 (D-310): trang gộp Phân tích & Cảnh báo, chuyển hướng /m11/canh-bao, menu một mục. */
import { screen, waitFor, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { apiError, jsonResponse, renderApp } from '../../test/fakeApi';
import { callsTo, CURRENT_COURSES, m11Api } from './testData';

const search = () => screen.getByTestId('search').textContent;
const path = () => screen.getByTestId('path').textContent;

describe('Phân tích & Cảnh báo', () => {
  it('một h1, khối Cảnh báo học vụ giữ nguyên và danh sách môn đang học', async () => {
    m11Api('student');
    renderApp('/m11/phan-tich');

    expect(await screen.findByRole('heading', { level: 1 })).toHaveTextContent(
      'Phân tích & Cảnh báo',
    );
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1);
    expect(screen.getByRole('heading', { name: 'Cảnh báo học vụ' })).toBeInTheDocument();
    expect(await screen.findByText('Mức chung')).toBeInTheDocument();
    const table = await screen.findByRole('table', {
      name: 'Môn đang học và dữ liệu LMS mới nhất',
    });
    const rows = within(table).getAllByRole('row').slice(1);
    expect(rows).toHaveLength(2);
    expect(rows[0]).toHaveTextContent('CNTT1188');
    expect(rows[0]).toHaveTextContent('Thứ 4');
    expect(rows[0]).toHaveTextContent('Tuần 8 (21/10/2026–27/10/2026)');
    expect(rows[0]).toHaveTextContent('1/8 buổi, 1 có phép');
    expect(rows[0]).toHaveTextContent('4/7 đã nộp · 3 quá hạn · 1 nộp muộn');
    // D-313: điểm bài tập hiện tại tính bài quá hạn là 0 (không còn 7,75).
    expect(rows[0]).toHaveTextContent('4,43');
    expect(rows[0]).toHaveTextContent('7,50');
    expect(rows[0]).toHaveTextContent('4,81');
    expect(rows[1]).toHaveTextContent('Chưa có mã');
    expect(rows[1]).toHaveTextContent('Chưa có dữ liệu LMS');
    expect(rows[1]).toHaveTextContent('Chưa có lịch');
    expect(screen.getByText(/Ngày hệ thống: 26\/10\/2026/)).toBeInTheDocument();
  });

  it('không còn các khối M11-04 đến M11-08, không gọi API của chúng', async () => {
    const fetchMock = m11Api('student');
    renderApp('/m11/phan-tich');
    await screen.findByRole('table', { name: 'Môn đang học và dữ liệu LMS mới nhất' });

    for (const title of [
      'Xu hướng GPA',
      'Tiến độ tín chỉ',
      'Đối chiếu chương trình đào tạo',
      'Điểm mạnh và điểm yếu',
      'So sánh hai kỳ',
    ]) {
      expect(screen.queryByText(title)).toBeNull();
    }
    for (const api of ['gpa-trend', 'credits', 'curriculum-check', 'strengths', 'compare']) {
      expect(callsTo(fetchMock, `/api/m11/${api}`)).toEqual([]);
    }
  });

  it('kỳ đã qua: khối cảnh báo theo kỳ đó, danh sách môn đang học chỉ có ở kỳ hiện tại', async () => {
    const fetchMock = m11Api('student');
    renderApp('/m11/phan-tich?semester=S4');

    expect(await screen.findByText(/chỉ có ở kỳ hiện tại/)).toBeInTheDocument();
    expect(screen.queryByRole('table', { name: /Môn đang học/ })).toBeNull();
    await waitFor(() =>
      expect(callsTo(fetchMock, '/api/m11/risks').at(-1).get('semester_id')).toBe('S4'),
    );
  });

  it('kỳ hiện tại chưa có môn đang học: trạng thái rỗng', async () => {
    m11Api('student', {
      'GET /api/m11/current-courses': () => jsonResponse(200, { ...CURRENT_COURSES, items: [] }),
    });
    renderApp('/m11/phan-tich');
    expect(await screen.findByText('Kỳ này chưa có môn đang học')).toBeInTheDocument();
  });

  it('lỗi tải môn đang học: báo lỗi, khối cảnh báo vẫn hiện', async () => {
    m11Api('student', {
      'GET /api/m11/current-courses': () => apiError(500, 'INTERNAL_ERROR', 'Lỗi'),
    });
    renderApp('/m11/phan-tich');
    expect(await screen.findByText('Không tải được các môn đang học')).toBeInTheDocument();
    expect(await screen.findByText('Mức chung')).toBeInTheDocument();
  });

  it('cố vấn xem sinh viên đã chọn: gửi student_id', async () => {
    const fetchMock = m11Api('advisor');
    renderApp('/m11/phan-tich?student=SV04');
    await screen.findByRole('table', { name: /Môn đang học/ });
    expect(callsTo(fetchMock, '/api/m11/current-courses').at(-1).get('student_id')).toBe('SV04');
  });
});

describe('chuyển hướng và menu (D-310)', () => {
  it('/m11/canh-bao chuyển sang /m11/phan-tich, giữ ?student= và ?semester=', async () => {
    m11Api('admin');
    renderApp('/m11/canh-bao?student=SV04&semester=S4');
    await waitFor(() => expect(path()).toBe('/m11/phan-tich'));
    expect(new URLSearchParams(search()).get('student')).toBe('SV04');
    expect(new URLSearchParams(search()).get('semester')).toBe('S4');
    expect(await screen.findByRole('heading', { name: 'Phân tích & Cảnh báo' })).toBeTruthy();
  });

  it('menu chỉ còn một mục cho Phân tích và Cảnh báo', async () => {
    m11Api('student');
    renderApp('/');
    const nav = await screen.findByRole('navigation', { name: 'Menu chính' });
    expect(within(nav).getByRole('link', { name: 'Phân tích & Cảnh báo' })).toHaveAttribute(
      'href',
      '/m11/phan-tich',
    );
    expect(within(nav).queryByRole('link', { name: 'Cảnh báo' })).toBeNull();
    expect(within(nav).queryByRole('link', { name: 'Phân tích' })).toBeNull();
  });
});
