/** CR-13b (D-315): đường dẫn phân cấp của trang chi tiết môn, dữ liệu biểu đồ theo tuần. */
import { screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { pageMetaFor } from '../../components/menu';
import { renderApp } from '../../test/fakeApi';
import { toWeeklyData } from './CourseDetailPage';
import { COURSE_DETAIL, m11Api } from './testData';

describe('đường dẫn phân cấp trang chi tiết môn', () => {
  it('Tổng quan / Học tập / Phân tích & Cảnh báo / <tên môn>, liên kết giữ ?student=', async () => {
    m11Api('advisor');
    renderApp('/m11/phan-tich/mon/CNTT1188?student=SV04');
    await screen.findByRole('heading', { level: 1, name: 'Lập trình Web' });
    const trail = screen.getByRole('navigation', { name: 'Vị trí trang' });
    expect(await within(trail).findByText('Lập trình Web')).toBeInTheDocument();
    expect(
      within(trail)
        .getAllByRole('listitem')
        .map((item) => item.textContent),
    ).toEqual(['Tổng quan', 'Học tập', 'Phân tích & Cảnh báo', 'Lập trình Web']);
    expect(within(trail).getByRole('link', { name: 'Phân tích & Cảnh báo' })).toHaveAttribute(
      'href',
      '/m11/phan-tich?student=SV04',
    );
  });

  it('chưa tải xong: nhãn chung "Chi tiết môn"; trang khác không bị nhãn cũ', () => {
    expect(pageMetaFor('/m11/phan-tich/mon/X').trail.at(-1).label).toBe('Chi tiết môn');
    expect(pageMetaFor('/m11/phan-tich').trail.at(-1).label).toBe('Phân tích & Cảnh báo');
  });

  it('rời trang chi tiết thì đường dẫn phân cấp không còn tên môn', async () => {
    m11Api('student');
    renderApp('/m11/phan-tich/mon/CNTT1188');
    await screen.findByRole('heading', { level: 1, name: 'Lập trình Web' });
    const back = document.querySelector('.back-link');
    back.click();
    await screen.findByRole('table', { name: 'Môn đang học và điểm dự kiến' });
    const trail = screen.getByRole('navigation', { name: 'Vị trí trang' });
    expect(trail).not.toHaveTextContent('Lập trình Web');
  });
});

describe('dữ liệu biểu đồ theo tuần', () => {
  it('nhãn từng tuần T1…T8, giá trị vẽ = plot ÷ 100, nhãn hiển thị là chuỗi gốc', () => {
    const data = toWeeklyData(COURSE_DETAIL.prediction.weekly);
    expect(data.map((point) => point.label)).toEqual([
      'T1',
      'T2',
      'T3',
      'T4',
      'T5',
      'T6',
      'T7',
      'T8',
    ]);
    expect(data[0]).toEqual({ label: 'T1', name: 'Tuần 1', raw: '8.07', plotted: 8.07 });
    expect(data.at(-1).plotted).toBe(6.78);
  });

  it('bỏ tuần không có điểm (không đủ điều kiện, chưa đủ dữ liệu)', () => {
    const weekly = [
      { week_no: 1, as_of: '2026-09-01', score: '7.00', plot: 700, level: 'ok' },
      { week_no: 2, as_of: '2026-09-08', score: null, plot: null, level: 'barred' },
    ];
    expect(toWeeklyData(weekly).map((point) => point.label)).toEqual(['T1']);
  });
});
