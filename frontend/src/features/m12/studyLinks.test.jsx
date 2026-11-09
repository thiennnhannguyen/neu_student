/** D-324: ô "Tự học ngoài chương trình" gắn link học W3Schools nếu W3Schools có bài. */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { cwd } from 'node:process';
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import CareerProjects from './CareerProjects';
import { studyLink } from './studyLinks';

const careers = JSON.parse(
  readFileSync(resolve(cwd(), '../backend/app/seed/fixtures_demo_k68/careers.json'), 'utf8'),
).careers;
const backend = careers.find((career) => career.slug === 'backend-developer').self_study;

describe('Link học W3Schools (D-324)', () => {
  it('Backend: ô có bài W3Schools là liên kết mở tab mới, ô không có bài để chữ thường', () => {
    render(
      <CareerProjects
        nodes={[]}
        selfStudy={backend}
        student={{ isStudent: true }}
        onChanged={() => {}}
      />,
    );
    const block = screen.getByRole('region', { name: 'Tự học ngoài chương trình' });
    const links = within(block).getAllByRole('link');
    expect(links.map((link) => [link.textContent, link.getAttribute('href')])).toEqual([
      [
        'Flask/FastAPI/Django hoặc Spring Boot (W3Schools, mở tab mới)',
        'https://www.w3schools.com/django/',
      ],
      ['HTTP/REST (W3Schools, mở tab mới)', 'https://www.w3schools.com/tags/ref_httpmethods.asp'],
      ['PostgreSQL (W3Schools, mở tab mới)', 'https://www.w3schools.com/postgresql/'],
      ['Git (W3Schools, mở tab mới)', 'https://www.w3schools.com/git/'],
      [
        'OWASP API Security (W3Schools, mở tab mới)',
        'https://www.w3schools.com/cybersecurity/cybersecurity_web_applications.php',
      ],
    ]);
    for (const link of links) {
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    }
    for (const plain of ['ORM', 'Redis', 'OAuth/JWT', 'Docker', 'pytest/JUnit', 'CI/CD']) {
      const item = within(block).getByText(plain);
      expect(item.tagName).toBe('LI');
      expect(within(item).queryByRole('link')).toBeNull();
    }
  });

  it('mọi link đều trỏ W3Schools và mỗi nghề có ít nhất một ô gắn link', () => {
    for (const career of careers) {
      const hrefs = career.self_study.map(studyLink).filter(Boolean);
      expect(hrefs.length, career.slug).toBeGreaterThan(0);
      for (const href of hrefs) {
        expect(href.startsWith('https://www.w3schools.com/')).toBe(true);
      }
    }
    expect(studyLink('Docker')).toBeNull();
    expect(studyLink('Không có')).toBeNull();
  });
});
