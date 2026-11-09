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

describe('Link học W3Schools (D-324) và tài liệu chính thức (D-331)', () => {
  it('Backend: mọi ô đều là liên kết mở tab mới, ghi nguồn; W3Schools trước, còn lại tài liệu chính thức', () => {
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
    // D-331 thay kỳ vọng D-324 ("ORM, Redis, OAuth/JWT, Docker, pytest/JUnit, CI/CD để chữ thường").
    expect(links.map((link) => [link.textContent, link.getAttribute('href')])).toEqual([
      [
        'Flask/FastAPI/Django hoặc Spring Boot (W3Schools, mở tab mới)',
        'https://www.w3schools.com/django/',
      ],
      ['HTTP/REST (W3Schools, mở tab mới)', 'https://www.w3schools.com/tags/ref_httpmethods.asp'],
      ['PostgreSQL (W3Schools, mở tab mới)', 'https://www.w3schools.com/postgresql/'],
      [
        'ORM (SQLAlchemy Docs, mở tab mới)',
        'https://docs.sqlalchemy.org/en/21/orm/quickstart.html',
      ],
      ['Redis (Redis Docs, mở tab mới)', 'https://redis.io/docs/latest/get-started/'],
      ['OAuth/JWT (RFC 7519, mở tab mới)', 'https://datatracker.ietf.org/doc/html/rfc7519'],
      ['Docker (Docker Docs, mở tab mới)', 'https://docs.docker.com/get-started/introduction/'],
      ['Git (W3Schools, mở tab mới)', 'https://www.w3schools.com/git/'],
      [
        'pytest/JUnit (pytest Docs, mở tab mới)',
        'https://docs.pytest.org/en/stable/getting-started.html',
      ],
      ['CI/CD (GitHub Actions Docs, mở tab mới)', 'https://docs.github.com/en/actions'],
      [
        'OWASP API Security (W3Schools, mở tab mới)',
        'https://www.w3schools.com/cybersecurity/cybersecurity_web_applications.php',
      ],
    ]);
    for (const link of links) {
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    }
  });

  it('mỗi nghề có ít nhất một ô gắn link; link W3Schools ghi nguồn W3Schools; mọi link https', () => {
    for (const career of careers) {
      const links = career.self_study.map(studyLink).filter(Boolean);
      expect(links.length, career.slug).toBeGreaterThan(0);
      for (const { href, source } of links) {
        expect(href.startsWith('https://')).toBe(true);
        expect(href.startsWith('https://www.w3schools.com/')).toBe(source === 'W3Schools');
      }
    }
    // Có bài W3Schools thì không dùng tài liệu chính thức.
    expect(studyLink('Git').source).toBe('W3Schools');
    // Mục chung chung không có tài liệu chính thức rõ: chữ thường.
    for (const plain of ['testing cơ bản', 'RAG', 'IAM', 'storytelling with data', 'Không có']) {
      expect(studyLink(plain), plain).toBeNull();
    }
  });
});
