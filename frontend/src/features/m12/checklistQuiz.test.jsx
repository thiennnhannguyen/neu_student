/** D-318: Checklist – kỹ năng có bài kiểm tra mô-đun chỉ có dấu tick (đạt) hoặc ô vuông trống. */
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import CareerProjects from './CareerProjects';

const skill = (id, title, status) => ({
  id: `n-${id}`,
  kind: 'skill',
  skill_id: id,
  title,
  status,
});

const NODES = [
  {
    id: 'stage',
    children: [
      skill('s1', 'Mô-đun 1: Nền tảng lập trình', 'done'),
      skill('s3', 'Mô-đun 3: Cơ sở dữ liệu', 'not_started'),
      skill('s9', 'Mô-đun 9: Bảo mật', 'pending'),
      skill('x', 'Viết báo cáo', 'not_started'),
    ],
  },
];

function renderList() {
  render(
    <CareerProjects
      nodes={NODES}
      selfStudy={[]}
      student={{ isStudent: true }}
      onChanged={() => {}}
      moduleSkillIds={new Set(['s1', 's3', 's9'])}
    />,
  );
  const list = screen.getByRole('region', { name: 'Checklist sẵn sàng thực tập' });
  return (name) => within(list).getByText(name).closest('li');
}

describe('Checklist: kỹ năng có bài kiểm tra mô-đun (D-318)', () => {
  it('không còn dòng "Đạt qua bài kiểm tra, xem tab Khung năng lực"', () => {
    renderList();
    expect(screen.queryByText(/Đạt qua bài kiểm tra/)).toBeNull();
  });

  it('đã đạt: dấu tick tròn; chưa đạt (kể cả đang chờ): ô vuông trống', () => {
    const row = renderList();
    const done = within(row('Mô-đun 1: Nền tảng lập trình')).getByRole('img', {
      name: 'Đã đạt',
    });
    expect(done).toHaveClass('quiz-mark--done');
    expect(done.querySelector('svg')).not.toBeNull();
    for (const name of ['Mô-đun 3: Cơ sở dữ liệu', 'Mô-đun 9: Bảo mật']) {
      const box = within(row(name)).getByRole('img', {
        name: 'Chưa đạt – làm bài kiểm tra ở tab Khung năng lực',
      });
      expect(box).not.toHaveClass('quiz-mark--done');
      expect(box).toBeEmptyDOMElement();
    }
  });

  it('ô vuông không bấm được: không có ô đánh dấu hay nút ở dòng mô-đun', () => {
    const row = renderList();
    for (const name of ['Mô-đun 1: Nền tảng lập trình', 'Mô-đun 3: Cơ sở dữ liệu']) {
      expect(within(row(name)).queryByRole('checkbox')).toBeNull();
      expect(within(row(name)).queryByRole('button')).toBeNull();
    }
  });

  it('kỹ năng không có bài kiểm tra vẫn nộp minh chứng như cũ', () => {
    const row = renderList();
    expect(
      within(row('Viết báo cáo')).getByRole('img', { name: 'Chưa có minh chứng' }),
    ).toBeVisible();
    expect(
      within(row('Viết báo cáo')).getByRole('button', { name: 'Nộp minh chứng' }),
    ).toBeVisible();
  });
});
