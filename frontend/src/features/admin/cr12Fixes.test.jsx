/**
 * Phản hồi CR-11, các sửa nhỏ đầu CR-12 (bổ sung D-309):
 * B1 giờ hệ thống ghi "(giờ thật)" khi có ngày demo; B3 trang LMS Demo ẩn ô chọn sinh viên của
 * thanh trên cùng; B4 ô ngày của form có thêm chữ dd/mm/yyyy.
 */
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it } from 'vitest';
import { identityFor, jsonResponse, renderApp } from '../../test/fakeApi';
import { systemTimeText } from '../m11/SystemTime';
import { m11Api } from '../m11/testData';

const OPTIONS = {
  today: '2026-10-26',
  semester: { id: 'S5', name: 'HK1 2026-2027', start_date: '2026-09-01', end_date: '2027-01-15' },
  students: [
    {
      id: 'NEU-KHMT-001',
      student_code: 'NEU-KHMT-001',
      full_name: 'Nguyễn Thiện Nhân',
      courses: [{ id: 'CNTT9999', code: 'CNTT9999', name: 'Môn chưa có lịch', schedule: null }],
    },
  ],
};

const NOTIFICATIONS = { items: [], unread_count: 0, page: 1, page_size: 20, total: 0, note: '' };

function api(role, demoToday, extra = {}) {
  return m11Api(role, {
    'GET /api/auth/me': () => jsonResponse(200, { ...identityFor(role), demo_today: demoToday }),
    'GET /api/lms/form-options': () => jsonResponse(200, OPTIONS),
    'GET /api/notifications': () => jsonResponse(200, NOTIFICATIONS),
    ...extra,
  });
}

afterEach(() => window.localStorage.clear());

describe('B1: giờ hệ thống khi có ngày demo', () => {
  it('có DEMO_TODAY: dòng tham chiếu ghi "Tính lúc (giờ thật)" và "Ngày hệ thống"', async () => {
    api('student', '2026-10-26');
    renderApp('/m11/phan-tich');
    const line = await screen.findByText(/Kỳ tham chiếu/);
    expect(line).toHaveTextContent('Tính lúc (giờ thật)');
    expect(line).toHaveTextContent('Ngày hệ thống 26/10/2026');
    expect(line).not.toHaveTextContent('Cập nhật');
  });

  it('không có DEMO_TODAY: giữ "Cập nhật", không có "(giờ thật)"', async () => {
    api('student', null);
    renderApp('/m11/phan-tich');
    const line = await screen.findByText(/Kỳ tham chiếu/);
    expect(line).toHaveTextContent('Cập nhật');
    expect(line).not.toHaveTextContent('giờ thật');
  });
});

describe('B1: chữ giờ hệ thống dùng chung (chứng chỉ, minh chứng, làm lại bài)', () => {
  it('thêm "(giờ thật)" chỉ khi có ngày demo và có giờ', () => {
    expect(systemTimeText('2026-11-09T03:05:00Z', '2026-10-26')).toMatch(/ \(giờ thật\)$/);
    expect(systemTimeText('2026-11-09T03:05:00Z', null)).not.toMatch(/giờ thật/);
    expect(systemTimeText(null, '2026-10-26')).not.toMatch(/giờ thật/);
  });
});

describe('B3: một ô chọn sinh viên ở trang LMS Demo', () => {
  it('trang LMS Demo không có ô chọn sinh viên của thanh trên cùng', async () => {
    api('admin', '2026-10-26');
    renderApp('/quan-tri/lms-demo');
    expect(await screen.findByLabelText('Sinh viên nhận dữ liệu')).toBeInTheDocument();
    const topbar = screen.getByRole('banner');
    expect(within(topbar).queryByLabelText('Sinh viên')).toBeNull();
    expect(within(topbar).queryByLabelText('Tìm sinh viên')).toBeNull();
  });

  it('trang khác vẫn có ô chọn sinh viên của thanh trên cùng', async () => {
    api('admin', '2026-10-26');
    renderApp('/m11/phan-tich');
    const topbar = await screen.findByRole('banner');
    expect(await within(topbar).findByLabelText('Sinh viên')).toBeInTheDocument();
  });
});

describe('B4: ô ngày của form LMS Demo', () => {
  it('ghi thêm ngày đã chọn dạng dd/mm/yyyy, đổi theo ô', async () => {
    const user = userEvent.setup();
    api('admin', '2026-10-26');
    renderApp('/quan-tri/lms-demo');
    const input = await screen.findByLabelText('Giả lập ngày hôm nay');
    expect(screen.getByText('Ngày đã chọn: 26/10/2026')).toBeInTheDocument();
    await user.clear(input);
    await user.type(input, '2026-10-27');
    expect(screen.getByText('Ngày đã chọn: 27/10/2026')).toBeInTheDocument();
  });
});
